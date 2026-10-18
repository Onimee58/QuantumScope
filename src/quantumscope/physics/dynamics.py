"""Exact coherent time evolution of hydrogen Coulomb eigenstates (no external field)."""
from dataclasses import dataclass
import numpy as np
from scipy import constants
from quantumscope.physics.hydrogen import HydrogenState


@dataclass(frozen=True)
class HydrogenSuperposition:
    """Normalized sum of two orthogonal bound states. Coefficients are amplitudes.

    Length coordinates are in reduced-mass Bohr radii. Time is in femtoseconds.
    States must be distinct eigenfunctions in the complex spherical-harmonic basis.
    """
    first: HydrogenState
    second: HydrogenState
    probability_first: float = 0.5
    relative_phase: float = 0.0

    def __post_init__(self):
        if self.first == self.second:
            raise ValueError("Choose distinct states; identical states need coefficient renormalization")
        if not np.isfinite(self.probability_first) or not 0 <= self.probability_first <= 1:
            raise ValueError("First-state probability must be between 0 and 1")
        if not np.isfinite(self.relative_phase):
            raise ValueError("Relative phase must be finite")

    @property
    def energies_ev(self):
        return (self.first.energy_ev, self.second.energy_ev)

    @property
    def beat_period_fs(self):
        delta = abs(self.first.energy_ev - self.second.energy_ev)
        return float('inf') if delta < 1e-13 else float(
            2 * np.pi * constants.hbar / (delta * constants.e) * 1e15)

    def wavefunction(self, x, y, z, time_fs=0.0):
        if not np.isfinite(time_fs):
            raise ValueError("Time must be finite")
        # Eliminate a common global phase; only the relative dynamical phase
        # changes density. This also avoids unnecessary huge phase arguments.
        angle = (-(self.second.energy_ev - self.first.energy_ev) * constants.e
                 * (time_fs * 1e-15) / constants.hbar + self.relative_phase)
        a = np.sqrt(self.probability_first)
        b = np.sqrt(1 - self.probability_first)
        return (a * self.first.wavefunction(x, y, z)
                + b * np.exp(1j * np.remainder(angle, 2*np.pi))
                * self.second.wavefunction(x, y, z))

    def density(self, x, y, z, time_fs=0.0):
        return np.abs(self.wavefunction(x, y, z, time_fs))**2

    def slice_density(self, extent=20.0, resolution=180, time_fs=0.0, plane='xz'):
        if not 32 <= resolution <= 600:
            raise ValueError("Resolution out of range")
        if not np.isfinite(extent) or extent <= 0:
            raise ValueError("Extent must be positive")
        axis = np.linspace(-extent, extent, resolution)
        a, b = np.meshgrid(axis, axis, indexing='ij')
        zero = np.zeros_like(a)
        if plane == 'xz': coords = (a, zero, b)
        elif plane == 'xy': coords = (a, b, zero)
        elif plane == 'yz': coords = (zero, a, b)
        else: raise ValueError("Plane must be xz, xy, or yz")
        return axis, self.density(*coords, time_fs=time_fs)
