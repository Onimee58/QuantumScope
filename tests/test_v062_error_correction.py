"""v0.6.2 (8b): repetition codes, the Shor code and logical error rates."""
import numpy as np
import pytest

from quantumscope.editor import qec_analysis as qa
from quantumscope.editor.circuit_model import CircuitModel
from quantumscope.physics import qec
from quantumscope.physics.initial_states import InitialState


def example(key, **params):
    m = CircuitModel()
    m.load_library(key, params)
    return m


@pytest.mark.parametrize('key,kind', [('bit_flip_code', 'X'), ('phase_flip_code', 'Z')])
@pytest.mark.parametrize('error', ['none', 'q0', 'q1', 'q2'])
def test_repetition_codes_correct_every_single_error(key, kind, error):
    m = example(key, logical='+i', error=error, p=0.1)
    rows, _ = m.verification()
    assert m.dynamic and len(rows) == 6 and all(r.passed for r in rows)
    assert sum(1 for g in m.gates.values() if g.name == kind) >= (0 if error == 'none' else 1)


@pytest.mark.parametrize('key', ['bit_flip_code', 'phase_flip_code'])
def test_two_errors_are_beyond_the_code(key):
    rows, note = example(key, logical='0', error='q0q1', p=0.1).verification()
    assert not all(r.passed for r in rows) and 'limit' in note


def test_shor_code_corrects_any_single_error():
    for error in ('none', 'X0', 'Y4', 'Z8', 'Y7', 'X3'):
        rows, _ = example('shor_code', logical='+i', error=error).verification()
        assert len(rows) == 6 and all(r.passed for r in rows), error


def test_shor_code_check_fails_without_the_majority_vote():
    m = example('shor_code', logical='+', error='Z0')
    toffolis = [key for key, g in m.gates.items() if g.name == 'CCX']
    m.remove(*toffolis[-1])                                      # drop the final phase majority vote
    assert not all(r.passed for r in m.verification()[0])


@pytest.mark.parametrize('code,channel', [('bit_flip', 'bit_flip'), ('phase_flip', 'phase_flip'),
                                          ('bit_flip', 'phase_flip'), ('phase_flip', 'bit_flip')])
def test_logical_failure_matches_the_closed_forms(code, channel):
    model, data = qa.example_model(code, channel)
    for p in (0.02, 0.1, 0.25, 0.4):
        assert qa.logical_failure(model, p, data) == pytest.approx(qec.repetition_theory(code, channel, p), abs=1e-9)


@pytest.mark.parametrize('channel', ['bit_flip', 'phase_flip', 'depolarizing'])
def test_unprotected_qubit_matches_the_channel(channel):
    model, data = qa.example_model('none', channel)
    for p in (0.1, 0.3):
        assert qa.logical_failure(model, p, data) == pytest.approx(qec.unprotected_failure(channel, p))


def test_which_code_helps_against_which_noise():
    p = 0.1
    helps = lambda code, channel: qa.logical_failure(qa.example_model(code, channel)[0], p) < qec.unprotected_failure(channel, p)
    assert helps('bit_flip', 'bit_flip') and helps('phase_flip', 'phase_flip')
    assert not helps('bit_flip', 'phase_flip') and not helps('bit_flip', 'depolarizing')


def test_the_sweep_uses_the_current_circuit():
    m = example('bit_flip_code', logical='0', error='random', p=0.1)
    before = qa.logical_failure(m, 0.1)
    key = next(k for k, g in m.gates.items() if g.name == 'X' and k in m.conditions)
    m.remove(*key)                                               # remove one correction
    assert qa.logical_failure(m, 0.1) > before + 0.01


def test_random_errors_place_noise_boxes_and_the_check_explains():
    m = example('bit_flip_code', logical='0', error='random', p=0.2)
    assert qa.noise_kind(m) == 'bit_flip' and len(m.noise) == 3
    rows, note = m.verification()
    assert not all(r.passed for r in rows) and 'Plot logical error rate' in note


def test_logical_state_and_examples_menu():
    assert np.allclose(qec.logical_state('bit_flip', [0, 1]), np.eye(8)[7])
    plus = qec.logical_state('phase_flip', [1, 0])
    assert np.allclose(np.abs(plus) ** 2, np.full(8, 1 / 8))
    from quantumscope.physics.algorithms import LIBRARY
    titles = [e.title for e in LIBRARY if e.menu == 'Examples']
    assert {'Bit-flip code', 'Phase-flip code', 'Shor code (9 qubits)'} <= set(titles)
