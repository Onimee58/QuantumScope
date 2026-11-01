"""v0.6.1 (7a): mid-circuit measurement, classical conditions and reset."""
import json

import numpy as np
import pytest

from quantumscope.editor.circuit_model import CircuitModel, EditorError
from quantumscope.physics import dynamic as D
from quantumscope.physics import noise as N
from quantumscope.physics.circuit_files import from_native, from_native_layout, to_native_measured
from quantumscope.physics.circuits import Gate

OFF = N.NoiseModel()
RNG = np.random.default_rng(11)


def zero(n):
    v = np.zeros(2 ** n, complex)
    v[0] = 1
    return v


def random_qubit():
    a = RNG.normal(size=2) + 1j * RNG.normal(size=2)
    return a / np.linalg.norm(a)


TELEPORT = [[Gate('H', (1,))], [Gate('CX', (1, 2))], [Gate('CX', (0, 1))], [Gate('H', (0,))],
            [D.Measure(0, 0), D.Measure(1, 1)], [D.Conditioned(Gate('X', (2,)), 1, 1)],
            [D.Conditioned(Gate('Z', (2,)), 0, 1)]]


# ---- the engine ---------------------------------------------------------------------------------

def test_teleportation_works_for_random_inputs_in_every_branch():
    for _ in range(20):
        a = random_qubit()
        final = D.simulate(3, TELEPORT, np.kron(a, zero(2)), OFF)[-1]
        assert sorted(b.bits for b in final) == [(0, 0), (0, 1), (1, 0), (1, 1)]
        for branch in final:
            assert branch.probability == pytest.approx(0.25)
            q2 = N.partial_trace(branch.rho, 3, [2])
            assert np.real(np.vdot(a, q2 @ a)) == pytest.approx(1)


def test_teleportation_without_corrections_fails_in_three_branches():
    a = np.array([1, 1j]) / np.sqrt(2)
    final = D.simulate(3, TELEPORT[:5], np.kron(a, zero(2)), OFF)[-1]
    fidelities = sorted(np.real(np.vdot(a, N.partial_trace(b.rho, 3, [2]) @ a)) for b in final)
    assert fidelities[-1] == pytest.approx(1) and fidelities[0] < 0.01      # corrections matter


@pytest.mark.parametrize('message', ['00', '01', '10', '11'])
def test_superdense_coding_sends_two_bits(message):
    columns = [[Gate('H', (0,))], [Gate('CX', (0, 1))]]
    if message[1] == '1':
        columns.append([Gate('X', (0,))])
    if message[0] == '1':
        columns.append([Gate('Z', (0,))])
    columns += [[Gate('CX', (0, 1))], [Gate('H', (0,))], [D.Measure(0, 0), D.Measure(1, 1)]]
    record = D.record_distribution(D.simulate(2, columns, zero(2), OFF)[-1])
    assert record == pytest.approx({message: 1.0})


def test_mid_circuit_bell_measurement_and_averaged_state():
    history = D.simulate(2, [[Gate('H', (0,))], [Gate('CX', (0, 1))], [D.Measure(0, 0)]], zero(2), OFF)
    final = history[-1]
    assert D.record_distribution(final) == pytest.approx({'0': 0.5, '1': 0.5})
    for branch in final:                                      # each branch is the correlated product state
        bit = branch.bits[0]
        assert branch.rho[3 * bit, 3 * bit].real == pytest.approx(1)
    assert N.purity(D.averaged(final)) == pytest.approx(0.5)
    assert len(history) == 4                                  # before + 3 columns


def test_reset_and_conditions():
    reset = D.averaged(D.simulate(1, [[Gate('H', (0,))], [D.Reset(0)]], zero(1), OFF)[-1])
    assert np.allclose(reset, [[1, 0], [0, 0]])
    flip_if_zero = D.averaged(D.simulate(1, [[D.Measure(0, 0)], [D.Conditioned(Gate('X', (0,)), 0, 0)]], zero(1), OFF)[-1])
    assert np.allclose(flip_if_zero, [[0, 0], [0, 1]])
    # reset by feed-forward: measure, then X if the result was 1 — any input ends in |0⟩
    a = random_qubit()
    ff = D.averaged(D.simulate(1, [[D.Measure(0, 0)], [D.Conditioned(Gate('X', (0,)), 0, 1)]], a, OFF)[-1])
    assert np.allclose(ff, [[1, 0], [0, 0]])


def test_readout_error_on_mid_circuit_records():
    final = D.simulate(1, [[D.Measure(0, 0)]], zero(1), OFF, readout=0.1)[-1]
    assert D.record_distribution(final) == pytest.approx({'0': 0.9, '1': 0.1})
    wrong = next(b for b in final if b.bits == (1,))
    assert wrong.rho[0, 0].real == pytest.approx(1)           # the qubit itself is still |0⟩


def test_without_measurements_matches_the_noise_engine():
    columns = [[Gate('H', (0,))], [Gate('CX', (0, 1))], [N.NoiseElement('depolarizing', 1, 0.3)]]
    model = N.PRESETS['Moderate']
    assert np.allclose(D.averaged(D.simulate(2, columns, zero(2), model)[-1]), N.simulate(2, columns, zero(2), model)[-1])


def test_branches_are_merged_and_bounded():
    columns = [[Gate('H', (q,)) for q in range(3)], [D.Measure(0, 0), D.Measure(1, 0), D.Measure(2, 1)]]
    final = D.simulate(3, columns, zero(3), OFF)[-1]
    assert len(final) <= 4 and sum(b.probability for b in final) == pytest.approx(1)


def test_invalid_items():
    with pytest.raises(ValueError):
        D.Measure(0, D.MAX_BITS)
    with pytest.raises(ValueError):
        D.Conditioned(Gate('X', (0,)), 0, 2)
    with pytest.raises(ValueError):
        D.item_from_record({'op': 'teleport', 'qubit': 0})


# ---- the editor model -------------------------------------------------------------------------

def teleport_model():
    m = CircuitModel(3)
    m.place('H', 1, 0)
    m.place('CX', 2, 1)
    m.add_operand(1, 1)
    m.place('CX', 1, 2)
    m.add_operand(0, 2)
    m.place('H', 0, 3)
    m.place_measure(0, 4)
    m.place_measure(1, 4)
    m.place('X', 2, 5)
    m.set_condition(2, 5, 1)
    m.place('Z', 2, 6)
    m.set_condition(2, 6, 0)
    return m


def test_model_teleportation_end_to_end():
    m = teleport_model()
    assert m.dynamic and m.noisy and m.operation_at(0, 4)[0] == 'measure'
    m.initial_states = list(m.initial_states)
    from quantumscope.physics.initial_states import InitialState
    m.set_initial_state(0, InitialState.preset('+i'))
    _, history = m.simulate_branches()
    target = np.array([1, 1j]) / np.sqrt(2)
    for branch in history[-1]:
        assert np.real(np.vdot(target, N.partial_trace(branch.rho, 3, [2]) @ target)) == pytest.approx(1)
    occupied, averaged = m.simulate_noisy()
    assert len(averaged) == len(occupied) + 1


def test_conditions_follow_their_gate_and_undo():
    m = teleport_model()
    assert m.conditions[(2, 5)] == (1, 1)
    m.move(2, 5, 2, 7)
    assert (2, 7) in m.conditions and (2, 5) not in m.conditions
    m.insert_column(0)
    assert (2, 8) in m.conditions and m.operation_at(0, 5)[0] == 'measure'
    m.remove(2, 8)
    assert (2, 8) not in m.conditions
    m.undo()
    assert m.conditions[(2, 8)] == (1, 1)
    assert m.clear_condition(2, 8) and (2, 8) not in m.conditions


def test_measure_and_reset_placement_rules():
    m = CircuitModel(2)
    m.place('H', 0, 0)
    with pytest.raises(EditorError, match='occupied'):
        m.place_measure(0, 0)
    m.place_measure(0, 1, cbit=3)
    assert m.wires[(0, 1)] == D.Measure(0, 3)
    assert m.set_measure_bit(0, 1, 1) and m.wires[(0, 1)].cbit == 1
    m.place_reset(1, 1)
    assert m.operation_at(1, 1)[0] == 'reset'
    m.move(1, 1, 1, 2)
    assert m.wires[(1, 2)] == D.Reset(1)
    m.place('M', 0, 3)
    with pytest.raises(EditorError, match='before the final'):
        m.place_reset(1, 3)
    with pytest.raises(EditorError):
        m.set_condition(0, 1, 0)                              # a measurement is not a gate


def test_noise_view_and_tools_that_refuse_dynamic_circuits():
    m = teleport_model()
    assert m.noise == {}                                      # measurements are not noise
    assert m.noise_layout() == []
    with pytest.raises(EditorError, match='Simplify'):
        m.simplification()
    assert m.noisy_verification() is None


def test_plain_circuits_are_not_dynamic():
    m = CircuitModel(2)
    m.place('H', 0, 0)
    assert not m.dynamic and not m.noisy


# ---- files ------------------------------------------------------------------------------------------

def saved(m):
    gates, cols, mcol, total = m.layout()
    classical, conditions = m.classical_layout()
    return to_native_measured(m.n, gates, sorted(m.measurements), layout={
        'columns': cols, 'measurement_column': mcol, 'total_columns': total, 'initial_states': m.initial_states,
        'blocks': [(pl.block, pl.col, pl.expanded) for pl in m.blocks.values()],
        'noise': m.noise_layout(), 'noise_model': m.noise_model, 'classical': classical, 'conditions': conditions})


def load(text):
    n, gates, measured, layout = from_native_layout(text)
    copy = CircuitModel()
    copy.set_circuit(n, gates, layout['columns'], measured, layout['measurement_column'], layout['total_columns'],
                     layout['initial_states'], layout['blocks'], layout['noise'], layout['noise_model'],
                     layout['classical'], layout['conditions'])
    return copy


def test_schema_5_round_trip():
    m = teleport_model()
    m.place_reset(0, 5)
    text = saved(m)
    assert json.loads(text)['schema_version'] == 5
    copy = load(text)
    assert copy.wires == m.wires and copy.conditions == m.conditions
    assert np.allclose(copy.simulate_noisy()[1][-1], m.simulate_noisy()[1][-1])


def test_older_readers_refuse_and_bad_data_is_rejected():
    m = teleport_model()
    data = json.loads(saved(m))
    with pytest.raises(ValueError):
        from_native(json.dumps(data))
    for change in (lambda d: d.update(schema_version=4), lambda d: d['classical'][0].update(op='boom'),
                   lambda d: d['classical'][0].update(qubit=7), lambda d: d['conditions'][0].update(column=0),
                   lambda d: d['conditions'][0].update(value=5)):
        broken = json.loads(json.dumps(data))
        change(broken)
        with pytest.raises(ValueError):
            load(json.dumps(broken))


def test_circuits_without_dynamic_parts_keep_their_schema():
    m = CircuitModel(2)
    m.place('H', 0, 0)
    assert json.loads(saved(m))['schema_version'] == 1


# ---- OpenQASM 2 ---------------------------------------------------------------------------------

from quantumscope.physics.circuit_files import (convert, dynamic_sequence, from_qasm_layout,  # noqa: E402
                                                to_qasm_dynamic)

TELEPORT_QASM = '''OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg a[1];
creg b[1];
h q[1];
cx q[1],q[2];
cx q[0],q[1];
h q[0];
measure q[0] -> a[0];
measure q[1] -> b[0];
if(b==1) x q[2];
if(a==1) z q[2];
'''


def model_from_qasm(text):
    n, gates, measured, layout, _ = from_qasm_layout(text)
    m = CircuitModel()
    m.set_circuit(n, gates, layout['columns'], measured, classical=layout['classical'], conditions=layout['conditions'])
    return m


def teleports(m):
    from quantumscope.physics.initial_states import InitialState
    m.set_initial_state(0, InitialState.preset('+i'))
    target = np.array([1, 1j]) / np.sqrt(2)
    final = m.simulate_branches()[1][-1]
    return len(final) == 4 and all(
        np.real(np.vdot(target, N.partial_trace(b.rho, 3, [2]) @ target)) > 1 - 1e-9 for b in final)


def test_qasm_import_of_teleportation_teleports():
    m = model_from_qasm(TELEPORT_QASM)
    assert m.dynamic and len(m.conditions) == 2 and teleports(m)


def test_imported_conditions_come_after_their_measurement():
    m = model_from_qasm(TELEPORT_QASM)
    measured_at = {item.cbit: c for (r, c), item in m.wires.items() if isinstance(item, D.Measure)}
    for (r, c), (cbit, _) in m.conditions.items():
        assert c > measured_at[cbit]


def test_qasm_export_round_trip_keeps_the_physics():
    m = teleport_model()
    gates, columns, _, _ = m.layout()
    classical, conditions = m.classical_layout()
    text = to_qasm_dynamic(3, dynamic_sequence(3, gates, columns, (), classical, conditions))
    assert 'creg m0[1];' in text and 'if(m1==1) x q[2];' in text and 'measure q[0] -> m0[0];' in text
    assert teleports(model_from_qasm(text))


def test_converter_round_trip_between_formats():
    native = convert(TELEPORT_QASM, 'qasm')
    assert json.loads(native)['schema_version'] == 5
    back = convert(native, 'qscope')
    assert teleports(model_from_qasm(back))


def test_reset_and_terminal_measurements_in_qasm():
    text = TELEPORT_QASM + 'reset q[0];\ncreg c[3];\nmeasure q[2] -> c[2];\n'
    m = model_from_qasm(text)
    assert any(isinstance(item, D.Reset) for item in m.wires.values())


# Multi-bit register conditions are supported since v0.6.2; out-of-range values are still rejected.
@pytest.mark.parametrize('bad', ['creg r[2];\nif(r==4) x q[0];', 'if(zz==1) x q[0];', 'creg a1[1];\nif(a1==2) x q[0];'])
def test_unsupported_conditions_are_rejected(bad):
    with pytest.raises(ValueError):
        from_qasm_layout('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\n' + bad)


def test_ordinary_qasm_still_uses_the_original_importer():
    plain = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];\n'
    n, gates, measured, layout, _ = from_qasm_layout(plain)
    assert measured == [0, 1] and not layout.get('classical')


def test_import_sorts_gates_into_column_order():
    # Preparation gates on q0 come first in the program, then a gate on q1 fits into column 0.
    text = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg a[1];\nh q[0];\ns q[0];\nh q[1];\nmeasure q[0] -> a[0];\nif(a==1) x q[1];\n'
    n, gates, measured, layout, _ = from_qasm_layout(text)
    assert layout['columns'] == sorted(layout['columns'])
    m = model_from_qasm(text)
    assert m.dynamic and len(m.conditions) == 1


# ---- examples and their checks ----------------------------------------------------------------------

@pytest.mark.parametrize('state', ['0', '1', '+', '-', '+i', '-i'])
def test_teleportation_example_passes_for_every_input(state):
    m = CircuitModel()
    m.load_library('teleportation', {'input': state})
    rows, _ = m.verification()
    assert m.dynamic and len(rows) == 10 and all(r.passed for r in rows)


def test_teleportation_check_fails_without_a_correction():
    m = CircuitModel()
    m.load_library('teleportation', {'input': '+'})
    z = next(key for key, (cbit, _) in m.conditions.items() if cbit == 0)
    m.remove(*z)                                              # drop the Z correction
    rows, _ = m.verification()
    assert not all(r.passed for r in rows)


def test_teleportation_check_tests_the_current_circuit_not_the_shown_input():
    m = CircuitModel()
    m.load_library('teleportation', {'input': '0'})
    x = next(key for key, (cbit, _) in m.conditions.items() if cbit == 1)
    m.clear_condition(*x)                                     # an unconditional X: wrong, though |0⟩ alone might hide it
    assert not all(r.passed for r in m.verification()[0])


@pytest.mark.parametrize('b0,b1', [(0, 0), (0, 1), (1, 0), (1, 1)])
def test_superdense_example_sends_every_message(b0, b1):
    m = CircuitModel()
    m.load_library('superdense', {'b0': b0, 'b1': b1})
    row = m.verification()[0][0]
    assert row.passed and f'received {b0}{b1}' in row.output_label


def test_library_packs_conditions_after_their_measurements():
    m = CircuitModel()
    m.load_library('teleportation', {'input': '+i'})
    measured_at = {item.cbit: c for (r, c), item in m.wires.items() if isinstance(item, D.Measure)}
    assert all(c > measured_at[cbit] for (r, c), (cbit, _) in m.conditions.items())


# ---- lab checks and links ---------------------------------------------------------------------------

def test_dynamic_lab_checks():
    from quantumscope.learn import labs
    m = CircuitModel()
    m.load_library('teleportation', {'input': '+i'})
    for condition in ('measures >= 2', 'conditions = 2', 'branches = 4', 'teleports 0 2',
                      'record 00=0.25 01=0.25 10=0.25 11=0.25'):
        assert labs.check(m, condition)[0], condition
    assert not labs.check(m, 'teleports 0 1')[0]
    r = CircuitModel(1)
    r.place('H', 0, 0)
    assert not labs.check(r, 'settles 0 0')[0]
    r.place_measure(0, 1)
    r.place('X', 0, 2)
    r.set_condition(0, 2, 0, 1)
    assert labs.check(r, 'settles 0 0')[0] and labs.check(r, 'branches = 2')[0]


def test_dynamic_try_it_links():
    from quantumscope.learn import actions
    a = actions.parse('qs:circuit?n=2&gates=H:0;CX:0,1&measures=0:2:0;1:2:1&resets=0:3')
    kinds = sorted(type(e).__name__ for e, _ in a.params['elements'])
    assert kinds == ['Measure', 'Measure', 'Reset']
    with pytest.raises(ValueError):
        actions.parse('qs:circuit?n=2&measures=5:0:0')
    assert actions.parse('qs:example/Quantum teleportation').kind == 'example'
