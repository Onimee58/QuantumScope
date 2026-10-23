"""v0.5.0: Hydrogen Dynamics view helpers (fit-to-states, display contrast)."""
import math

import numpy as np
import pytest

from quantumscope.physics.dynamics import enclosing_radius, suggested_half_width
from quantumscope.physics.dynamics_export import CONTRAST_MODES, LOG_DECADES, display_intensity
from quantumscope.physics.hydrogen import HydrogenAtom

ATOM = HydrogenAtom()


def test_enclosing_radius_matches_analytic_1s():
    # P(r < R) = 1 - e^{-2R}(1 + 2R + 2R²) for 1s in units of a_mu.
    for fraction in (0.5, 0.9, 0.995):
        r = enclosing_radius(ATOM.state(1, 0, 0), fraction)
        assert 1 - math.exp(-2 * r) * (1 + 2 * r + 2 * r * r) == pytest.approx(fraction, abs=1e-6)


@pytest.mark.parametrize('nlm', [(1, 0, 0), (2, 0, 0), (2, 1, 0), (3, 2, 0), (4, 1, 0)])
def test_suggested_half_width_contains_the_probability(nlm):
    state = ATOM.state(*nlm)
    width = suggested_half_width([state])
    r = np.linspace(0, width, 20001)
    integrate = getattr(np, "trapezoid", None) or np.trapz      # NumPy 2 renamed trapz
    inside = integrate(state.radial_probability(r), r)
    assert inside >= 0.995 - 1e-6 or width == 5.0


def test_suggested_half_width_uses_the_larger_state_and_bounds():
    small, large = ATOM.state(1, 0, 0), ATOM.state(4, 1, 0)
    assert suggested_half_width([small]) == 5.0                     # minimum
    assert suggested_half_width([small, large]) == suggested_half_width([large]) == 44.0
    assert suggested_half_width([large], maximum=30) == 30
    with pytest.raises(ValueError):
        enclosing_radius(small, 1.0)


def test_radius_grows_with_n():
    radii = [enclosing_radius(ATOM.state(n, 0, 0)) for n in (1, 2, 3, 4)]
    assert radii == sorted(radii)


@pytest.mark.parametrize('mode', CONTRAST_MODES)
def test_display_intensity_is_monotonic_and_bounded(mode):
    density = np.linspace(0, 2.0, 500)
    out = display_intensity(density, peak=1.0, mode=mode)
    assert out.min() >= 0 and out.max() <= 1 and np.all(np.diff(out) >= -1e-12)
    assert display_intensity(np.array([1.0]), 1.0, mode)[0] == pytest.approx(1)


def test_linear_is_proportional_and_log_spans_decades():
    assert display_intensity(np.array([0.25]), 1.0, 'Linear')[0] == pytest.approx(0.25)
    assert display_intensity(np.array([0.25]), 1.0, 'Enhanced (√)')[0] == pytest.approx(0.5)
    log = display_intensity(np.array([10 ** -LOG_DECADES, 1e-2, 1e-9]), 1.0, 'Logarithmic')
    assert log == pytest.approx([0.0, 0.5, 0.0])
    with pytest.raises(ValueError):
        display_intensity(np.array([1.0]), 1.0, 'Neon')


def test_contrast_never_changes_the_density_array():
    density = np.array([0.1, 0.5])
    display_intensity(density, 1.0, 'Logarithmic')
    assert np.array_equal(density, [0.1, 0.5])
