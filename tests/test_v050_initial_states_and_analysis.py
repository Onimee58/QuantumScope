"""v0.5.0: initial states, schema-2 files, and the State Inspector's physics."""
import json
import math

import numpy as np
import pytest

from quantumscope.editor.circuit_model import CircuitModel, EditorError
from quantumscope.physics.circuits import Gate, evolution, parse_qasm
from quantumscope.physics.circuit_files import (convert, from_native, from_native_layout, from_native_measured,
                                                from_qasm_layout, to_native, to_native_measured, to_qasm_measured)
from quantumscope.physics.initial_states import (PRESETS, PRESET_ORDER, InitialState, all_default, defaults,
                                                 preparation_gates, product_state)
from quantumscope.physics.state_analysis import (amplitude_rows, analyze_circuit, dirac_latex, dirac_text,
                                                 entropy_bits, is_clifford, minimum_depth, purity,
                                                 reduced_density_matrix, reduced_summary, remove_global_phase,
                                                 state_csv)

S = InitialState


def run(n, gates, states=None):
    return evolution(n, gates, None if states is None else product_state(states))[-1]


# Initial states ---------------------------------------------------------------------

@pytest.mark.parametrize('key', PRESET_ORDER)
def test_preset_vectors_and_bloch_vectors(key):
    state = S.preset(key)
    expected_bloch = {'0': (0, 0, 1), '1': (0, 0, -1), '+': (1, 0, 0), '-': (-1, 0, 0),
                      '+i': (0, 1, 0), '-i': (0, -1, 0)}[key]
    assert state.bloch() == pytest.approx(expected_bloch, abs=1e-12)
    assert np.isclose(np.linalg.norm(state.vector()), 1)
    assert state.preset_key == key and state.label == PRESETS[key][2]


@pytest.mark.parametrize('key', PRESET_ORDER)
def test_preset_preparation_gates_are_exact(key):
    state = S.preset(key)
    assert np.allclose(run(1, state.preparation(0)), state.vector())


@pytest.mark.parametrize('theta,phi', [(0.3, 0.0), (math.pi / 3, 1.2), (2.9, 5.5), (math.pi / 2, 0.4)])
def test_custom_states_and_their_u_preparation(theta, phi):
    state = S(theta, phi)
    assert state.preset_key is None and state.label == '|ψ⟩'
    expected = [math.cos(theta / 2), np.exp(1j * phi) * math.sin(theta / 2)]
    assert np.allclose(state.vector(), expected)
    assert np.allclose(run(1, state.preparation(0)), expected)


def test_custom_state_equal_to_a_preset_takes_its_label():
    assert S(math.pi / 2, 0).label == '|+⟩'
    assert S(math.pi / 2, -math.pi / 2).label == '|−i⟩'     # φ normalized into [0, 2π)


def test_phase_is_irrelevant_at_the_poles():
    assert S(math.pi, 2.0) == S.preset('1') and S(0.0, 1.0) == S.preset('0')


@pytest.mark.parametrize('theta,phi', [(-0.1, 0), (3.3, 0), (float('nan'), 0), (1, float('inf'))])
def test_invalid_custom_angles(theta, phi):
    with pytest.raises(ValueError):
        S(theta, phi)


def test_product_state_order_is_q0_first():
    states = [S.preset('1'), S.preset('0')]          # |10⟩
    assert np.allclose(product_state(states), [0, 0, 1, 0])


def test_record_round_trip():
    for state in [S.preset(k) for k in PRESET_ORDER] + [S(1.1, 2.2)]:
        assert S.from_record(json.loads(json.dumps(state.to_record()))) == state
    with pytest.raises(ValueError):
        S.from_record({'preset': 'nope'})


# Files and QASM -------------------------------------------------------------------------

GATES = [Gate('H', (0,)), Gate('CX', (0, 1)), Gate('T', (2,))]
STATES = [S.preset('1'), S.preset('0'), S(math.pi / 3, 1.2)]
LAYOUT = {'columns': [0, 1, 1], 'measurement_column': 3, 'total_columns': 5, 'initial_states': STATES}


def test_non_default_initial_states_use_schema_2():
    data = json.loads(to_native_measured(3, GATES, [1], layout=LAYOUT))
    assert data['schema_version'] == 2 and len(data['initial_states']) == 3


def test_default_initial_states_stay_schema_1():
    data = json.loads(to_native_measured(3, GATES, layout={**LAYOUT, 'initial_states': defaults(3)}))
    assert data['schema_version'] == 1 and 'initial_states' not in data


def test_schema_2_round_trip():
    n, gates, measured, layout = from_native_layout(to_native_measured(3, GATES, [1], layout=LAYOUT))
    assert (n, gates, measured) == (3, GATES, [1])
    assert layout['initial_states'] == STATES and layout['columns'] == [0, 1, 1]


def test_readers_that_cannot_carry_initial_states_refuse_instead_of_dropping_them():
    text = to_native_measured(3, GATES, [1], layout=LAYOUT)
    for reader in (from_native, from_native_measured):
        with pytest.raises(ValueError, match='initial states'):
            reader(text)


def test_v040_style_reader_rejects_schema_2():
    # v0.4.x accepted only schema_version 1, so it refuses rather than simulating from |0⟩.
    data = json.loads(to_native_measured(3, GATES, layout=LAYOUT))
    assert data['schema_version'] != 1


@pytest.mark.parametrize('bad', [{'schema_version': 2}, {'schema_version': 2, 'initial_states': [{'preset': '0'}]},
                                 {'schema_version': 1, 'initial_states': [{'preset': '0'}] * 3}])
def test_malformed_initial_states_are_rejected(bad):
    data = json.loads(to_native(3, GATES))
    data.pop('schema_version')
    data.update(bad)
    with pytest.raises(ValueError):
        from_native_layout(json.dumps(data))


def test_qasm_export_prepares_initial_states_exactly():
    qasm = to_qasm_measured(3, GATES, [1], STATES)
    assert qasm.isascii()
    assert '// Initial-state preparation' in qasm and 'x q[0];' in qasm and 'u3(' in qasm
    n, gates, measured, _, _ = from_qasm_layout(qasm)
    assert measured == [1]
    assert np.allclose(run(3, gates), run(3, GATES, STATES))


def test_converter_notes_initial_states():
    notes = []
    qasm = convert(to_native_measured(3, GATES, layout=LAYOUT), 'qscope', notes)
    assert notes and 'preparation gates' in notes[0] and 'x q[0];' in qasm


def test_qasm_import_starts_from_zero():
    *_, layout, _ = from_qasm_layout('OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; h q[0];')
    assert all_default(layout['initial_states'])


# Editor model ---------------------------------------------------------------------------

def test_model_simulates_from_initial_states_and_undoes_changes():
    m = CircuitModel(2)
    m.place('CX', 1, 0)
    m.add_operand(0, 0)
    assert m.set_initial_state(0, S.preset('1')) is True
    assert m.set_initial_state(0, S.preset('1')) is False      # unchanged, no undo entry
    final = m.simulate().column_states[-1]
    assert np.allclose(final, [0, 0, 0, 1])                    # |10⟩ → CX → |11⟩
    m.undo()
    assert all_default(m.initial_states)
    m.redo()
    assert m.initial_states[0] == S.preset('1')


def test_model_initial_states_follow_resize_clear_and_loading():
    m = CircuitModel(2)
    m.set_initial_state(1, S.preset('-'))
    m.resize(4)
    assert m.initial_states[1] == S.preset('-') and len(m.initial_states) == 4
    m.resize(1)
    assert m.initial_states == defaults(1)
    m.set_initial_state(0, S.preset('+'))
    m.clear()
    assert all_default(m.initial_states)
    m.set_initial_state(0, S.preset('+'))
    m.load_example('GHZ')
    assert all_default(m.initial_states)
    with pytest.raises(EditorError):
        m.set_initial_state(7, S.preset('1'))


def test_verification_notes_that_initial_states_are_not_used():
    m = CircuitModel(3)
    m.load_example('Half adder (a=1,b=1)')
    m.set_initial_state(2, S.preset('1'))
    rows, note = m.verification()
    assert all(r.passed for r in rows) and 'does not use the chosen initial states' in note


def test_set_circuit_validates_initial_states():
    m = CircuitModel(2)
    with pytest.raises(ValueError):
        m.set_circuit(2, [Gate('H', (0,))], initial_states=[S.preset('1')])


# State analysis ---------------------------------------------------------------------------

BELL = run(2, [Gate('H', (0,)), Gate('CX', (0, 1))])
GHZ = run(3, [Gate('H', (0,)), Gate('CX', (0, 1)), Gate('CX', (1, 2))])


def test_bell_reduced_states_are_maximally_mixed():
    for q in (0, 1):
        info = reduced_summary(BELL, 2, [q])
        assert np.allclose(info['rho'], np.eye(2) / 2)
        assert info['purity'] == pytest.approx(0.5) and info['entropy'] == pytest.approx(1.0)
        assert info['verdict'].startswith('Mixed') and info['bloch'] == pytest.approx((0, 0, 0))
    whole = reduced_summary(BELL, 2, [0, 1])
    assert whole['purity'] == pytest.approx(1) and whole['verdict'].startswith('Pure: this is the whole')


def test_ghz_every_qubit_and_pair_is_mixed():
    for keep in ([0], [1], [2], [0, 1], [1, 2]):
        assert reduced_summary(GHZ, 3, keep)['entropy'] == pytest.approx(1.0)


def test_product_state_is_pure_on_each_qubit():
    state = run(3, [Gate('H', (0,)), Gate('RY', (1,), 0.7), Gate('T', (2,))], [S.preset('0'), S.preset('0'), S(1.0, 0.5)])
    for q in range(3):
        info = reduced_summary(state, 3, [q])
        assert info['entropy'] == pytest.approx(0, abs=1e-9) and info['verdict'].startswith('Pure: not entangled')
        assert np.linalg.norm(info['bloch']) == pytest.approx(1)


def test_reduced_matrix_properties_on_random_states():
    rng = np.random.default_rng(3)
    for _ in range(20):
        n = int(rng.integers(2, 6))
        psi = rng.normal(size=1 << n) + 1j * rng.normal(size=1 << n)
        psi /= np.linalg.norm(psi)
        keep = sorted(rng.choice(n, size=int(rng.integers(1, min(3, n - 1) + 1)), replace=False).tolist())
        rho = reduced_density_matrix(psi, n, keep)
        assert np.isclose(np.trace(rho), 1) and np.allclose(rho, rho.conj().T)
        assert np.linalg.eigvalsh(rho).min() > -1e-12
        rest = [q for q in range(n) if q not in keep]
        # Schmidt symmetry: both sides of a pure-state bipartition have equal entropy.
        assert entropy_bits(rho) == pytest.approx(entropy_bits(reduced_density_matrix(psi, n, rest)), abs=1e-9)
        assert 1 / rho.shape[0] - 1e-9 <= purity(rho) <= 1 + 1e-9


def test_reduced_state_qubit_order_and_limit():
    state = product_state([S.preset('1'), S.preset('0'), S.preset('0')])     # |100⟩
    rho = reduced_density_matrix(state, 3, [2, 0])                           # keep q0, q2 (q0 first)
    assert np.isclose(rho[2, 2], 1)                                          # |q0 q2⟩ = |10⟩
    with pytest.raises(ValueError):
        reduced_summary(GHZ, 3, [0, 1, 2, 3])


def test_amplitude_rows_filter_sort_and_phases():
    state = run(2, [Gate('H', (0,)), Gate('S', (0,)), Gate('RY', (1,), 1.0)])
    rows = amplitude_rows(state, 2)
    assert [r['label'] for r in rows] == ['|00⟩', '|01⟩', '|10⟩', '|11⟩']
    assert rows[2]['phase_text'] == 'π/2'
    assert sum(r['probability'] for r in rows) == pytest.approx(1)
    by_prob = amplitude_rows(state, 2, order='probability')
    assert by_prob[0]['probability'] >= by_prob[-1]['probability']
    assert len(amplitude_rows(BELL, 2)) == 2 and len(amplitude_rows(BELL, 2, show_all=True)) == 4
    assert amplitude_rows(BELL, 2, show_all=True)[1]['phase_text'] == '—'


def test_global_phase_removal_keeps_physics():
    state = np.exp(0.9j) * BELL
    fixed = remove_global_phase(state)
    assert np.isclose(fixed[0].imag, 0) and fixed[0].real > 0
    assert np.allclose(np.abs(fixed), np.abs(state))
    assert np.isclose(abs(np.vdot(fixed, state)), 1)


def test_dirac_text_and_latex():
    assert dirac_text(BELL, 2) == '(1/√2)|00⟩ + (1/√2)|11⟩'
    assert dirac_latex(BELL, 2) == r'\frac{1}{\sqrt{2}}\lvert 00\rangle + \frac{1}{\sqrt{2}}\lvert 11\rangle'
    minus = run(1, [Gate('X', (0,)), Gate('H', (0,))])
    assert dirac_text(minus, 1) == '(1/√2)|0⟩ - (1/√2)|1⟩'
    assert dirac_text(run(1, [Gate('X', (0,))]), 1) == '|1⟩'
    assert dirac_text(-1 * run(1, [Gate('X', (0,))]), 1) == '-|1⟩'
    assert dirac_text(-1 * run(1, [Gate('X', (0,))]), 1, relative_phase=True) == '|1⟩'


def test_csv_has_every_basis_state_at_full_precision():
    lines = state_csv(BELL, 2).strip().splitlines()
    assert lines[0].startswith('basis,real,imag') and len(lines) == 5
    values = np.array([float(line.split(',')[1]) + 1j * float(line.split(',')[2]) for line in lines[1:]])
    assert np.allclose(values, BELL, atol=1e-15)


# Circuit analysis --------------------------------------------------------------------------

@pytest.mark.parametrize('gate,clifford', [
    (Gate('H', (0,)), True), (Gate('S', (0,)), True), (Gate('SX', (0,)), True), (Gate('T', (0,)), False),
    (Gate('RZ', (0,), math.pi / 2), True), (Gate('RX', (0,), math.pi), True), (Gate('RY', (0,), 0.4), False),
    (Gate('U', (0,), math.pi / 2, 0, math.pi), True),        # U(π/2, 0, π) = H
    (Gate('CX', (0, 1)), True), (Gate('SWAP', (0, 1)), True), (Gate('CCX', (0, 1, 2)), False)])
def test_clifford_classification(gate, clifford):
    assert is_clifford(gate) is clifford


def test_minimum_depth_versus_drawn_depth():
    gates = [Gate('H', (0,)), Gate('H', (1,)), Gate('CX', (0, 1)), Gate('X', (2,))]
    assert minimum_depth(3, gates) == 2
    stats = analyze_circuit(3, gates, columns=[0, 1, 2, 5])
    assert stats['drawn_depth'] == 4 and stats['minimum_depth'] == 2


def test_analyze_circuit_counts():
    gates = [Gate('H', (0,)), Gate('T', (1,)), Gate('TDG', (1,)), Gate('CX', (0, 1)), Gate('RZ', (2,), 0.3),
             Gate('CCX', (0, 1, 2))]
    stats = analyze_circuit(4, gates, list(range(6)), measured=[3])
    assert stats['counts'] == {'CCX': 1, 'CX': 1, 'H': 1, 'RZ': 1, 'T': 1, 'TDG': 1}
    assert (stats['single_qubit'], stats['two_qubit'], stats['three_qubit']) == (4, 1, 1)
    assert stats['t_count'] == 2 and stats['clifford'] == 2 and stats['non_clifford'] == 4
    assert stats['parameterized'] == 1 and stats['qubits_used'] == [0, 1, 2, 3] and stats['measurements'] == 1


def test_model_analysis_matches_layout():
    m = CircuitModel(3)
    m.load_example('2-bit ripple-carry adder (1+1)')
    stats = m.analysis()
    assert stats['total'] == 8 and stats['three_qubit'] == 3 and stats['drawn_depth'] >= stats['minimum_depth']
