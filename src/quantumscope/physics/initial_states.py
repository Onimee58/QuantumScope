"""Per-qubit initial states: six Bloch-axis presets or a custom (θ, φ) state.

A single-qubit pure state is |ψ(θ, φ)⟩ = cos(θ/2)|0⟩ + e^{iφ} sin(θ/2)|1⟩,
with θ ∈ [0, π] and φ ∈ [0, 2π). The register starts in the product of the
qubits' states, q0 being the most significant (leftmost) factor.

At the poles (θ = 0 or π) φ only changes a global phase, so it is set to 0
there; this keeps |1⟩ a single, unambiguous state.
"""
from dataclasses import dataclass
import math

import numpy as np

from .circuits import Gate, MAX_QUBITS

TOL = 1e-9

# key -> (θ, φ, display label, preparation gates from |0⟩)
PRESETS = {
    '0':  (0.0,         0.0,             '|0⟩',  ()),
    '1':  (math.pi,     0.0,             '|1⟩',  ('X',)),
    '+':  (math.pi / 2, 0.0,             '|+⟩',  ('H',)),
    '-':  (math.pi / 2, math.pi,         '|−⟩',  ('X', 'H')),
    '+i': (math.pi / 2, math.pi / 2,     '|+i⟩', ('H', 'S')),
    '-i': (math.pi / 2, 3 * math.pi / 2, '|−i⟩', ('H', 'SDG')),
}
PRESET_ORDER = ('0', '1', '+', '-', '+i', '-i')


def _close(a, b):
    return abs(a - b) < TOL


@dataclass(frozen=True)
class InitialState:
    theta: float = 0.0
    phi: float = 0.0

    def __post_init__(self):
        theta, phi = float(self.theta), float(self.phi)
        if not (math.isfinite(theta) and math.isfinite(phi)):
            raise ValueError('Initial-state angles must be finite')
        if theta < -TOL or theta > math.pi + TOL:
            raise ValueError('θ must be between 0 and π')
        theta = min(max(theta, 0.0), math.pi)
        phi = phi % (2 * math.pi)
        if _close(phi, 2 * math.pi):
            phi = 0.0
        if _close(theta, 0.0) or _close(theta, math.pi):
            phi = 0.0  # only a global phase at the poles
        object.__setattr__(self, 'theta', theta)
        object.__setattr__(self, 'phi', phi)

    @classmethod
    def preset(cls, key):
        if key not in PRESETS:
            raise ValueError('Unknown initial state: ' + str(key))
        theta, phi, _, _ = PRESETS[key]
        return cls(theta, phi)

    @property
    def preset_key(self):
        """The matching preset key, or None for a custom state."""
        for key, (theta, phi, _, _) in PRESETS.items():
            if _close(self.theta, theta) and _close(self.phi, phi):
                return key
        return None

    @property
    def is_default(self):
        return self.preset_key == '0'

    @property
    def label(self):
        key = self.preset_key
        return PRESETS[key][2] if key else '|ψ⟩'

    def vector(self):
        return np.array([math.cos(self.theta / 2),
                         np.exp(1j * self.phi) * math.sin(self.theta / 2)], complex)

    def bloch(self):
        return (math.sin(self.theta) * math.cos(self.phi),
                math.sin(self.theta) * math.sin(self.phi), math.cos(self.theta))

    def preparation(self, qubit):
        """Gates that prepare this state from |0⟩ on the given qubit.

        Presets use the textbook gates; a custom state uses U(θ, φ, 0),
        which maps |0⟩ to exactly cos(θ/2)|0⟩ + e^{iφ} sin(θ/2)|1⟩.
        """
        key = self.preset_key
        if key is not None:
            return [Gate(name, (qubit,)) for name in PRESETS[key][3]]
        return [Gate('U', (qubit,), self.theta, self.phi, 0.0)]

    def to_record(self):
        key = self.preset_key
        return {'preset': key} if key else {'theta_radians': self.theta, 'phi_radians': self.phi}

    @classmethod
    def from_record(cls, record):
        if not isinstance(record, dict):
            raise ValueError('Invalid initial-state record')
        if 'preset' in record:
            return cls.preset(record['preset'])
        theta, phi = record.get('theta_radians'), record.get('phi_radians', 0.0)
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (theta, phi)):
            raise ValueError('Invalid initial-state angles')
        return cls(float(theta), float(phi))


DEFAULT = InitialState()


def defaults(n):
    return [DEFAULT] * n


def all_default(states):
    return all(s.is_default for s in states)


def product_state(states):
    """Statevector of the product state, q0 as the most significant factor."""
    if not 1 <= len(states) <= MAX_QUBITS:
        raise ValueError(f'Qubits must be 1–{MAX_QUBITS}')
    vec = np.array([1.0 + 0j])
    for s in states:
        vec = np.kron(vec, s.vector())
    return vec


def preparation_gates(states):
    """Preparation gates for all non-default qubits, in qubit order."""
    gates = []
    for q, s in enumerate(states):
        gates.extend(s.preparation(q))
    return gates
