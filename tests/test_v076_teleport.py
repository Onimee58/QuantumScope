"""v0.7.6: teleportation with a noisy pair and without Bob's correction (teleport_story)."""
import numpy as np
import pytest

from quantumscope.physics import teleport_story as T
from quantumscope.physics.initial_states import InitialState

INPUTS = [InitialState(t, p).vector() for t, p in ((0, 0), (np.pi, 0), (1.1, 0.7), (2.3, 4.0))]
RECORDS = ('00', '01', '10', '11')


@pytest.mark.parametrize('v', [1.0, 0.8, 1 / 3, 0.0])
def test_noisy_pair_fidelity_is_one_plus_v_over_two_for_every_result(v):
    for psi in INPUTS:
        for record in RECORDS:
            assert T.state_at(psi, 4, record, v)['bob_fidelity'] == pytest.approx((1 + v) / 2)
        assert sum(T.state_at(psi, 3, visibility=v)['probabilities'].values()) == pytest.approx(1)
    assert T.expected_fidelity(v) == pytest.approx((1 + v) / 2)
    if v == pytest.approx(1 / 3):
        assert T.expected_fidelity(v) == pytest.approx(T.CLASSICAL_LIMIT)       # the classical limit


def test_without_the_correction_bob_is_random_on_average():
    for psi in INPUTS:
        fidelities = [T.state_at(psi, 4, record, 1.0, correct=False)['bob_fidelity'] for record in RECORDS]
        assert fidelities[0] == pytest.approx(1)                                 # 00 needs no correction
        assert np.mean(fidelities) == pytest.approx(0.5)
        assert T.state_at(psi, 4, None, 1.0, correct=False)['bob_purity'] == pytest.approx(0.5)   # ρ = I/2
    assert T.expected_fidelity(1.0, correct=False) == 0.5


def test_clean_results_are_unchanged_and_one_run_works():
    for psi in INPUTS:
        for record in RECORDS:
            assert T.state_at(psi, 4, record)['bob_fidelity'] == pytest.approx(1)
    record, fidelity = T.teleport_once(INPUTS[2], 0.5, rng=np.random.default_rng(1))
    assert record in RECORDS and fidelity == pytest.approx(0.75)
    with pytest.raises(ValueError):
        T.state_at(INPUTS[0], 3, 'zz')
