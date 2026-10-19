import numpy as np
from quantumscope.visualization.phase import phase_with_node_mask


def test_phase_mask_at_nodes():
    re = np.array([0., 1., -1., 1.e-8])
    im = np.zeros(4)
    phase = phase_with_node_mask(re, im, 1., relative_cutoff=1e-5)
    assert np.isnan(phase[0]) and np.isnan(phase[3])
    assert np.isclose(phase[1], 0.)
    assert np.isclose(abs(phase[2]), np.pi)


def test_complex_phase_angle():
    value = phase_with_node_mask(np.array([0.]), np.array([1.]), 1.)
    assert np.isclose(value[0], np.pi/2)
