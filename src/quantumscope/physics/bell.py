"""Two-qubit Bell experiments, exactly (no Qt): states, noise, measurements, correlations, CHSH.

Measurement axes lie in the x–z plane: an angle a (degrees) means the direction (sin a, 0, cos a),
so 0° is z and 90° is x, as on the Superposition sphere. Outcome +1 means "along the axis".
States are density matrices; a visibility v < 1 mixes in complete randomness:
ρ = v |ψ⟩⟨ψ| + (1 − v) I/4 (a Werner-type state).
"""
import math

import numpy as np

I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)
_r = 1 / math.sqrt(2)
STATES = {
    'phi+': ('|Φ⁺⟩ = (|00⟩ + |11⟩)/√2', np.array([_r, 0, 0, _r], dtype=complex)),
    'phi-': ('|Φ⁻⟩ = (|00⟩ − |11⟩)/√2', np.array([_r, 0, 0, -_r], dtype=complex)),
    'psi+': ('|Ψ⁺⟩ = (|01⟩ + |10⟩)/√2', np.array([0, _r, _r, 0], dtype=complex)),
    'psi-': ('|Ψ⁻⟩ = (|01⟩ − |10⟩)/√2', np.array([0, _r, -_r, 0], dtype=complex)),
    'classical': ('Classically correlated: |00⟩ or |11⟩, 50% each', None),
}
CLASSICAL_LIMIT = 2.0
QUANTUM_LIMIT = 2 * math.sqrt(2)                          # Tsirelson's bound


def density(name='phi+', visibility=1.0):
    """The pair's density matrix (4×4); visibility in [0, 1] mixes in complete randomness."""
    if name not in STATES:
        raise ValueError(f'Unknown state {name!r}')
    v = float(min(1.0, max(0.0, visibility)))
    vector = STATES[name][1]
    if vector is None:                                     # ½(|00⟩⟨00| + |11⟩⟨11|): no superposition
        rho = np.diag([0.5, 0, 0, 0.5]).astype(complex)
    else:
        rho = np.outer(vector, vector.conj())
    return v * rho + (1 - v) * np.eye(4) / 4


def axis(angle):
    a = math.radians(angle)
    return np.array([math.sin(a), 0.0, math.cos(a)])


def projector(angle, outcome):
    """Projector for result outcome (+1 or −1) along the axis at `angle` degrees."""
    n = axis(angle)
    return (I2 + outcome * (n[0] * X + n[1] * Y + n[2] * Z)) / 2


def joint(rho, a, b):
    """2×2 array of p(Alice, Bob) with rows/columns ordered (+1, −1)."""
    out = np.zeros((2, 2))
    for i, s in enumerate((1, -1)):
        for j, t in enumerate((1, -1)):
            out[i, j] = float(np.real(np.trace(rho @ np.kron(projector(a, s), projector(b, t)))))
    return out


def correlation(rho, a, b):
    """E(a, b) = ⟨A·B⟩, from −1 (always opposite) to +1 (always equal)."""
    p = joint(rho, a, b)
    return float(p[0, 0] + p[1, 1] - p[0, 1] - p[1, 0])


def bloch(rho, qubit):
    """The Bloch vector of one qubit's own (reduced) state: 0 = Alice, 1 = Bob."""
    r = rho.reshape(2, 2, 2, 2)
    reduced = np.trace(r, axis1=1, axis2=3) if qubit == 0 else np.trace(r, axis1=0, axis2=2)
    return np.array([float(np.real(np.trace(reduced @ P))) for P in (X, Y, Z)])


def after_alice(rho, a, outcome):
    """(probability, Bob's Bloch vector) once Alice has found `outcome` along `a`."""
    P = np.kron(projector(a, outcome), I2)
    post = P @ rho @ P
    probability = float(np.real(np.trace(post)))
    if probability < 1e-12:
        return 0.0, np.zeros(3)
    return probability, bloch(post / probability, 1)


def sample(rho, a, b, count, rng=None):
    """count pairs: arrays (alice, bob) of ±1 outcomes."""
    rng = rng or np.random.default_rng()
    p = joint(rho, a, b).ravel()
    p = np.clip(p, 0, None)
    picks = rng.choice(4, size=int(count), p=p / p.sum())
    return np.where(picks < 2, 1, -1), np.where(picks % 2 == 0, 1, -1)


def chsh(rho, a, a2, b, b2):
    """S = E(a,b) + E(a,b′) + E(a′,b) − E(a′,b′)."""
    return (correlation(rho, a, b) + correlation(rho, a, b2) + correlation(rho, a2, b)
            - correlation(rho, a2, b2))


def chsh_angles(name='phi+'):
    """The four axes (a, a′, b, b′) giving the largest |S| for this state.
    Φ⁺ and Ψ⁻ correlate cos(a − b); Φ⁻ and Ψ⁺ correlate cos(a + b), so Bob's axes are mirrored."""
    standard, mirrored = (0, 90, 45, -45), (0, 90, -45, 45)
    rho = density(name)
    return max((standard, mirrored), key=lambda angles: abs(chsh(rho, *angles)))


def classical_model(name, a, b):
    """A simple local hidden-variable model with the same perfect correlations as the pure state:
    the quantum cos replaced by a straight-line (triangle) wave. None for the classical mixture."""
    sign_and_angle = {'phi+': (1, a - b), 'psi-': (-1, a - b), 'phi-': (1, a + b), 'psi+': (-1, a + b)}
    if name not in sign_and_angle:
        return None
    sign, angle = sign_and_angle[name]
    u = math.radians((angle + 180) % 360 - 180)            # into [−180°, 180°)
    return sign * (1 - 2 * abs(u) / math.pi)
