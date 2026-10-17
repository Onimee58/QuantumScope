import numpy as np
import pytest
from scipy.integrate import quad
from scipy.special import sph_harm_y
from quantumscope.physics.hydrogen import (
    HydrogenState, HydrogenAtom, captured_probability, density_grid,
    enclosing_density_threshold,
)


def test_ground_state_origin():
    value = HydrogenState().wavefunction(0, 0, 0)
    np.testing.assert_allclose(value, 1 / np.sqrt(np.pi), rtol=1e-13)


@pytest.mark.parametrize("n,l,m", [(1,0,0), (2,0,0), (2,1,-1), (2,1,0), (3,2,2), (4,3,1)])
def test_radial_normalization(n, l, m):
    state = HydrogenState(n, l, m)
    integral = quad(lambda r: float(state.radial_probability(r)), 0, np.inf, epsabs=1e-10)[0]
    assert integral == pytest.approx(1.0, abs=1e-9)


def test_energy_ratio():
    assert HydrogenState(2, 1, 0).energy_ev / HydrogenState().energy_ev == pytest.approx(0.25)


def test_radial_nodes_2s():
    assert HydrogenState(2, 0, 0).radial(2.0) == pytest.approx(0.0, abs=1e-14)


def test_2p_z_nodal_plane():
    assert abs(HydrogenState(2, 1, 0).wavefunction(1, 0, 0)) < 1e-12
    assert abs(HydrogenState(2, 1, 0).wavefunction(0, 0, 1)) > 0


def test_spherical_harmonic_convention():
    st = HydrogenState(2, 1, 1)
    r = 1.75
    assert st.wavefunction(r, 0, 0) == pytest.approx(st.radial(r) * sph_harm_y(1, 1, np.pi/2, 0))


def test_grid_ground_state_integral():
    axis, density, psi = density_grid(HydrogenAtom().state(), 96, 12)
    assert density.shape == psi.shape == (96, 96, 96)
    assert captured_probability(axis, density) == pytest.approx(1.0, abs=0.003)


def test_enclosing_threshold():
    axis, density, _ = density_grid(HydrogenState(), 48)
    t90 = enclosing_density_threshold(density, axis[1]-axis[0], 0.9)
    t50 = enclosing_density_threshold(density, axis[1]-axis[0], 0.5)
    assert 0 < t90 < t50 < density.max()


@pytest.mark.parametrize("numbers", [(0,0,0), (2,2,0), (2,1,2), (2,-1,0), (1,0,.5)])
def test_invalid_quantum_numbers(numbers):
    with pytest.raises(ValueError):
        HydrogenState(*numbers)
