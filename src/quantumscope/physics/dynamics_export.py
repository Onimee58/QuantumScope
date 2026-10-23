"""Pure NumPy frame generation for a full hydrogen quantum beat period."""
import numpy as np


def density_frames(psi_a, psi_b, probability_a, initial_phase, count):
    """Return exactly `count` frames covering [0, 2*pi), without a duplicate endpoint.

    For a two-eigenstate superposition, relative phase advances by 2*pi over
    one beat period; the direction does not affect full-period coverage.
    """
    if count < 2 or not 0 <= probability_a <= 1:
        raise ValueError("At least two frames and a valid probability are required")
    first, second = np.broadcast_arrays(np.asarray(psi_a), np.asarray(psi_b))
    for fraction in np.arange(count, dtype=float) / count:
        wave = (np.sqrt(probability_a) * first
                + np.sqrt(1 - probability_a) * np.exp(1j * (initial_phase - 2*np.pi*fraction)) * second)
        yield np.abs(wave)**2


CONTRAST_MODES = ('Linear', 'Enhanced (√)', 'Logarithmic')
LOG_DECADES = 4.0


def display_intensity(density, peak, mode='Linear'):
    """Map density to [0, 1] for display only; the physical density is unchanged.

    Linear shows density proportionally. Enhanced uses a square root, and
    Logarithmic spans LOG_DECADES decades below the peak, so weak lobes stay
    visible next to a much denser state (for example 3d beside 1s).
    """
    x = np.clip(np.asarray(density, dtype=float) / max(float(peak), 1e-300), 0.0, 1.0)
    if mode == 'Linear':
        return x
    if mode == 'Enhanced (√)':
        return np.sqrt(x)
    if mode == 'Logarithmic':
        with np.errstate(divide='ignore'):
            return np.clip(1.0 + np.log10(np.maximum(x, 1e-300)) / LOG_DECADES, 0.0, 1.0)
    raise ValueError('Unknown contrast mode: ' + str(mode))
