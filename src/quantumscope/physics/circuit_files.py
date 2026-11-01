"""Versioned QuantumScope circuit interchange, limited to the simulator gate set.

OpenQASM 2 interoperation supports unitary gates in circuits.ALL, not measurement,
classical registers, arbitrary custom gates, or control flow. No silent data loss.
"""
import json
import math
from .circuits import Gate, ALL, DUAL, TRIPLE, MAX_QUBITS, parse_qasm, parse_qasm_detailed, zero
from .circuit_layout import pack_and_order, validate_columns
from .initial_states import InitialState, defaults, all_default, preparation_gates
from .blocks import Block, BlockPlacement, check_layout, flatten_with_comments
from .noise import NoiseElement, NoiseModel
from .dynamic import item_from_record

FORMAT = 'quantumscope-circuit'

def validate(n, gates):
    zero(n)
    for g in gates:
        if g.name not in ALL or len(g.targets) != (3 if g.name in TRIPLE else 2 if g.name in DUAL else 1):
            raise ValueError('Unsupported gate: ' + str(g.name))
        if len(set(g.targets)) != len(g.targets) or any(not isinstance(q, int) or q < 0 or q >= n for q in g.targets):
            raise ValueError('Invalid qubit targets')
        if not all(math.isfinite(x) for x in (g.angle,g.phi,g.lam)):
            raise ValueError('Invalid rotation angle')

def to_native(n, gates):
    validate(n, gates)
    return json.dumps({'format':FORMAT,'schema_version':1,'qubits':n,
        'operations':[{'gate':g.name,'qubits':list(g.targets), 'angle_radians':g.angle,'phi_radians':g.phi,'lambda_radians':g.lam} for g in gates]},indent=2)+'\n'

def from_native(text):
    try: obj=json.loads(text)
    except json.JSONDecodeError as exc: raise ValueError('Invalid .qscope JSON') from exc
    if not isinstance(obj, dict) or obj.get('format')!=FORMAT or obj.get('schema_version') not in (1,2):
        raise ValueError('Unsupported .qscope file format or version')
    n=obj.get('qubits'); ops=obj.get('operations')
    if type(n) is not int or not isinstance(ops,list): raise ValueError('Invalid circuit structure')
    gates=[]
    for op in ops:
        if not isinstance(op,dict) or not isinstance(op.get('gate'),str) or not isinstance(op.get('qubits'),list):
            raise ValueError('Invalid gate record')
        if any(type(q) is not int for q in op['qubits']): raise ValueError('Invalid qubit index')
        a=op.get('angle_radians',0)
        if not isinstance(a,(int,float)):raise ValueError('Invalid angle')
        gates.append(Gate(op['gate'],tuple(op['qubits']),float(a),float(op.get('phi_radians',0)),float(op.get('lambda_radians',0))))
    validate(n,gates)
    if not all_default(_initial_states(obj,n)):
        raise ValueError('This circuit uses initial states; read it with from_native_layout')
    return n,gates

def _initial_states(obj,n):
    """Initial states stored in a schema-2, 3 or 4 document (|0⟩ for schema 1)."""
    if obj.get('schema_version') in (3,4,5,6) and 'initial_states' not in obj:
        return defaults(n)
    if obj.get('schema_version') not in (2,3,4,5,6):
        if 'initial_states' in obj:raise ValueError('initial_states requires schema_version 2')
        return defaults(n)
    records=obj.get('initial_states')
    if not isinstance(records,list) or len(records)!=n:
        raise ValueError('Schema 2 files need one initial state per qubit')
    return [InitialState.from_record(r) for r in records]

def to_qasm(n, gates):
    validate(n,gates)
    lines=['OPENQASM 2.0;','include "qelib1.inc";',f'qreg q[{n}];']
    for g in gates:
        params=(f'({g.angle:.17g},{g.phi:.17g},{g.lam:.17g})' if g.name=='U' else f'({g.angle:.17g})' if g.name in ('RX','RY','RZ','P','CP') else '')
        lines.append(f'{"u3" if g.name=="U" else g.name.lower()}{params} '+','.join(f'q[{q}]' for q in g.targets)+';')
    return '\n'.join(lines)+'\n'

def from_qasm(text):
    return parse_qasm(text)

def convert(text,source_format,notes=None):
    """Convert between formats. If notes is a list, import notices are appended."""
    if source_format=='qasm':
        n,gates,measured,layout,found=from_qasm_layout(text)
        if notes is not None:notes.extend(found)
        return to_native_measured(n,gates,measured,layout=layout)
    if source_format=='qscope':
        n,gates,measured,layout=from_native_layout(text)
        if layout.get('classical') or layout.get('conditions'):
            sequence=dynamic_sequence(n,gates,layout['columns'],layout['blocks'],layout['classical'],layout['conditions'])
            return to_qasm_dynamic(n,sequence,measured,layout['initial_states'])
        states=layout['initial_states']
        if notes is not None and not all_default(states):
            notes.append('OpenQASM 2 has no initial states, so they were written as preparation gates at the start.')
        placements=[BlockPlacement(b,c,e) for b,c,e in layout['blocks']]
        free=[(g.targets[0],c,g) for g,c in zip(gates,layout['columns'])]
        flat,comments=flatten_with_comments(free,placements)
        if notes is not None and placements:
            notes.append('Blocks were written as their gates, each marked with a // block comment.')
        return to_qasm_measured(n,flat,measured,states,comments)
    raise ValueError('Unknown source format')

# Terminal measurements are deliberately distinct from unitary Gate instances.
# Legacy (unitary-only) .qscope files and OpenQASM 2 files remain compatible.
def _measure_indices(n, measured):
    measured=list(measured)
    if len(set(measured))!=len(measured) or any(type(q) is not int or q<0 or q>=n for q in measured):
        raise ValueError('Invalid terminal measurement indices')
    return sorted(measured)

def to_native_measured(n,gates,measured=(),layout=None):
    """Write a .qscope document.

    layout (optional, added in v0.4.1) is a dict with 'columns' (one column per
    operation), 'measurement_column' and 'total_columns'. It is stored as
    optional fields, so v0.4.0 can still open the file (ignoring the layout).
    layout may also hold 'initial_states' (v0.5.0). If any qubit does not
    start in |0⟩ the file is written as schema 2, which older versions refuse
    to open rather than silently simulating from |0⟩.
    """
    data=json.loads(to_native(n,gates))
    states=(layout or {}).get('initial_states')
    if states is not None:
        if len(states)!=n:raise ValueError('Need one initial state per qubit')
        if not all_default(states):
            data['schema_version']=2
            data['initial_states']=[s.to_record() for s in states]
    blocks=(layout or {}).get('blocks') or []
    if blocks:
        # Schema 3 (v0.5.1): blocks are stored with their real gates, so the file
        # does not depend on how a later version builds them. Older versions refuse it.
        placements=[BlockPlacement(b,c,bool(e)) for b,c,e in blocks]
        if (layout or {}).get('columns') is not None:
            check_layout(n,gates,list(layout['columns']),placements)
        data['schema_version']=3
        data['blocks']=[{'column':pl.col,'expanded':pl.expanded,**pl.block.to_record()} for pl in placements]
    noise=(layout or {}).get('noise') or []
    noise_model=(layout or {}).get('noise_model')
    if noise or (noise_model is not None and noise_model!=NoiseModel()):
        # Schema 4 (v0.6.0): noise changes the results, so older versions must refuse the file.
        data['schema_version']=4
        if noise_model is not None:data['noise_model']=noise_model.to_record()
        data['noise']=[{**e.to_record(),'column':c} for e,c in noise]
    example=(layout or {}).get('example')
    if example:
        data['example']=example               # optional: older versions ignore it
    classical=(layout or {}).get('classical') or []
    conditions=(layout or {}).get('conditions') or []
    if classical or conditions:
        # Schema 5 (v0.6.1): mid-circuit measurement, reset and classical conditions.
        data['schema_version']=5
        data['classical']=[{**item.to_record(),'column':c} for item,c in classical]
        data['conditions']=[]
        for key,cbit,value in conditions:
            if isinstance(cbit,(tuple,list)):
                # Schema 6 (v0.6.2): conditions on several classical bits at once.
                data['schema_version']=6
                data['conditions'].append({'row':key[0],'column':key[1],'cbits':list(cbit),'values':list(value)})
            else:
                data['conditions'].append({'row':key[0],'column':key[1],'cbit':cbit,'value':value})
    data['terminal_measurements']=_measure_indices(n,measured)
    if layout is not None:
        columns=list(layout.get('columns') or [])
        validate_columns(gates,columns)
        for op,col in zip(data['operations'],columns):op['column']=col
        mcol=layout.get('measurement_column')
        if data['terminal_measurements'] and mcol is not None:
            if type(mcol) is not int or (columns and mcol<=max(columns)):
                raise ValueError('Measurement column must follow all gate columns')
            data['measurement_column']=mcol
        total=layout.get('total_columns')
        if total is not None:
            if type(total) is not int or total<1 or total>100000:raise ValueError('Invalid total column count')
            data['total_columns']=total
    return json.dumps(data,indent=2)+'\n'

def from_native_measured(text):
    n,gates=from_native(text)
    data=json.loads(text)
    measured=_measure_indices(n,data.get('terminal_measurements',[]))
    return n,gates,measured

def _from_native_any(text):
    """(n, gates, measured, initial states, document) for schema 1 or 2."""
    try: obj=json.loads(text)
    except json.JSONDecodeError as exc: raise ValueError('Invalid .qscope JSON') from exc
    if not isinstance(obj,dict) or obj.get('format')!=FORMAT or obj.get('schema_version') not in (1,2,3,4,5,6):
        raise ValueError('Unsupported .qscope file format or version')
    n=obj.get('qubits')
    if type(n) is not int:raise ValueError('Invalid circuit structure')
    states=_initial_states(obj,n)
    plain=dict(obj);plain['schema_version']=1
    for extra in ('initial_states','blocks','noise','noise_model','classical','conditions'):plain.pop(extra,None)
    n,gates,measured=from_native_measured(json.dumps(plain))
    return n,gates,measured,states,obj

def _noise_in(obj,n):
    """(noise model, [(NoiseElement, column)]) stored in a schema-4 document."""
    if obj.get('schema_version') not in (4,5,6):
        if 'noise' in obj or 'noise_model' in obj:raise ValueError('noise requires schema_version 4')
        return NoiseModel(),[]
    model=NoiseModel.from_record(obj['noise_model']) if 'noise_model' in obj else NoiseModel()
    records=obj.get('noise',[])
    if not isinstance(records,list) or len(records)>10000:raise ValueError('Invalid noise elements')
    elements=[]
    for r in records:
        if not isinstance(r,dict) or type(r.get('column')) is not int or r['column']<0:
            raise ValueError('Invalid noise element placement')
        element=NoiseElement.from_record(r)
        if not 0<=element.qubit<n:raise ValueError('Noise element outside the circuit')
        elements.append((element,r['column']))
    return model,elements

def _classical_in(obj,n):
    """([(Measure/Reset, column)], [((row, column), cbit, value)]) in a schema-5 document."""
    if obj.get('schema_version') not in (5,6):
        if 'classical' in obj or 'conditions' in obj:raise ValueError('mid-circuit operations require schema_version 5')
        return [],[]
    items=[]
    for r in obj.get('classical',[]):
        if not isinstance(r,dict) or type(r.get('column')) is not int or r['column']<0:raise ValueError('Invalid classical placement')
        item=item_from_record(r)
        if not 0<=item.qubit<n:raise ValueError('Classical operation outside the circuit')
        items.append((item,r['column']))
    conditions=[]
    for r in obj.get('conditions',[]):
        if not isinstance(r,dict) or not all(type(r.get(k)) is int for k in ('row','column')):
            raise ValueError('Invalid classical condition')
        if 'cbits' in r:                              # several bits (schema 6)
            bits,values=r.get('cbits'),r.get('values')
            if obj.get('schema_version')!=6 or not isinstance(bits,list) or not isinstance(values,list) \
                    or not all(type(x) is int for x in bits+values):
                raise ValueError('Invalid classical condition')
            conditions.append(((r['row'],r['column']),tuple(bits),tuple(values)))
        else:
            if not all(type(r.get(k)) is int for k in ('cbit','value')):raise ValueError('Invalid classical condition')
            conditions.append(((r['row'],r['column']),r['cbit'],r['value']))
    return items,conditions

def _blocks_in(obj,n):
    if obj.get('schema_version') not in (3,4,5,6):
        if 'blocks' in obj:raise ValueError('blocks require schema_version 3')
        return []
    records=obj.get('blocks',[])                # a schema-4 file may have noise but no blocks
    if not isinstance(records,list) or len(records)>1000:raise ValueError('Invalid blocks')
    out=[]
    for r in records:
        if not isinstance(r,dict) or type(r.get('column')) is not int or r['column']<0 or not isinstance(r.get('expanded',False),bool):
            raise ValueError('Invalid block placement')
        out.append((Block.from_record(r,n),r['column'],r.get('expanded',False)))
    return out

def from_native_layout(text):
    """Return (n, gates, measured, layout).

    Files without stored columns (v0.4.0 and earlier) get a packed layout, so
    simultaneous gates share a column instead of one gate per column.
    """
    n,gates,measured,states,data=_from_native_any(text)
    blocks=_blocks_in(data,n)
    noise_model,noise=_noise_in(data,n)
    classical,conditions=_classical_in(data,n)
    stored=[op.get('column') for op in data['operations']]
    if gates and all(c is not None for c in stored):
        validate_columns(gates,stored);columns=stored
    elif any(c is not None for c in stored):
        raise ValueError('Layout columns must be given for every operation or none')
    else:
        gates,columns=pack_and_order(n,gates)
    check_layout(n,gates,columns,[BlockPlacement(b,c,e) for b,c,e in blocks])
    last=max(list(columns)+[BlockPlacement(b,c,e).end for b,c,e in blocks]+[c for _,c in noise]+[c for _,c in classical],default=-1)
    mcol=data.get('measurement_column')
    if mcol is not None and (type(mcol) is not int or mcol<=last or mcol>100000):
        raise ValueError('Invalid measurement column')
    if mcol is None:mcol=last+1
    total=data.get('total_columns')
    if total is not None and (type(total) is not int or total<1 or total>100000):
        raise ValueError('Invalid total column count')
    return n,gates,measured,{'columns':columns,'measurement_column':mcol if measured else None,'total_columns':total,
                            'initial_states':states,'blocks':blocks,'noise':noise,'noise_model':noise_model,
                            'classical':classical,'conditions':conditions,
                            'example':data.get('example') if isinstance(data.get('example'),dict) else None}

def to_qasm_measured(n,gates,measured=(),initial_states=None,comments=None):
    """OpenQASM 2 text. Non-|0⟩ initial states become preparation gates at the
    start (OpenQASM 2 has no initial-state syntax), marked with comments.
    comments maps a gate index to a comment written just before that gate
    (used to mark where each block's expanded gates begin)."""
    measured=_measure_indices(n,measured)
    prep=preparation_gates(initial_states) if initial_states is not None else []
    if initial_states is not None and len(initial_states)!=n:raise ValueError('Need one initial state per qubit')
    qasm=to_qasm(n,prep+list(gates))
    lines=qasm.rstrip().splitlines()
    if comments:
        header,body=lines[:3],lines[3:]
        marked=[]
        for i,line in enumerate(body):
            if i>=len(prep) and (i-len(prep)) in comments:
                marked.append('// '+''.join(ch if ord(ch)<128 else '?' for ch in comments[i-len(prep)]))
            marked.append(line)
        lines=header+marked
    if prep:
        ascii_label=lambda s:s.label.replace('⟩','>').replace('−','-').replace('ψ','psi')
        described=', '.join(f'q{q}={ascii_label(s)}'+('' if s.preset_key else f'(theta={s.theta:.17g}, phi={s.phi:.17g})')
                            for q,s in enumerate(initial_states) if not s.is_default)
        lines.insert(3,f'// Initial-state preparation from QuantumScope: {described}')
        lines.insert(4+len(prep),'// Circuit')
    if not measured:return '\n'.join(lines)+'\n'
    lines.insert(3,f'creg c[{n}];')
    lines.extend(f'measure q[{q}] -> c[{q}];' for q in measured)
    return '\n'.join(lines)+'\n'

def from_qasm_measured(text):
    import re
    stripped=re.sub(r'//[^\n]*','',text)
    statements=[x.strip() for x in stripped.split(';') if x.strip()]
    retained=[]; measured=[]; classical=None; terminal=False
    for item in statements:
        stmt=' '.join(item.split())
        creg=re.fullmatch(r'creg\s+(\w+)\[(\d+)\]',stmt,re.I)
        if creg:
            if classical is not None:raise ValueError('Only one classical register supported')
            classical=(creg.group(1),int(creg.group(2)))
            continue
        m=re.fullmatch(r'measure\s+(\w+)\[(\d+)\]\s*->\s*(\w+)\[(\d+)\]',stmt,re.I)
        if m:
            if classical is None or m.group(3)!=classical[0] or int(m.group(4))!=int(m.group(2)):
                raise ValueError('Only matching q[i] -> c[i] terminal measurements are supported')
            if int(m.group(2))>=classical[1]:raise ValueError('Classical bit out of range')
            terminal=True;measured.append(int(m.group(2)));continue
        if terminal:raise ValueError('Operations after measurement are unsupported')
        retained.append(item)
    n,gates=parse_qasm(';'.join(retained)+';')
    return n,gates,_measure_indices(n,measured)

def from_qasm_layout(text):
    """Return (n, gates, measured, layout, notes) for an OpenQASM 2 import.

    Gates are packed into the earliest available column; barriers start a new
    column and are reported in notes rather than dropped silently.
    """
    import re
    statements=[' '.join(x.split()) for x in re.sub(r'//[^\n]*','',text).split(';') if x.strip()]
    if _is_dynamic_qasm(statements):
        return from_qasm_dynamic(text)
    n,gates,measured=from_qasm_measured(text)
    # Recover barrier positions from the unitary part of the program.
    stripped=re.sub(r'//[^\n]*','',text)
    unitary=[x for x in stripped.split(';') if x.strip() and not re.match(r'\s*(creg|measure)\b',x,re.I)]
    _,_,fences,notes=parse_qasm_detailed(';'.join(unitary)+';')
    gates,columns=pack_and_order(n,gates,fences)
    last=max(columns,default=-1)
    return n,gates,measured,{'columns':columns,'measurement_column':last+1 if measured else None,'total_columns':None,'initial_states':defaults(n)},notes


# ---- dynamic circuits in OpenQASM 2 (v0.6.1) ----------------------------------------------------
# Each classical bit k becomes its own one-bit register m<k>, so that OpenQASM 2's
# register conditions `if(m1==1) …` express single-bit conditions exactly.

def dynamic_sequence(n, gates, columns, blocks=(), classical=(), conditions=()):
    """Operations in simulation order: ('gate', Gate, (cbit, value) or None), ('measure', Measure),
    ('reset', Reset) or ('comment', text). Within a column, gates come before measurements and
    resets, matching the simulator."""
    from .blocks import placed_items
    condition_of = {tuple(key): (cbit, value) for key, cbit, value in conditions}
    by_column = {}
    seen_blocks = set()
    placements = [BlockPlacement(b, c, e) for b, c, e in blocks]
    for c, r, _, g, pl in placed_items(((g.targets[0], col, g) for g, col in zip(gates, columns)), placements):
        ops = by_column.setdefault(c, [])
        if pl is not None and id(pl) not in seen_blocks:
            seen_blocks.add(id(pl))
            ops.append(('comment', f'block: {pl.block.label}'))
        ops.append(('gate', g, condition_of.get((r, c)) if pl is None else None))
    for item, c in sorted(classical, key=lambda x: (x[1], x[0].qubit)):
        by_column.setdefault(c, []).append(('measure' if hasattr(item, 'cbit') else 'reset', item))
    return [op for c in sorted(by_column) for op in by_column[c]]


def _classical_registers(sequence):
    """Map classical bits to OpenQASM 2 registers.

    Bits that appear together in a multi-bit condition share one register r<i> (OpenQASM 2
    compares whole registers); every other bit gets its own one-bit register m<k>.
    Returns {bit: (register name, index)} and {register name: size}.
    """
    from .dynamic import condition_parts
    used = set()
    parent = {}

    def find(b):
        while parent.setdefault(b, b) != b:
            b = parent[b]
        return b
    for op in sequence:
        if op[0] == 'measure':
            used.add(op[1].cbit)
        elif op[0] == 'gate' and op[2]:
            bits = condition_parts(*op[2])[0]
            used.update(bits)
            for b in bits[1:]:
                parent[find(b)] = find(bits[0])
    groups = {}
    for b in sorted(used):
        groups.setdefault(find(b), []).append(b)
    where, sizes = {}, {}
    shared = 0
    for members in sorted(groups.values()):
        if len(members) == 1:
            where[members[0]] = (f'm{members[0]}', 0)
            sizes[f'm{members[0]}'] = 1
        else:
            name = f'r{shared}'
            shared += 1
            sizes[name] = len(members)
            for j, b in enumerate(sorted(members)):
                where[b] = (name, j)
    return where, sizes


def _condition_lines(condition, where, sizes, line):
    """`if(reg==value) …;` lines for a condition. A condition on part of a shared register becomes
    one line per full-register value matching it — exactly one of them can be true."""
    from .dynamic import condition_parts
    bits, values = condition_parts(*condition)
    name = where[bits[0]][0]
    fixed = {where[b][1]: v for b, v in zip(bits, values)}
    free = [j for j in range(sizes[name]) if j not in fixed]
    lines = []
    for combo in range(1 << len(free)):
        assignment = dict(fixed)
        for k, j in enumerate(free):
            assignment[j] = (combo >> k) & 1
        value = sum(bit << j for j, bit in assignment.items())          # register bit j has weight 2^j
        lines.append(f'if({name}=={value}) {line}')
    return lines


def to_qasm_dynamic(n, sequence, measured=(), initial_states=None):
    """OpenQASM 2 for a circuit with mid-circuit measurement, conditions and reset."""
    measured = _measure_indices(n, measured)
    prep = preparation_gates(initial_states) if initial_states is not None else []
    where, sizes = _classical_registers(sequence)
    gate_line = lambda g: to_qasm(n, [g]).rstrip().splitlines()[-1]
    lines = ['OPENQASM 2.0;', 'include "qelib1.inc";', f'qreg q[{n}];']
    lines += [f'creg {name}[{size}];' for name, size in sorted(sizes.items(), key=lambda x: (x[0][0] != 'm', x[0]))]
    if measured:
        lines.append(f'creg c[{n}];')
    if prep:
        lines.append('// Initial-state preparation from QuantumScope')
        lines += [gate_line(g) for g in prep]
        lines.append('// Circuit')
    for op in sequence:
        if op[0] == 'comment':
            lines.append('// ' + ''.join(ch if ord(ch) < 128 else '?' for ch in op[1]))
        elif op[0] == 'gate':
            line = gate_line(op[1])
            lines.extend(_condition_lines(op[2], where, sizes, line) if op[2] else [line])
        elif op[0] == 'measure':
            name, j = where[op[1].cbit]
            lines.append(f'measure q[{op[1].qubit}] -> {name}[{j}];')
        else:
            lines.append(f'reset q[{op[1].qubit}];')
    lines += [f'measure q[{q}] -> c[{q}];' for q in measured]
    return '\n'.join(lines) + '\n'


def _is_dynamic_qasm(statements):
    """True for programs that need the dynamic importer (if, reset, or measurements followed
    by more operations, or into anything other than a matching c[i])."""
    import re
    seen_measure = False
    for stmt in statements:
        if re.match(r'(if\s*\(|reset\b)', stmt, re.I):
            return True
        m = re.fullmatch(r'measure\s+\w+\[(\d+)\]\s*->\s*(\w+)\[(\d+)\]', stmt, re.I)
        if m:
            seen_measure = True
            if m.group(2) != 'c' or m.group(1) != m.group(3):
                return True
        elif seen_measure and not re.match(r'(creg|barrier)\b', stmt, re.I):
            return True
    return False


def from_qasm_dynamic(text):
    """(n, gates, measured, layout, notes) for programs with mid-circuit operations.

    Single-bit conditions only: `if(r==v)` where r is a one-bit register. Operations are
    packed into the earliest column after everything they depend on.
    """
    import re
    from .dynamic import Measure, Reset
    stripped = re.sub(r'//[^\n]*', '', text)
    statements = [' '.join(x.split()) for x in stripped.split(';') if x.strip()]
    n = None
    registers = {}                       # name -> size
    bit_of = {}                          # (register, index) -> classical bit number
    ops = []                             # ('gate', Gate, cond) / ('measure', Measure) / ('reset', Reset) / ('fence',)
    header = None
    for stmt in statements:
        if re.match(r'(OPENQASM|include)\b', stmt, re.I):
            continue
        q = re.fullmatch(r'qreg\s+(\w+)\[(\d+)\]', stmt, re.I)
        if q:
            if n is not None:
                raise ValueError('Only one quantum register is supported')
            n = int(q.group(2))
            header = f'OPENQASM 2.0;include "qelib1.inc";qreg {q.group(1)}[{n}];'
            continue
        c = re.fullmatch(r'creg\s+(\w+)\[(\d+)\]', stmt, re.I)
        if c:
            registers[c.group(1)] = int(c.group(2))
            continue
        if n is None:
            raise ValueError('qreg must come before operations')
        if re.match(r'barrier\b', stmt, re.I):
            ops.append(('fence',))
            continue
        m = re.fullmatch(r'measure\s+\w+\[(\d+)\]\s*->\s*(\w+)\[(\d+)\]', stmt, re.I)
        if m:
            reg, index = m.group(2), int(m.group(3))
            if reg not in registers or index >= registers[reg]:
                raise ValueError(f'Unknown classical bit {reg}[{index}]')
            bit = bit_of.setdefault((reg, index), len(bit_of))
            ops.append(('measure', Measure(int(m.group(1)), bit)))
            continue
        r = re.fullmatch(r'reset\s+\w+\[(\d+)\]', stmt, re.I)
        if r:
            ops.append(('reset', Reset(int(r.group(1)))))
            continue
        cond = re.fullmatch(r'if\s*\(\s*(\w+)\s*==\s*(\d+)\s*\)\s*(.+)', stmt, re.I)
        condition = None
        if cond:
            reg, value, stmt = cond.group(1), int(cond.group(2)), cond.group(3)
            if reg not in registers:
                raise ValueError(f'Unknown classical register {reg}')
            size = registers[reg]
            if not 0 <= value < (1 << size):
                raise ValueError(f'{reg} has {size} bit(s), so it cannot equal {value}')
            bits = tuple(bit_of.setdefault((reg, j), len(bit_of)) for j in range(size))
            values = tuple((value >> j) & 1 for j in range(size))          # register bit j has weight 2^j
            condition = (bits[0], values[0]) if size == 1 else (bits, values)
        _, parsed = parse_qasm(header + stmt + ';')
        if len(parsed) != 1:
            raise ValueError(f'Unsupported statement: {stmt}')
        ops.append(('gate', parsed[0], condition))
    if n is None:
        raise ValueError('No quantum register')
    if len(bit_of) > 10:
        raise ValueError('At most 10 classical bits are supported')
    # Pack into columns: after the qubits' previous operations and after the measurement a
    # condition depends on (gates in a column act before that column's measurements).
    free = [0] * n
    ready = {}                           # classical bit -> first column where its value is known
    gates, columns, classical, conditions = [], [], [], []
    for op in ops:
        if op[0] == 'fence':
            top = max(free, default=0)
            free = [top] * n
            continue
        if op[0] == 'gate':
            g, condition = op[1], op[2]
            col = max(free[q] for q in g.targets)
            if condition:
                from .dynamic import condition_parts
                col = max([col] + [ready.get(b, 0) for b in condition_parts(*condition)[0]])
            gates.append(g)
            columns.append(col)
            if condition:
                conditions.append(((g.targets[0], col), *condition))
            for q in g.targets:
                free[q] = col + 1
        else:
            item = op[1]
            col = free[item.qubit]
            classical.append((item, col))
            free[item.qubit] = col + 1
            if op[0] == 'measure':
                ready[item.cbit] = col + 1
    # The editor stores gates in column order; packing follows program order (e.g. preparation
    # gates on one qubit, then a gate on another that fits into an earlier column).
    order = sorted(range(len(gates)), key=lambda i: (columns[i], gates[i].targets[0]))
    gates, columns = [gates[i] for i in order], [columns[i] for i in order]
    layout = {'columns': columns, 'measurement_column': None, 'total_columns': None,
              'initial_states': defaults(n), 'blocks': [], 'classical': classical, 'conditions': conditions}
    names = ', '.join(f'{reg}[{i}] → c{b}' for (reg, i), b in sorted(bit_of.items(), key=lambda x: x[1]))
    notes = [f'Mid-circuit operations imported; classical bits: {names}.'] if bit_of else []
    return n, gates, [], layout, notes
