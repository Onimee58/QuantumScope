"""Far-field double-slit probability model for noninteracting particles.

Assumptions: coherent monochromatic illumination, two equal uniformly illuminated
rectangular slits, scalar Fraunhofer diffraction, paraxial screen coordinates.
This is a distribution model, NOT a time-dependent Schrodinger solver.
"""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class DoubleSlit:
    wavelength_nm: float = 500.0
    slit_width_um: float = 20.0
    slit_separation_um: float = 100.0
    screen_distance_m: float = 1.0
    screen_halfwidth_mm: float = 40.0

    def __post_init__(self):
        values = (self.wavelength_nm, self.slit_width_um,
                  self.slit_separation_um, self.screen_distance_m,
                  self.screen_halfwidth_mm)
        if not all(np.isfinite(x) and x > 0 for x in values):
            raise ValueError('All experiment parameters must be finite and positive')
        if self.slit_separation_um < self.slit_width_um:
            raise ValueError('Slit separation must not be smaller than slit width')

    def distribution(self, points=2001, which_path=False):
        """Return screen x [mm] and normalized density [1/mm].

        Uses sin(theta) approximately equal to x/L (paraxial assumption).
        np.sinc has the definition sin(pi*x)/(pi*x).
        """
        if not isinstance(points, int) or points < 101 or points > 200001:
            raise ValueError('points must be an integer between 101 and 200001')
        x = np.linspace(-self.screen_halfwidth_mm, self.screen_halfwidth_mm, points)
        lam = self.wavelength_nm * 1e-9
        theta = x * 1e-3 / self.screen_distance_m
        a = self.slit_width_um * 1e-6
        d = self.slit_separation_um * 1e-6
        envelope = np.sinc(a * theta / lam) ** 2
        fringes = np.cos(np.pi * d * theta / lam) ** 2
        # A fully distinguishing which-path measurement removes the cross term.
        # In the far field, incoherent paths yield the single-slit envelope.
        intensity = envelope if which_path else envelope * fringes
        area = float(np.trapezoid(intensity, x))
        if not np.isfinite(area) or area <= 0:
            raise ValueError('Degenerate sampled diffraction pattern; change parameters')
        return x, intensity / area

    def sample_detections(self, count, seed=None, points=4001, which_path=False):
        """Draw independent screen hits via inverse-CDF sampling [mm]."""
        if not isinstance(count, int) or count < 0 or count > 200000:
            raise ValueError('count must be an integer from 0 to 200000')
        x, density = self.distribution(points, which_path=which_path)
        dx = np.diff(x)
        cdf = np.concatenate(([0.0], np.cumsum((density[:-1] + density[1:]) * dx / 2)))
        cdf /= cdf[-1]
        return np.interp(np.random.default_rng(seed).random(count), cdf, x)
