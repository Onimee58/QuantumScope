"""Nonrelativistic hydrogenic bound states, using the electron-proton reduced mass.

Coordinates provided to wavefunction() are in units of the reduced-mass Bohr radius a_mu.
The wavefunction is normalized in these dimensionless coordinates; its units are
(a_mu)^(-3/2) when coordinates are expressed in physical length units.
Density therefore has units a_mu^(-3). No spin/fine/hyperfine structure included.
"""
from dataclasses import dataclass
import math

import numpy as np
from scipy import constants
from scipy.special import eval_genlaguerre, gammaln, sph_harm_y

MU = constants.m_e * constants.m_p / (constants.m_e + constants.m_p)
A_MU_METERS = 4 * np.pi * constants.epsilon_0 * constants.hbar**2 / (MU * constants.e**2)
E1_EV = -(MU * constants.e**4 / (2 * (4 * np.pi * constants.epsilon_0)**2 * constants.hbar**2)) / constants.e


@dataclass(frozen=True)
class HydrogenState:
    n: int = 1
    l: int = 0
    m: int = 0

    def __post_init__(self):
        if not all(isinstance(v, int) and not isinstance(v, bool) for v in (self.n, self.l, self.m)):
            raise ValueError("Quantum numbers must be integers")
        if self.n < 1 or not 0 <= self.l < self.n or abs(self.m) > self.l:
            raise ValueError("Require n>=1, 0<=l<n, and -l<=m<=l")

    @property
    def energy_ev(self) -> float:
        return float(E1_EV / self.n**2)

    def radial(self, r):
        """Normalized R_nl(r), with r given in a_mu and R units a_mu^-3/2."""
        r = np.asarray(r, dtype=float)
        if np.any(r < 0):
            raise ValueError("Radius must be nonnegative")
        rho = 2.0 * r / self.n
        # (2/n)^(3/2) * sqrt((n-l-1)!/[2n(n+l)!])
        log_norm = (1.5 * math.log(2.0 / self.n)
                    + 0.5 * (gammaln(self.n - self.l)
                             - math.log(2 * self.n) - gammaln(self.n + self.l + 1)))
        return np.exp(log_norm) * np.exp(-rho / 2) * rho**self.l * eval_genlaguerre(
            self.n - self.l - 1, 2 * self.l + 1, rho
        )

    def wavefunction(self, x, y, z):
        """Complex wavefunction psi(x,y,z) for Cartesian coordinates in a_mu."""
        x, y, z = np.broadcast_arrays(np.asarray(x, dtype=float),
                                      np.asarray(y, dtype=float), np.asarray(z, dtype=float))
        r = np.sqrt(x*x + y*y + z*z)
        theta = np.arccos(np.clip(np.divide(z, r, out=np.ones_like(r), where=r > 0), -1, 1))
        phi = np.arctan2(y, x)
        # SciPy sph_harm_y signature: degree l, order m, polar angle theta, azimuth phi
        return self.radial(r) * sph_harm_y(self.l, self.m, theta, phi)

    def probability_density(self, x, y, z):
        return np.abs(self.wavefunction(x, y, z))**2

    def radial_probability(self, r):
        """P(r)=r^2 |R_nl(r)|^2; integral from 0 to infinity is unity."""
        r = np.asarray(r, dtype=float)
        return r*r * self.radial(r)**2


class HydrogenAtom:
    """Convenience factory for hydrogen stationary states."""
    def state(self, n=1, l=0, m=0) -> HydrogenState:
        return HydrogenState(n, l, m)


def density_grid(state: HydrogenState, resolution=80, half_width=None):
    """Return coordinate axis and density/psi grids in (x,y,z) array ordering.

    half_width is measured in a_mu. The grid is for rendering, not infinite-space
    normalization. Use captured_probability to assess truncated domain.
    """
    if not isinstance(resolution, int) or not 32 <= resolution <= 160:
        raise ValueError("resolution must be an integer between 32 and 160")
    if half_width is None:
        half_width = float(max(12, 6 * state.n**2))
    if not np.isfinite(half_width) or half_width <= 0:
        raise ValueError("half_width must be positive and finite")
    axis = np.linspace(-half_width, half_width, resolution)
    x, y, z = np.meshgrid(axis, axis, axis, indexing="ij", sparse=True)
    psi = state.wavefunction(x, y, z)
    density = np.abs(psi)**2
    return axis, density, psi


def captured_probability(axis, density):
    """Midpoint-style cell approximation on sampled grid; useful as a diagnostic."""
    delta = float(axis[1] - axis[0])
    return float(density.sum() * delta**3)


def enclosing_density_threshold(density, spacing, fraction=0.9):
    """Density isovalue for a selected *grid-captured* probability fraction.

    Returns the threshold, not a guarantee that a mesh encloses exactly fraction
    of true infinite-domain probability. Fraction applies to the grid integral.
    """
    if not 0 < fraction < 1:
        raise ValueError("fraction must lie strictly between 0 and 1")
    ranked = np.sort(np.asarray(density).ravel())[::-1]
    weights = ranked * float(spacing)**3
    i = np.searchsorted(np.cumsum(weights), fraction * weights.sum())
    return float(ranked[min(i, len(ranked) - 1)])


@dataclass(frozen=True)
class RealHydrogenState(HydrogenState):
    """Normalized real tesseral hydrogen orbital, with |m| and cosine/sine choice.

    For m=0 this is Y_l^0. For m>0 the real and imaginary combinations of
    Y_l^(+m) and Y_l^(-m) are orthonormal; their overall sign is conventional.
    """
    kind: str = "cos"

    def __post_init__(self):
        super().__post_init__()
        if self.m < 0 or self.kind not in ("cos", "sin"):
            raise ValueError("Real orbitals require m>=0 and kind cos/sin")
        if self.m == 0 and self.kind != "cos":
            raise ValueError("The m=0 sine orbital is identically zero")

    def wavefunction(self, x, y, z):
        positive = super().wavefunction(x, y, z)
        if self.m == 0:
            return positive.real
        # Condon-Shortley: Y_l^-m = (-1)^m conjugate(Y_l^m).
        # Both combinations are orthonormal under integration over solid angle.
        if self.kind == "cos":
            return np.sqrt(2.0) * positive.real
        return np.sqrt(2.0) * positive.imag

    @property
    def label(self):
        if self.l == 1 and self.m == 1:
            return f"{self.n}p_" + ("x" if self.kind == "cos" else "y")
        if self.l == 1 and self.m == 0:
            return f"{self.n}p_z"
        return f"{self.n}{'spdf'[self.l]} real {self.kind}({self.m}phi)"
