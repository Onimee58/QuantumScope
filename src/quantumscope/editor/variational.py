"""Optimizing circuit parameters (Qt-free): energies, parameter-shift gradients, landscapes.

Every gate a parameter is bound to (RX, RY, RZ, P, CP and U angles) has a generator with
eigenvalue gap 1, so the exact parameter-shift rule applies to each occurrence:
    ∂E/∂g = [E(g + π/2) − E(g − π/2)] / 2,
and a parameter's gradient is the sum over its gates, each times its factor.
"""
import copy
import math

import numpy as np

from quantumscope.physics.circuits import Gate
from quantumscope.physics.observables import expectation, ground_energy, parse


class Evaluator:
    """Fast ⟨H⟩ for a model at different parameter values, without touching the model."""

    def __init__(self, model):
        if not model.observable:
            raise ValueError('Set an observable first (for example a Hamiltonian).')
        if not model.parameters:
            raise ValueError('The circuit has no parameters to optimize.')
        self.model = copy.deepcopy(model)
        self.names = list(model.parameters)
        self.terms = parse(model.observable, model.n)
        self.calls = 0

    def energy(self, values, shift=None):
        """⟨H⟩ at the given parameter values; shift=(key, field, δ) moves one gate angle only."""
        m = self.model
        m.parameters = dict(zip(self.names, map(float, values)))
        m._apply_bindings()
        if shift is not None:
            (r, c, field), delta = shift
            g = m.gates[(r, c)]
            fields = {'angle': g.angle, 'phi': g.phi, 'lam': g.lam}
            fields[field] += delta
            m.gates[(r, c)] = Gate(g.name, g.targets, fields['angle'], fields['phi'], fields['lam'])
        self.calls += 1
        state = m.simulate_noisy(store=False)[1][-1] if m.noisy else m.simulate().column_states[-1]
        return expectation(state, m.n, self.terms)

    def gradient(self, values):
        """Exact gradient by the parameter-shift rule (two circuit runs per bound gate)."""
        grad = np.zeros(len(self.names))
        index = {name: i for i, name in enumerate(self.names)}
        for key, (name, factor) in self.model.bindings.items():
            if name not in index:
                continue
            plus = self.energy(values, (key, math.pi / 2))
            minus = self.energy(values, (key, -math.pi / 2))
            grad[index[name]] += factor * (plus - minus) / 2
        return grad

    def exact_minimum(self):
        return ground_energy(self.model.n, self.terms) if self.model.n <= 10 else None


class History(list):
    """[(values, energy), …] of the steps taken, with the number of circuit evaluations used."""
    evaluations = 0


def optimize(model, method='BFGS', steps=100, rate=0.2, callback=None, tolerance=1e-7):
    """Minimize ⟨observable⟩ over the model's parameters.

    method: 'BFGS' (quasi-Newton with exact parameter-shift gradients), 'gradient' (plain descent
    with parameter-shift gradients), 'COBYLA' or 'Nelder-Mead' (gradient-free, from scipy).
    callback(iteration, values, energy) may return False to stop. Returns the history
    [(values, energy), …], starting with the current parameters.
    """
    ev = Evaluator(model)
    values = np.array([model.parameters[n] for n in ev.names], float)
    history = History([(values.copy(), ev.energy(values))])
    try:
        return _optimize(ev, values, history, method, steps, rate, callback, tolerance)
    finally:
        history.evaluations = ev.calls


def _optimize(ev, values, history, method, steps, rate, callback, tolerance):
    if callback is not None and callback(0, values, history[0][1]) is False:
        return history
    if method == 'gradient':
        # Gradient descent with a backtracking line search: a step that would raise ⟨H⟩ is
        # rejected and the step size halved; after a success it grows a little. A fixed step
        # overshoots when gradients are large (e.g. QAOA on bigger graphs) and oscillates.
        energy = history[0][1]
        for it in range(1, steps + 1):
            grad = ev.gradient(values)
            if np.linalg.norm(grad) < tolerance:
                break
            for _ in range(30):
                trial = values - rate * grad
                trial_energy = ev.energy(trial)
                if trial_energy <= energy:
                    break
                rate *= 0.5
            else:
                break                                              # no downhill step exists at this scale
            improvement = energy - trial_energy
            values, energy = trial, trial_energy
            rate = min(rate * 1.2, 2.0)
            history.append((values.copy(), energy))
            if callback is not None and callback(it, values, energy) is False:
                break
            if improvement < tolerance * 1e-2:
                break
        return history
    from scipy.optimize import minimize

    class Stop(Exception):
        pass

    def tracked(x):
        # Gradient-free methods try many probe points; only improvements are steps actually taken,
        # so the path and the curve show the trajectory (evaluations are counted separately).
        energy = ev.energy(x)
        if energy < history[-1][1] - 1e-15:
            history.append((np.array(x, float), energy))
            if callback is not None and callback(len(history) - 1, x, energy) is False:
                raise Stop
        elif callback is not None and ev.calls % 25 == 0 and callback(len(history) - 1, history[-1][0], history[-1][1]) is False:
            raise Stop
        return energy
    try:
        if method == 'BFGS':                                   # one recorded point per iteration
            def each(x):
                energy = ev.energy(x)
                history.append((np.array(x, float), energy))
                if callback is not None and callback(len(history) - 1, x, energy) is False:
                    raise Stop
            minimize(ev.energy, values, jac=ev.gradient, method='BFGS', callback=each,
                     options={'maxiter': steps, 'gtol': 1e-8})
        else:
            options = ({'maxiter': steps, 'rhobeg': 0.5} if method == 'COBYLA'
                       else {'maxiter': steps, 'xatol': 1e-6, 'fatol': 1e-9})
            minimize(tracked, values, method=method, options=options)
    except Stop:
        pass
    return history


def landscape(model, first, second=None, points=41, span=math.pi):
    """⟨H⟩ over one parameter (a curve) or two (a grid), others held at their current values.

    Returns (xs, energies) or (xs, ys, grid) with grid[i][j] at (xs[j], ys[i])."""
    ev = Evaluator(model)
    base = np.array([model.parameters[n] for n in ev.names], float)
    i1 = ev.names.index(first)
    xs = np.linspace(-span, span, points)
    if second is None:
        out = []
        for x in xs:
            v = base.copy()
            v[i1] = x
            out.append(ev.energy(v))
        return xs, np.array(out)
    i2 = ev.names.index(second)
    grid = np.zeros((points, points))
    for i, y in enumerate(xs):
        for j, x in enumerate(xs):
            v = base.copy()
            v[i1], v[i2] = x, y
            grid[i, j] = ev.energy(v)
    return xs, xs.copy(), grid


def wrap_safely(model, values):
    """Map parameters into [−π, π) where that cannot change the circuit's results: every gate a
    parameter drives has a whole-number factor, so shifting it by 2π changes each angle by a
    multiple of 2π (at most a global sign). Other parameters are returned unchanged."""
    names = list(model.parameters)
    factors = {name: [] for name in names}
    for _, (name, factor) in model.bindings.items():
        if name in factors:
            factors[name].append(factor)
    out = []
    for name, value in zip(names, values):
        whole = all(abs(f - round(f)) < 1e-12 for f in factors[name])
        out.append(float((value + math.pi) % (2 * math.pi) - math.pi) if whole else float(value))
    return out
