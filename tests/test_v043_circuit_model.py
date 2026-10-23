"""v0.4.3 (R-06): the circuit editor's rules, tested without Qt."""
import math

import numpy as np
import pytest

from quantumscope.editor.circuit_model import CircuitModel, EditorError
from quantumscope.physics.circuits import Gate, evolution
from quantumscope.physics.circuit_examples import EXAMPLE_NAMES
from quantumscope.physics.circuit_files import from_native_layout, to_native_measured


def model(n=3):
    return CircuitModel(n)


def place_cx(m, target, control, col):
    """Editor gesture: drop CX on the target, then click the control."""
    assert 'anchored' in m.place('CX', target, col)
    assert m.add_operand(control, col) is True


# Columns -------------------------------------------------------------------------

def test_empty_circuit_has_two_columns_and_grows_with_one_spare():
    m = model()
    assert m.columns == 2
    m.place('H', 0, 1)
    assert m.columns == 3
    m.place('X', 0, 2)
    assert m.columns == 4


def test_columns_shrink_after_removal():
    m = model()
    m.place('H', 0, 0); m.place('X', 0, 1); m.place('Z', 0, 2)
    m.remove(0, 2)
    assert m.columns == 3


def test_insert_and_delete_columns_shift_operations():
    m = model()
    m.place('H', 0, 0); m.place('X', 1, 1); m.place('M', 2, 2)
    assert m.insert_column(1)
    assert set(m.gates) == {(0, 0), (1, 2)} and m.measurements == {2: 3}
    assert m.delete_empty_column(1)
    assert set(m.gates) == {(0, 0), (1, 1)} and m.measurements == {2: 2}
    with pytest.raises(EditorError, match='Delete the gates'):
        m.delete_empty_column(0)


def test_inserted_trailing_column_is_kept():
    m = model()
    m.place('H', 0, 0)
    m.insert_column(2)
    assert m.columns == 4 and m.reserved_columns == 4


# Placement ----------------------------------------------------------------------

def test_single_gate_placement_and_parameters():
    m = model()
    assert m.place('RY', 1, 0, angle=0.5) is True
    assert m.place('U', 2, 0, angle=0.1, phi=0.2, lam=0.3) is True
    assert m.gates[(1, 0)] == Gate('RY', (1,), 0.5)
    assert m.gates[(2, 0)] == Gate('U', (2,), 0.1, 0.2, 0.3)


def test_unparameterized_gate_ignores_angles():
    m = model()
    m.place('H', 0, 0, angle=1.0, phi=2.0, lam=3.0)
    assert m.gates[(0, 0)] == Gate('H', (0,))


def test_only_one_spare_column_is_available():
    m = model()
    m.place('H', 0, 0)
    assert m.place('X', 0, 2) is False     # column 3 does not exist yet
    assert m.place('X', 0, 1) is True


def test_drops_outside_grid_or_unknown_names_are_ignored():
    m = model()
    assert m.place('H', 5, 0) is False and m.place('H', 0, 9) is False and m.place('FOO', 0, 0) is False
    assert m.gates == {} and m.undo_stack == []


def test_occupied_cell_and_collisions_are_rejected():
    m = model()
    m.place('H', 0, 0)
    with pytest.raises(EditorError, match='Cell occupied'):
        m.place('X', 0, 0)
    with pytest.raises(EditorError, match='collision'):
        m.place('CX', 1, 0, operands=(0, 1))


def test_cx_is_anchored_on_target_then_control():
    m = model()
    place_cx(m, target=2, control=0, col=0)
    assert m.gates == {(2, 0): Gate('CX', (0, 2))}
    assert m.pending is None


def test_ccx_needs_two_controls_and_stores_target_last():
    m = model()
    m.place('CCX', 2, 0)
    assert 'final qubit' in m.add_operand(0, 0)
    assert m.add_operand(1, 0) is True
    assert m.gates == {(2, 0): Gate('CCX', (0, 1, 2))}


def test_swap_operands_keep_click_order():
    m = model()
    m.place('SWAP', 1, 0)
    m.add_operand(0, 0)
    assert m.gates == {(1, 0): Gate('SWAP', (1, 0))}


def test_invalid_operands_keep_placement_pending():
    m = model()
    m.place('H', 0, 0)
    m.place('CX', 2, 0)
    for row, col, message in [(1, 1, 'column 1'), (2, 0, 'another qubit'), (0, 0, 'occupied')]:
        with pytest.raises(EditorError, match=message):
            m.add_operand(row, col)
        assert m.pending == ('CX', 0, (2,))


def test_multi_qubit_gate_needs_enough_qubits_and_empty_anchor():
    with pytest.raises(EditorError, match='Not enough qubits'):
        model(2).place('CCX', 0, 0)
    m = model()
    m.place('H', 0, 0)
    with pytest.raises(EditorError, match='empty cell'):
        m.place('CX', 0, 0)


def test_cancel_pending():
    m = model()
    m.place('CZ', 0, 0)
    assert m.cancel_pending() is True and m.pending is None and m.gates == {}
    assert m.add_operand(1, 0) is None


# Terminal measurements --------------------------------------------------------------

def test_measurements_must_be_terminal_and_share_a_column():
    m = model()
    m.place('H', 0, 1)
    with pytest.raises(EditorError, match='terminal'):
        m.place('M', 1, 1)     # same column as a gate
    with pytest.raises(EditorError, match='terminal'):
        m.place('M', 1, 0)     # before a gate
    m.place('M', 0, 2)
    with pytest.raises(EditorError, match='final circuit column'):
        m.place('M', 1, 3)
    m.place('M', 1, 2)
    with pytest.raises(EditorError, match='already has'):
        m.place('M', 0, 3)
    assert m.measurements == {0: 2, 1: 2}


def test_no_gates_after_or_on_measured_qubits():
    m = model()
    m.place('M', 0, 1)
    with pytest.raises(EditorError, match='Remove this qubit'):
        m.place('H', 0, 0)
    with pytest.raises(EditorError, match='before terminal'):
        m.place('H', 1, 1)


# Moving ------------------------------------------------------------------------------

def test_move_gate_and_whole_multi_qubit_operation():
    m = model()
    place_cx(m, target=1, control=0, col=0)
    assert m.move(0, 0, 1, 1) is True     # grab the control wire, move down one and right
    assert m.gates == {(1, 1): Gate('CX', (1, 2))}


def test_move_rejections():
    m = model()
    place_cx(m, target=1, control=0, col=0)          # CX on q0,q1
    with pytest.raises(EditorError, match='outside'):
        m.move(0, 0, 2, 1)                             # shifting both wires down 2 leaves the 3 qubits
    m.place('X', 2, 1)
    with pytest.raises(EditorError, match='occupied'):
        m.move(0, 0, 1, 1)                             # would cover q2 where X sits
    assert m.place('M', 0, 2) is True
    with pytest.raises(EditorError, match='past terminal'):
        m.move(2, 1, 2, 2)
    assert m.move(0, 0, 0, 0) is False                 # same cell
    assert m.move(2, 0, 0, 1) is False                 # nothing at the source
    assert m.move(2, 1, 9, 1) is False                 # destination outside the grid


def test_move_measurement_rules():
    m = model()
    m.place('H', 0, 0); m.place('M', 0, 1); m.place('M', 1, 1)
    assert m.move(0, 1, 2, 1) is True and m.measurements == {1: 1, 2: 1}
    with pytest.raises(EditorError, match='already measured'):
        m.move(2, 1, 1, 1)
    with pytest.raises(EditorError, match='follow all unitary'):
        m.move(2, 1, 2, 0)
    with pytest.raises(EditorError, match='shared terminal'):
        m.move(2, 1, 2, 2)


# Removal and parameter editing --------------------------------------------------------

def test_remove_multi_qubit_gate_from_any_wire():
    m = model()
    place_cx(m, target=2, control=0, col=0)
    assert m.remove(0, 0) is True and m.gates == {}
    assert m.remove(0, 0) is False


def test_remove_measurement():
    m = model()
    m.place('M', 1, 0)
    assert m.remove(1, 0) and m.measurements == {}


def test_edit_parameters_only_for_parameterized_gates():
    m = model()
    m.place('U', 0, 0, angle=0.1, phi=0.2, lam=0.3)
    m.place('H', 1, 0)
    m.edit_parameters(0, 0, 1.0, lam=2.0)
    assert m.gates[(0, 0)] == Gate('U', (0,), 1.0, 0.2, 2.0)
    assert m.editable_gate(1, 0) is None
    with pytest.raises(EditorError):
        m.edit_parameters(1, 0, 1.0)


# Undo / redo ----------------------------------------------------------------------------

def test_undo_redo_round_trip():
    m = model()
    m.place('H', 0, 0); m.place('X', 1, 0); m.insert_column(0)
    after = (dict(m.gates), m.reserved_columns)
    assert m.undo() and m.undo() and set(m.gates) == {(0, 0)}
    assert m.redo() and m.redo() and (dict(m.gates), m.reserved_columns) == after
    assert m.redo() is False


def test_new_edit_clears_redo_and_undo_is_capped():
    m = model()
    m.place('H', 0, 0); m.undo()
    m.place('X', 0, 0)
    assert m.redo_stack == []
    for _ in range(100):
        m.insert_column(0)
    assert len(m.undo_stack) == 80


def test_undo_restores_example_state_and_clears_pending():
    m = model()
    m.load_example('Half adder (a=1,b=1)')
    assert 'anchored' in m.place('CX', 0, 3)
    assert m.pending
    m.undo()
    assert m.active_example is None and m.pending is None


def test_rejected_edits_do_not_create_undo_entries():
    m = model()
    m.place('H', 0, 0)
    depth = len(m.undo_stack)
    for bad in (lambda: m.place('X', 0, 0), lambda: m.delete_empty_column(0), lambda: m.move(0, 0, 9, 0)):
        try:
            bad()
        except EditorError:
            pass
    assert len(m.undo_stack) == depth


# Resizing, loading and examples ----------------------------------------------------------

def test_resize_drops_out_of_range_operations():
    m = model()
    place_cx(m, target=2, control=0, col=0); m.place('H', 1, 1); m.place('M', 2, 2)
    assert m.removes_gates(2) and not m.removes_gates(3)
    m.resize(2)
    assert set(m.gates) == {(1, 1)} and m.measurements == {}
    with pytest.raises(EditorError):
        m.resize(11)


def test_loading_a_circuit_clears_pending_placement():
    m = model()
    m.place('CX', 0, 0)
    m.set_circuit(2, [Gate('H', (0,))])
    assert m.pending is None


def test_set_circuit_with_layout_and_measurements():
    m = model()
    m.set_circuit(3, [Gate('H', (0,)), Gate('H', (1,)), Gate('CX', (0, 2))], [0, 0, 3], [1], 5, 9)
    assert set(m.gates) == {(0, 0), (1, 0), (0, 3)} and m.measurements == {1: 5} and m.columns == 9


def test_bell_button_grows_one_qubit_circuit():
    m = model(1)
    m.load_bell()
    assert m.n == 2 and m.active_example == 'Bell pair' and len(m.undo_stack) == 2


@pytest.mark.parametrize('name', EXAMPLE_NAMES)
def test_every_example_loads_and_verifies(name):
    m = model()
    m.load_example(name)
    rows, note = m.verification()
    assert m.active_example == name and not m.is_edited_example()
    if rows and rows[0].passed is not None:
        assert all(r.passed for r in rows)


def test_edited_example_reports_failure_with_note():
    m = model()
    m.load_example('Half adder (a=1,b=1)')
    cx = next(k for k, g in m.gates.items() if g.name == 'CX')
    m.remove(*cx)
    rows, note = m.verification()
    assert note.startswith('Edited Half adder') and any(r.passed is False for r in rows)


def test_clear_resets_everything():
    m = model()
    m.load_example('GHZ'); m.insert_column(0)
    m.clear()
    assert (m.gates, m.measurements, m.reserved_columns, m.active_example) == ({}, {}, 2, None)


# Simulation and saving ---------------------------------------------------------------------

def test_simulation_matches_physics_evolution():
    m = model()
    m.place('H', 0, 0); m.place('H', 1, 0)
    place_cx(m, target=2, control=0, col=1)
    m.place('RY', 1, 2, angle=0.7)
    m.insert_column(1)                     # leave an empty column between layers
    sim = m.simulate()
    assert sim.occupied_columns == [0, 2, 3] and len(sim.column_states) == 4
    assert np.allclose(sim.column_states[-1], evolution(3, m.ordered())[-1])
    assert np.allclose(sim.states[-1], sim.column_states[-1])


def test_layout_round_trips_through_qscope_file():
    m = model()
    m.place('H', 0, 0); m.place('X', 1, 0); m.place('Z', 1, 3); m.place('M', 0, 5); m.insert_column(7)
    gates, columns, mcol, total = m.layout()
    text = to_native_measured(m.n, gates, sorted(m.measurements),
                              layout={'columns': columns, 'measurement_column': mcol, 'total_columns': total})
    n, ops, measured, layout = from_native_layout(text)
    copy = model()
    copy.set_circuit(n, ops, layout['columns'], measured, layout['measurement_column'], layout['total_columns'])
    assert (copy.gates, copy.measurements, copy.columns) == (m.gates, m.measurements, m.columns)
