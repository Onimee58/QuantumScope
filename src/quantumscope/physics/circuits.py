"""Small exact statevector simulator and intentionally restricted OpenQASM 2 reader.

Bit order: qubit zero is the most significant tensor factor, |q0 q1 ...>.
"""
from dataclasses import dataclass
import math
import re
import numpy as np

MAX_QUBITS = 10
SINGLE = ('H', 'X', 'Y', 'Z', 'S', 'T', 'SDG', 'TDG', 'SX', 'P', 'RX', 'RY', 'RZ', 'U')
DUAL = ('CX', 'CZ', 'SWAP')
TRIPLE = ('CCX', 'CSWAP')
ALL = SINGLE + DUAL + TRIPLE

@dataclass(frozen=True)
class Gate:
    name: str
    targets: tuple[int, ...]
    angle: float = 0.0
    phi: float = 0.0
    lam: float = 0.0


def unitary(gate):
    name, a = gate.name, gate.angle
    if name == 'H': return np.array([[1, 1], [1, -1]], complex) / math.sqrt(2)
    if name == 'X': return np.array([[0, 1], [1, 0]], complex)
    if name == 'Y': return np.array([[0, -1j], [1j, 0]], complex)
    if name == 'Z': return np.diag([1, -1]).astype(complex)
    if name == 'S': return np.diag([1, 1j]).astype(complex)
    if name == 'T': return np.diag([1, np.exp(1j*math.pi/4)]).astype(complex)
    if name == 'SDG': return np.diag([1, -1j]).astype(complex)
    if name == 'TDG': return np.diag([1, np.exp(-1j*math.pi/4)]).astype(complex)
    if name == 'SX': return .5*np.array([[1+1j,1-1j],[1-1j,1+1j]],complex)
    if name == 'P': return np.diag([1,np.exp(1j*a)]).astype(complex)
    if name == 'U':
        c,s=math.cos(a/2),math.sin(a/2)
        return np.array([[c,-np.exp(1j*gate.lam)*s],[np.exp(1j*gate.phi)*s,np.exp(1j*(gate.phi+gate.lam))*c]],complex)
    if name == 'RX': return math.cos(a/2)*np.eye(2)-1j*math.sin(a/2)*unitary(Gate('X',(0,)))
    if name == 'RY': return math.cos(a/2)*np.eye(2)-1j*math.sin(a/2)*unitary(Gate('Y',(0,)))
    if name == 'RZ': return np.diag([np.exp(-1j*a/2),np.exp(1j*a/2)])
    raise ValueError('Unknown gate: ' + name)


def apply_gate(state, n, gate):
    name = gate.name.upper()
    ids = gate.targets
    if name not in ALL: raise ValueError('Unsupported gate ' + name)
    if len(ids) != (3 if name in TRIPLE else 2 if name in DUAL else 1) or len(set(ids)) != len(ids) or any(q < 0 or q >= n for q in ids):
        raise ValueError('Invalid target qubits')
    result = np.array(state, dtype=complex, copy=True)
    if name in SINGLE:
        mask = 1 << (n-1-ids[0]); u = unitary(gate)
        for i in range(1 << n):
            if i & mask: continue
            j = i | mask
            a,b = result[i],result[j]
            result[i],result[j] = u[0,0]*a+u[0,1]*b, u[1,0]*a+u[1,1]*b
    elif name in TRIPLE:
        m1,m2,m3=(1<<(n-1-q) for q in ids)
        for i in range(1<<n):
            if name=='CCX' and (i&m1) and (i&m2) and not (i&m3):
                j=i|m3;result[i],result[j]=result[j],result[i]
            elif name=='CSWAP' and (i&m1) and not (i&m2) and (i&m3):
                j=i^m2^m3;result[i],result[j]=result[j],result[i]
    else:
        m1,m2 = (1<<(n-1-q) for q in ids)
        if name in ('CX','CZ'):
            for i in range(1 << n):
                if i & m1:
                    if name == 'CZ' and i & m2: result[i] *= -1
                    elif name == 'CX' and not i & m2:
                        j=i|m2; result[i],result[j]=result[j],result[i]
        else:
            for i in range(1 << n):
                if not (i&m1) and i&m2:
                    j=i^m1^m2; result[i],result[j]=result[j],result[i]
    return result


def zero(n):
    if not 1 <= n <= MAX_QUBITS: raise ValueError(f'Qubits must be 1–{MAX_QUBITS}')
    v=np.zeros(1<<n,complex); v[0]=1; return v


def evolution(n, gates):
    states=[zero(n)]
    for g in gates: states.append(apply_gate(states[-1],n,g))
    return states


def bloch(state,n,q):
    """Bloch coordinates of reduced qubit, including mixed local states."""
    axis = np.asarray(state).reshape((2,)*n)
    v=np.moveaxis(axis,q,0).reshape(2,-1)
    rho=v@v.conj().T
    return (float(2*rho[0,1].real),float(-2*rho[0,1].imag),float((rho[0,0]-rho[1,1]).real))


def distribution(state):
    return np.abs(state)**2


def sample(state,shots,seed=None):
    if not 1 <= shots <= 100000: raise ValueError('Shots out of range')
    return np.random.default_rng(seed).multinomial(shots,distribution(state))


def parse_qasm(text):
    """OpenQASM 2 subset: qreg + H/X/Y/Z/S/T, rotations, CX/CZ/SWAP, barriers.

    Reject measurements, custom gates, conditionals, multi-register circuits etc.
    rather than silently change semantics.
    """
    text=re.sub(r'//[^\n]*','',text)
    statements=[x.strip() for x in text.split(';') if x.strip()]
    n=None; gates=[]; reg=None; header=False
    for statement in statements:
        s=' '.join(statement.split())
        if re.fullmatch(r'OPENQASM\s+2\.0',s,re.I): header=True; continue
        if re.fullmatch(r'include\s+"qelib1\.inc"',s,re.I): continue
        m=re.fullmatch(r'qreg\s+(\w+)\[(\d+)\]',s,re.I)
        if m:
            if n is not None: raise ValueError('Only one quantum register supported')
            reg,n=m.group(1),int(m.group(2)); zero(n);continue
        if s.lower().startswith('barrier '): continue
        if not header or n is None: raise ValueError(f'Expected OPENQASM 2.0 and qreg before: {s}')
        pat=rf'({re.escape(reg)})\[(\d+)\]'
        m=re.fullmatch(r'(h|x|y|z|s|t|sdg|tdg|sx|cx|cz|swap|ccx|cswap)\s+(.+)',s,re.I)
        if m:
            name=m.group(1).upper()
            args=[a.strip() for a in m.group(2).split(',')]
            indexes=[]
            for arg in args:
                mq=re.fullmatch(pat,arg)
                if not mq:raise ValueError('Invalid QASM qubit operand: '+arg)
                indexes.append(int(mq.group(2)))
            g=Gate(name,tuple(indexes));apply_gate(zero(n),n,g);gates.append(g);continue
        m=re.fullmatch(r'(rx|ry|rz|p)\s*\(([^()]*)\)\s*'+pat,s,re.I)
        if m:
            expr=m.group(2).replace(' ','').lower()
            if not re.fullmatch(r'[0-9.pi+*/-]+',expr): raise ValueError('Unsupported rotation expression')
            try: angle=float(eval(expr,{'__builtins__':{}},{'pi':math.pi}))
            except (SyntaxError,ValueError,TypeError,ZeroDivisionError) as exc: raise ValueError('Invalid rotation angle') from exc
            if not math.isfinite(angle): raise ValueError('Nonfinite rotation')
            g=Gate(m.group(1).upper(),(int(m.group(4)),),angle);apply_gate(zero(n),n,g);gates.append(g);continue
        m=re.fullmatch(r'(u3|u)\s*\(([^()]*)\)\s*'+pat,s,re.I)
        if m:
            exprs=[v.strip() for v in m.group(2).split(',')]
            if len(exprs)!=3:raise ValueError('U requires three angles')
            vals=[]
            for expr in exprs:
                if not re.fullmatch(r'[0-9.pi+*/ -]+',expr.lower()):raise ValueError('Unsupported U angle')
                try:val=float(eval(expr,{'__builtins__':{}},{'pi':math.pi}))
                except (SyntaxError,ValueError,TypeError,ZeroDivisionError) as exc:raise ValueError('Invalid U angle') from exc
                if not math.isfinite(val):raise ValueError('Nonfinite U angle')
                vals.append(val)
            g=Gate('U',(int(m.group(4)),),*vals);gates.append(g);continue
        raise ValueError('Unsupported OpenQASM statement: '+s)
    if not header or n is None: raise ValueError('Missing OPENQASM 2.0 or qreg')
    return n,gates


def measurement_marginal(probabilities, n, measured, counts=None):
    """Marginalize q0-first computational-basis distributions to selected wires.

    Returns (theoretical probabilities, sampled counts or None). This does not
    collapse a state and is intended for terminal measurements only.
    """
    measured=tuple(sorted(measured))
    if not measured or len(set(measured))!=len(measured) or any(q<0 or q>=n for q in measured):
        raise ValueError('Choose distinct valid measured qubits')
    probs=np.asarray(probabilities,dtype=float)
    if probs.shape!=(1<<n,):raise ValueError('Invalid state probability vector length')
    if counts is not None:
        counts=np.asarray(counts)
        if counts.shape!=probs.shape:raise ValueError('Invalid counts vector length')
    marginal=np.zeros(1<<len(measured),dtype=float)
    sampled=np.zeros(1<<len(measured),dtype=int) if counts is not None else None
    for index,prob in enumerate(probs):
        outcome=0
        for q in measured:outcome=(outcome<<1)|((index>>(n-1-q))&1)
        marginal[outcome]+=prob
        if sampled is not None:sampled[outcome]+=int(counts[index])
    return marginal,sampled
