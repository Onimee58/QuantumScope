"""Ideal spin-1/2 qubits and two-electron spin singlet.

No signaling, no literal spin trajectories. Measurement bases are directions in
one plane of the Bloch sphere; angles are measured in degrees from +z toward +x.
"""
import numpy as np


def qubit_state(theta_deg=90.0, phi_deg=0.0):
    """Return cos(theta/2)|up> + exp(i phi)sin(theta/2)|down>."""
    theta, phi = np.deg2rad([theta_deg, phi_deg])
    return np.array([np.cos(theta / 2), np.exp(1j * phi) * np.sin(theta / 2)], dtype=complex)


def spin_probabilities(state, angle_deg=0.0):
    """Born probabilities of +/- outcomes along direction in xz-plane."""
    state = np.asarray(state, dtype=complex)
    norm = np.linalg.norm(state)
    if state.shape != (2,) or not np.isfinite(norm) or norm == 0:
        raise ValueError('A normalized two-amplitude spin state is required')
    state = state / norm
    plus = qubit_state(angle_deg, 0)
    p = float(np.clip(abs(np.vdot(plus, state))**2, 0, 1))
    return np.array([p, 1-p])


def singlet_joint_probabilities(a_deg, b_deg):
    """Matrix p(A=+/- , B=+/-) for spin-singlet measurements."""
    correlation = -np.cos(np.deg2rad(a_deg - b_deg))
    return np.array([[(1+correlation)/4, (1-correlation)/4],
                     [(1-correlation)/4, (1+correlation)/4]])


def singlet_correlation(a_deg, b_deg):
    return float(-np.cos(np.deg2rad(a_deg - b_deg)))


def chsh_value(a=0, a_prime=90, b=45, b_prime=-45):
    return abs(singlet_correlation(a,b) + singlet_correlation(a,b_prime) +
               singlet_correlation(a_prime,b) - singlet_correlation(a_prime,b_prime))


# Gate-based two-spin preparation used by the interactive entanglement station.
# H on Alice followed by controlled-NOT (Alice controls Bob) is unitary.
# It produces |Phi+> from |up,up>, but does NOT entangle every possible input.
HADAMARD = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
CNOT = np.array([[1, 0, 0, 0], [0, 1, 0, 0],
                 [0, 0, 0, 1], [0, 0, 1, 0]], dtype=complex)


def prepare_gate_pair(alice, bob):
    """Return input product state and joint output after H(A), CNOT(A,B)."""
    product = np.kron(np.asarray(alice, dtype=complex), np.asarray(bob, dtype=complex))
    product = product / np.linalg.norm(product)
    output = CNOT @ (np.kron(HADAMARD, np.eye(2)) @ product)
    return product, output


def pair_concurrence(state):
    """Pure two-qubit entanglement concurrence: 0 product, 1 maximally entangled."""
    a, b, c, d = np.asarray(state, dtype=complex).reshape(4)
    return float(np.clip(2 * abs(a*d-b*c), 0, 1))


def pair_joint_probabilities(state, alice_axis=0, bob_axis=0):
    """Joint Born distribution for independent local axes in the xz plane."""
    state=np.asarray(state,dtype=complex).reshape(4)
    state=state/np.linalg.norm(state)
    a=qubit_state(alice_axis)
    b=qubit_state(bob_axis)
    axes_a=(a, qubit_state(alice_axis + 180))
    axes_b=(b, qubit_state(bob_axis + 180))
    probs=np.array([[abs(np.vdot(np.kron(u,v),state))**2 for v in axes_b]
                    for u in axes_a], dtype=float)
    return probs/probs.sum()


def local_measure_pair(state, axis, electron, rng=None):
    """Sample a local projective measurement and return result and post-measurement joint state."""
    if electron not in ('alice','bob'):
        raise ValueError('electron must be alice or bob')
    rng=np.random.default_rng() if rng is None else rng
    state=np.asarray(state,dtype=complex).reshape(4)
    state=state/np.linalg.norm(state)
    plus=qubit_state(axis)
    minus=qubit_state(axis+180)
    eye=np.eye(2,dtype=complex)
    projectors=[]
    for vector in (plus,minus):
        local=np.outer(vector,vector.conj())
        projectors.append(np.kron(local,eye) if electron=='alice' else np.kron(eye,local))
    probabilities=np.array([np.linalg.norm(P@state)**2 for P in projectors]);probabilities/=probabilities.sum()
    idx=int(rng.choice(2,p=probabilities))
    collapsed=projectors[idx]@state
    return (1 if idx==0 else -1), collapsed/np.linalg.norm(collapsed)
