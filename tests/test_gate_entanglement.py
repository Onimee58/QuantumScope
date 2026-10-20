import numpy as np
from quantumscope.physics.qubits import (qubit_state, prepare_gate_pair,
    pair_concurrence, pair_joint_probabilities, local_measure_pair)


def test_default_input_generates_bell_phi_plus():
    original, output = prepare_gate_pair(qubit_state(0), qubit_state(0))
    np.testing.assert_allclose(original, [1,0,0,0], atol=1e-12)
    np.testing.assert_allclose(output, [2**-.5,0,0,2**-.5], atol=1e-12)
    assert np.isclose(pair_concurrence(output),1)
    np.testing.assert_allclose(pair_joint_probabilities(output), [[.5,0],[0,.5]], atol=1e-12)


def test_other_initial_inputs_can_remain_separable():
    # Alice |+> becomes |up> after the H gate, CNOT then does not entangle Bob.
    _, output=prepare_gate_pair(qubit_state(90),qubit_state(0))
    assert pair_concurrence(output)<1e-12
    np.testing.assert_allclose(pair_joint_probabilities(output).sum(),1, atol=1e-12)


def test_local_sequential_measurements_preserve_bell_correlations():
    _, state=prepare_gate_pair(qubit_state(0),qubit_state(0))
    rng=np.random.default_rng(314)
    first,post=local_measure_pair(state,0,'alice',rng)
    second,_=local_measure_pair(post,0,'bob',rng)
    assert first==second


def test_axis_changes_modulate_joint_distribution():
    _, state=prepare_gate_pair(qubit_state(0),qubit_state(0))
    opposite=pair_joint_probabilities(state,0,180)
    np.testing.assert_allclose(opposite, [[0,.5],[.5,0]],atol=1e-12)


def test_output_state_is_normalized_with_complex_input():
    _, output=prepare_gate_pair(qubit_state(65,41),qubit_state(110,127))
    assert np.isclose(np.vdot(output,output),1)
    assert 0 <= pair_concurrence(output) <= 1
