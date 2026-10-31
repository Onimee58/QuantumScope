"""Noise: quantum channels, density-matrix simulation and readout error (no Qt).

A density matrix ρ describes a mixed state; a channel maps ρ → Σ K ρ K† with
Kraus operators satisfying Σ K†K = I (trace preserving). With no noise the
density simulation reproduces the statevector simulation exactly
(ρ = |ψ⟩⟨ψ|), which the tests check.

Conventions: q0 is the most significant bit; ρ for n qubits is 2^n × 2^n.
Depolarizing(p) replaces the state by the maximally mixed state with
probability p: ρ → (1 − p)ρ + p·I/d.
"""
from dataclasses import dataclass, field
import itertools
import math

import numpy as np

from .circuits import Gate

MAX_STORED_QUBITS = 8           # above this, per-column density matrices are not kept (memory)
_I = np.eye(2, dtype=complex)
_X = np.array([[0, 1], [1, 0]], dtype=complex)
_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
_Z = np.array([[1, 0], [0, -1]], dtype=complex)
PAULIS = (_I, _X, _Y, _Z)

CHANNELS = {
    # kind: (label, parameter name, qubits)
    'bit_flip': ('Bit flip', 'p', 1),
    'phase_flip': ('Phase flip', 'p', 1),
    'depolarizing': ('Depolarizing', 'p', 1),
    'amplitude_damping': ('Amplitude damping', 'γ', 1),
    'phase_damping': ('Phase damping', 'λ', 1),
}


def kraus(kind, p, qubits=1):
    """Kraus operators of a channel with strength p ∈ [0, 1]."""
    if not 0.0 <= p <= 1.0 or not math.isfinite(p):
        raise ValueError('Noise strength must be between 0 and 1')
    if kind == 'bit_flip':
        return [math.sqrt(1 - p) * _I, math.sqrt(p) * _X]
    if kind == 'phase_flip':
        return [math.sqrt(1 - p) * _I, math.sqrt(p) * _Z]
    if kind == 'depolarizing':
        d = 2 ** qubits
        paulis = [np.array([[1]], dtype=complex)]
        for _ in range(qubits):
            paulis = [np.kron(a, b) for a in paulis for b in PAULIS]
        weights = [1 - p + p / d ** 2] + [p / d ** 2] * (d ** 2 - 1)
        return [math.sqrt(w) * P for w, P in zip(weights, paulis) if w > 0]
    if kind == 'amplitude_damping':
        return [np.array([[1, 0], [0, math.sqrt(1 - p)]], dtype=complex),
                np.array([[0, math.sqrt(p)], [0, 0]], dtype=complex)]
    if kind == 'phase_damping':
        return [np.array([[1, 0], [0, math.sqrt(1 - p)]], dtype=complex),
                np.array([[0, 0], [0, math.sqrt(p)]], dtype=complex)]
    raise ValueError(f'Unknown channel: {kind}')


@dataclass(frozen=True)
class NoiseElement:
    """A channel placed on one wire of the circuit, like a gate (drawn as a dashed box)."""
    kind: str
    qubit: int
    p: float

    def __post_init__(self):
        if self.kind not in CHANNELS:
            raise ValueError(f'Unknown channel: {self.kind}')
        kraus(self.kind, self.p)                 # validates p
        object.__setattr__(self, 'p', float(self.p))

    @property
    def label(self):
        name, symbol, _ = CHANNELS[self.kind]
        return f'{name} {symbol}={self.p:g}'

    def to_record(self):
        return {'channel': self.kind, 'qubit': self.qubit, 'p': self.p}

    @classmethod
    def from_record(cls, record):
        if not isinstance(record, dict) or type(record.get('qubit')) is not int:
            raise ValueError('Invalid noise element')
        p = record.get('p')
        if isinstance(p, bool) or not isinstance(p, (int, float)):
            raise ValueError('Invalid noise strength')
        return cls(str(record.get('channel')), record['qubit'], float(p))


@dataclass(frozen=True)
class NoiseModel:
    """Global noise, applied after every gate (and optionally to idle qubits).

    single:   depolarizing probability after each single-qubit gate
    two:      depolarizing probability after each multi-qubit gate (2-qubit
              depolarizing on 2-qubit gates; on 3-qubit gates, 1-qubit
              depolarizing at this rate on each of their qubits)
    damping:  amplitude damping γ on each qubit a gate acts on
    dephasing: phase damping λ on each qubit a gate acts on
    readout:  probability that a measured bit is reported wrongly
    idle:     also apply damping and dephasing to qubits waiting in a column
    """
    enabled: bool = False
    single: float = 0.0
    two: float = 0.0
    damping: float = 0.0
    dephasing: float = 0.0
    readout: float = 0.0
    idle: bool = False

    def __post_init__(self):
        for name in ('single', 'two', 'damping', 'dephasing', 'readout'):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0.0 <= value <= 1.0:
                raise ValueError(f'{name} must be between 0 and 1')
            object.__setattr__(self, name, float(value))

    @property
    def active(self):
        return self.enabled and any((self.single, self.two, self.damping, self.dephasing, self.readout))

    def to_record(self):
        return {'enabled': self.enabled, 'single': self.single, 'two': self.two, 'damping': self.damping,
                'dephasing': self.dephasing, 'readout': self.readout, 'idle': self.idle}

    @classmethod
    def from_record(cls, record):
        if not isinstance(record, dict):
            raise ValueError('Invalid noise model')
        values = {k: record[k] for k in ('single', 'two', 'damping', 'dephasing', 'readout') if k in record}
        return cls(bool(record.get('enabled', False)), idle=bool(record.get('idle', False)), **values)


# Illustrative teaching levels — not measurements of any particular device.
PRESETS = {
    'Ideal': NoiseModel(False),
    'Gentle': NoiseModel(True, 0.001, 0.01, 0.001, 0.002, 0.01),
    'Moderate': NoiseModel(True, 0.005, 0.03, 0.005, 0.01, 0.03),
    'Very noisy': NoiseModel(True, 0.02, 0.10, 0.02, 0.04, 0.08),
}


# ---- density-matrix operations -------------------------------------------------------------

def density(state):
    state = np.asarray(state, complex)
    return np.outer(state, state.conj())


def _apply(rho, n, matrix, targets):
    """matrix · ρ · matrix† on the given qubits (vectorized over the rest)."""
    k = len(targets)
    t = np.asarray(rho).reshape((2,) * (2 * n))
    rows = list(targets)
    cols = [q + n for q in targets]
    m = matrix.reshape((2,) * (2 * k))
    # Left multiply on the row indices.
    t = np.tensordot(m, t, axes=(list(range(k, 2 * k)), rows))
    t = np.moveaxis(t, list(range(k)), rows)
    # Right multiply by matrix† on the column indices.
    t = np.tensordot(t, m.conj(), axes=(cols, list(range(k, 2 * k))))
    t = np.moveaxis(t, list(range(2 * n - k, 2 * n)), cols)
    return t.reshape(2 ** n, 2 ** n)


def apply_unitary(rho, n, gate):
    from .gate_education import gate_matrix
    return _apply(rho, n, gate_matrix(gate.name, gate.angle, gate.phi, gate.lam), gate.targets)


def apply_channel(rho, n, operators, targets):
    return sum(_apply(rho, n, K, targets) for K in operators)


def depolarize(rho, n, p, targets):
    """Exact depolarizing channel without Kraus sums: (1 − p)ρ + p · (I/d on targets) ⊗ Tr_targets ρ.

    Equivalent to the Kraus form (tests check both) but one partial trace
    instead of d² operator products, which keeps 9–10 qubit noise usable.
    """
    if not p:
        return rho
    targets = list(targets)
    rest = [q for q in range(n) if q not in targets]
    k = len(targets)
    d, r = 2 ** k, 2 ** (n - k)
    order = targets + rest + [q + n for q in targets] + [q + n for q in rest]
    t = np.transpose(rho.reshape((2,) * (2 * n)), order).reshape(d, r, d, r)
    reduced = np.einsum('aiaj->ij', t)
    mixed = np.einsum('ab,ij->aibj', np.eye(d) / d, reduced)
    out = ((1 - p) * t + p * mixed).reshape((2,) * (2 * n))
    return np.transpose(out, np.argsort(order)).reshape(2 ** n, 2 ** n)


def relax(rho, n, q, gamma=0.0, lam=0.0, inplace=False):
    """Exact amplitude damping (γ) then phase damping (λ) on qubit q, element-wise.

    Amplitude damping moves a fraction γ of |1⟩'s population to |0⟩ and scales
    coherences by √(1 − γ); phase damping scales coherences by √(1 − λ).
    With inplace=True the caller's own matrix is modified (no 16 MB copies).
    """
    if not gamma and not lam:
        return rho
    if not inplace or not rho.flags.c_contiguous:
        rho = np.array(rho, dtype=complex, order='C')
    t = np.moveaxis(rho.reshape((2,) * (2 * n)), [q, q + n], [0, 1])   # a view: writes reach rho
    if gamma:
        t[0, 0] += gamma * t[1, 1]
        t[1, 1] *= 1 - gamma
    factor = math.sqrt((1 - gamma) * (1 - lam))
    t[0, 1] *= factor
    t[1, 0] *= factor
    return rho


def damp(rho, n, gamma, q):
    return relax(rho, n, q, gamma=gamma)


def dephase(rho, n, lam, q):
    return relax(rho, n, q, lam=lam)


def apply_element(rho, n, element):
    if element.kind == 'phase_damping':
        return dephase(rho, n, element.p, element.qubit)
    if element.kind == 'amplitude_damping':
        return damp(rho, n, element.p, element.qubit)
    if element.kind == 'depolarizing':
        return depolarize(rho, n, element.p, (element.qubit,))
    return apply_channel(rho, n, kraus(element.kind, element.p), (element.qubit,))


def gate_noise(rho, n, gate, model):
    """Noise following one gate under the global model."""
    if not model.active:
        return rho
    targets = gate.targets
    rate = model.single if len(targets) == 1 else model.two
    if rate:
        if len(targets) <= 2:
            rho = depolarize(rho, n, rate, targets)
        else:
            for q in targets:
                rho = depolarize(rho, n, rate, (q,))
    for q in targets:
        rho = relax(rho, n, q, model.damping, model.dephasing, inplace=True)
    return rho


def idle_noise(rho, n, qubits, model):
    if not (model.active and model.idle):
        return rho
    for q in qubits:
        rho = relax(rho, n, q, model.damping, model.dephasing, inplace=True)
    return rho


def simulate(n, columns, initial_state, model, store=None):
    """Density-matrix evolution column by column.

    columns: list of lists of Gate or NoiseElement, one list per occupied column.
    Returns the density matrix before the first column and after each column
    (only the final one when `store` is False; by default stored up to
    MAX_STORED_QUBITS qubits).
    """
    store = (n <= MAX_STORED_QUBITS) if store is None else store
    rho = density(initial_state)                  # a fresh matrix: noise may update it in place
    history = [rho]
    for column in columns:
        busy = set()
        for item in column:
            if isinstance(item, NoiseElement):
                rho = apply_element(rho, n, item)
                busy.add(item.qubit)
            else:
                rho = apply_unitary(rho, n, item)
                rho = gate_noise(rho, n, item, model)
                busy.update(item.targets)
        rho = idle_noise(rho, n, [q for q in range(n) if q not in busy], model)
        if store:
            history.append(rho)
            rho = rho.copy()                          # stored states must not change later
    if not store:
        history = [history[0], rho]
    return history


# ---- measures and readout ------------------------------------------------------------------------

def populations(rho):
    return np.clip(np.real(np.diag(rho)), 0.0, 1.0)


def purity(rho):
    return float(np.real(np.trace(rho @ rho)))


def fidelity_with_pure(rho, state):
    """⟨ψ|ρ|ψ⟩: how close the mixed state is to the intended pure state."""
    state = np.asarray(state, complex)
    return float(np.real(np.vdot(state, rho @ state)))


def partial_trace(rho, n, keep):
    """Reduced density matrix of the kept qubits (q_keep[0] most significant)."""
    keep = sorted(set(keep))
    rest = [q for q in range(n) if q not in keep]
    t = rho.reshape((2,) * (2 * n))
    t = np.transpose(t, keep + rest + [q + n for q in keep] + [q + n for q in rest])
    dk, dr = 2 ** len(keep), 2 ** len(rest)
    return np.trace(t.reshape(dk, dr, dk, dr), axis1=1, axis2=3)


def bloch(rho_one):
    return (float(2 * rho_one[0, 1].real), float(-2 * rho_one[0, 1].imag), float((rho_one[0, 0] - rho_one[1, 1]).real))


def apply_readout(probs, n, qubits, error):
    """Outcome probabilities after each measured bit is misreported with probability `error`."""
    probs = np.asarray(probs, dtype=float).copy()
    if not error:
        return probs
    for q in qubits:
        shaped = probs.reshape((2,) * n)
        flipped = np.flip(shaped, axis=q)
        probs = ((1 - error) * shaped + error * flipped).reshape(-1)
    return probs
