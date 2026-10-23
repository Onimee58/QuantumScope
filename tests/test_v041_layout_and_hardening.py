"""v0.4.1: safe QASM angles (R-02), barrier notices (R-03), layout
persistence (R-01) and example verification after edits (R-04)."""
import json
import math
import time

import numpy as np
import pytest

from quantumscope.physics.circuits import Gate, evolution, parse_qasm, parse_qasm_detailed
from quantumscope.physics.circuit_files import (convert, from_native, from_native_layout,
    from_native_measured, from_qasm_layout, to_native, to_native_measured)
from quantumscope.physics.circuit_layout import pack_and_order, pack_columns, validate_columns
from quantumscope.physics.circuit_examples import EXAMPLE_NAMES, example_circuit, has_specification
from quantumscope.physics.circuit_verification import verify_example
from quantumscope.physics.expressions import parse_angle
from quantumscope.physics.gate_education import parse_angle as reexported_parse_angle

HEADER = 'OPENQASM 2.0; include "qelib1.inc"; qreg q[3];'


def final_state(n, gates):
    return evolution(n, gates)[-1]


# R-02: safe, bounded angle expressions -------------------------------------

@pytest.mark.parametrize('expr', ['9**9**9**9', '9^9^9', '(10**6)**13', '1e400', '2**2**2**2**2'])
def test_qasm_rejects_unbounded_angles_quickly(expr):
    start = time.perf_counter()
    with pytest.raises(ValueError):
        parse_qasm(HEADER + f' rx({expr}) q[0];')
    assert time.perf_counter() - start < 1.0


@pytest.mark.parametrize('expr', ['+'.join(['1'] * 150), '-' * 60 + '1',
                                  '__import__("os")', 'pi.real', 'e', '1j'])
def test_angle_parser_rejects_long_deep_or_non_numeric_input(expr):
    with pytest.raises(ValueError):
        parse_angle(expr)


def test_qasm_angles_match_editor_parser():
    n, gates = parse_qasm(HEADER + ' rx(-pi/2) q[0]; u3(pi, pi/2, 3*pi/4) q[1]; p(pi^2/4) q[2];')
    assert gates[0].angle == pytest.approx(-math.pi / 2)
    assert (gates[1].angle, gates[1].phi, gates[1].lam) == pytest.approx((math.pi, math.pi / 2, 3 * math.pi / 4))
    assert gates[2].angle == pytest.approx(math.pi ** 2 / 4)
    assert reexported_parse_angle is parse_angle


# R-03: barriers are reported and act as column separators -------------------

def test_barrier_is_reported_not_silently_dropped():
    n, gates, fences, notes = parse_qasm_detailed(HEADER + ' h q[0]; barrier q; x q[1];')
    assert [g.name for g in gates] == ['H', 'X'] and fences == [1]
    assert notes and 'barrier' in notes[0]
    assert parse_qasm(HEADER + ' h q[0]; x q[1];') == (n, gates)


def test_barrier_separates_columns_on_import():
    _, _, _, with_barrier, notes = from_qasm_layout(HEADER + ' h q[0]; barrier q; x q[1];')
    _, _, _, without, none = from_qasm_layout(HEADER + ' h q[0]; x q[1];')
    assert with_barrier['columns'] == [0, 1] and without['columns'] == [0, 0]
    assert notes and none == []


def test_converter_reports_barrier_notes():
    notes = []
    convert(HEADER + ' h q[0]; barrier q[0],q[1]; cx q[0],q[1];', 'qasm', notes)
    assert len(notes) == 1


def test_barrier_with_measurement_keeps_measurement_terminal():
    text = HEADER + ' creg c[3]; h q[0]; barrier q; cx q[0],q[1]; measure q[1] -> c[1];'
    n, gates, measured, layout, notes = from_qasm_layout(text)
    assert measured == [1] and layout['columns'] == [0, 1] and layout['measurement_column'] == 2 and notes


# R-01: layout packing and persistence ----------------------------------------

def test_packing_puts_disjoint_gates_in_one_column():
    gates = [Gate('H', (0,)), Gate('H', (1,)), Gate('H', (2,)), Gate('CX', (0, 1))]
    assert pack_columns(3, gates) == [0, 0, 0, 1]


def test_packing_reserves_connector_span():
    # CX(0,2) draws a line across q1, so X on q1 must not share its column.
    assert pack_columns(3, [Gate('CX', (0, 2)), Gate('X', (1,))]) == [0, 1]


def test_pack_and_order_preserves_the_unitary():
    rng = np.random.default_rng(7)
    names = ['H', 'X', 'T', 'CX', 'CZ', 'CCX', 'SWAP']
    for _ in range(40):
        gates = []
        for _ in range(12):
            name = names[rng.integers(len(names))]
            k = 3 if name == 'CCX' else 2 if name in ('CX', 'CZ', 'SWAP') else 1
            gates.append(Gate(name, tuple(int(q) for q in rng.permutation(4)[:k])))
        ordered, columns = pack_and_order(4, gates)
        validate_columns(ordered, columns)
        assert np.allclose(final_state(4, gates), final_state(4, ordered))


def test_native_layout_round_trip_keeps_parallel_and_empty_columns():
    gates = [Gate('H', (0,)), Gate('H', (1,)), Gate('CX', (0, 1)), Gate('X', (2,))]
    layout = {'columns': [0, 0, 3, 5], 'measurement_column': 7, 'total_columns': 10}
    text = to_native_measured(3, gates, [0, 2], layout=layout)
    n, restored, measured, back = from_native_layout(text)
    assert (n, restored, measured) == (3, gates, [0, 2])
    assert back == layout


def test_layout_file_still_opens_with_v040_reader():
    text = to_native_measured(2, [Gate('H', (0,)), Gate('X', (1,))], [0],
                              layout={'columns': [0, 0], 'measurement_column': 1, 'total_columns': 3})
    assert from_native(text) == (2, [Gate('H', (0,)), Gate('X', (1,))])
    assert from_native_measured(text) == (2, [Gate('H', (0,)), Gate('X', (1,))], [0])


def test_legacy_file_without_columns_is_packed():
    n, gates, measured, layout = from_native_layout(to_native(3, [Gate('H', (0,)), Gate('H', (1,)), Gate('H', (2,))]))
    assert layout['columns'] == [0, 0, 0] and layout['measurement_column'] is None


@pytest.mark.parametrize('columns', [[1, 0], [0, 0], [0], [-1, 2]])
def test_inconsistent_layouts_are_rejected(columns):
    gates = [Gate('X', (0,)), Gate('H', (0,))]
    data = json.loads(to_native(1, gates))
    for op, col in zip(data['operations'], columns):
        op['column'] = col
    with pytest.raises(ValueError):
        from_native_layout(json.dumps(data))


def test_measurement_column_must_follow_gates():
    data = json.loads(to_native_measured(2, [Gate('H', (0,))], [1], layout={'columns': [2]}))
    data['measurement_column'] = 1
    with pytest.raises(ValueError):
        from_native_layout(json.dumps(data))


# R-04: examples keep their specification through edits ------------------------

@pytest.mark.parametrize('name', [x for x in EXAMPLE_NAMES if has_specification(x)])
def test_packed_examples_still_pass_verification(name):
    n, gates = example_circuit(name)
    ordered, _ = pack_and_order(n, gates)
    rows, _ = verify_example(name, n, ordered)
    assert rows and all(row.passed for row in rows)


def test_edited_adder_reports_failures_instead_of_losing_its_check():
    n, gates = example_circuit('Half adder (a=1,b=1)')
    broken = gates[:-1]  # remove the CX that forms the sum bit
    rows, _ = verify_example('Half adder (a=1,b=1)', n, broken)
    assert rows and any(row.passed is False for row in rows)


def test_verification_handles_too_few_qubits():
    rows, note = verify_example('2-bit ripple-carry adder (1+1)', 3, [Gate('X', (1,)), Gate('X', (0,))])
    assert rows == [] and '6 qubits' in note
