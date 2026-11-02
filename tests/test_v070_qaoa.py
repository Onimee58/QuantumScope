"""v0.7.0 (9d): QAOA for MaxCut."""
import pytest

from quantumscope.editor import variational as V
from quantumscope.editor.circuit_model import CircuitModel
from quantumscope.physics import maxcut as M
from quantumscope.physics.algorithms import qaoa_report
from quantumscope.physics.observables import ground_energy, parse


def optimized(graph, layers):
    m = CircuitModel()
    params = {'graph': graph, 'layers': layers}
    m.load_library('qaoa', params)
    for name, value in zip(list(m.parameters), V.optimize(m, 'BFGS', steps=300)[-1][0]):
        m.set_parameter(name, value)
    return m, params


@pytest.mark.parametrize('graph,best', [('ring4', 4), ('diamond', 4), ('ring5', 4), ('ring6', 6), ('prism', 7)])
def test_maximum_cuts_and_hamiltonian_minimum(graph, best):
    _, n, edges, _ = M.GRAPHS[graph]
    assert M.best_cuts(n, edges)[0] == best
    assert ground_energy(n, parse(M.hamiltonian(edges))) == pytest.approx(-best)


def test_cut_values():
    edges = M.GRAPHS['ring4'][2]
    assert M.cut_value('0101', edges) == 4 and M.cut_value('0011', edges) == 2 and M.cut_value('0000', edges) == 0
    assert M.expected_cut({'0101': 0.5, '0000': 0.5}, edges) == 2


def test_circuit_structure_and_bindings():
    m = CircuitModel()
    m.load_library('qaoa', {'graph': 'ring4', 'layers': 2})
    assert list(m.parameters) == ['γ0', 'β0', 'γ1', 'β1'] and m.roles[0] == 'node 0'
    factors = sorted({v for v in m.bindings.values()})
    assert ('γ0', -1.0) in factors and ('β1', 2.0) in factors
    assert sum(1 for v in m.bindings.values() if v[0] == 'γ0') == 4      # one RZ per edge
    assert sum(1 for v in m.bindings.values() if v[0] == 'β0') == 4      # one RX per node
    assert sorted(m.measurements) == [0, 1, 2, 3]


@pytest.mark.parametrize('graph', ['ring4', 'ring6'])
def test_even_rings_reach_three_quarters_at_one_layer(graph):
    m, params = optimized(graph, 1)
    average, best, *_ = qaoa_report(params, m.simulate().column_states[-1])
    assert average / best == pytest.approx(0.75, abs=1e-6)               # the known p = 1 result for rings


def test_two_layers_solve_the_square():
    m, params = optimized('ring4', 2)
    _, _, p_best, _, _ = qaoa_report(params, m.simulate().column_states[-1])
    assert p_best == pytest.approx(1, abs=1e-6)


@pytest.mark.parametrize('graph', ['ring4', 'diamond', 'ring5', 'ring6', 'prism'])
def test_check_passes_after_optimizing(graph):
    m, _ = optimized(graph, 1)
    rows, note = m.verification()
    assert all(r.passed for r in rows) and 'maximum cut' in note


def test_more_layers_raise_the_chance_of_a_best_cut():
    chances = []
    for layers in (1, 2):
        m, params = optimized('prism', layers)
        chances.append(qaoa_report(params, m.simulate().column_states[-1])[2])
    assert chances[1] > chances[0] + 0.2
