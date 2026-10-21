"""Gate reference material and safe mathematical angle expression parser."""
import ast
import math
import operator
import numpy as np
from .circuits import Gate, SINGLE, DUAL, TRIPLE, unitary, apply_gate

_OP={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv}

def parse_angle(text):
    """Evaluate arithmetic in radians without eval or arbitrary function calls."""
    try:tree=ast.parse(text.strip().replace('π','pi').replace('^','**'),mode='eval')
    except (SyntaxError,ValueError) as exc:raise ValueError('Enter a valid angle, e.g. pi/2') from exc
    def parse(node):
        if isinstance(node,ast.Expression):return parse(node.body)
        if isinstance(node,ast.Constant) and type(node.value) in (int,float):return float(node.value)
        if isinstance(node,ast.Name) and node.id=='pi':return math.pi
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
            v=parse(node.operand);return v if isinstance(node.op,ast.UAdd) else -v
        if isinstance(node,ast.BinOp) and type(node.op) in _OP:return _OP[type(node.op)](parse(node.left),parse(node.right))
        if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Pow):
            base=parse(node.left);exp=parse(node.right)
            if abs(exp)>12 or abs(base)>1e6:raise ValueError('Angle expression too large')
            return base**exp
        raise ValueError('Only numbers, pi, +, -, *, /, ** and parentheses are allowed')
    try:value=float(parse(tree))
    except (OverflowError,ZeroDivisionError,TypeError) as exc:raise ValueError('Invalid or unbounded angle') from exc
    if not math.isfinite(value) or abs(value)>1e9:raise ValueError('Angle must be finite and reasonable')
    return value

DESCRIPTIONS={
'H':('Hadamard','Creates superposition and recombines probability amplitudes.','Superposition, Bell pairs, interference'),
'X':('Pauli X','Flips computational-basis states |0> and |1>.','Bit flips and reversible NOT'),
'Y':('Pauli Y','Rotates the Bloch vector by π around the y axis (up to global phase).','Pauli operations'),
'Z':('Pauli Z','Changes the phase of |1> by π.','Phase flips and interference'),
'S':('S phase','Adds a π/2 relative phase to |1>.','Clifford phase operations'),
'T':('T phase','Adds a π/4 relative phase to |1>.','Universal gate sets'),
'SDG':('S dagger','Inverse of S; adds a -π/2 phase to |1>.','Inverse phase operations'),
'TDG':('T dagger','Inverse of T; adds a -π/4 phase to |1>.','Inverse phase operations'),
'SX':('Square root of X','Two applications equal X (up to numerical precision).','Native-style single-qubit gates'),
'P':('Phase rotation','Applies phase exp(iλ) to |1>.','Interference and relative phase'),
'RX':('Rotation X','Rotates the Bloch state about the x axis by θ.','Parameterized state preparation'),
'RY':('Rotation Y','Rotates the Bloch state about the y axis by θ.','Parameterized state preparation'),
'RZ':('Rotation Z','Rotates the Bloch state about the z axis by θ.','Parameterized phase control'),
'U':('General U3','General single-qubit U(θ,φ,λ) operation.','Single-qubit synthesis'),
'CX':('Controlled X','Flips the target if the control is |1>.','Entanglement and XOR'),
'CZ':('Controlled Z','Adds phase -1 to |11>.','Entanglement and phase oracles'),
'SWAP':('SWAP','Exchanges the states of two qubits.','Qubit routing'),
'CCX':('Toffoli','Flips target if both controls are |1>.','Reversible logic and arithmetic'),
'CSWAP':('Fredkin','Swaps two targets if control is |1>.','Reversible conditional exchange'),
'M':('Measurement','Reads a terminal computational-basis measurement outcome using Born probabilities.','Readout and measurement statistics'),
}

def gate_information(name):
    name=name.upper()
    if name not in DESCRIPTIONS:raise ValueError('Unknown gate')
    title,description,uses=DESCRIPTIONS[name]
    n=3 if name in TRIPLE else 2 if name in DUAL else 1
    parameters='θ, φ, λ' if name=='U' else ('λ' if name=='P' else ('θ' if name in ('RX','RY','RZ') else 'None'))
    return {'name':name,'title':title,'description':description,'applications':uses,'qubits':n,'parameters':parameters,'measurement':name=='M'}

def transformation_rows(name,angle=math.pi/2):
    name=name.upper()
    if name=='M':return [('0','P(0)=1'),('1','P(1)=1')]
    info=gate_information(name);n=info['qubits']
    g=Gate(name,tuple(range(n)),angle)
    items=[]
    for index in range(1<<n):
        inp=np.zeros(1<<n,complex);inp[index]=1
        out=apply_gate(inp,n,g)
        expression=' + '.join(f'({z.real:+.3g}{z.imag:+.3g}j)|{j:0{n}b}>' for j,z in enumerate(out) if abs(z)>1e-8)
        items.append((f'|{index:0{n}b}>',expression))
    return items
