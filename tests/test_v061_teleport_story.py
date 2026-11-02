"""v0.6.1: the teleportation story (Quantum Principles experiment)."""
import numpy as np
import pytest

from quantumscope.physics import teleport_story as story
from quantumscope.physics.initial_states import InitialState

INPUTS = [InitialState.preset(k) for k in ('0', '1', '+', '-', '+i', '-i')] + [InitialState(1.1, 0.7), InitialState(2.5, 4.0)]


@pytest.mark.parametrize('state', INPUTS, ids=lambda s: s.label)
def test_bob_is_random_until_corrected_then_exactly_the_input(state):
    a = state.vector()
    for step in (1, 2, 3):                                     # without the bits, Bob sees a random qubit
        view = story.state_at(a, step)
        assert view['bob_purity'] == pytest.approx(0.5) and np.allclose(view['blochs'][2], 0, atol=1e-12)
    final = story.state_at(a, 4)
    assert final['bob_fidelity'] == pytest.approx(1) and np.allclose(final['blochs'][2], state.bloch(), atol=1e-12)


@pytest.mark.parametrize('state', INPUTS, ids=lambda s: s.label)
def test_every_result_is_corrected_and_all_results_are_equally_likely(state):
    a = state.vector()
    assert story.state_at(a, 3)['probabilities'] == pytest.approx({'00': .25, '01': .25, '10': .25, '11': .25})
    for record in ('00', '01', '10', '11'):
        assert story.state_at(a, 4, record)['bob_fidelity'] == pytest.approx(1)
        assert story.state_at(a, 3, record)['bob_purity'] == pytest.approx(1)      # a definite, rotated state


def test_alices_original_is_destroyed_no_cloning():
    a = InitialState.preset('+i').vector()
    view = story.state_at(a, 4, '10')
    assert np.allclose(view['blochs'][0], (0, 0, -1), atol=1e-12)                # collapsed to |1⟩, not the input
    assert np.allclose(story.state_at(a, 4)['blochs'][0], 0, atol=1e-12)         # averaged: random


def test_record_validation_and_random_records():
    with pytest.raises(ValueError):
        story.state_at([1, 0], 3, '22')
    rng = np.random.default_rng(0)
    assert {story.random_record(rng) for _ in range(200)} == {'00', '01', '10', '11'}


def test_story_matches_the_circuit_example():
    from quantumscope.editor.circuit_model import CircuitModel
    from quantumscope.physics.noise import partial_trace
    m = CircuitModel()
    m.load_library('teleportation', {'input': '-'})
    final = m.simulate_branches()[1][-1]
    a = InitialState.preset('-').vector()
    for branch in final:
        bits = ''.join(map(str, branch.bits))
        q2 = partial_trace(branch.rho, 3, [2])
        assert np.allclose(story.state_at(a, 4, bits)['blochs'][2],
                           (2 * q2[0, 1].real, -2 * q2[0, 1].imag, (q2[0, 0] - q2[1, 1]).real), atol=1e-12)
