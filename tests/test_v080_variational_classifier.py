"""v0.8.0 (16c): the variational quantum classifier (quantumscope.ml.variational)."""
import math

import numpy as np
import pytest

from quantumscope.ml import datasets as D
from quantumscope.ml import variational as V
from quantumscope.physics.circuits import evolution

RNG = np.random.default_rng(5)


@pytest.mark.parametrize('feature_map', ['angle', 'zz'])
@pytest.mark.parametrize('n', [1, 2, 3, 4])
def test_batched_model_matches_the_circuit_simulator(feature_map, n):
    model = V.Classifier(n, layers=2, feature_map=feature_map, reps=2, bandwidth=0.8)
    model.theta = RNG.uniform(-math.pi, math.pi, model.theta.size)
    z0 = 1 - 2 * ((np.arange(2 ** n) >> (n - 1)) & 1)
    X = RNG.uniform(0, math.pi, (3, n))
    for x, value in zip(X, model.expectation(X)):
        state = evolution(n, model.gates(x))[-1]
        assert float(np.abs(state) ** 2 @ z0) == pytest.approx(value, abs=1e-12)


def test_parameter_shift_gradient_is_exact():
    model = V.Classifier(3, layers=2, feature_map='zz')
    model.theta, model.bias = RNG.uniform(-1, 1, 6), 0.3
    X, y = RNG.uniform(0, math.pi, (8, 3)), np.where(RNG.uniform(size=8) > 0.5, 1.0, -1.0)
    grad, grad_bias = model.gradient(X, y)
    h = 1e-6
    for k in range(6):
        e = np.eye(6)[k] * h
        assert grad[k] == pytest.approx((model.loss(X, y, model.theta + e) - model.loss(X, y, model.theta - e)) / (2 * h),
                                        abs=1e-8)
    assert grad_bias == pytest.approx((model.loss(X, y, bias=0.3 + h) - model.loss(X, y, bias=0.3 - h)) / (2 * h), abs=1e-8)


@pytest.mark.parametrize('method', ['BFGS', 'Adam'])
def test_training_lowers_the_loss_and_classifies(method):
    p = D.prepare(D.load('circles'), D.Recipe())
    model = V.Classifier(2, layers=3, seed=0)
    steps = []
    history = model.train(p.X_train, p.y_train, method=method, steps=80, callback=lambda *s: steps.append(s))
    assert history[-1][1] < history[0][1] and steps == history
    assert np.mean(model.predict(p.X_test) == p.y_test) >= 0.85


def test_training_can_be_stopped_and_is_reproducible():
    p = D.prepare(D.load('moons'), D.Recipe())
    model = V.Classifier(2, layers=2, seed=1)
    history = model.train(p.X_train, p.y_train, method='Adam', steps=50, callback=lambda step, *_: step < 5)
    assert len(history) == 6                                                     # stopped after step 5
    a = V.Classifier(2, layers=2, seed=4).train(p.X_train, p.y_train, method='BFGS', steps=20)
    b = V.Classifier(2, layers=2, seed=4).train(p.X_train, p.y_train, method='BFGS', steps=20)
    assert a == b
    with pytest.raises(ValueError):
        model.train(p.X_train, p.y_train, method='nope')
