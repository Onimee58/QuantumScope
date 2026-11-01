"""v0.6.2 (8c): quantum phase estimation; example titles, qubit roles and saving them."""
import json
import math

import pytest

from quantumscope.editor.circuit_model import CircuitModel
from quantumscope.physics.algorithms import _phase_value, marginal
from quantumscope.physics.circuit_files import from_native_layout, to_native_measured


def qpe(t, phase):
    m = CircuitModel()
    m.load_library('qpe', {'t': t, 'phase': phase})
    return m


@pytest.mark.parametrize('t,phase', [(3, '3/8'), (2, '1/4'), (4, '5/16'), (6, '5/16')])
def test_exact_phases_are_read_with_certainty(t, phase):
    m = qpe(t, phase)
    rows, note = m.verification()
    assert rows[0].passed and rows[0].probability == pytest.approx(1) and 'certain' in note


@pytest.mark.parametrize('t,phase', [(3, '1/3'), (4, '1/3'), (5, '0.3'), (6, '0.1'), (2, '0.3')])
def test_inexact_phases_peak_at_the_closest_estimate(t, phase):
    m = qpe(t, phase)
    rows, _ = m.verification()
    assert rows[0].passed and 4 / math.pi ** 2 - 1e-9 <= rows[0].probability < 1


def test_more_counting_qubits_sharpen_the_estimate():
    def within_one(t):
        m = qpe(t, '1/3')
        probs = marginal(m.circuit_view().final_state, m.n, list(range(t)))
        best = round(_phase_value('1/3') * 2 ** t) % 2 ** t
        return sum(probs.get(format((best + d) % 2 ** t, f'0{t}b'), 0) for d in (-1, 0, 1))
    assert within_one(3) < within_one(6) or within_one(6) > 0.85
    errors = []
    for t in (2, 4, 6):
        probs = marginal(qpe(t, '1/3').circuit_view().final_state, t + 1, list(range(t)))
        best = max(probs, key=probs.get)
        errors.append(abs(int(best, 2) / 2 ** t - 1 / 3))
    assert errors[0] > errors[-1]


def test_qpe_check_fails_if_a_controlled_power_is_wrong():
    m = qpe(4, '5/16')
    key = next(k for k, g in m.gates.items() if g.name == 'CP')
    m.remove(*key)
    assert not m.verification()[0][0].passed


def test_qpe_layout_roles_and_measurements():
    m = qpe(4, '1/4')
    assert m.n == 5 and m.roles == ['count'] * 4 + ['eigenstate'] and sorted(m.measurements) == [0, 1, 2, 3]
    assert m.initial_states[4].label == '|1⟩' and any(pl.block.kind == 'iqft' for pl in m.blocks.values())


# ---- example identity ---------------------------------------------------------------------------

def test_roles_for_examples_and_none_for_plain_circuits():
    m = CircuitModel()
    m.load_library('bit_flip_code', {'logical': '0', 'error': 'q1', 'p': 0.1})
    assert m.roles == ['data'] * 3 + ['syndrome'] * 2
    m.load_library('teleportation', {'input': '+'})
    assert m.roles == ['Alice · input', 'Alice', 'Bob']
    m.set_circuit(2, [])
    assert m.roles == [] and m.active_entry is None


def test_edited_tracking_follows_edits_and_undo():
    m = CircuitModel()
    m.load_library('superdense', {'b0': 1, 'b1': 0})
    assert not m.entry_edited
    m.place('X', 1, 0)
    assert m.entry_edited
    m.undo()
    assert not m.entry_edited
    from quantumscope.physics.initial_states import InitialState
    m.set_initial_state(1, InitialState.preset('1'))
    assert m.entry_edited


def saved(m):
    gates, cols, mcol, total = m.layout()
    classical, conditions = m.classical_layout()
    return to_native_measured(m.n, gates, sorted(m.measurements), layout={
        'columns': cols, 'measurement_column': mcol, 'total_columns': total, 'initial_states': m.initial_states,
        'blocks': [(pl.block, pl.col, pl.expanded) for pl in m.blocks.values()], 'noise': m.noise_layout(),
        'noise_model': m.noise_model, 'classical': classical, 'conditions': conditions, 'example': m.example_meta()})


def reload(text):
    n, gates, measured, layout = from_native_layout(text)
    m = CircuitModel()
    m.set_circuit(n, gates, layout['columns'], measured, layout['measurement_column'], layout['total_columns'],
                  layout['initial_states'], layout['blocks'], layout['noise'], layout['noise_model'],
                  layout['classical'], layout['conditions'])
    m.restore_example(layout['example'])
    return m


@pytest.mark.parametrize('key,params', [('bit_flip_code', {'logical': '1', 'error': 'q2', 'p': 0.1}),
                                        ('teleportation', {'input': '-i'}), ('qpe', {'t': 3, 'phase': '3/8'}),
                                        ('shor_code', {'logical': '+', 'error': 'Z5'})])
def test_saved_examples_reopen_with_title_roles_and_check(key, params):
    m = CircuitModel()
    m.load_library(key, params)
    copy = reload(saved(m))
    assert copy.active_entry == m.active_entry and copy.roles == m.roles and not copy.entry_edited
    assert all(r.passed for r in copy.verification()[0])


def test_edited_examples_stay_edited_after_saving():
    m = CircuitModel()
    m.load_library('superdense', {'b0': 0, 'b1': 1})
    m.place('Z', 1, 0)
    copy = reload(saved(m))
    assert copy.active_entry is not None and copy.entry_edited


@pytest.mark.parametrize('meta', [{'key': 'nope', 'params': {}}, {'key': 'qpe', 'params': {'t': 99, 'phase': '1/4'}},
                                  {'key': 'qpe'}, 'not a dict'])
def test_invalid_metadata_opens_as_a_plain_circuit(meta):
    m = CircuitModel()
    m.load_library('qpe', {'t': 3, 'phase': '1/4'})
    data = json.loads(saved(m))
    data['example'] = meta
    copy = reload(json.dumps(data))
    assert copy.active_entry is None and copy.roles == []


def test_metadata_does_not_change_the_schema():
    m = CircuitModel()
    m.load_library('teleportation', {'input': '+'})
    assert json.loads(saved(m))['schema_version'] == 5          # optional field: older versions ignore it
