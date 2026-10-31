"""v0.6.0 (6a): noise in the editor model and in .qscope files."""
import json

import numpy as np
import pytest

from quantumscope.editor.circuit_model import CircuitModel, EditorError
from quantumscope.physics import noise as N
from quantumscope.physics.circuit_files import from_native, from_native_layout, to_native_measured
from quantumscope.physics.circuits import Gate
from quantumscope.physics.blocks import Block


def bell():
    m = CircuitModel(2)
    m.place('H', 0, 0)
    m.place('CX', 1, 1)
    m.add_operand(0, 1)
    return m


def test_place_move_edit_remove_noise():
    m = bell()
    assert m.place_noise('depolarizing', 1, 2, 0.2) is True
    assert m.operation_at(1, 2)[0] == 'noise' and m.noisy
    assert m.columns == 4
    assert m.move(1, 2, 0, 2) is True and (0, 2) in m.noise and m.noise[(0, 2)].qubit == 0
    assert m.edit_noise(0, 2, p=0.5) is True and m.noise[(0, 2)].p == 0.5
    assert m.remove(0, 2) is True and not m.noise and not m.noisy


def test_noise_collisions_with_gates_blocks_and_measurements():
    m = bell()
    with pytest.raises(EditorError, match='occupied'):
        m.place_noise('bit_flip', 0, 0, 0.1)                   # H is there
    with pytest.raises(EditorError, match='occupied'):
        m.place_noise('bit_flip', 0, 1, 0.1)                   # CX control wire
    m.place_noise('bit_flip', 0, 2, 0.1)
    with pytest.raises(EditorError, match='occupied'):
        m.place('X', 0, 2)                                     # gates cannot land on noise
    with pytest.raises(EditorError):
        m.place_noise('bit_flip', 1, 2, 7)                     # invalid strength
    m.place('M', 0, 3)
    with pytest.raises(EditorError, match='before terminal'):
        m.place_noise('bit_flip', 1, 3, 0.1)
    b = CircuitModel(3)
    b.add_block(Block('custom', 'B', (0, 2), (Gate('CX', (0, 2)),)), 0)
    with pytest.raises(EditorError, match='occupied'):
        b.place_noise('bit_flip', 1, 0, 0.1)                   # inside the block's span


def test_undo_columns_and_resize():
    m = bell()
    m.place_noise('phase_flip', 1, 2, 0.3)
    m.set_noise_model(N.PRESETS['Gentle'])
    m.undo()
    assert m.noise_model == N.NoiseModel() and m.noise
    m.undo()
    assert not m.noise
    m.redo()
    m.insert_column(0)
    assert (1, 3) in m.noise
    m.delete_empty_column(0)
    assert (1, 2) in m.noise
    with pytest.raises(EditorError):
        m.delete_empty_column(2)                               # the noise element occupies it
    m.resize(1)
    assert not m.noise


def test_noise_model_persists_across_loading_examples_but_elements_do_not():
    m = bell()
    m.place_noise('bit_flip', 0, 2, 0.1)
    m.set_noise_model(N.PRESETS['Moderate'])
    m.load_example('GHZ')
    assert not m.noise and m.noise_model == N.PRESETS['Moderate']


def test_noisy_simulation_equals_ideal_without_noise():
    m = bell()
    occupied, history = m.simulate_noisy()
    ideal = m.simulate()
    assert occupied == ideal.occupied_columns
    for rho, psi in zip(history, ideal.column_states):
        assert np.allclose(rho, N.density(psi))


def test_noise_elements_change_the_state_and_get_their_own_columns():
    m = bell()
    m.place_noise('depolarizing', 1, 2, 1.0)
    occupied, history = m.simulate_noisy()
    assert occupied == [0, 1, 2]
    reduced = N.partial_trace(history[-1], 2, [1])
    assert np.allclose(reduced, np.eye(2) / 2) and N.purity(history[-1]) < 1


def test_global_model_lowers_bell_fidelity():
    m = bell()
    m.set_noise_model(N.PRESETS['Moderate'])
    _, history = m.simulate_noisy()
    target = m.simulate().column_states[-1]
    fidelity = N.fidelity_with_pure(history[-1], target)
    assert 0.8 < fidelity < 1


def test_ideal_path_is_untouched_by_noise():
    m = bell()
    before = m.simulate().column_states[-1]
    m.place_noise('bit_flip', 0, 2, 0.5)
    m.set_noise_model(N.PRESETS['Very noisy'])
    assert np.allclose(m.simulate().column_states[-1], before)          # the ideal circuit is unchanged
    assert m.ordered() == [Gate('H', (0,)), Gate('CX', (0, 1))]


# ---- files --------------------------------------------------------------------------------------

def saved(m):
    gates, cols, mcol, total = m.layout()
    return to_native_measured(m.n, gates, sorted(m.measurements), layout={
        'columns': cols, 'measurement_column': mcol, 'total_columns': total, 'initial_states': m.initial_states,
        'blocks': [(pl.block, pl.col, pl.expanded) for pl in m.blocks.values()],
        'noise': m.noise_layout(), 'noise_model': m.noise_model})


def test_schema_4_round_trip():
    m = bell()
    m.place_noise('amplitude_damping', 1, 2, 0.25)
    m.set_noise_model(N.NoiseModel(True, 0.01, 0.05, 0.0, 0.02, 0.03, idle=True))
    text = saved(m)
    assert json.loads(text)['schema_version'] == 4
    n, gates, measured, layout = from_native_layout(text)
    copy = CircuitModel()
    copy.set_circuit(n, gates, layout['columns'], measured, layout['measurement_column'], layout['total_columns'],
                     layout['initial_states'], layout['blocks'], layout['noise'], layout['noise_model'])
    assert copy.noise == m.noise and copy.noise_model == m.noise_model
    assert np.allclose(copy.simulate_noisy()[1][-1], m.simulate_noisy()[1][-1])


def test_files_without_noise_keep_their_schema_and_older_readers_refuse_noise():
    m = bell()
    assert json.loads(saved(m))['schema_version'] == 1
    m.place_noise('bit_flip', 0, 2, 0.1)
    with pytest.raises(ValueError):
        from_native(saved(m))


@pytest.mark.parametrize('change', [lambda d: d['noise'][0].update(qubit=9), lambda d: d['noise'][0].update(p=3),
                                    lambda d: d['noise'][0].update(column=1),
                                    lambda d: d.update(schema_version=3)])
def test_invalid_noise_in_files_is_rejected(change):
    m = bell()
    m.place_noise('bit_flip', 1, 2, 0.1)
    data = json.loads(saved(m))
    change(data)
    with pytest.raises(ValueError):
        n, gates, measured, layout = from_native_layout(json.dumps(data))
        CircuitModel().set_circuit(n, gates, layout['columns'], measured, noise=layout['noise'])
