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
