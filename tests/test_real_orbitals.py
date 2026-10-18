"""Real tesseral orbital consistency checks."""
import numpy as np
import pytest
from quantumscope.physics.hydrogen import HydrogenState, RealHydrogenState


def test_real_orbitals_match_complex_pair_density_sum():
    rng = np.random.default_rng(42)
    x, y, z = rng.normal(size=(3, 150)) * 3
    for l in (1, 2, 3):
        for m in range(1, l + 1):
            n = l + 1
            cosine = RealHydrogenState(n, l, m, "cos").wavefunction(x,y,z)
            sine = RealHydrogenState(n, l, m, "sin").wavefunction(x,y,z)
            original = HydrogenState(n,l,m).wavefunction(x,y,z)
            assert np.allclose(cosine.imag if np.iscomplexobj(cosine) else 0, 0)
            assert np.allclose(cosine**2 + sine**2, 2*np.abs(original)**2)


def test_px_py_orientation_and_z_node():
    px = RealHydrogenState(2,1,1,"cos")
    py = RealHydrogenState(2,1,1,"sin")
    pz = RealHydrogenState(2,1,0,"cos")
    assert abs(px.wavefunction(0,2,0)) < 1e-12
    assert abs(py.wavefunction(2,0,0)) < 1e-12
    assert abs(pz.wavefunction(1,0,0)) < 1e-12
    assert abs(px.wavefunction(2,0,0)) > 0
    assert abs(py.wavefunction(0,2,0)) > 0
    assert abs(pz.wavefunction(0,0,2)) > 0


def test_invalid_real_orbitals():
    with pytest.raises(ValueError):
        RealHydrogenState(2,1,-1,"cos")
    with pytest.raises(ValueError):
        RealHydrogenState(2,1,0,"sin")
