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
'CP':('Controlled phase','Adds phase exp(iλ) to |11>; symmetric in its two qubits.','Quantum Fourier transform, phase estimation'),
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
    parameters='θ, φ, λ' if name=='U' else ('λ' if name in ('P','CP') else ('θ' if name in ('RX','RY','RZ') else 'None'))
    return {'name':name,'title':title,'description':description,'applications':uses,'qubits':n,'parameters':parameters,'measurement':name=='M'}

def transformation_rows(name,angle=math.pi/2,phi=0.0,lam=0.0):
    name=name.upper()
    if name=='M':return [('0','P(0)=1'),('1','P(1)=1')]
    info=gate_information(name);n=info['qubits']
    g=Gate(name,tuple(range(n)),angle,phi,lam)
    items=[]
    for index in range(1<<n):
        inp=np.zeros(1<<n,complex);inp[index]=1
        out=apply_gate(inp,n,g)
        terms=[(format_amplitude(z),j) for j,z in enumerate(out) if abs(z)>1e-8]
        from .display import ket
        expression=' + '.join(ket(j,n,True) if a=='1' else f'({a}){ket(j,n,True)}' for a,j in terms)
        items.append((ket(index,n,True),expression.replace('+ (-','- (')))
    return items


# --- Mathematical properties for the Gate Explorer ---------------------------

_NAMED = ((1.0,'1'),(1/math.sqrt(2),'1/√2'),(0.5,'1/2'),(math.sqrt(3)/2,'√3/2'),
          (1/(2*math.sqrt(2)),'1/(2√2)'))


def _real_text(x):
    for value,text in _NAMED:
        if abs(abs(x)-value)<1e-9:return ('-' if x<0 else '')+text
    return f'{x:.4f}'.rstrip('0').rstrip('.')


def format_amplitude(z,tol=1e-9,exact=None):
    """Readable complex amplitude: exact forms for common values (1/√2, i, ...),
    or decimals when the display number format is 'decimal' (or exact=False)."""
    from .display import OPTIONS
    re_,im=(0.0 if abs(z.real)<tol else z.real),(0.0 if abs(z.imag)<tol else z.imag)
    if re_==0 and im==0:return '0'
    if exact is False or (exact is None and OPTIONS['number_format']=='decimal'):
        d=OPTIONS['decimals']
        def num(x):
            text=f'{x:.{d}f}'.rstrip('0').rstrip('.')
            return '0' if text in ('-0','') else text
        if im==0:return num(re_)
        if re_==0:return num(im)+'i'
        return f'{num(re_)} {"+" if im>0 else "-"} {num(abs(im))}i'
    if im==0:return _real_text(re_)
    if re_==0:
        return ('-' if im<0 else '')+_imag_text(abs(im))
    return f'{_real_text(re_)} {"+" if im>0 else "-"} {_imag_text(abs(im))}'


def _imag_text(x):
    """Positive imaginary magnitude as text: i, i/√2, i√3/2, 0.25i."""
    t=_real_text(x)
    if t=='1':return 'i'
    if t.startswith('1/'):return 'i'+t[1:]
    if '/' in t:return 'i'+t
    return t+'i'


def gate_matrix(name,angle=math.pi/2,phi=0.0,lam=0.0):
    """Full matrix on qubits 0..n-1 (q0 most significant; controls first)."""
    n=gate_information(name)['qubits']
    g=Gate(name.upper(),tuple(range(n)),angle,phi,lam)
    cols=[]
    for index in range(1<<n):
        v=np.zeros(1<<n,complex);v[index]=1
        cols.append(apply_gate(v,n,g))
    return np.array(cols).T


RELATED={
'H':('X','Z','S'), 'X':('Y','Z','SX','CX'), 'Y':('X','Z','RY'), 'Z':('S','T','P','RZ','CZ'),
'S':('SDG','T','Z','P'), 'SDG':('S','TDG','Z'), 'T':('TDG','S','P'), 'TDG':('T','SDG','P'),
'SX':('X','RX','H'), 'P':('RZ','S','T','Z'), 'RX':('X','SX','U'), 'RY':('Y','U'),
'RZ':('Z','P','U'), 'U':('RX','RY','RZ','P'), 'CX':('CZ','CCX','X'), 'CZ':('CX','Z','CP'), 'CP':('CZ','P','S','T'),
'SWAP':('CSWAP','CX'), 'CCX':('CX','CSWAP'), 'CSWAP':('SWAP','CCX'),
}

_CLIFFORD={'H','X','Y','Z','S','SDG','SX','CX','CZ','SWAP'}
_IDENTITIES={
'H':'H X H = Z and H Z H = X', 'X':'X² = I; X = H Z H', 'Y':'Y = i X Z', 'Z':'Z = S², Z = H X H',
'S':'S² = Z, S = T²', 'SDG':'S† S = I', 'T':'T² = S, T⁸ = I', 'TDG':'T† T = I',
'SX':'SX² = X', 'P':'P(π) = Z, P(π/2) = S, P(π/4) = T', 'RZ':'RZ(θ) = e^(−iθ/2) P(θ)',
'U':'U(θ, −π/2, π/2) = RX(θ); U(θ, 0, 0) = RY(θ)', 'CX':'CZ = (I⊗H) CX (I⊗H)',
'CZ':'CZ is symmetric in its two qubits', 'CP':'CP(π) = CZ; CP(λ) is symmetric in its two qubits', 'SWAP':'SWAP = three alternating CX gates',
'CCX':'Toffoli is universal for reversible classical logic', 'CSWAP':'Fredkin conserves the number of 1s',
}


def angle_text(x):
    """Angle in radians as a multiple of π when simple (e.g. -π/2, 3π/4)."""
    if abs(x)<1e-12:return '0'
    from fractions import Fraction
    f=Fraction(x/math.pi).limit_denominator(12)
    if f.denominator in (1,2,3,4,6,8,12) and abs(float(f)*math.pi-x)<1e-9:
        num=abs(f.numerator);sign='-' if f<0 else ''
        top='π' if num==1 else f'{num}π'
        return sign+(top if f.denominator==1 else f'{top}/{f.denominator}')
    return f'{x:.4f}'


def inverse_description(name,angle=0.0,phi=0.0,lam=0.0):
    """(text, list of gates) implementing the inverse, for display and testing."""
    name=name.upper()
    simple={'S':'SDG','SDG':'S','T':'TDG','TDG':'T'}
    if name in simple:return simple[name],[Gate(simple[name],(0,))]
    if name in ('RX','RY','RZ','P','CP'):
        sym='λ' if name in ('P','CP') else 'θ'
        return f'{name}(−{sym}); at this angle {name}({angle_text(-angle)})',[Gate(name,(0,1) if name=='CP' else (0,),-angle)]
    if name=='U':return 'U(−θ, −λ, −φ)',[Gate('U',(0,),-angle,-lam,-phi)]
    if name=='SX':return 'SX applied three times (SX⁴ = I)',[Gate('SX',(0,))]*3
    n=gate_information(name)['qubits']
    return f'{name} (self-inverse)',[Gate(name,tuple(range(n)),angle,phi,lam)]


def gate_properties(name,angle=math.pi/2,phi=0.0,lam=0.0):
    """Properties shown in the Gate Explorer, computed from the gate matrix."""
    name=name.upper()
    if name=='M':
        return {'unitary':False,'hermitian':None,'self_inverse':None,'clifford':None,
                'inverse':'None: measurement is irreversible','related':(),'identity':'',
                'eigenvalues':None,'on_zero':None}
    u=gate_matrix(name,angle,phi,lam)
    dim=u.shape[0]
    hermitian=bool(np.allclose(u,u.conj().T,atol=1e-9))
    if name in _CLIFFORD:clifford='Yes'
    elif name in ('RX','RY','RZ','P'):
        k=angle/(math.pi/2)
        clifford='Yes (angle is a multiple of π/2)' if abs(k-round(k))<1e-9 else 'No at this angle (Clifford only at multiples of π/2)'
    elif name=='CP':
        k=angle/math.pi
        clifford='Yes (angle is a multiple of π)' if abs(k-round(k))<1e-9 else 'No at this angle (Clifford only at multiples of π)'
    elif name=='U':clifford='Depends on the angles'
    else:clifford='No'
    eig=None;on_zero=None
    if dim==2:
        eig=[format_amplitude(v) for v in np.linalg.eigvals(u)]
        out=u@np.array([1,0],complex)
        from .circuits import bloch
        on_zero=tuple(round(float(c),4)+0.0 for c in bloch(out,1,0))
    return {'unitary':bool(np.allclose(u.conj().T@u,np.eye(dim),atol=1e-9)),'hermitian':hermitian,
            'self_inverse':hermitian,'clifford':clifford,'inverse':inverse_description(name,angle,phi,lam)[0],
            'related':RELATED.get(name,()),'identity':_IDENTITIES.get(name,''),'eigenvalues':eig,'on_zero':on_zero}


# --- Worked identities (shown step by step in the Gate Explorer) -----------------------

# gate -> (title, sequence of gate names applied in order, gate the sequence equals)
WORKED = {
    'H':   ('H Z H = X', ('H', 'Z', 'H'), 'X'),
    'X':   ('H Z H = X', ('H', 'Z', 'H'), 'X'),
    'Z':   ('H X H = Z', ('H', 'X', 'H'), 'Z'),
    'S':   ('S · S = Z', ('S', 'S'), 'Z'),
    'T':   ('T · T = S', ('T', 'T'), 'S'),
    'SDG': ('S† · S = I (S† undoes S)', ('S', 'SDG'), None),
    'TDG': ('T† · T = I (T† undoes T)', ('T', 'TDG'), None),
    'SX':  ('SX · SX = X', ('SX', 'SX'), 'X'),
    'CZ':  ('H on q1, then CX, then H on q1 = CZ', (('H', 1), ('CX', 0, 1), ('H', 1)), 'CZ'),
    'CX':  ('H on q1, then CZ, then H on q1 = CX', (('H', 1), ('CZ', 0, 1), ('H', 1)), 'CX'),
    'SWAP': ('CX · CX(reversed) · CX = SWAP', (('CX', 0, 1), ('CX', 1, 0), ('CX', 0, 1)), 'SWAP'),
}


def _step_gate(step, n):
    if isinstance(step, tuple):
        return Gate(step[0], tuple(step[1:]))
    return Gate(step, tuple(range(n)) if gate_information(step)['qubits'] == n else (0,))


def worked_identity(name):
    """Step-by-step check of the identity for `name`, or None.

    Returns dict(title, steps (labels), rows): each row is (input, [state after
    each step], state from the single equivalent gate, equal?), with states in
    Dirac notation. Equality is exact (no global phase allowance needed here).
    """
    from .state_analysis import dirac_text
    name = name.upper()
    if name not in WORKED:
        return None
    title, sequence, target = WORKED[name]
    n = 2 if any(isinstance(s, tuple) for s in sequence) else 1   # tuples name explicit qubits
    gates = [_step_gate(s, n) for s in sequence]
    labels = [s if isinstance(s, str) else f'{s[0]} on ' + ','.join(f'q{q}' for q in s[1:]) for s in sequence]
    rows = []
    for index in range(1 << n):
        state = np.zeros(1 << n, complex)
        state[index] = 1
        start = state.copy()
        after = []
        for g in gates:
            state = apply_gate(state, n, g)
            after.append(dirac_text(state, n))
        reference = start if target is None else apply_gate(start, n, _step_gate(target, n))
        rows.append((dirac_text(start, n), after, dirac_text(reference, n), bool(np.allclose(state, reference))))
    return {'title': title, 'steps': labels, 'target': target or 'I', 'rows': rows}


def try_it_circuit(name, angle=math.pi / 2, phi=0.0, lam=0.0):
    """(n, gates, initial state keys) for the Gate Explorer's "Try it" button.

    Starting states are chosen so the gate's effect is visible: phase gates act
    on |+⟩ (a phase on |0⟩ alone would be invisible), controlled gates get a
    control in |+⟩ so they create entanglement, and swaps get distinct inputs.
    """
    name = name.upper()
    n = gate_information(name)['qubits']
    gate = Gate(name, tuple(range(n)), angle, phi, lam)
    phase_like = {'Z', 'S', 'T', 'SDG', 'TDG', 'P', 'RZ'}
    if name in phase_like:
        starts = ['+']
    elif n == 1:
        starts = ['0']
    elif name in ('CX', 'CCX'):
        starts = ['+'] * (n - 1) + ['0']
    elif name in ('CZ', 'CP'):
        starts = ['+', '+']
    elif name == 'SWAP':
        starts = ['1', '0']
    else:                                   # CSWAP
        starts = ['1', '1', '0']
    return n, [gate], starts
