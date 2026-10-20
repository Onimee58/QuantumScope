import numpy as np
from quantumscope.physics.qubits import (qubit_state, spin_probabilities,
    singlet_joint_probabilities, singlet_correlation, chsh_value)


def test_normalized_spin_state():
    assert np.isclose(np.linalg.norm(qubit_state(78, 231)), 1)


def test_z_basis_measurements():
    assert np.allclose(spin_probabilities(qubit_state(0), 0), [1, 0])
    assert np.allclose(spin_probabilities(qubit_state(180), 0), [0, 1])
    assert np.allclose(spin_probabilities(qubit_state(0), 90), [.5, .5])


def test_singlet_anticorrelated_parallel_axes():
    assert np.allclose(singlet_joint_probabilities(0,0), [[0, .5],[.5,0]])


def test_singlet_marginal_no_signaling():
    for angle in [-90,0,15,90,177]:
        p = singlet_joint_probabilities(22,angle)
        assert np.allclose(p.sum(axis=0), [.5,.5])
        assert np.allclose(p.sum(axis=1), [.5,.5])


def test_singlet_chsh():
    assert np.isclose(chsh_value(), 2*np.sqrt(2))
    assert np.isclose(singlet_correlation(0,90),0,atol=1e-12)
