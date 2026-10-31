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
    if obj.get('schema_version') in (3,4,5) and 'initial_states' not in obj:
        return defaults(n)
    if obj.get('schema_version') not in (2,3,4,5):
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
    classical=(layout or {}).get('classical') or []
    conditions=(layout or {}).get('conditions') or []
    if classical or conditions:
        # Schema 5 (v0.6.1): mid-circuit measurement, reset and classical conditions.
        data['schema_version']=5
        data['classical']=[{**item.to_record(),'column':c} for item,c in classical]
        data['conditions']=[{'row':key[0],'column':key[1],'cbit':cbit,'value':value} for key,cbit,value in conditions]
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
    if not isinstance(obj,dict) or obj.get('format')!=FORMAT or obj.get('schema_version') not in (1,2,3,4,5):
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
    if obj.get('schema_version') not in (4,5):
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
    if obj.get('schema_version')!=5:
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
        if not isinstance(r,dict) or not all(type(r.get(k)) is int for k in ('row','column','cbit','value')):
            raise ValueError('Invalid classical condition')
        conditions.append(((r['row'],r['column']),r['cbit'],r['value']))
    return items,conditions

def _blocks_in(obj,n):
    if obj.get('schema_version') not in (3,4,5):
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
                            'classical':classical,'conditions':conditions}

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
    n,gates,measured=from_qasm_measured(text)
    # Recover barrier positions from the unitary part of the program.
    stripped=re.sub(r'//[^\n]*','',text)
    unitary=[x for x in stripped.split(';') if x.strip() and not re.match(r'\s*(creg|measure)\b',x,re.I)]
    _,_,fences,notes=parse_qasm_detailed(';'.join(unitary)+';')
    gates,columns=pack_and_order(n,gates,fences)
    last=max(columns,default=-1)
    return n,gates,measured,{'columns':columns,'measurement_column':last+1 if measured else None,'total_columns':None,'initial_states':defaults(n)},notes
