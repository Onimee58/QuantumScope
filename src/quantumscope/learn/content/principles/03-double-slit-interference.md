---
title: "Interference: the double slit"
area: principles
kind: lecture
order: 3
objectives: Explain interference as adding amplitudes, not probabilities | Predict the fringe spacing | Explain why which-path information destroys interference
---
# Interference: the double slit

## Adding amplitudes

A particle passing a screen with two slits reaches a point $y$ on the detector by two paths with amplitudes $\psi_1(y)$ and $\psi_2(y)$. Quantum mechanics adds the **amplitudes**, then squares:

$$P(y) = |\psi_1(y) + \psi_2(y)|^2 = |\psi_1|^2 + |\psi_2|^2 + 2\,\mathrm{Re}\,(\psi_1^*\psi_2)$$

The last term is **interference**: it can be positive (bright fringes) or negative (dark fringes), so at some points adding a second slit *reduces* the chance of arrival.

## Fringe spacing

For slits a distance $d$ apart, a screen at distance $L$ and wavelength $\lambda$ (for particles, the de Broglie wavelength $h/p$), the path difference sets the phase, and the bright fringes are separated by

$$\Delta y = \frac{\lambda L}{d}$$

Each slit's finite width adds a broad diffraction envelope that modulates the fringes. QuantumScope's double-slit view keeps the two apart: the ideal two-path pattern and the full diffraction pattern.

[Try it: the double-slit experiment](qs:open/doubleslit)

## Which-path information

If anything records which slit the particle used, the two paths become distinguishable and the cross term vanishes: the pattern becomes the plain sum of two single-slit patterns. Interference needs the paths to be indistinguishable.

## The same physics in a circuit

A Mach–Zehnder interferometer is two Hadamards: $H\,H|0\rangle = |0\rangle$ because the two paths to $|1\rangle$ cancel. A phase on one path, $P(\varphi)$ between the Hadamards, moves the fringe: $P(1) = \sin^2(\varphi/2)$.

[Try it: H, phase π, H](qs:circuit?n=1&gates=H:0;P:0:pi;H:0&inspector=1)

## Check your understanding

```quiz
Q: The slit separation d is doubled. What happens to the fringe spacing?
- It doubles
* It halves
- It stays the same
E: Δy = λL/d, so doubling d halves Δy.
```

```quiz
Q: A detector records which slit each particle uses. What do you see?
- The same fringes, dimmer
* No interference fringes, just the sum of two single-slit patterns
- Fringes twice as fine
E: Which-path information makes the paths distinguishable and removes the interference term.
```

## Summary

- Interference comes from adding amplitudes before squaring.
- Bright fringes are λL/d apart; slit width adds a diffraction envelope.
- Which-path information removes the interference term.
