"""v0.7.5: exact Bell-experiment physics (physics/bell.py)."""
import math

import numpy as np
import pytest

from quantumscope.physics import bell as B
from quantumscope.physics.qubits import singlet_correlation, singlet_joint_probabilities

PURE = ('phi+', 'phi-', 'psi+', 'psi-')
ANGLES = [(a, b) for a in (-90, -30, 0, 22.5, 60, 135) for b in (-45, 0, 30, 90, 170)]


def test_states_are_valid_density_matrices():
    for name in B.STATES:
        for v in (1, 0.7, 0):
            rho = B.density(name, v)
            assert np.allclose(rho, rho.conj().T) and np.trace(rho) == pytest.approx(1)
            assert np.linalg.eigvalsh(rho).min() > -1e-12
    with pytest.raises(ValueError):
        B.density('nope')


@pytest.mark.parametrize('name,formula', [('phi+', lambda a, b: math.cos(a - b)), ('psi-', lambda a, b: -math.cos(a - b)),
                                          ('phi-', lambda a, b: math.cos(a + b)), ('psi+', lambda a, b: -math.cos(a + b)),
                                          ('classical', lambda a, b: math.cos(a) * math.cos(b))])
def test_correlations_match_the_textbook_formulas(name, formula):
    rho = B.density(name)
    for a, b in ANGLES:
        p = B.joint(rho, a, b)
        assert p.sum() == pytest.approx(1) and p.min() > -1e-12
        assert B.correlation(rho, a, b) == pytest.approx(formula(math.radians(a), math.radians(b)), abs=1e-12)
        assert B.correlation(B.density(name, 0.6), a, b) == pytest.approx(0.6 * formula(math.radians(a), math.radians(b)))


def test_agrees_with_the_existing_singlet_functions():
    rho = B.density('psi-')
    for a, b in ANGLES:
        assert np.allclose(B.joint(rho, a, b), singlet_joint_probabilities(a, b))
        assert B.correlation(rho, a, b) == pytest.approx(singlet_correlation(a, b))


def test_each_qubit_alone_is_random_and_alice_fixes_bob():
    for name in PURE:
        rho = B.density(name)
        assert np.allclose(B.bloch(rho, 0), 0) and np.allclose(B.bloch(rho, 1), 0)      # maximally mixed
        for a in (0, 37, 90):
            total = 0
            for s in (1, -1):
                p, bob = B.after_alice(rho, a, s)
                total += p
                assert p == pytest.approx(0.5) and np.linalg.norm(bob) == pytest.approx(1)  # now definite
                # Bob's own statistics along any axis b equal the prediction of the joint table
                for b in (0, 50):
                    assert (1 + bob @ B.axis(b)) / 2 == pytest.approx(B.joint(rho, a, b)[0 if s == 1 else 1, 0] / p)
            assert total == pytest.approx(1)
    _, bob = B.after_alice(B.density('phi+', 0.5), 0, 1)
    assert np.linalg.norm(bob) == pytest.approx(0.5)                                    # noise: only partly


def test_no_signalling_bobs_average_state_is_unchanged():
    for name in B.STATES:
        rho = B.density(name, 0.8)
        for a in (0, 60, 90):
            mixed = sum(p * bob for p, bob in (B.after_alice(rho, a, s) for s in (1, -1)))
            assert np.allclose(mixed, B.bloch(rho, 1))


def test_chsh_quantum_and_classical_limits():
    for name in PURE:
        angles = B.chsh_angles(name)
        assert abs(B.chsh(B.density(name), *angles)) == pytest.approx(B.QUANTUM_LIMIT)
        for v in (0.9, 1 / math.sqrt(2), 0.5):
            assert abs(B.chsh(B.density(name, v), *angles)) == pytest.approx(B.QUANTUM_LIMIT * v)
    assert abs(B.chsh(B.density('phi+', 1 / math.sqrt(2)), *B.chsh_angles('phi+'))) == pytest.approx(B.CLASSICAL_LIMIT)
    rho = B.density('classical')
    grid = np.arange(-180, 180, 30)                                                     # a coarse search is enough
    best = max(abs(B.chsh(rho, a, a2, b, b2)) for a in grid[::2] for a2 in grid[::2] for b in grid[::2] for b2 in grid[::2])
    assert best <= B.CLASSICAL_LIMIT + 1e-9                                             # never beats 2


def test_classical_model_has_the_same_perfect_correlations():
    for name in PURE:
        rho = B.density(name)
        for a, b in ANGLES:
            model = B.classical_model(name, a, b)
            assert -1 - 1e-12 <= model <= 1 + 1e-12
            if abs(B.correlation(rho, a, b)) > 1 - 1e-9:
                assert model == pytest.approx(B.correlation(rho, a, b))
    assert B.classical_model('classical', 0, 0) is None


def test_sampling_follows_the_joint_probabilities():
    rho = B.density('phi+', 0.9)
    alice, bob = B.sample(rho, 0, 60, 40000, rng=np.random.default_rng(4))
    assert set(np.unique(alice)) <= {1, -1}
    assert np.mean(alice * bob) == pytest.approx(B.correlation(rho, 0, 60), abs=0.02)
