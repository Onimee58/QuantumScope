"""Input/output checks driven by the exact statevector gate simulator.

The truth table always reports measured basis outputs; expected arithmetic
outputs are checked only for examples with a documented register convention.
"""
from dataclasses import dataclass
import numpy as np
from .circuits import Gate, zero, apply_gate, distribution
from .display import ket

@dataclass(frozen=True)
class VerificationRow:
    input_label: str
    output_label: str
    expected_label: str
    probability: float
    passed: bool | None


def simulate_input(n, operations, initial_bits):
    state = zero(n)
    for q, bit in enumerate(initial_bits):
        if bit:
            state = apply_gate(state, n, Gate('X', (q,)))
    for gate in operations:
        state = apply_gate(state, n, gate)
    return distribution(state)


def verify_example(name, n, gates):
    """Return (rows, note), without using hard-coded simulated results.

    Example circuits include initial X gates setting their demonstration input;
    strip only those known preparation gates to evaluate every input case.
    """
    if name.startswith('Half adder'):
        prep=2; inputs=(0, 1); width=2
        def expected(a,b):return (a ^ b, a & b)
        def output(bits):return (bits[1],bits[2])
        description='Sum=q1, carry=q2; q0 retains A.'
    elif name.startswith('Half subtractor'):
        prep=2; inputs=(0, 1); width=2
        def expected(a,b):return (a ^ b, (1-a)&b)
        def output(bits):return (bits[1],bits[2])
        description='Difference=q1, borrow=q2; q0 retains A.'
    elif name.startswith('2-bit ripple-carry'):
        prep=2; inputs=(0,1,2,3); width=4
        def expected(a,b):
            total=a+b
            return (total&1, (total>>1)&1, (total>>2)&1)
        def output(bits):return (bits[1],bits[2],bits[5])
        description='Expected output convention: sum LSB=q1, next bit=q2, carry=q5; input A=q0q1 and B=q2q3. Failing rows indicate a circuit or register-mapping issue.'
    else:
        return [], 'Choose an arithmetic example for exhaustive input/output verification.'
    required=6 if name.startswith('2-bit ripple-carry') else 3
    if n<required:
        return [], f'This example needs {required} qubits; restore the qubit count to verify it.'
    if any(g.name!='X' for g in gates[:prep]):
        return [], 'Circuit has been edited: preset input preparation cannot be identified. Use basis-state inspection instead.'
    logic=gates[prep:]
    rows=[]
    for value in range(1<<width):
        input_bits=[0]*n
        for pos,q in enumerate(inputs):input_bits[q]=(value>>(width-1-pos))&1
        probs=simulate_input(n,logic,input_bits)
        peak=int(np.argmax(probs));p=float(probs[peak]);bits=tuple((peak>>(n-1-i))&1 for i in range(n))
        if width==2:
            a,b=input_bits[0],input_bits[1]
        else:
            a,b=2*input_bits[0]+input_bits[1],2*input_bits[2]+input_bits[3]
        observed=output(bits);correct=expected(a,b)
        passed_=observed==correct and p>1-1e-8
        rows.append(VerificationRow(f'{a} + {b}' if 'adder' in name else f'{a} - {b}', ''.join(map(str,observed)), ''.join(map(str,correct)),p,passed_))
    return rows,description


def inspect_basis(n, gates, max_rows=16):
    """Inspect selected computational-basis inputs, preserving superpositions."""
    from .circuits import evolution
    rows=[]
    for value in range(min(1<<n,max_rows)):
        state=np.zeros(1<<n,complex);state[value]=1
        for gate in gates: state=apply_gate(state,n,gate)
        p=distribution(state);top=int(np.argmax(p));prob=float(p[top])
        label=ket(top,n) if prob>1-1e-8 else f'non-deterministic ({prob*100:.1f}% at {ket(top,n)})'
        rows.append(VerificationRow(ket(value,n),label,'—',prob,None))
    return rows, f'First {len(rows)} computational-basis inputs; superposition-producing circuits are not assigned arithmetic PASS/FAIL.'
