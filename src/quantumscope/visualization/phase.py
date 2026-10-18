"""Numerical phase utilities independent of the renderer."""
import numpy as np

def phase_with_node_mask(real, imag, global_amplitude, relative_cutoff=1e-4):
    """Phase is undefined at nodes; mark numerically tiny amplitudes as NaN."""
    amplitude = np.hypot(real, imag)
    phase = np.angle(real + 1j * imag).astype(np.float32)
    phase[amplitude <= max(1e-15, relative_cutoff * global_amplitude)] = np.nan
    return phase


