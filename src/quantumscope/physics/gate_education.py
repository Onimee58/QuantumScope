"""Gate reference material; re-exports the safe angle expression parser."""
import math
import numpy as np
from .circuits import Gate, SINGLE, DUAL, TRIPLE, unitary, apply_gate

# parse_angle lives in expressions.py (shared with the QASM reader); re-exported here.
from .expressions import parse_angle  # noqa: F401

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
