"""v0.7.0 (9c): optimizer, parameter-shift gradients, landscapes and VQE."""
import math

import numpy as np
import pytest

from quantumscope.editor import variational as V
from quantumscope.editor.circuit_model import CircuitModel
from quantumscope.physics.algorithms import H2_HAMILTONIAN, vqe_problem
from quantumscope.physics.observables import ground_energy, parse


def vqe(problem='h2', layers=1):
    m = CircuitModel()
    m.load_library('vqe', {'problem': problem, 'layers': layers})
    return m


def test_h2_hamiltonian_reproduces_the_known_ground_energy():
    assert ground_energy(2, parse(H2_HAMILTONIAN)) == pytest.approx(-1.137306, abs=1e-6)


@pytest.mark.parametrize('problem,expected', [('ising-2', -math.sqrt(2)), ('heisenberg-2', -3.0), ('heisenberg-3', -4.0)])
def test_spin_model_ground_energies(problem, expected):
    n, h, _ = vqe_problem(problem)
    assert ground_energy(n, parse(h)) == pytest.approx(expected)


def test_parameter_shift_gradient_is_exact():
    m = vqe('ising-3', 1)
    m.bind(0, 0, 'angle', 'θ0', 1.0)
    m.bind(1, 0, 'angle', 'θ0', -2.0)                         # one parameter on several gates, with factors
    ev = V.Evaluator(m)
    x = np.array([m.parameters[n] for n in ev.names]) + 0.37
    eps = 1e-6
    fd = [(ev.energy(x + eps * e) - ev.energy(x - eps * e)) / (2 * eps) for e in np.eye(len(x))]
    assert np.allclose(ev.gradient(x), fd, atol=1e-7)


def test_parameter_shift_with_p_and_u_gates():
    m = CircuitModel(1)
    m.place('H', 0, 0)
    m.place('P', 0, 1, angle=0.3)
    m.place('U', 0, 2, angle=0.4, phi=0.2, lam=0.1)
    m.bind(0, 1, 'angle', 'a')
    m.bind(0, 2, 'lam', 'b')
    m.set_observable('X0 + 0.3 Y0')
    ev = V.Evaluator(m)
    x = np.array([0.7, -0.4])
    fd = [(ev.energy(x + 1e-6 * e) - ev.energy(x - 1e-6 * e)) / 2e-6 for e in np.eye(2)]
    assert np.allclose(ev.gradient(x), fd, atol=1e-7)


@pytest.mark.parametrize('problem,layers', [('h2', 1), ('ising-2', 1), ('ising-3', 2), ('heisenberg-2', 1),
                                            ('heisenberg-3', 2)])
def test_vqe_reaches_the_exact_ground_energy(problem, layers):
    m = vqe(problem, layers)
    history = V.optimize(m, 'BFGS', steps=300)
    assert history[-1][1] - V.Evaluator(m).exact_minimum() < 1e-6
    assert history[-1][1] <= history[0][1]


def test_too_few_layers_stop_above_the_minimum():
    m = vqe('heisenberg-3', 1)
    gap = V.optimize(m, 'BFGS', steps=300)[-1][1] - V.Evaluator(m).exact_minimum()
    assert gap > 0.1                                           # the circuit cannot represent the ground state


@pytest.mark.parametrize('method', ['gradient', 'COBYLA', 'Nelder-Mead'])
def test_other_methods_lower_the_energy(method):
    m = vqe('h2', 1)
    history = V.optimize(m, method, steps=400)
    assert history[-1][1] < history[0][1] - 0.5 and history[-1][1] - (-1.137306) < 0.01


def test_callback_can_stop_and_model_is_untouched():
    m = vqe('h2', 1)
    before = dict(m.parameters)
    history = V.optimize(m, 'BFGS', callback=lambda i, v, e: i < 3)
    assert len(history) <= 5 and m.parameters == before        # optimize() never edits the model itself


def test_vqe_check_and_errors():
    m = vqe('h2', 1)
    assert not m.verification()[0][0].passed
    values = V.optimize(m, 'BFGS')[-1][0]
    for name, v in zip(list(m.parameters), values):
        m.set_parameter(name, v)
    rows, note = m.verification()
    assert rows[0].passed and 'found the ground state' in note
    empty = CircuitModel(1)
    with pytest.raises(ValueError):
        V.Evaluator(empty)


def test_landscape_curve_and_grid():
    m = vqe('ising-2', 1)
    xs, energies = V.landscape(m, 'θ0', points=21)
    assert len(xs) == 21 and energies.shape == (21,)
    xs, ys, grid = V.landscape(m, 'θ0', 'θ1', points=9)
    assert grid.shape == (9, 9)
    ev = V.Evaluator(m)
    v = np.array([m.parameters[n] for n in ev.names])
    v[0], v[1] = xs[3], ys[5]
    assert grid[5, 3] == pytest.approx(ev.energy(v))
    assert grid.min() >= V.Evaluator(m).exact_minimum() - 1e-9    # no state beats the ground energy
