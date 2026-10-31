"""Circuit tools: safe gate simplification and unitary equivalence (no Qt).

Simplification only combines two gates that act on exactly the same qubits
with nothing in between on those qubits, so the rest of the circuit cannot
interfere. Every result is checked against the full unitary before it is
offered (see `simplify` and `equivalent`).
"""
import math

import numpy as np

from .circuits import Gate, MAX_QUBITS

TOL = 1e-9
SELF_INVERSE = {'H', 'X', 'Y', 'Z', 'CX', 'CZ', 'SWAP', 'CCX', 'CSWAP'}
INVERSE_PAIRS = {('S', 'SDG'), ('SDG', 'S'), ('T', 'TDG'), ('TDG', 'T')}
MERGEABLE = {'RX', 'RY', 'RZ', 'P', 'CP'}


# ---- unitaries -----------------------------------------------------------------------------

def _local_matrix(gate):
    from .gate_education import gate_matrix
    return gate_matrix(gate.name, gate.angle, gate.phi, gate.lam)


def circuit_unitary(n, gates):
    """The 2^n × 2^n unitary of a gate list (q0 is the most significant bit).

    Vectorized: each gate acts on all columns at once through a tensor reshape,
    so 10-qubit circuits take well under a second.
    """
    if not 1 <= n <= MAX_QUBITS:
        raise ValueError('Qubit count out of range')
    dim = 1 << n
    u = np.eye(dim, dtype=complex).reshape((2,) * n + (dim,))
    for g in gates:
        k = len(g.targets)
        m = _local_matrix(g)
        axes = list(g.targets)
        moved = np.moveaxis(u, axes, list(range(k)))
        shape = moved.shape
        moved = (m @ moved.reshape(1 << k, -1)).reshape(shape)
        u = np.moveaxis(moved, list(range(k)), axes)
    return u.reshape(dim, dim)


def equivalent(n, first, second):
    """(equal?, global phase, largest deviation): first == phase · second as unitaries."""
    a, b = circuit_unitary(n, first), circuit_unitary(n, second)
    overlap = np.vdot(b, a) / (1 << n)          # = Tr(B†A)/N, the phase if A = e^{iφ}B
    if abs(overlap) < TOL:
        return False, None, float(np.max(np.abs(a - b)))
    phase = overlap / abs(overlap)
    deviation = float(np.max(np.abs(a - phase * b)))
    return deviation < 1e-8, complex(phase), deviation


# ---- simplification ------------------------------------------------------------------------------

def _same_operands(a, b):
    if a.name != b.name:
        return set(a.targets) == set(b.targets) and len(a.targets) == len(b.targets)
    if a.name in ('CZ', 'SWAP', 'CP'):
        return set(a.targets) == set(b.targets)
    if a.name == 'CCX':
        return set(a.targets[:2]) == set(b.targets[:2]) and a.targets[2] == b.targets[2]
    if a.name == 'CSWAP':
        return a.targets[0] == b.targets[0] and set(a.targets[1:]) == set(b.targets[1:])
    return a.targets == b.targets


def _identity_note(gate):
    """None if the gate is not the identity; '' if exactly I; a note if I up to global phase."""
    a = gate.angle
    if gate.name in ('P', 'CP'):
        return '' if abs(math.remainder(a, 2 * math.pi)) < TOL else None
    if gate.name in ('RX', 'RY', 'RZ'):
        if abs(math.remainder(a, 4 * math.pi)) < TOL:
            return ''
        if abs(math.remainder(a, 2 * math.pi)) < TOL:
            return ' (equals −I: a global phase only)'
    return None


def _combine(first, second):
    """('cancel', None), ('merge', gate) or None for two adjacent gates on the same qubits."""
    if not _same_operands(first, second):
        return None
    if first.name == second.name and first.name in SELF_INVERSE:
        return 'cancel', None
    if (first.name, second.name) in INVERSE_PAIRS:
        return 'cancel', None
    if first.name == second.name and first.name in MERGEABLE:
        return 'merge', Gate(first.name, first.targets, first.angle + second.angle)
    return None


def _describe(g):
    from .gate_education import angle_text
    name = {'SDG': 'S†', 'TDG': 'T†'}.get(g.name, g.name)
    params = f'({angle_text(g.angle)})' if g.name in MERGEABLE else ''
    return f'{name}{params} on ' + ','.join(f'q{q}' for q in g.targets)


def simplify_sequence(items):
    """Simplify a circuit given in simulation order.

    items: ('gate', key, Gate) for editable gates, or ('barrier', key, wires)
    for anything that must not be changed or looked through (a block).
    Returns (kept, changes): kept maps each surviving gate key to its (possibly
    merged) Gate; changes is a list of human-readable descriptions.
    """
    seq = [list(item) for item in items]
    changes = []
    progress = True
    while progress:
        progress = False
        last = {}                                # wire -> index in seq of the last item touching it
        for i, item in enumerate(seq):
            if item is None:
                continue
            kind, key, payload = item
            wires = set(payload.targets) if kind == 'gate' else set(payload)
            previous = {last.get(w) for w in wires}
            if kind == 'gate' and len(previous) == 1 and None not in previous:
                j = previous.pop()
                earlier = seq[j]
                if earlier[0] == 'gate' and set(earlier[2].targets) == wires:
                    result = _combine(earlier[2], payload)
                    if result is not None:
                        action, merged = result
                        if action == 'cancel':
                            changes.append(f'Cancelled {_describe(earlier[2])} followed by {_describe(payload)}')
                            seq[j] = seq[i] = None
                        else:
                            note = _identity_note(merged)
                            if note is not None:
                                changes.append(f'Removed {_describe(earlier[2])} + {_describe(payload)}: '
                                               f'together the identity{note}')
                                seq[j] = seq[i] = None
                            else:
                                changes.append(f'Merged {_describe(earlier[2])} and {_describe(payload)} '
                                               f'into {_describe(merged)}')
                                seq[j] = ['gate', earlier[1], merged]
                                seq[i] = None
                        progress = True
                        break
            if kind == 'gate':
                note = _identity_note(payload)
                if note is not None:
                    changes.append(f'Removed {_describe(payload)}: the identity{note}')
                    seq[i] = None
                    progress = True
                    break
            for w in wires:
                last[w] = i
        seq = [item for item in seq if item is not None] if progress else seq
    kept = {item[1]: item[2] for item in seq if item is not None and item[0] == 'gate'}
    return kept, changes
