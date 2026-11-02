"""v0.6.2 (8a): conditions on several classical bits ("if c0c1 = 10")."""
import json

import numpy as np
import pytest

from quantumscope.editor.circuit_model import CircuitModel, EditorError
from quantumscope.physics import dynamic as D
from quantumscope.physics import noise as N
from quantumscope.physics.circuit_files import (dynamic_sequence, from_native, from_native_layout, from_qasm_layout,
                                                to_native_measured, to_qasm_dynamic)
from quantumscope.physics.circuits import Gate

OFF = N.NoiseModel()
CORRECTIONS = {0: ((0, 1), (1, 0)), 1: ((0, 1), (1, 1)), 2: ((0, 1), (0, 1))}


def bit_flip_model(error=None, logical=1, corrections=None):
    """3-qubit bit-flip code: data q0–q2, syndrome ancillas q3, q4 measured into c0, c1."""
    gates, cols = [], []
    def add(g, c):
        gates.append(g)
        cols.append(c)
    if logical:
        add(Gate('X', (0,)), 0)
    add(Gate('CX', (0, 1)), 1)
    add(Gate('CX', (0, 2)), 2)
    if error is not None:
        add(Gate('X', (error,)), 3)
    for c, (control, target) in enumerate(((0, 3), (1, 3), (1, 4), (2, 4)), start=4):
        add(Gate('CX', (control, target)), c)
    conditions = []
    for q, col in ((0, 9), (1, 10), (2, 11)):
        rule = (corrections or CORRECTIONS).get(q)
        if rule is None:
            continue
        add(Gate('X', (q,)), col)
        conditions.append(((q, col), *rule))
    m = CircuitModel()
    m.set_circuit(5, gates, cols, classical=[(D.Measure(3, 0), 8), (D.Measure(4, 1), 8)], conditions=conditions)
    return m


def data_state(m):
    rho = D.averaged(m.simulate_branches()[1][-1])
    return N.partial_trace(rho, 5, [0, 1, 2])


# ---- engine --------------------------------------------------------------------------------------

def test_condition_holds_and_labels():
    c = D.Conditioned(Gate('X', (0,)), (0, 1), (1, 0))
    assert c.holds((1, 0)) and not c.holds((1, 1)) and c.label == 'if c0c1 = 10'
    assert D.Conditioned(Gate('X', (0,)), 2, 1).bits == (2,)
    for bad in (((0, 0), (1, 1)), ((0, 1), (1,)), ((0, 1), (1, 2)), ((), ())):
        with pytest.raises(ValueError):
            D.Conditioned(Gate('X', (0,)), *bad)


@pytest.mark.parametrize('error,syndrome', [(None, '00'), (0, '10'), (1, '11'), (2, '01')])
@pytest.mark.parametrize('logical', [0, 1])
def test_bit_flip_code_corrects_every_single_error(error, syndrome, logical):
    m = bit_flip_model(error, logical)
    record = D.record_distribution(m.simulate_branches()[1][-1])
    assert record == pytest.approx({syndrome: 1.0})
    index = 7 if logical else 0
    assert data_state(m)[index, index].real == pytest.approx(1)


def test_single_bit_conditions_alone_would_cause_a_logical_error():
    # Without multi-bit conditions: "X q0 if c0", "X q2 if c1" turns an error on q1 into a logical flip.
    m = bit_flip_model(1, 1, corrections={0: (0, 1), 2: (1, 1)})
    assert data_state(m)[0, 0].real == pytest.approx(1)          # |000⟩: the logical 1 became logical 0


# ---- model -----------------------------------------------------------------------------------------

def test_model_conditions_with_several_bits():
    m = bit_flip_model(1)
    assert m.conditions[(1, 10)] == ((0, 1), (1, 1))
    m.move(1, 10, 1, 12)
    assert m.conditions[(1, 12)] == ((0, 1), (1, 1))
    m.undo()
    assert (1, 10) in m.conditions
    assert m.set_condition(1, 10, 0, 1) and m.conditions[(1, 10)] == (0, 1)
    with pytest.raises(EditorError):
        m.set_condition(1, 10, (0, 0), (1, 1))




# ---- files and QASM -----------------------------------------------------------------------------------

def saved(m):
    gates, cols, mcol, total = m.layout()
    classical, conditions = m.classical_layout()
    return to_native_measured(m.n, gates, sorted(m.measurements), layout={
        'columns': cols, 'measurement_column': mcol, 'total_columns': total, 'initial_states': m.initial_states,
        'blocks': [], 'noise': [], 'noise_model': m.noise_model, 'classical': classical, 'conditions': conditions})


def reload(text):
    n, gates, measured, layout = from_native_layout(text)
    m = CircuitModel()
    m.set_circuit(n, gates, layout['columns'], measured, classical=layout['classical'], conditions=layout['conditions'])
    return m


def test_schema_6_round_trip_and_older_readers_refuse():
    m = bit_flip_model(2)
    text = saved(m)
    data = json.loads(text)
    assert data['schema_version'] == 6 and {'cbits', 'values'} <= set(data['conditions'][0])
    copy = reload(text)
    assert copy.conditions == m.conditions and np.allclose(data_state(copy), data_state(m))
    with pytest.raises(ValueError):
        from_native(text)
    data['schema_version'] = 5                                   # a v0.6.1 reader rejects multi-bit records
    with pytest.raises(ValueError):
        reload(json.dumps(data))


def test_single_bit_circuits_keep_schema_5():
    m = CircuitModel(2)
    m.place_measure(0, 0)
    m.place('X', 1, 1)
    m.set_condition(1, 1, 0, 1)
    assert json.loads(saved(m))['schema_version'] == 5


def qasm_of(m):
    gates, cols, _, _ = m.layout()
    classical, conditions = m.classical_layout()
    return to_qasm_dynamic(m.n, dynamic_sequence(m.n, gates, cols, (), classical, conditions))


def test_qasm_shared_register_and_expanded_partial_conditions():
    m = bit_flip_model(0)
    m.place('H', 4, 12)
    m.set_condition(4, 12, 1, 1)                                 # a single-bit condition inside the shared register
    text = qasm_of(m)
    assert 'creg r0[2];' in text and 'measure q[3] -> r0[0];' in text
    assert 'if(r0==1) x q[0];' in text and 'if(r0==3) x q[1];' in text and 'if(r0==2) x q[2];' in text
    assert 'if(r0==2) h q[4];' in text and 'if(r0==3) h q[4];' in text


@pytest.mark.parametrize('error', [None, 0, 1, 2])
def test_qasm_round_trip_preserves_the_correction(error):
    m = bit_flip_model(error)
    n, gates, measured, layout, _ = from_qasm_layout(qasm_of(m))
    copy = CircuitModel()
    copy.set_circuit(n, gates, layout['columns'], measured, classical=layout['classical'], conditions=layout['conditions'])
    assert data_state(copy)[7, 7].real == pytest.approx(1)


def test_qasm_import_of_a_multi_bit_register():
    text = ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[3];\ncreg s[2];\nx q[0];\nmeasure q[0] -> s[0];\n'
            'measure q[1] -> s[1];\nif(s==1) x q[2];\n')
    n, gates, measured, layout, _ = from_qasm_layout(text)
    assert layout['conditions'][0][1:] == ((0, 1), (1, 0))
    with pytest.raises(ValueError):
        from_qasm_layout(text.replace('if(s==1)', 'if(s==4)'))


def test_single_bit_qasm_is_unchanged_from_v061():
    m = CircuitModel(3)
    m.place_measure(0, 0)
    m.place('X', 2, 1)
    m.set_condition(2, 1, 0, 1)
    text = qasm_of(m)
    assert 'creg m0[1];' in text and 'if(m0==1) x q[2];' in text


def test_library_packing_waits_for_every_bit():
    from quantumscope.physics import algorithms
    from quantumscope.physics.initial_states import defaults
    entry = algorithms.Entry('_t', 'Examples', 'T', (), lambda p: algorithms.Built(
        3, [D.Measure(0, 0), Gate('H', (1,)), Gate('H', (1,)), D.Measure(1, 1),
            D.Conditioned(Gate('X', (2,)), (0, 1), (1, 1))], defaults(3)), lambda p, v: ([], ''), '')
    algorithms.ENTRIES['_t'] = entry
    try:
        m = CircuitModel()
        m.load_library('_t', {})
        measured_at = {item.cbit: c for (r, c), item in m.wires.items() if isinstance(item, D.Measure)}
        (key, condition), = m.conditions.items()
        assert key[1] > max(measured_at.values())
    finally:
        del algorithms.ENTRIES['_t']
