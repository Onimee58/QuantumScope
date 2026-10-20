"""Versioned QuantumScope circuit interchange, limited to the simulator gate set.

OpenQASM 2 interoperation supports unitary gates in circuits.ALL, not measurement,
classical registers, arbitrary custom gates, or control flow. No silent data loss.
"""
import json
import math
from .circuits import Gate, ALL, DUAL, TRIPLE, MAX_QUBITS, parse_qasm, zero

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
    if not isinstance(obj, dict) or obj.get('format')!=FORMAT or obj.get('schema_version')!=1:
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
    return n,gates

def to_qasm(n, gates):
    validate(n,gates)
    lines=['OPENQASM 2.0;','include "qelib1.inc";',f'qreg q[{n}];']
    for g in gates:
        params=(f'({g.angle:.17g},{g.phi:.17g},{g.lam:.17g})' if g.name=='U' else f'({g.angle:.17g})' if g.name in ('RX','RY','RZ','P') else '')
        lines.append(f'{"u3" if g.name=="U" else g.name.lower()}{params} '+','.join(f'q[{q}]' for q in g.targets)+';')
    return '\n'.join(lines)+'\n'

def from_qasm(text):
    return parse_qasm(text)

def convert(text,source_format):
    if source_format=='qasm':
        n,gates,measured=from_qasm_measured(text);return to_native_measured(n,gates,measured)
    if source_format=='qscope':
        n,gates,measured=from_native_measured(text);return to_qasm_measured(n,gates,measured)
    raise ValueError('Unknown source format')

# Terminal measurements are deliberately distinct from unitary Gate instances.
# Legacy (unitary-only) .qscope files and OpenQASM 2 files remain compatible.
def _measure_indices(n, measured):
    measured=list(measured)
    if len(set(measured))!=len(measured) or any(type(q) is not int or q<0 or q>=n for q in measured):
        raise ValueError('Invalid terminal measurement indices')
    return sorted(measured)

def to_native_measured(n,gates,measured=()):
    data=json.loads(to_native(n,gates))
    data['terminal_measurements']=_measure_indices(n,measured)
    return json.dumps(data,indent=2)+'\n'

def from_native_measured(text):
    n,gates=from_native(text)
    data=json.loads(text)
    measured=_measure_indices(n,data.get('terminal_measurements',[]))
    return n,gates,measured

def to_qasm_measured(n,gates,measured=()):
    measured=_measure_indices(n,measured)
    qasm=to_qasm(n,gates)
    if not measured:return qasm
    lines=qasm.rstrip().splitlines()
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
