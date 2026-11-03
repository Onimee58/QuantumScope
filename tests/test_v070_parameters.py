"""v0.7.0 (9b): parameterized circuits and observables."""
import json
import math

import numpy as np
import pytest

from quantumscope.editor.circuit_model import CircuitModel, EditorError
from quantumscope.physics import observables as O
from quantumscope.physics.circuit_files import from_native, from_native_layout, to_native_measured

RNG = np.random.default_rng(9)


# ---- observables ---------------------------------------------------------------------------------

@pytest.mark.parametrize('text', ['Z0 Z1 + 0.5 X0', '-1.2 Y1 Y2 + 0.3 X0 Y1 Z2 - 0.7', 'X0*Z2', '2 Z0 − 0.5 Z1'])
def test_expectation_matches_the_matrix_for_pure_and_mixed_states(text):
    n = 3
    terms = O.parse(text, n)
    M = O.matrix(n, terms)
    psi = RNG.normal(size=8) + 1j * RNG.normal(size=8)
    psi /= np.linalg.norm(psi)
    A = RNG.normal(size=(8, 8)) + 1j * RNG.normal(size=(8, 8))
    rho = A @ A.conj().T
    rho /= np.trace(rho)
    assert O.expectation(psi, n, terms) == pytest.approx(np.vdot(psi, M @ psi).real)
    assert O.expectation(rho, n, terms) == pytest.approx(np.trace(rho @ M).real)
    assert np.allclose(M, M.conj().T)


def test_ground_energy_and_text():
    assert O.ground_energy(1, O.parse('Z0 + 0.5 X0')) == pytest.approx(-math.sqrt(1.25))
    assert O.ground_energy(2, O.parse('Z0 Z1 + 0.5 X0')) == pytest.approx(-math.sqrt(1.25))
    assert O.text(O.parse('Z0 Z1 - 0.5 X0')) == 'Z0 Z1 - 0.5 X0'


@pytest.mark.parametrize('bad', ['', 'Z0 Z0', 'Q1', 'Z0 + ', 'Z5'])
def test_unreadable_observables(bad):
    with pytest.raises(ValueError):
        O.parse(bad, n=3) if bad != 'Z0 + ' else O.parse('Z0 + Q', n=3)


# ---- parameters and bindings ------------------------------------------------------------------------

def ansatz():
    m = CircuitModel(2)
    m.place('RY', 0, 0, angle=0.4)
    m.place('RY', 1, 0)
    m.place('CX', 1, 1)
    m.add_operand(0, 1)
    return m


def test_binding_a_new_parameter_keeps_the_circuit():
    m = ansatz()
    m.bind(0, 0, 'angle', 'θ')
    assert m.parameters['θ'] == pytest.approx(0.4) and m.gates[(0, 0)].angle == pytest.approx(0.4)
    m.bind(0, 0, 'angle', 'half', 2.0)                          # new parameter with a factor: value = angle / 2
    assert m.parameters['half'] == pytest.approx(0.2) and m.gates[(0, 0)].angle == pytest.approx(0.4)


def test_parameters_drive_every_bound_gate():
    m = ansatz()
    m.bind(0, 0, 'angle', 'θ')
    m.bind(1, 0, 'angle', 'θ', -2.0)
    m.set_parameter('θ', 0.3)
    assert m.gates[(0, 0)].angle == pytest.approx(0.3) and m.gates[(1, 0)].angle == pytest.approx(-0.6)
    assert m.binding_text((1, 0)) == '-2·θ'


def test_bindings_follow_moves_and_columns_and_undo():
    m = ansatz()
    m.bind(0, 0, 'angle', 'θ')
    m.insert_column(0)
    assert (0, 1, 'angle') in m.bindings
    m.move(0, 1, 0, 3)
    assert (0, 3, 'angle') in m.bindings
    m.set_parameter('θ', 1.0)
    assert m.gates[(0, 3)].angle == pytest.approx(1.0)
    m.undo()
    assert m.parameters['θ'] == pytest.approx(0.4)
    m.remove(0, 3)
    assert not m.bindings and 'θ' in m.parameters


def test_slider_moves_are_one_undo_step():
    m = ansatz()
    m.bind(0, 0, 'angle', 'θ')
    m.snapshot()                                                 # the panel snapshots when a drag starts
    for v in (0.5, 0.7, 0.9):
        m.set_parameter('θ', v, record=False)
    m.undo()
    assert m.parameters['θ'] == pytest.approx(0.4)


def test_removing_a_parameter_keeps_current_angles():
    m = ansatz()
    m.bind(0, 0, 'angle', 'θ')
    m.set_parameter('θ', 1.1)
    m.remove_parameter('θ')
    assert not m.bindings and m.gates[(0, 0)].angle == pytest.approx(1.1)


@pytest.mark.parametrize('call', [lambda m: m.add_parameter('2bad'), lambda m: m.add_parameter('pi'),
                                  lambda m: m.bind(0, 1, 'angle', 'θ'), lambda m: m.bind(0, 0, 'angle', 'θ', 0),
                                  lambda m: m.set_parameter('nope', 1), lambda m: m.set_observable('Z9')])
def test_invalid_parameter_operations(call):
    m = ansatz()
    with pytest.raises(EditorError):
        call(m)


def test_u_gate_fields_and_expectation_with_noise_and_branches():
    m = CircuitModel(1)
    m.place('U', 0, 0, angle=0.1, phi=0.2, lam=0.3)
    m.bind(0, 0, 'phi', 'φ')
    m.set_parameter('φ', 1.0)
    assert m.gates[(0, 0)].phi == pytest.approx(1.0) and m.gates[(0, 0)].angle == pytest.approx(0.1)
    p = CircuitModel(1)
    p.place('H', 0, 0)
    p.set_observable('X0')
    assert p.expectation() == pytest.approx(1)
    from quantumscope.physics.noise import NoiseModel
    p.set_noise_model(NoiseModel(True, single=0.5))
    assert p.expectation() == pytest.approx(0.5)                  # depolarizing p shrinks ⟨X⟩ by 1 − p
    p.set_noise_model(NoiseModel())
    p.place_measure(0, 1)
    assert p.expectation() == pytest.approx(0)                    # measuring removes the coherence


# ---- files -----------------------------------------------------------------------------------------

def saved(m):
    gates, cols, mcol, total = m.layout()
    return to_native_measured(m.n, gates, sorted(m.measurements), layout={
        'columns': cols, 'measurement_column': mcol, 'total_columns': total, 'initial_states': m.initial_states,
        'blocks': [], 'noise': [], 'noise_model': m.noise_model, 'classical': [], 'conditions': [],
        'variational': m.variational_meta()})


def test_round_trip_and_older_readers_use_current_angles():
    m = ansatz()
    m.bind(0, 0, 'angle', 'θ')
    m.bind(1, 0, 'angle', 'θ', 2.0)
    m.set_parameter('θ', 0.35)
    m.set_observable('Z0 Z1')
    text = saved(m)
    data = json.loads(text)
    assert data['schema_version'] == 1 and data['variational']['parameters'] == {'θ': 0.35}
    n, gates, measured, layout = from_native_layout(text)
    copy = CircuitModel()
    copy.set_circuit(n, gates, layout['columns'], measured)
    assert copy.restore_variational(layout['variational'])
    assert copy.bindings == m.bindings and copy.observable == 'Z0 Z1' and copy.expectation() == pytest.approx(m.expectation())
    old_gates = from_native(text)[1]                              # an older reader: concrete current angles
    assert sorted(g.angle for g in old_gates if g.name == 'RY') == pytest.approx([0.35, 0.7])


@pytest.mark.parametrize('meta', [{'parameters': {'2x': 1}}, {'parameters': {'a': 1}, 'bindings': [
    {'row': 0, 'column': 0, 'field': 'angle', 'name': 'missing', 'factor': 1}]}, {'observable': 'Q7'}, 'nope'])
def test_invalid_variational_metadata_is_ignored(meta):
    m = ansatz()
    assert m.restore_variational(meta) is False and not m.parameters


@pytest.mark.parametrize('typed,name', [('\\gamma0', 'γ0'), ('\\theta', 'θ'), ('\\alpha2', 'α2'),
                                        ('\\beta_1', 'β_1'), ('theta', 'theta'), ('gamma0', 'gamma0'), ('b1', 'b1')])
def test_latex_greek_names(typed, name):
    m = CircuitModel(1)
    m.add_parameter(typed)
    assert list(m.parameters) == [name]


def test_pi_and_unknown_latex_names_are_rejected():
    m = CircuitModel(1)
    for bad in ('pi', '\\gammas', '\\'):
        with pytest.raises(EditorError):
            m.add_parameter(bad)


def test_latex_names_reach_existing_greek_parameters():
    m = CircuitModel()
    m.load_library('qaoa', {'graph': 'ring4', 'layers': 1})
    m.set_parameter('\\gamma0', 0.7)
    assert m.parameters['γ0'] == pytest.approx(0.7)
    before = set(m.parameters)
    key = next(k for k, g in m.gates.items() if g.name == 'RX')
    m.bind(*key, 'angle', '\\beta0', 2.0)
    assert set(m.parameters) == before and m.bindings[(*key, 'angle')] == ('β0', 2.0)


def test_randomize_parameters_range_undo_and_one_name():
    import numpy as np
    m = CircuitModel()
    m.load_library('qaoa', {'graph': 'ring4', 'layers': 2})
    before = dict(m.parameters)
    chosen = m.randomize_parameters(rng=np.random.default_rng(5))
    assert set(chosen) == set(before) and all(-math.pi <= v < math.pi for v in chosen.values())
    key = next(k for k, v in m.bindings.items() if v[0] == 'β0')
    assert m.gates[key[:2]].angle == pytest.approx(2 * m.parameters['β0'])     # gates follow
    m.undo()
    assert m.parameters == before
    m.randomize_parameters(['γ1'], rng=np.random.default_rng(6))
    assert all(m.parameters[n] == before[n] for n in before if n != 'γ1') and m.parameters['γ1'] != before['γ1']
    assert m.randomize_parameters(['nope']) == {}
