"""Quantum kernels and kernel classifiers (NumPy only, no Qt).

A feature map turns a data point x into a quantum state |φ(x)⟩; the quantum kernel is
K(x, x′) = |⟨φ(x)|φ(x′)⟩|², the overlap of two such states. A classical method (kernel ridge, or a
support vector machine) then separates the classes using only these overlaps.

Feature maps (one feature per qubit):
  angle — RY(xᵢ) on qubit i: a product state, K = ∏ cos²((xᵢ − x′ᵢ)/2).
  zz    — the ZZ feature map of Havlíček et al. (2019): reps × [H on every qubit, then
          exp(i Σᵢ xᵢ Zᵢ + i Σᵢ<ⱼ (π − xᵢ)(π − xⱼ) Zᵢ Zⱼ)], here with all-to-all pairs.
A bandwidth b scales the data first (x → b·x): small b makes the kernel smoother, which often
generalizes better (Shaydulin & Wild, 2022; Canatar et al., 2023).
On a quantum computer each kernel entry is estimated from shots (the share of all-zero results of
the circuit U(x′)† U(x)), so it carries statistical noise; estimate() reproduces that.
"""
import math

import numpy as np

from quantumscope.physics.circuits import Gate

FEATURE_MAPS = {'angle': 'Angle encoding (RY on each qubit)', 'zz': 'ZZ feature map (entangling)'}


def _zz_phases(x):
    """φᵢ = xᵢ and φᵢⱼ = (π − xᵢ)(π − xⱼ) for every pair i < j."""
    n = len(x)
    pairs = [(i, j, (math.pi - x[i]) * (math.pi - x[j])) for i in range(n) for j in range(i + 1, n)]
    return [(i, x[i]) for i in range(n)], pairs


def circuit(x, kind='zz', reps=2, bandwidth=1.0):
    """The feature-map circuit for one data point, as gates for the circuit simulator.
    exp(iφZ) is RZ(−2φ), and exp(iφ ZᵢZⱼ) is CX(i→j), RZ(−2φ) on j, CX(i→j)."""
    x = [float(v) * bandwidth for v in x]
    n = len(x)
    if kind == 'angle':
        return [Gate('RY', (i,), x[i]) for i in range(n)]
    if kind != 'zz':
        raise ValueError(f'Unknown feature map {kind!r}')
    gates = []
    for _ in range(max(1, int(reps))):
        gates += [Gate('H', (i,)) for i in range(n)]
        singles, pairs = _zz_phases(x)
        gates += [Gate('RZ', (i,), -2 * phi) for i, phi in singles]
        for i, j, phi in pairs:
            gates += [Gate('CX', (i, j)), Gate('RZ', (j,), -2 * phi), Gate('CX', (i, j))]
    return gates


def _z_values(n):
    """zₖ = ±1 for every basis state, q0 as the most significant bit (as in the simulator)."""
    index = np.arange(2 ** n)
    return np.array([1 - 2 * ((index >> (n - 1 - k)) & 1) for k in range(n)], float)   # n × 2ⁿ


def states(X, kind='zz', reps=2, bandwidth=1.0):
    """|φ(x)⟩ for every row of X: an array of shape (samples, 2ⁿ)."""
    X = np.atleast_2d(np.asarray(X, float)) * bandwidth
    samples, n = X.shape
    if kind == 'angle':
        out = np.ones((samples, 1), complex)
        for k in range(n):
            qubit = np.stack([np.cos(X[:, k] / 2), np.sin(X[:, k] / 2)], axis=1)
            out = np.einsum('si,sj->sij', out, qubit).reshape(samples, -1)
        return out
    if kind != 'zz':
        raise ValueError(f'Unknown feature map {kind!r}')
    z = _z_values(n)
    phase = X @ z                                                        # Σᵢ xᵢ zᵢ
    for i in range(n):
        for j in range(i + 1, n):
            phase += np.outer((math.pi - X[:, i]) * (math.pi - X[:, j]), z[i] * z[j])
    diagonal = np.exp(1j * phase)                                        # samples × 2ⁿ
    hadamard = np.ones((2 ** n, 2 ** n))
    for k in range(n):                                                   # H⊗ⁿ: (−1)^(popcount(i & j))
        bit = 1 << (n - 1 - k)
        rows = (np.arange(2 ** n)[:, None] & bit) > 0
        cols = (np.arange(2 ** n)[None, :] & bit) > 0
        hadamard *= np.where(rows & cols, -1.0, 1.0)
    hadamard /= math.sqrt(2 ** n)
    state = np.zeros((samples, 2 ** n), complex)
    state[:, 0] = 1
    for _ in range(max(1, int(reps))):
        state = (state @ hadamard.T) * diagonal
    return state


def kernel(A, B=None, kind='zz', reps=2, bandwidth=1.0):
    """K[a, b] = |⟨φ(A[a])|φ(B[b])⟩|² (B defaults to A)."""
    SA = states(A, kind, reps, bandwidth)
    SB = SA if B is None else states(B, kind, reps, bandwidth)
    return np.abs(SA.conj() @ SB.T) ** 2


def estimate(K, shots, rng=None, symmetric=False):
    """K as a quantum computer would estimate it: each entry from `shots` runs (the share of
    all-zero results). symmetric: a training kernel, with its diagonal exactly 1 (no circuit needed)."""
    rng = rng or np.random.default_rng()
    if not shots:
        return np.array(K, float)
    noisy = rng.binomial(int(shots), np.clip(K, 0, 1)) / int(shots)
    if symmetric:
        upper = np.triu(noisy, 1)
        noisy = upper + upper.T + np.eye(len(K))
    return noisy


def rbf(A, B=None, gamma=1.0):
    """The classical Gaussian (RBF) kernel exp(−γ |a − b|²), for comparison."""
    A = np.atleast_2d(np.asarray(A, float))
    B = A if B is None else np.atleast_2d(np.asarray(B, float))
    d2 = (A ** 2).sum(1)[:, None] + (B ** 2).sum(1)[None, :] - 2 * A @ B.T
    return np.exp(-gamma * np.clip(d2, 0, None))


def accuracy(y_true, y_pred):
    return float(np.mean(np.asarray(y_true) == np.asarray(y_pred)))


class KernelRidge:
    """Kernel ridge classification: α = (K + λI)⁻¹ y, f(x) = Σ αᵢ K(x, xᵢ), label sign(f)."""

    def __init__(self, regularization=0.1):
        self.regularization = float(regularization)

    def fit(self, K, y):
        y = np.asarray(y, float)
        self.alpha = np.linalg.solve(K + self.regularization * np.eye(len(y)), y)
        return self

    def decision(self, K_test):
        """K_test: test × training kernel."""
        return K_test @ self.alpha

    def predict(self, K_test):
        return np.where(self.decision(K_test) >= 0, 1, -1)


class SVM:
    """A support vector machine for a precomputed kernel, trained with Platt's SMO algorithm.

    It solves  max Σαᵢ − ½ ΣΣ αᵢαⱼ yᵢyⱼ Kᵢⱼ  with 0 ≤ αᵢ ≤ C and Σ αᵢ yᵢ = 0;
    the decision is f(x) = Σ αᵢ yᵢ K(x, xᵢ) + b. Points with αᵢ > 0 are the support vectors.
    """

    def __init__(self, C=1.0, tolerance=1e-4, max_passes=200, seed=0):
        self.C, self.tolerance, self.max_passes, self.seed = float(C), tolerance, max_passes, seed

    def _f(self, i):
        return float((self.alpha * self.y) @ self.K[:, i] + self.b)

    def _step(self, i, j):
        if i == j:
            return False
        C, K, y, a = self.C, self.K, self.y, self.alpha
        Ei, Ej = self._f(i) - y[i], self._f(j) - y[j]
        if y[i] != y[j]:
            low, high = max(0.0, a[j] - a[i]), min(C, C + a[j] - a[i])
        else:
            low, high = max(0.0, a[i] + a[j] - C), min(C, a[i] + a[j])
        if high - low < 1e-12:
            return False
        eta = K[i, i] + K[j, j] - 2 * K[i, j]
        if eta <= 1e-12:                                                 # flat direction: skip this pair
            return False
        aj = float(np.clip(a[j] + y[j] * (Ei - Ej) / eta, low, high))
        if abs(aj - a[j]) < 1e-10:
            return False
        ai = a[i] + y[i] * y[j] * (a[j] - aj)
        b1 = self.b - Ei - y[i] * (ai - a[i]) * K[i, i] - y[j] * (aj - a[j]) * K[i, j]
        b2 = self.b - Ej - y[i] * (ai - a[i]) * K[i, j] - y[j] * (aj - a[j]) * K[j, j]
        self.alpha[i], self.alpha[j] = ai, aj
        self.b = b1 if 0 < ai < C else b2 if 0 < aj < C else (b1 + b2) / 2
        return True

    def fit(self, K, y):
        self.K, self.y = np.asarray(K, float), np.asarray(y, float)
        m = len(self.y)
        self.alpha, self.b = np.zeros(m), 0.0
        rng = np.random.default_rng(self.seed)
        tol, C = self.tolerance, self.C
        for _ in range(self.max_passes):
            changed = 0
            for i in rng.permutation(m):
                Ei = self._f(i) - self.y[i]
                r = Ei * self.y[i]
                if (r < -tol and self.alpha[i] < C) or (r > tol and self.alpha[i] > 0):
                    errors = (self.alpha * self.y) @ self.K + self.b - self.y
                    order = np.argsort(-np.abs(errors - Ei))                 # the largest step first
                    for j in order[:5]:
                        if self._step(i, int(j)):
                            changed += 1
                            break
                    else:
                        for j in rng.permutation(m):
                            if self._step(i, int(j)):
                                changed += 1
                                break
            if changed == 0:
                break
        self.support = np.flatnonzero(self.alpha > 1e-8)
        free = [k for k in self.support if self.alpha[k] < C - 1e-8]
        if free:                                                         # b from the margin's points
            self.b = float(np.mean([self.y[k] - (self.alpha * self.y) @ self.K[:, k] for k in free]))
        return self

    def dual_objective(self):
        ay = self.alpha * self.y
        return float(self.alpha.sum() - 0.5 * ay @ self.K @ ay)

    def decision(self, K_test):
        """K_test: test × training kernel."""
        return K_test @ (self.alpha * self.y) + self.b

    def predict(self, K_test):
        return np.where(self.decision(K_test) >= 0, 1, -1)
