"""A variational quantum classifier (NumPy and SciPy, no Qt).

For a data point x (one feature per qubit) the circuit is
    feature map U(x), then `layers` × [RY(θ) on every qubit, then a ring of CNOTs],
and the model's output is f(x) = ⟨Z₀⟩ + b, between −1 and 1 plus a bias b; the predicted class is
sign(f). Training lowers the mean squared error ½·mean((f − y)²) for labels y = ±1, with exact
gradients from the parameter-shift rule (every θ sits in an RY gate). The whole training set is
simulated at once, so training takes seconds.
"""
import math

import numpy as np

from quantumscope.ml import kernels
from quantumscope.physics.circuits import Gate


class Classifier:
    def __init__(self, qubits, layers=2, feature_map='angle', reps=1, bandwidth=1.0, seed=0):
        self.qubits, self.layers = int(qubits), int(layers)
        self.feature_map, self.reps, self.bandwidth = feature_map, reps, bandwidth
        rng = np.random.default_rng(seed)
        self.theta = rng.uniform(-0.1, 0.1, self.layers * self.qubits)    # near the identity
        self.bias = 0.0

    # ---- the circuit -----------------------------------------------------------------------------
    def gates(self, x, theta=None):
        """The full circuit for one data point, as gates for the circuit simulator."""
        theta = self.theta if theta is None else theta
        out = kernels.circuit(x, self.feature_map, self.reps, self.bandwidth)
        for layer in range(self.layers):
            out += [Gate('RY', (q,), float(theta[layer * self.qubits + q])) for q in range(self.qubits)]
            out += self._ring()
        return out

    def _ring(self):
        n = self.qubits
        if n == 1:
            return []
        if n == 2:
            return [Gate('CX', (0, 1))]
        return [Gate('CX', (q, (q + 1) % n)) for q in range(n)]

    # ---- batched simulation ----------------------------------------------------------------------
    def _ry(self, states, qubit, angle):
        n = self.qubits
        c, s = math.cos(angle / 2), math.sin(angle / 2)
        view = states.reshape(len(states), 2 ** qubit, 2, 2 ** (n - qubit - 1))
        zero, one = view[:, :, 0, :].copy(), view[:, :, 1, :].copy()
        view[:, :, 0, :] = c * zero - s * one
        view[:, :, 1, :] = s * zero + c * one
        return states

    def _cx(self, states, control, target):
        n = self.qubits
        index = np.arange(2 ** n)
        flipped = np.where((index >> (n - 1 - control)) & 1, index ^ (1 << (n - 1 - target)), index)
        return states[:, flipped]

    def _forward(self, start, theta):
        states = start.copy()
        for layer in range(self.layers):
            for q in range(self.qubits):
                states = self._ry(states, q, theta[layer * self.qubits + q])
            for gate in self._ring():
                states = self._cx(states, *gate.targets)
        z0 = 1 - 2 * ((np.arange(2 ** self.qubits) >> (self.qubits - 1)) & 1)   # Z on q0
        return (np.abs(states) ** 2) @ z0

    def expectation(self, X, theta=None):
        """⟨Z₀⟩ for every row of X."""
        theta = self.theta if theta is None else theta
        return self._forward(kernels.states(X, self.feature_map, self.reps, self.bandwidth), theta)

    def decision(self, X):
        return self.expectation(X) + self.bias

    def predict(self, X):
        return np.where(self.decision(X) >= 0, 1, -1)

    # ---- training --------------------------------------------------------------------------------
    def loss(self, X, y, theta=None, bias=None):
        theta = self.theta if theta is None else theta
        bias = self.bias if bias is None else bias
        return float(0.5 * np.mean((self.expectation(X, theta) + bias - y) ** 2))

    def gradient(self, X, y, theta=None, bias=None):
        """Exact gradient of the loss: the parameter-shift rule for each θ, plus ∂/∂b."""
        theta = self.theta if theta is None else theta
        bias = self.bias if bias is None else bias
        start = kernels.states(X, self.feature_map, self.reps, self.bandwidth)
        residual = self._forward(start, theta) + bias - y
        grad = np.zeros(len(theta))
        for k in range(len(theta)):
            shift = np.zeros(len(theta))
            shift[k] = math.pi / 2
            d = (self._forward(start, theta + shift) - self._forward(start, theta - shift)) / 2
            grad[k] = float(np.mean(residual * d))
        return grad, float(np.mean(residual))

    def train(self, X, y, method='BFGS', steps=100, rate=0.1, callback=None):
        """Lower the loss. callback(step, loss, accuracy) after every step; return False to stop.
        Returns the history: a list of (step, loss, training accuracy)."""
        X, y = np.asarray(X, float), np.asarray(y, float)
        history = []

        def report(theta, bias):
            self.theta, self.bias = np.array(theta), float(bias)
            entry = (len(history), self.loss(X, y), float(np.mean(self.predict(X) == y)))
            history.append(entry)
            return callback is None or callback(*entry) is not False
        report(self.theta, self.bias)
        if method == 'BFGS':
            from scipy.optimize import minimize
            stop = [False]

            def objective(v):
                return self.loss(X, y, v[:-1], v[-1])

            def jacobian(v):
                g, gb = self.gradient(X, y, v[:-1], v[-1])
                return np.r_[g, gb]

            def step(v):
                if not stop[0] and not report(v[:-1], v[-1]):
                    stop[0] = True
                    raise StopIteration
            try:
                result = minimize(objective, np.r_[self.theta, self.bias], jac=jacobian, method='BFGS',
                                  callback=step, options={'maxiter': int(steps), 'gtol': 1e-6})
                self.theta, self.bias = result.x[:-1], float(result.x[-1])
            except StopIteration:
                pass
            return history
        if method != 'Adam':
            raise ValueError(f'Unknown method {method!r}')
        m, v = np.zeros(len(self.theta) + 1), np.zeros(len(self.theta) + 1)
        params = np.r_[self.theta, self.bias]
        for t in range(1, int(steps) + 1):
            g, gb = self.gradient(X, y, params[:-1], params[-1])
            g = np.r_[g, gb]
            m = 0.9 * m + 0.1 * g
            v = 0.999 * v + 0.001 * g * g
            params = params - rate * (m / (1 - 0.9 ** t)) / (np.sqrt(v / (1 - 0.999 ** t)) + 1e-8)
            if not report(params[:-1], params[-1]):
                break
        return history
