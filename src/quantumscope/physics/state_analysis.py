"""State and circuit analysis for the State Inspector (no Qt).

Conventions match the rest of QuantumScope: q0 is the most significant
(leftmost) bit of a basis label, and the state analysed is the ideal pure
state before any terminal measurement.
"""
from collections import Counter
import math

import numpy as np

from .circuits import Gate, unitary
from .gate_education import angle_text, format_amplitude

NOISE = 1e-10   # amplitudes and eigenvalues below this are numerical noise


# ---- amplitudes -------------------------------------------------------------------

def basis_label(index, n):
    return f'|{index:0{n}b}⟩'


def remove_global_phase(state):
    """Rotate the global phase so the first nonzero amplitude is real and positive."""
    state = np.asarray(state, complex)
    nonzero = np.flatnonzero(np.abs(state) > NOISE)
    if not len(nonzero):
        return state.copy()
    first = state[nonzero[0]]
    return state * (abs(first) / first)


def phase_text(phase):
    """Phase in (−π, π] as a multiple of π where simple."""
    phase = math.remainder(phase, 2 * math.pi)
    if abs(phase + math.pi) < 1e-9:
        phase = math.pi
    return angle_text(phase)


def amplitude_rows(state, n, show_all=False, relative_phase=False, order='basis'):
    """Rows for the amplitude table.

    Each row: dict(index, label, amplitude (complex), text, magnitude,
    probability, phase (radians, or None for a zero amplitude), phase_text).
    order is 'basis' or 'probability' (largest first, ties by basis order).
    """
    state = np.asarray(state, complex)
    if state.shape != (1 << n,):
        raise ValueError('State has the wrong dimension')
    if relative_phase:
        state = remove_global_phase(state)
    rows = []
    for index, amp in enumerate(state):
        mag = abs(amp)
        if mag <= NOISE and not show_all:
            continue
        zero = mag <= NOISE
        phase = None if zero else float(np.angle(amp))
        rows.append({'index': index, 'label': basis_label(index, n), 'amplitude': complex(amp),
                     'text': format_amplitude(0j if zero else amp), 'magnitude': float(mag),
                     'probability': float(mag * mag), 'phase': phase,
                     'phase_text': '—' if zero else phase_text(phase)})
    if order == 'probability':
        rows.sort(key=lambda r: (-round(r['probability'], 12), r['index']))
    elif order != 'basis':
        raise ValueError('order must be basis or probability')
    return rows


# ---- notation and export ---------------------------------------------------------------

def _terms(state, n, relative_phase):
    state = remove_global_phase(state) if relative_phase else np.asarray(state, complex)
    return [(format_amplitude(a), i) for i, a in enumerate(state) if abs(a) > NOISE]


def _joined(parts):
    """Join signed terms: 'a', '-b' -> 'a - b'."""
    out = ''
    for k, p in enumerate(parts):
        if k == 0:
            out = p
        elif p.startswith('-'):
            out += ' - ' + p[1:]
        else:
            out += ' + ' + p
    return out


def dirac_text(state, n, relative_phase=False):
    """e.g. '(1/√2)|00⟩ + (1/√2)|11⟩'."""
    parts = []
    for amp, i in _terms(state, n, relative_phase):
        ket = basis_label(i, n)
        if amp == '1':
            parts.append(ket)
        elif amp == '-1':
            parts.append('-' + ket)
        elif amp.startswith('-') and ' ' not in amp:
            parts.append(f'-({amp[1:]}){ket}')
        else:
            parts.append(f'({amp}){ket}')
    return _joined(parts) or '0'


def _latex_amp(text):
    t = text.replace('√', r'\sqrt')
    # \sqrt2 -> \sqrt{2}, \sqrt3 -> \sqrt{3}
    for d in '23':
        t = t.replace(r'\sqrt' + d, r'\sqrt{' + d + '}')
    return t


def dirac_latex(state, n, relative_phase=False):
    r"""e.g. '\frac{1}{\sqrt{2}}\lvert 00\rangle + \frac{1}{\sqrt{2}}\lvert 11\rangle'."""
    parts = []
    for amp, i in _terms(state, n, relative_phase):
        ket = r'\lvert ' + f'{i:0{n}b}' + r'\rangle'
        sign = ''
        if amp.startswith('-') and ' ' not in amp:
            sign, amp = '-', amp[1:]
        fractions = {'1/√2': r'\frac{1}{\sqrt{2}}', '1/2': r'\frac{1}{2}', '√3/2': r'\frac{\sqrt{3}}{2}',
                     '1/(2√2)': r'\frac{1}{2\sqrt{2}}', 'i/√2': r'\frac{i}{\sqrt{2}}', 'i/2': r'\frac{i}{2}',
                     'i√3/2': r'\frac{i\sqrt{3}}{2}'}
        if amp == '1':
            coef = ''
        elif amp in fractions:
            coef = fractions[amp]
        elif ' ' in amp:
            coef = r'\left(' + _latex_amp(amp) + r'\right)'
        else:
            coef = _latex_amp(amp)
        parts.append(sign + coef + ket)
    return _joined(parts) or '0'


def state_csv(state, n):
    """CSV with full-precision amplitudes for every basis state."""
    lines = ['basis,real,imag,magnitude,probability,phase_radians']
    for i, a in enumerate(np.asarray(state, complex)):
        mag = abs(a)
        phase = float(np.angle(a)) if mag > NOISE else 0.0
        lines.append(f'{i:0{n}b},{a.real:.17g},{a.imag:.17g},{mag:.17g},{mag * mag:.17g},{phase:.17g}')
    return '\n'.join(lines) + '\n'


# ---- reduced states ------------------------------------------------------------------------

MAX_REDUCED_QUBITS = 3


def reduced_density_matrix(state, n, keep):
    """ρ of the kept qubits (tracing out the rest), ordered q_keep[0] most significant."""
    keep = sorted(set(keep))
    if not keep or any(q < 0 or q >= n for q in keep):
        raise ValueError('Choose valid qubits to keep')
    psi = np.asarray(state, complex).reshape((2,) * n)
    rest = [q for q in range(n) if q not in keep]
    m = np.transpose(psi, keep + rest).reshape(1 << len(keep), -1)
    return m @ m.conj().T


def purity(rho):
    return float(np.real(np.trace(rho @ rho)))


def entropy_bits(rho):
    """Von Neumann entropy S(ρ) = −Tr ρ log₂ ρ, in bits."""
    values = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    values = values[values > NOISE]
    return float(max(0.0, -np.sum(values * np.log2(values))))


def bloch_from_rho(rho):
    """Bloch vector (x, y, z) of a single-qubit density matrix."""
    return (float(2 * rho[0, 1].real), float(-2 * rho[0, 1].imag), float((rho[0, 0] - rho[1, 1]).real))


def reduced_summary(state, n, keep):
    """Everything the density-matrix tab shows for the kept qubits."""
    if len(set(keep)) > MAX_REDUCED_QUBITS:
        raise ValueError(f'Choose at most {MAX_REDUCED_QUBITS} qubits')
    rho = reduced_density_matrix(state, n, keep)
    p, s = purity(rho), entropy_bits(rho)
    keep = sorted(set(keep))
    whole = len(keep) == n
    if whole:
        verdict = 'Pure: this is the whole register.'
    elif s < 1e-9:
        verdict = 'Pure: not entangled with the other qubits.'
    else:
        verdict = 'Mixed: entangled with the other qubits.'
    return {'keep': keep, 'rho': rho, 'purity': p, 'entropy': s, 'verdict': verdict,
            'bloch': bloch_from_rho(rho) if len(keep) == 1 else None,
            'max_entropy': float(len(keep))}


# ---- circuit analysis -------------------------------------------------------------------------

_PAULIS = {'X': np.array([[0, 1], [1, 0]], complex), 'Y': np.array([[0, -1j], [1j, 0]], complex),
           'Z': np.array([[1, 0], [0, -1]], complex)}
_CLIFFORD_MULTI = {'CX', 'CZ', 'SWAP'}


def _is_pauli_up_to_phase(m):
    for p in _PAULIS.values():
        k = np.argmax(np.abs(p))
        r, c = divmod(int(k), 2)
        if abs(m[r, c]) < 1e-9:
            continue
        phase = m[r, c] / p[r, c]
        if abs(abs(phase) - 1) < 1e-9 and np.allclose(m, phase * p, atol=1e-9):
            return True
    return False


def is_clifford(gate):
    """True if the gate maps Pauli operators to Pauli operators (up to phase).

    Single-qubit gates are tested exactly from their matrix, so rotations
    count as Clifford at multiples of π/2. CX, CZ and SWAP are Clifford;
    CCX and CSWAP are not.
    """
    if gate.name == 'CP':
        k = gate.angle / math.pi                 # CP(0) = I, CP(π) = CZ; CP(π/2) (controlled-S) is not Clifford
        return abs(k - round(k)) < 1e-9
    if len(gate.targets) > 1:
        return gate.name in _CLIFFORD_MULTI
    u = unitary(Gate(gate.name, (0,), gate.angle, gate.phi, gate.lam))
    return all(_is_pauli_up_to_phase(u @ _PAULIS[a] @ u.conj().T) for a in ('X', 'Z'))


def minimum_depth(n, gates):
    """Fewest layers when gates on different qubits run in parallel."""
    free = [0] * n
    for g in gates:
        layer = max(free[q] for q in g.targets)
        for q in g.targets:
            free[q] = layer + 1
    return max(free, default=0)


def analyze_circuit(n, gates, columns=None, measured=()):
    """Gate statistics for the Circuit tab. gates are in simulation order."""
    counts = Counter(g.name for g in gates)
    by_size = Counter(len(g.targets) for g in gates)
    clifford = sum(1 for g in gates if is_clifford(g))
    used = sorted({q for g in gates for q in g.targets} | set(measured))
    return {
        'qubits': n,
        'qubits_used': used,
        'total': len(gates),
        'counts': dict(sorted(counts.items())),
        'single_qubit': by_size[1], 'two_qubit': by_size[2], 'three_qubit': by_size[3],
        't_count': counts['T'] + counts['TDG'],
        'clifford': clifford, 'non_clifford': len(gates) - clifford,
        'parameterized': sum(1 for g in gates if g.name in ('RX', 'RY', 'RZ', 'P', 'U', 'CP')),
        'drawn_depth': len(set(columns)) if columns is not None else None,
        'minimum_depth': minimum_depth(n, gates),
        'measurements': len(measured),
    }
