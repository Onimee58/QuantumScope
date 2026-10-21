"""Terminal measurements display only the classical bits that were measured."""
import numpy as np
import pytest
from quantumscope.physics.circuits import measurement_marginal


def test_measure_q2_only_in_bell_three_qubit_register():
    probabilities=np.zeros(8)
    probabilities[0]=.5  # |000>
    probabilities[6]=.5  # |110>
    counts=np.zeros(8,dtype=int)
    counts[0]=513
    counts[6]=511
    theory,shots=measurement_marginal(probabilities,3,[2],counts)
    np.testing.assert_allclose(theory,[1,0])
    assert shots.tolist()==[1024,0]


def test_measure_entangled_pair():
    probabilities=np.zeros(8)
    probabilities[0]=.5
    probabilities[6]=.5
    theory,_=measurement_marginal(probabilities,3,[0,1])
    np.testing.assert_allclose(theory,[.5,0,0,.5])


def test_subset_keeps_q0_first_bit_order():
    probabilities=np.zeros(8)
    probabilities[5]=1 # |101>, read q0 and q2 => |11>
    theory,_=measurement_marginal(probabilities,3,[2,0])
    np.testing.assert_allclose(theory,[0,0,0,1])


def test_invalid_measured_wire_rejected():
    with pytest.raises(ValueError):measurement_marginal(np.ones(8)/8,3,[3])
