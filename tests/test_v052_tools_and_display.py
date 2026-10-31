"""v0.5.2 patch 2a: circuit simplification, equivalence and display settings."""
import math

import numpy as np
import pytest

from quantumscope.editor.circuit_model import CircuitModel
from quantumscope.physics import display
from quantumscope.physics.circuits import ALL, DUAL, TRIPLE, Gate, apply_gate
from quantumscope.physics.gate_education import format_amplitude
from quantumscope.physics.optimize import circuit_unitary, equivalent, simplify_sequence
from quantumscope.physics.state_analysis import amplitude_rows, dirac_latex, dirac_text, state_csv


@pytest.fixture(autouse=True)
def default_display():
    yield
    display.configure(bit_order='q0_left', number_format='exact', decimals=4)


def random_circuit(rng, n, count):
    gates = []
    for _ in range(count):
        name = ALL[rng.integers(len(ALL))]
        k = 3 if name in TRIPLE else 2 if name in DUAL else 1
        if k > n:
            continue
        gates.append(Gate(name, tuple(int(q) for q in rng.permutation(n)[:k]), *map(float, rng.normal(size=3))))
    return gates


def test_circuit_unitary_matches_the_simulator():
    rng = np.random.default_rng(5)
    for _ in range(15):
        n = int(rng.integers(1, 5))
        gates = random_circuit(rng, n, 10)
        u = circuit_unitary(n, gates)
        for i in range(1 << n):
            v = np.zeros(1 << n, complex)
            v[i] = 1
            for g in gates:
                v = apply_gate(v, n, g)
            assert np.allclose(u[:, i], v)


def simplify(gates):
    kept, changes = simplify_sequence([('gate', i, g) for i, g in enumerate(gates)])
    return [kept[i] for i in range(len(gates)) if i in kept], changes


@pytest.mark.parametrize('pair', [('H', 'H'), ('X', 'X'), ('Z', 'Z'), ('S', 'SDG'), ('SDG', 'S'), ('T', 'TDG')])
def test_single_qubit_cancellations(pair):
    after, changes = simplify([Gate(pair[0], (0,)), Gate(pair[1], (0,))])
    assert after == [] and len(changes) == 1


@pytest.mark.parametrize('first,second', [(Gate('CX', (0, 1)), Gate('CX', (0, 1))), (Gate('CZ', (0, 1)), Gate('CZ', (1, 0))),
                                          (Gate('SWAP', (0, 1)), Gate('SWAP', (1, 0))),
                                          (Gate('CCX', (0, 1, 2)), Gate('CCX', (1, 0, 2))),
                                          (Gate('CSWAP', (0, 1, 2)), Gate('CSWAP', (0, 2, 1)))])
def test_multi_qubit_cancellations(first, second):
    assert simplify([first, second])[0] == []


@pytest.mark.parametrize('first,second', [(Gate('CX', (0, 1)), Gate('CX', (1, 0))), (Gate('CCX', (0, 1, 2)), Gate('CCX', (0, 2, 1))),
                                          (Gate('S', (0,)), Gate('S', (0,))), (Gate('H', (0,)), Gate('H', (1,)))])
def test_things_that_must_not_cancel(first, second):
    assert len(simplify([first, second])[0]) == 2


def test_rotations_merge_and_identity_rotations_disappear():
    after, _ = simplify([Gate('RZ', (0,), 0.2), Gate('RZ', (0,), 0.3)])
    assert after == [Gate('RZ', (0,), 0.5)]
    assert simplify([Gate('P', (0,), 2 * math.pi)])[0] == []
    after, changes = simplify([Gate('RX', (0,), 2 * math.pi)])
    assert after == [] and 'global phase' in changes[0]
    assert simplify([Gate('RX', (0,), math.pi)])[0] == [Gate('RX', (0,), math.pi)]


def test_gates_in_between_block_cancellation():
    gates = [Gate('CX', (0, 1)), Gate('Z', (1,)), Gate('CX', (0, 1))]
    assert simplify(gates)[0] == gates


def test_cascading_cancellation():
    after, changes = simplify([Gate('H', (0,)), Gate('X', (0,)), Gate('X', (0,)), Gate('H', (0,))])
    assert after == [] and len(changes) == 2


def test_barriers_are_never_looked_through():
    kept, changes = simplify_sequence([('gate', 0, Gate('H', (0,))), ('barrier', 'b', (0, 1)), ('gate', 1, Gate('H', (0,)))])
    assert len(kept) == 2 and not changes


def test_simplification_is_always_equivalent_on_random_circuits():
    rng = np.random.default_rng(11)
    pool = [Gate('H', (0,)), Gate('H', (1,)), Gate('S', (0,)), Gate('SDG', (0,)), Gate('CX', (0, 1)), Gate('CX', (1, 0)),
            Gate('RZ', (1,), 0.4), Gate('RZ', (1,), -0.4), Gate('CP', (0, 1), 0.3), Gate('T', (1,)), Gate('TDG', (1,))]
    for _ in range(200):
        gates = [pool[i] for i in rng.integers(len(pool), size=10)]
        after, _ = simplify(gates)
        assert equivalent(2, gates, after)[0] and len(after) <= len(gates)


def test_equivalence_detects_phase_and_difference():
    same, phase, _ = equivalent(1, [Gate('H', (0,)), Gate('Z', (0,)), Gate('H', (0,))], [Gate('X', (0,))])
    assert same and abs(phase - 1) < 1e-9
    same, phase, _ = equivalent(1, [Gate('RX', (0,), 2 * math.pi)], [])
    assert same and abs(phase + 1) < 1e-9
    assert not equivalent(2, [Gate('CX', (0, 1))], [Gate('CX', (1, 0))])[0]


def test_model_simplification_preview_apply_undo_and_blocks():
    m = CircuitModel(3)
    for name, r, c in (('H', 0, 0), ('H', 0, 1), ('T', 1, 0), ('TDG', 1, 1), ('X', 2, 0)):
        m.place(name, r, c)
    kept, changes, ok, _ = m.simplification()
    assert ok and len(changes) == 2 and list(kept.values()) == [Gate('X', (2,))]
    assert len(m.gates) == 5                           # preview changes nothing
    m.apply_simplification(kept)
    assert list(m.gates.values()) == [Gate('X', (2,))]
    m.undo()
    assert len(m.gates) == 5
    g = CircuitModel()
    g.load_library('grover', {'n': 2, 'marked': '11', 'iterations': 1})
    assert g.simplification()[1] == []                 # block contents are never touched


def test_bit_order_display():
    state = np.zeros(8, complex)
    state[4] = 1                                       # q0 = 1: |100⟩ in textbook order
    assert dirac_text(state, 3) == '|100⟩'
    display.configure(bit_order='q0_right')
    assert dirac_text(state, 3) == '|001⟩' and amplitude_rows(state, 3)[0]['label'] == '|001⟩'
    assert r'\lvert 001\rangle' in dirac_latex(state, 3)
    assert state_csv(state, 3).splitlines()[5].startswith('100,')   # CSV data stays q0 first


def test_decimal_number_format():
    display.configure(number_format='decimal', decimals=3)
    assert format_amplitude(1 / math.sqrt(2)) == '0.707' and format_amplitude(complex(0.5, -0.5)) == '0.5 - 0.5i'
    assert format_amplitude(1 / math.sqrt(2), exact=True) == '1/√2'
    with pytest.raises(ValueError):
        display.configure(bit_order='sideways')
