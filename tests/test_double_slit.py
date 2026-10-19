import numpy as np
import pytest
from quantumscope.physics.double_slit import DoubleSlit


def test_normalization():
    x, p = DoubleSlit().distribution()
    assert abs(np.trapezoid(p, x) - 1) < 1e-12


def test_symmetry_and_nonnegative():
    _, p = DoubleSlit().distribution()
    assert np.all(p >= 0)
    assert np.allclose(p, p[::-1], atol=1e-12)


def test_center_is_local_maximum():
    _, p = DoubleSlit().distribution()
    middle = len(p) // 2
    assert p[middle] >= p[middle-1] and p[middle] >= p[middle+1]


def test_sampled_detections_reproducible():
    m = DoubleSlit()
    a = m.sample_detections(1000, seed=21)
    b = m.sample_detections(1000, seed=21)
    assert np.array_equal(a,b)
    assert np.all(np.abs(a) <= m.screen_halfwidth_mm)


def test_bad_config():
    with pytest.raises(ValueError): DoubleSlit(slit_width_um=110, slit_separation_um=100)
    with pytest.raises(ValueError): DoubleSlit(wavelength_nm=-1)
    with pytest.raises(ValueError): DoubleSlit().distribution(points=2)


def test_sample_matches_probabilities():
    m = DoubleSlit()
    x,p = m.distribution()
    draws=m.sample_detections(50000, seed=11)
    assert abs(np.mean(draws)) < .25
    assert abs(np.std(draws)-np.sqrt(np.trapezoid(x*x*p,x))) < .4
