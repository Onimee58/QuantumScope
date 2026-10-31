---
title: Energy levels and spectra
area: hydrogen
kind: lecture
order: 4
objectives: Compute hydrogen's energy levels | Predict the wavelengths of spectral lines | State the dipole selection rule
---
# Energy levels and spectra

## Energy levels

The energies depend only on $n$:

$$E_n = -\frac{\mu}{m_e}\,\frac{13.606\ \mathrm{eV}}{n^2} \approx -\frac{13.598\ \mathrm{eV}}{n^2}$$

| n | Energy |
|---|---|
| 1 | −13.598 eV |
| 2 | −3.400 eV |
| 3 | −1.511 eV |
| 4 | −0.850 eV |

The negative sign means the electron is bound; 13.598 eV is needed to ionize the atom from its ground state.

## Spectral lines

A jump from level $n_i$ to $n_f$ emits a photon of energy $E_{n_i} - E_{n_f}$ and wavelength $\lambda = hc/\Delta E$:

$$\frac{1}{\lambda} = R_\mu\left(\frac{1}{n_f^2} - \frac{1}{n_i^2}\right)$$

| Line | Transition | Energy | Wavelength (vacuum) |
|---|---|---|---|
| Lyman α | 2 → 1 | 10.199 eV | 121.6 nm (ultraviolet) |
| Lyman β | 3 → 1 | 12.087 eV | 102.6 nm |
| Balmer α | 3 → 2 | 1.889 eV | 656.5 nm (red) |

Measured in air, Balmer α is the familiar 656.3 nm red line.

## Selection rules

Light emitted or absorbed in a single photon (electric dipole) changes $\ell$ by exactly one: $\Delta\ell = \pm 1$. So 2p → 1s is allowed, but 2s → 1s is not; the 2s state is **metastable** and lives far longer.

## Check your understanding

```quiz
Q: How much energy ionizes hydrogen from n = 2?
- 13.6 eV
- 10.2 eV
* 3.4 eV
E: The ionization energy from level n is −Eₙ; for n = 2, that is 13.598/4 ≈ 3.4 eV.
```

```quiz
Q: Which transition is allowed for a single photon?
* 3p → 1s
- 3d → 1s
- 2s → 1s
E: Δℓ must be ±1: p (ℓ = 1) → s (ℓ = 0) is allowed; d → s (Δℓ = 2) and s → s (Δℓ = 0) are not.
```

## Summary

- Eₙ ≈ −13.598 eV / n² (with the reduced mass).
- Photon wavelengths follow the Rydberg formula; Lyman α is 121.6 nm, Balmer α 656.5 nm in vacuum.
- Single-photon transitions obey Δℓ = ±1.
