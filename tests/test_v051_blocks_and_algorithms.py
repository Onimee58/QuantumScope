"""v0.5.1: CP gate, blocks, the algorithm/example library, schema-3 files and worked identities."""
import itertools
import json
import math

import numpy as np
import pytest

from quantumscope.editor.circuit_model import CircuitModel, EditorError
from quantumscope.physics.algorithms import (LIBRARY, CircuitView, build, dft_matrix, entry, grover_optimal_iterations,
                                             grover_success, iqft_block, mcz, mcz_work_needed, qft_block,
                                             rebuild_block, validate_params)
from quantumscope.physics.blocks import Block, BlockPlacement, check_layout, flatten_with_comments
from quantumscope.physics.circuits import Gate, apply_gate, evolution, parse_qasm
from quantumscope.physics.circuit_files import (convert, from_native, from_native_layout, from_qasm_layout,
                                                to_native_measured, to_qasm, to_qasm_measured)
from quantumscope.physics.gate_education import WORKED, gate_matrix, try_it_circuit, worked_identity
from quantumscope.physics.initial_states import product_state
from quantumscope.physics.state_analysis import is_clifford


def view_of(model):
    return model.circuit_view()


def loaded(key, values=None):
    m = CircuitModel()
    m.load_library(key, values)
    return m


# CP ------------------------------------------------------------------------------------

@pytest.mark.parametrize('angle', [0.0, math.pi / 4, math.pi / 2, math.pi, -1.1])
def test_cp_matrix_and_symmetry(angle):
    expected = np.diag([1, 1, 1, np.exp(1j * angle)])
    assert np.allclose(gate_matrix('CP', angle), expected)
    for index in range(4):
        v = np.zeros(4, complex)
        v[index] = 1
        assert np.allclose(apply_gate(v, 2, Gate('CP', (0, 1), angle)), apply_gate(v, 2, Gate('CP', (1, 0), angle)))


def test_cp_qasm_round_trip_and_cu1_alias():
    gates = [Gate('H', (0,)), Gate('CP', (1, 0), math.pi / 8)]
    assert parse_qasm(to_qasm(2, gates)) == (2, gates)
    assert parse_qasm('OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; cu1(pi/2) q[0],q[1];')[1] == [
        Gate('CP', (0, 1), math.pi / 2)]


@pytest.mark.parametrize('angle,clifford', [(0.0, True), (math.pi, True), (math.pi / 2, False), (0.3, False)])
def test_cp_clifford(angle, clifford):
    assert is_clifford(Gate('CP', (0, 1), angle)) is clifford


def test_pending_cp_keeps_its_angle():
    m = CircuitModel(2)
    m.place('CP', 1, 0, angle=0.7)
    m.add_operand(0, 0)
    assert list(m.gates.values()) == [Gate('CP', (1, 0), 0.7)]


# Multi-controlled Z ----------------------------------------------------------------------

@pytest.mark.parametrize('k', [1, 2, 3, 4, 5])
def test_mcz_flips_only_all_ones_and_cleans_work_qubits(k):
    work = list(range(k, k + mcz_work_needed(k)))
    n = k + len(work)
    gates = mcz(list(range(k)), work)
    for index in range(1 << k):
        v = np.zeros(1 << n, complex)
        v[index << len(work)] = 1                       # work qubits start in |0⟩
        out = v
        for g in gates:
            out = apply_gate(out, n, g)
        sign = -1 if index == (1 << k) - 1 else 1
        assert np.allclose(out, sign * v)


def test_mcz_needs_work_qubits():
    with pytest.raises(ValueError):
        mcz([0, 1, 2, 3], [])


# Blocks -----------------------------------------------------------------------------------

def test_block_validation_and_geometry():
    b = Block('custom', 'Test', (0, 2), (Gate('CX', (0, 2)), Gate('H', (2,))))
    assert (b.low, b.high, list(b.span)) == (0, 2, [0, 1, 2])
    assert b.expanded_width == 2 and b.shifted(1).qubits == (1, 3)
    with pytest.raises(ValueError):
        Block('custom', 'Bad', (0,), (Gate('CX', (0, 1)),))     # gate outside the block


def test_block_record_round_trip():
    b = qft_block([1, 2, 3])
    assert Block.from_record(json.loads(json.dumps(b.to_record())), 4) == b


def test_check_layout_rejects_overlaps():
    b = Block('custom', 'B', (0, 2), (Gate('H', (0,)),))
    with pytest.raises(ValueError):
        check_layout(3, [Gate('X', (1,))], [4], [BlockPlacement(b, 4)])   # q1 is inside the span
    with pytest.raises(ValueError):
        check_layout(2, [], [], [BlockPlacement(b, 0)])                    # does not fit


def grover_model():
    return loaded('grover', {'n': 3, 'marked': '101', 'iterations': -1})


def test_expand_and_collapse_keep_physics_and_layout():
    m = grover_model()
    final = m.simulate().column_states[-1]
    before = (dict(m.blocks), dict(m.measurements), m.columns)
    for bid, *_ in m.block_summary():
        m.expand_block(bid)
        assert np.allclose(m.simulate().column_states[-1], final)
    assert len(m.simulate().occupied_columns) > 7
    for bid, *_ in m.block_summary():
        m.collapse_block(bid)
    assert (dict(m.blocks), dict(m.measurements), m.columns) == before


def test_expanded_block_is_locked():
    m = grover_model()
    bid = m.block_summary()[0][0]
    m.expand_block(bid)
    pl = m.blocks[bid]
    for row in range(3):
        for col in range(pl.col, pl.end + 1):
            assert m.operation_at(row, col)[0] == 'block'
            with pytest.raises(EditorError, match='block'):
                m.place('X', row, col)
    with pytest.raises(EditorError, match='inside block'):
        m.insert_column(pl.col + 1)


def test_block_footprint_reserves_the_whole_span():
    m = CircuitModel(3)
    m.add_block(Block('custom', 'B', (0, 2), (Gate('CX', (0, 2)),)), 0)
    with pytest.raises(EditorError):
        m.place('H', 1, 0)                        # q1 lies between the block's qubits


def test_move_block_and_rejections():
    m = CircuitModel(4)
    bid = m.add_block(qft_block([0, 1]), 0)
    m.place('H', 3, 1)
    assert m.move(0, 0, 1, 1) is True and m.blocks[bid].block.qubits == (1, 2) and m.blocks[bid].col == 1
    with pytest.raises(EditorError, match='outside'):
        m.move(1, 1, 3, 1)
    m.place('X', 0, 2)
    with pytest.raises(EditorError, match='occupied'):
        m.move(1, 1, 0, 2)


def test_ungroup_turns_block_into_editable_gates():
    m = grover_model()
    final = m.simulate().column_states[-1]
    bid = m.block_summary()[0][0]
    count = len(m.ordered())
    m.ungroup_block(bid)
    assert bid not in m.blocks and len(m.ordered()) == count
    assert np.allclose(m.simulate().column_states[-1], final)
    assert any(m.operation_at(r, c)[0] == 'gate' for (r, c) in m.gates)
    m.undo()
    assert bid in m.blocks


def test_edit_block_rebuilds_and_keeps_expanded_state():
    m = grover_model()
    bid = m.block_summary()[0][0]
    m.expand_block(bid)
    assert m.edit_block(bid, {'marked': '011'}) is True
    assert m.blocks[bid].expanded and m.blocks[bid].block.param('marked') == '011'
    rows, note = m.verification()
    assert rows[0].passed is None and 'same item' in note        # oracles now disagree
    with pytest.raises(EditorError):
        m.edit_block(bid, {'marked': '11'})                         # wrong length
    m.undo()
    assert m.verification()[0][0].passed is True


def test_blocks_without_parameters_cannot_be_edited():
    m = loaded('qft', {'n': 3, 'x': 1, 'inverse': 'no'})
    with pytest.raises(EditorError, match='no editable'):
        m.edit_block(m.block_summary()[0][0], {})


def test_remove_resize_and_clear_blocks():
    m = grover_model()
    bid = m.block_summary()[0][0]
    pl = m.blocks[bid]
    assert m.remove(1, pl.col) and bid not in m.blocks          # removable from any wire
    m2 = loaded('bernstein_vazirani', {'n': 3, 's': '101'})
    assert m2.removes_gates(3)
    m2.resize(3)
    assert m2.blocks == {}
    m.clear()
    assert m.blocks == {} and m.active_entry is None


def test_analysis_counts_real_gates_inside_blocks():
    m = grover_model()
    stats = m.analysis()
    assert stats['total'] == 3 + 2 * (5 + 15) and stats['three_qubit'] == 4
    assert [b[0] for b in stats['blocks']] == ['Oracle', 'Diffusion', 'Oracle', 'Diffusion']
    assert stats['drawn_depth'] == 5                              # collapsed blocks are one column each


# Algorithms ---------------------------------------------------------------------------------

@pytest.mark.parametrize('e', LIBRARY, ids=[e.key for e in LIBRARY])
def test_every_library_entry_builds_and_passes(e):
    m = loaded(e.key)
    rows, _ = m.verification()
    assert rows and all(r.passed for r in rows)


@pytest.mark.parametrize('function', ['0', '1', 'x', 'not'])
def test_deutsch(function):
    assert loaded('deutsch', {'function': function}).verification()[0][0].passed


@pytest.mark.parametrize('n', [1, 2, 3, 4])
def test_bernstein_vazirani_every_secret(n):
    for s in (''.join(b) for b in itertools.product('01', repeat=n)):
        assert loaded('bernstein_vazirani', {'n': n, 's': s}).verification()[0][0].passed


@pytest.mark.parametrize('n', [1, 2, 3])
def test_deutsch_jozsa_constant_and_balanced(n):
    for function in ('constant0', 'constant1'):
        assert loaded('deutsch_jozsa', {'n': n, 'function': function, 's': '0' * n}).verification()[0][0].passed
    for s in (''.join(b) for b in itertools.product('01', repeat=n)):
        if '1' in s:
            assert loaded('deutsch_jozsa', {'n': n, 'function': 'balanced', 's': s}).verification()[0][0].passed
    with pytest.raises(ValueError):
        loaded('deutsch_jozsa', {'n': n, 'function': 'balanced', 's': '0' * n})


@pytest.mark.parametrize('n', [2, 3, 4, 5])
def test_grover_matches_sin_squared(n):
    marks = [format(i, f'0{n}b') for i in range(2 ** n)][:: 1 if n < 4 else 7]
    for marked in marks:
        for k in (0, 1, 2, -1):
            m = loaded('grover', {'n': n, 'marked': marked, 'iterations': k})
            row = m.verification()[0][0]
            kk = grover_optimal_iterations(n) if k < 0 else k
            assert row.passed and row.probability == pytest.approx(grover_success(n, kk), abs=1e-9)


def test_grover_optimum_and_overshoot():
    assert grover_optimal_iterations(2) == 1 and grover_success(2, 1) == pytest.approx(1)
    assert grover_success(3, 2) > grover_success(3, 3)          # going past the optimum lowers success


def test_grover_work_qubits_return_to_zero():
    m = loaded('grover', {'n': 5, 'marked': '10110', 'iterations': -1})
    final = m.simulate().column_states[-1]
    from quantumscope.physics.algorithms import marginal
    assert marginal(final, m.n, [5, 6]).get('00', 0) == pytest.approx(1)


def test_removing_an_iteration_still_matches_the_formula():
    m = grover_model()
    ids = [b[0] for b in m.block_summary()]
    for bid in ids[-2:]:
        m.remove(m.blocks[bid].block.low, m.blocks[bid].col)
    row = m.verification()[0][0]
    assert row.passed and row.probability == pytest.approx(grover_success(3, 1))


@pytest.mark.parametrize('n', [1, 2, 3, 4])
def test_qft_matches_dft_for_every_input(n):
    for x in range(2 ** n):
        for inverse in ('no', 'yes'):
            m = loaded('qft', {'n': n, 'x': x, 'inverse': inverse})
            assert m.verification()[0][0].passed


def test_qft_spec_follows_changed_initial_states():
    from quantumscope.physics.initial_states import InitialState
    m = loaded('qft', {'n': 3, 'x': 0, 'inverse': 'no'})
    m.set_initial_state(0, InitialState(1.0, 0.4))               # not even a basis state
    assert m.verification()[0][0].passed


def test_iqft_inverts_qft():
    q, iq = qft_block([0, 1, 2]), iqft_block([0, 1, 2])
    for index in range(8):
        v = np.zeros(8, complex)
        v[index] = 1
        out = v
        for g in q.gates + iq.gates:
            out = apply_gate(out, 3, g)
        assert np.allclose(out, v)


def test_parameter_validation():
    e = entry('grover')
    with pytest.raises(ValueError, match='bits'):
        validate_params(e.params, {'n': 3, 'marked': '10'})
    with pytest.raises(ValueError, match='from 2 to 5'):
        validate_params(e.params, {'n': 9})
    with pytest.raises(ValueError):
        build('qft', {'n': 2, 'x': 9, 'inverse': 'no'})


def test_rebuild_block_validates():
    oracle = loaded('bernstein_vazirani', {'n': 3, 's': '101'}).blocks
    block = next(iter(oracle.values())).block
    assert rebuild_block(block, {'s': '011', 'c': 1}).param('s') == '011'
    with pytest.raises(ValueError):
        rebuild_block(block, {'s': '01'})


# Reversible examples ---------------------------------------------------------------------------

@pytest.mark.parametrize('key', ['full_adder', 'comparator', 'controlled_increment', 'toffoli_and', 'fredkin_mux'])
def test_reversible_examples_pass_and_detect_edits(key):
    m = loaded(key)
    rows, note = m.verification()
    assert len(rows) == 2 ** len(entry(key).params) and all(r.passed for r in rows)
    assert 'does not use the chosen initial states' in note
    (r, c), _ = next(iter(m.gates.items()))
    m.remove(r, c)
    assert any(row.passed is False for row in m.verification()[0])


# Files -----------------------------------------------------------------------------------------

def saved(m):
    gates, cols, mcol, total = m.layout()
    layout = {'columns': cols, 'measurement_column': mcol, 'total_columns': total, 'initial_states': m.initial_states,
              'blocks': [(pl.block, pl.col, pl.expanded) for pl in m.blocks.values()]}
    return to_native_measured(m.n, gates, sorted(m.measurements), layout=layout)


def test_schema_3_round_trip_with_expanded_block():
    m = grover_model()
    m.expand_block(m.block_summary()[1][0])
    text = saved(m)
    assert json.loads(text)['schema_version'] == 3
    n, gates, measured, layout = from_native_layout(text)
    copy = CircuitModel()
    copy.set_circuit(n, gates, layout['columns'], measured, layout['measurement_column'], layout['total_columns'],
                     layout['initial_states'], layout['blocks'])
    assert [(pl.block, pl.col, pl.expanded) for pl in copy.blocks.values()] == [
        (pl.block, pl.col, pl.expanded) for pl in m.blocks.values()]
    assert np.allclose(copy.simulate().column_states[-1], m.simulate().column_states[-1])


def test_files_without_blocks_keep_their_schema():
    m = CircuitModel(2)
    m.place('H', 0, 0)
    assert json.loads(saved(m))['schema_version'] == 1


def test_older_readers_refuse_schema_3():
    with pytest.raises(ValueError):
        from_native(saved(grover_model()))


def test_overlapping_blocks_in_a_file_are_rejected():
    data = json.loads(saved(grover_model()))
    data['blocks'][1]['column'] = data['blocks'][0]['column']
    with pytest.raises(ValueError, match='overlaps'):
        from_native_layout(json.dumps(data))


def test_qasm_export_marks_blocks_and_is_exact():
    m = grover_model()
    gates, comments = m.qasm_items()
    qasm = to_qasm_measured(m.n, gates, sorted(m.measurements), m.initial_states, comments)
    assert qasm.isascii() and qasm.count('// block: ') == 4
    n, imported, measured, _, _ = from_qasm_layout(qasm)
    assert np.allclose(evolution(n, imported)[-1], m.simulate().column_states[-1])


def test_converter_flattens_blocks_with_a_note():
    notes = []
    qasm = convert(saved(grover_model()), 'qscope', notes)
    assert '// block: Oracle' in qasm and any('block' in n for n in notes)


# Gate Explorer additions ----------------------------------------------------------------------------

@pytest.mark.parametrize('name', sorted(WORKED))
def test_worked_identities_hold_on_every_basis_state(name):
    worked = worked_identity(name)
    assert worked['rows'] and all(row[3] for row in worked['rows'])


@pytest.mark.parametrize('name', ['H', 'T', 'CX', 'CZ', 'CP', 'SWAP', 'CSWAP', 'CCX', 'RY'])
def test_try_it_shows_a_visible_effect(name):
    n, gates, starts = try_it_circuit(name, 0.9)
    from quantumscope.physics.initial_states import InitialState
    start = product_state([InitialState.preset(k) for k in starts])
    end = evolution(n, gates, start)[-1]
    assert not np.allclose(end, start)                     # the gate visibly changes the state
