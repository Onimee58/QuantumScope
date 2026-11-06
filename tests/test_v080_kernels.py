"""v0.8.0 (16b): feature maps, quantum kernels, shot noise, kernel ridge and the SVM."""
import math

import numpy as np
import pytest
from scipy.optimize import minimize

from quantumscope.ml import datasets as D
from quantumscope.ml import kernels as Kn
from quantumscope.physics.circuits import evolution

RNG = np.random.default_rng(7)


@pytest.mark.parametrize('kind', ['angle', 'zz'])
@pytest.mark.parametrize('n', [1, 2, 3, 4])
def test_states_match_the_circuit_simulator(kind, n):
    X = RNG.uniform(0, math.pi, (4, n))
    for x, state in zip(X, Kn.states(X, kind, reps=2, bandwidth=0.7)):
        simulated = evolution(n, Kn.circuit(x, kind, reps=2, bandwidth=0.7))[-1]
        assert abs(np.vdot(simulated, state)) == pytest.approx(1, abs=1e-12)         # equal up to a phase


def test_kernel_properties_formula_and_bandwidth():
    A = RNG.uniform(0, math.pi, (7, 3))
    K = Kn.kernel(A, kind='angle')
    assert np.allclose(K, np.prod(np.cos((A[:, None] - A[None]) / 2) ** 2, axis=2))
    for kind in ('angle', 'zz'):
        K = Kn.kernel(A, kind=kind)
        assert np.allclose(K, K.T) and np.allclose(np.diag(K), 1) and np.linalg.eigvalsh(K).min() > -1e-10
        assert np.allclose(Kn.kernel(A, kind=kind, bandwidth=0.3), Kn.kernel(0.3 * A, kind=kind))
    B = RNG.uniform(0, math.pi, (2, 3))
    assert Kn.kernel(B, A).shape == (2, 7) and np.all(Kn.kernel(B, A) <= 1 + 1e-12)
    with pytest.raises(ValueError):
        Kn.states(A, kind='nope')


def test_shot_noise_estimates():
    K = Kn.kernel(RNG.uniform(0, math.pi, (30, 2)), kind='zz')
    noisy = Kn.estimate(K, 1000, rng=np.random.default_rng(0), symmetric=True)
    assert np.allclose(noisy, noisy.T) and np.allclose(np.diag(noisy), 1)
    error = (noisy - K)[np.triu_indices(30, 1)]
    Kc = np.clip(K, 0, 1)                                                              # rounding: K may exceed 1
    expected = np.sqrt(Kc * (1 - Kc) / 1000)[np.triu_indices(30, 1)]
    assert abs(error.std() / expected.mean() - 1) < 0.25                                 # binomial spread
    assert np.array_equal(Kn.estimate(K, 0), K)                                         # 0 shots: exact


def test_kernel_ridge_is_the_closed_form():
    K = Kn.kernel(RNG.uniform(0, math.pi, (12, 2)))
    y = np.where(RNG.uniform(size=12) > 0.5, 1, -1)
    model = Kn.KernelRidge(0.2).fit(K, y)
    assert np.allclose((K + 0.2 * np.eye(12)) @ model.alpha, y)
    assert set(model.predict(K)) <= {1, -1}


def test_svm_solves_the_dual_and_meets_the_optimality_conditions():
    p = D.prepare(D.load('moons', samples=60, noise=0.15, seed=1), D.Recipe())
    K, y, C = Kn.kernel(p.X_train, kind='angle'), p.y_train.astype(float), 1.0
    svm = Kn.SVM(C=C, tolerance=1e-6, max_passes=500).fit(K, y)
    a = svm.alpha
    assert np.all(a >= -1e-9) and np.all(a <= C + 1e-9) and abs(a @ y) < 1e-6        # feasible
    Q = (y[:, None] * y[None]) * K                                                     # an independent solver
    reference = minimize(lambda v: 0.5 * v @ Q @ v - v.sum(), np.zeros(len(y)), jac=lambda v: Q @ v - 1,
                         bounds=[(0, C)] * len(y), constraints={'type': 'eq', 'fun': lambda v: v @ y},
                         method='SLSQP', options={'maxiter': 500, 'ftol': 1e-12})
    assert svm.dual_objective() == pytest.approx(-reference.fun, rel=1e-4)
    margin = y * svm.decision(K)                                                       # KKT conditions
    assert np.all(margin[a < 1e-6] >= 1 - 1e-3)                                        # outside the margin
    free = (a > 1e-6) & (a < C - 1e-6)
    assert np.allclose(margin[free], 1, atol=1e-3)                                     # on the margin
    assert np.all(margin[a > C - 1e-6] <= 1 + 1e-3)                                    # inside, or wrong side


def test_classifiers_learn_real_data():
    for name, qubits, kind, bandwidth, at_least in (('circles', 2, 'angle', 1.0, 0.9), ('iris', 3, 'zz', 0.1, 0.95),
                                                    ('breast_cancer', 3, 'zz', 1.0, 0.85)):
        ds = D.load(name)
        p = D.prepare(ds, D.check(ds, qubits=qubits)[2])
        Ktr = Kn.kernel(p.X_train, kind=kind, bandwidth=bandwidth)
        Kte = Kn.kernel(p.X_test, p.X_train, kind=kind, bandwidth=bandwidth)
        assert Kn.accuracy(p.y_test, Kn.SVM().fit(Ktr, p.y_train).predict(Kte)) >= at_least, name
    assert Kn.rbf(np.zeros((1, 2)), np.ones((1, 2)), gamma=0.5)[0, 0] == pytest.approx(math.exp(-1))
