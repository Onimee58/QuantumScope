"""Small, transparent statevector engine for introductory gate demonstrations."""
import math
import re
import numpy as np

SINGLE = {
    'h': np.array([[1, 1], [1, -1]], complex) / math.sqrt(2),
    'x': np.array([[0, 1], [1, 0]], complex),
    'y': np.array([[0, -1j], [1j, 0]], complex),
    'z': np.diag([1, -1]).astype(complex),
    's': np.diag([1, 1j]).astype(complex),
    't': np.diag([1, np.exp(1j * math.pi / 4)]).astype(complex),
}
GATES = {'h', 'x', 'y', 'z', 's', 't', 'cx', 'cz', 'swap', 'measure'}


def _bit(q, n):
    return 1 << (n - 1 - q)


def simulate(n, operations):
    """Big-endian qubit order: q[0] is the leftmost displayed ket bit."""
    if not 1 <= n <= 6:
        raise ValueError('Select 1 to 6 qubits.')
    state = np.zeros(1 << n, complex)
    state[0] = 1
    for op in operations:
        gate, a, b = op
        if gate not in GATES:
            raise ValueError(f'Unsupported gate: {gate}')
        if not 0 <= a < n or (b is not None and not 0 <= b < n):
            raise ValueError('Qubit index outside register.')
        if gate in ('cx', 'cz', 'swap') and (b is None or a == b):
            raise ValueError(f'{gate} needs two different qubits.')
        if gate == 'measure':
            continue  # terminal samples are derived from probabilities, not collapse here
        if gate in SINGLE:
            bit = _bit(a, n)
            u = SINGLE[gate]
            for i in range(1 << n):
                if not i & bit:
                    j = i | bit
                    v, w = state[i], state[j]
                    state[i], state[j] = u[0, 0] * v + u[0, 1] * w, u[1, 0] * v + u[1, 1] * w
        elif gate in ('cx', 'cz'):
            control, target = _bit(a, n), _bit(b, n)
            for i in range(1 << n):
                if i & control:
                    if gate == 'cz':
                        if i & target:
                            state[i] *= -1
                    elif not i & target:
                        j = i | target
                        state[i], state[j] = state[j], state[i]
        else:
            aa, bb = _bit(a, n), _bit(b, n)
            for i in range(1 << n):
                if bool(i & aa) != bool(i & bb) and not i & aa:
                    j = i ^ (aa | bb)
                    state[i], state[j] = state[j], state[i]
    return state


def probabilities(n, operations):
    return np.abs(simulate(n, operations)) ** 2


def parse_qasm(source):
    """Strict OpenQASM 2 subset: one qreg, optional creg, basic gates, terminal measurement.

    Rejects conditions, includes other than qelib1.inc, barriers, and mid-circuit
    measurements instead of claiming to support them.
    """
    clean = re.sub(r'//[^\n]*', '', source)
    statements = [s.strip() for s in clean.split(';') if s.strip()]
    n = None
    creg = None
    ops = []
    seen_measure = False
    for stmt in statements:
        if re.fullmatch(r'OPENQASM\s+2\.0', stmt, re.I):
            continue
        if re.fullmatch(r'include\s+"qelib1\.inc"', stmt, re.I):
            continue
        m = re.fullmatch(r'qreg\s+([A-Za-z_]\w*)\[(\d+)\]', stmt)
        if m:
            if n is not None:
                raise ValueError('Only one quantum register is supported.')
            reg, n = m.group(1), int(m.group(2))
            if not 1 <= n <= 6:
                raise ValueError('This visual simulator supports 1–6 qubits.')
            continue
        m = re.fullmatch(r'creg\s+([A-Za-z_]\w*)\[(\d+)\]', stmt)
        if m:
            creg = (m.group(1), int(m.group(2)))
            continue
        if n is None:
            raise ValueError('Declare qreg before operations.')
        m = re.fullmatch(r'(h|x|y|z|s|t)\s+(\w+)\[(\d+)\]', stmt, re.I)
        if m:
            if seen_measure or m.group(2) != reg:
                raise ValueError('Unknown register or gate after measurement.')
            ops.append((m.group(1).lower(), int(m.group(3)), None))
            continue
        m = re.fullmatch(r'(cx|cz|swap)\s+(\w+)\[(\d+)\]\s*,\s*(\w+)\[(\d+)\]', stmt, re.I)
        if m:
            if seen_measure or m.group(2) != reg or m.group(4) != reg:
                raise ValueError('Unknown register or gate after measurement.')
            ops.append((m.group(1).lower(), int(m.group(3)), int(m.group(5))))
            continue
        m = re.fullmatch(r'measure\s+(\w+)\[(\d+)\]\s*->\s*(\w+)\[(\d+)\]', stmt, re.I)
        if m:
            if m.group(1) != reg or creg is None or m.group(3) != creg[0] or int(m.group(4)) >= creg[1]:
                raise ValueError('Invalid measurement register.')
            seen_measure = True
            ops.append(('measure', int(m.group(2)), None))
            continue
        raise ValueError(f'Unsupported OpenQASM statement: {stmt[:80]}')
    if n is None:
        raise ValueError('Missing qreg declaration.')
    # Validate complete circuit before returning.
    simulate(n, ops)
    return n, ops


def export_qasm(n, operations):
    lines = ['OPENQASM 2.0;', 'include "qelib1.inc";', f'qreg q[{n}];', f'creg c[{n}];']
    for gate, a, b in operations:
        if gate == 'measure':
            lines.append(f'measure q[{a}] -> c[{a}];')
        elif b is None:
            lines.append(f'{gate} q[{a}];')
        else:
            lines.append(f'{gate} q[{a}],q[{b}];')
    return '\n'.join(lines) + '\n'
