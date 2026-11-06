"""v0.8.0 (16e): the variational quantum linear solver (physics.vqls and Algorithms → VQLS)."""
import re

import numpy as np
import pytest

from quantumscope.editor import variational as V
from quantumscope.editor.circuit_model import CircuitModel
from quantumscope.physics import vqls as Q
from quantumscope.physics.algorithms import entry, validate_params
from quantumscope.physics.observables import ground_energy, matrix, parse


@pytest.mark.parametrize('problem', list(Q.PRESETS))
def test_cost_is_a_faithful_pauli_sum_with_minimum_zero_at_the_solution(problem):
    n, A, b, text, about = Q.system({'problem': problem})
    H = Q.cost_operator(A, b)
    terms = parse(Q.pauli_text(H, n), n)
    assert np.allclose(matrix(n, terms), H, atol=1e-6)                         # the text is H
    assert np.allclose(H, H.conj().T) and np.linalg.eigvalsh(H).min() > -1e-12  # Hermitian, never negative
    x = Q.classical_solution(A, b)
    assert abs(ground_energy(n, terms)) < 1e-6 and abs(np.vdot(x, H @ x)) < 1e-12
    assert Q.normalized_cost(A, b, x) == pytest.approx(0, abs=1e-12) and Q.fidelity(A, b, x) == pytest.approx(1)
    assert np.allclose(A @ x / np.linalg.norm(A @ x), b * np.vdot(b, A @ x) / abs(np.vdot(b, A @ x)))


def test_condition_numbers_and_bad_systems():
    assert Q.condition_number(Q.system({'problem': 'standard'})[1]) == pytest.approx(7 / 3)
    assert Q.condition_number(Q.system({'problem': 'harder'})[1]) == pytest.approx(19)
    with pytest.raises(ValueError, match='not invertible'):
        Q.a_matrix('X0 Z1 + Z1 X0 - 2 X0 Z1', 2)
    with pytest.raises(ValueError, match='A:'):
        Q.a_matrix('1 + 0.3 Q0', 2)
    with pytest.raises(ValueError):
        Q.a_matrix('1', 4)                                                       # at most 3 qubits
    spec = entry('vqls').params
    with pytest.raises(ValueError, match='not invertible'):                    # caught in the dialog's check
        validate_params(spec, {'problem': 'custom', 'qubits': 1, 'matrix': 'X0 - X0', 'b': 'zeros'})
    assert validate_params(spec, {'problem': 'standard', 'matrix': 'X0 - X0'})['problem'] == 'standard'


def test_pauli_text_reads_back_and_never_uses_exponents():
    rng = np.random.default_rng(3)
    M = rng.normal(size=(4, 4)) + 1j * rng.normal(size=(4, 4))
    H = (M + M.conj().T) * 1e-4                                                 # tiny coefficients
    text = Q.pauli_text(H, 2, digits=9)
    assert not re.search(r'\d[eE][-+]?\d', text), text                           # no 1e-05 forms
    assert np.allclose(matrix(2, parse(text, 2)), H, atol=1e-8)


@pytest.mark.parametrize('params', [{'problem': 'standard', 'layers': 2}, {'problem': 'harder', 'layers': 2},
                                    {'problem': 'single', 'layers': 1},
                                    {'problem': 'custom', 'qubits': 2, 'matrix': '1 + 0.3 Z0 Z1 + 0.2 X0', 'b': 'plus',
                                     'layers': 2}])
def test_optimizing_the_circuit_solves_the_system(params):
    m = CircuitModel()
    m.load_library('vqls', params)
    n, A, b, _, _ = Q.system(params)
    assert m.n == n and m.observable and m.parameters
    best = V.optimize(m, 'BFGS', steps=300)[-1]
    for name, value in zip(V.Evaluator(m).names, best[0]):
        m.set_parameter(name, float(value))
    state = m.simulate().column_states[-1]
    assert best[1] < 1e-8 and Q.fidelity(A, b, state) > 0.999


def test_specification_passes_only_at_the_solution():
    from quantumscope.physics.algorithms import CircuitView
    params = validate_params(entry('vqls').params, {'problem': 'single', 'layers': 1})
    n, A, b, _, _ = Q.system(params)
    view = CircuitView(n, [], np.eye(2)[0], [], (), final_state=Q.classical_solution(A, b))
    rows, message = entry('vqls').spec(params, view)
    assert all(r.passed for r in rows) and 'prepares the solution' in message
    view.final_state = np.array([1.0, 0.0], complex)
    rows, message = entry('vqls').spec(params, view)
    assert not rows[0].passed and 'Optimize' in message
