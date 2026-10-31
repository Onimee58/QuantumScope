---
title: The Schrödinger equation and the hydrogen atom
area: hydrogen
kind: lecture
order: 1
objectives: Write the time-independent Schrödinger equation for hydrogen | Explain the reduced mass and the length unit a_μ | Separate the wavefunction into radial and angular parts
---
# The Schrödinger equation and the hydrogen atom

## The equation

An electron bound to a proton by the Coulomb force obeys the time-independent Schrödinger equation

$$-\frac{\hbar^2}{2\mu}\nabla^2\psi - \frac{e^2}{4\pi\varepsilon_0 r}\psi = E\psi$$

Its solutions $\psi$ are the stationary states (**orbitals**) and $E$ their energies. Hydrogen is one of very few atoms for which this equation can be solved exactly.

## The reduced mass

The proton is not infinitely heavy: electron and proton both move around their common center of mass. This is handled exactly by replacing the electron mass with the **reduced mass**

$$\mu = \frac{m_e m_p}{m_e + m_p} \approx 0.99946\, m_e$$

QuantumScope uses $\mu$ throughout. Lengths are measured in the reduced-mass Bohr radius $a_\mu = a_0\, m_e/\mu \approx 52.95$ pm, slightly larger than the textbook $a_0 \approx 52.92$ pm, and energies come out about 0.05% smaller in magnitude than with an infinitely heavy proton.

## Separation of variables

Because the force depends only on distance, the solutions factor into a radial and an angular part:

$$\psi_{n\ell m}(r,\theta,\varphi) = R_{n\ell}(r)\,Y_{\ell m}(\theta,\varphi)$$

The **spherical harmonics** $Y_{\ell m}$ set the shape; the radial functions $R_{n\ell}$ set the size and the radial nodes. The three integers $n$, $\ell$, $m$ are the subject of the next lecture.

[Try it: the Hydrogen Explorer](qs:open/orbital)

## Check your understanding

```quiz
Q: Why does QuantumScope use the reduced mass μ instead of the electron mass?
* Because the proton also moves, about the common center of mass
- Because the electron is relativistic
- To make the equations simpler
E: Replacing m_e by μ accounts exactly for the motion of both particles in a two-body problem.
```

```quiz
Q: What determines the shape of an orbital?
- The radial function R(r)
* The spherical harmonic Y(θ, φ)
- The energy E
E: Y sets the angular dependence (s, p, d …); R sets size and radial nodes.
```

## Summary

- Hydrogen's stationary states solve −(ħ²/2μ)∇²ψ − e²/(4πε₀r)ψ = Eψ.
- The reduced mass μ ≈ 0.99946 mₑ makes the two-body problem exact; lengths use a_μ ≈ 52.95 pm.
- ψ = R(r) Y(θ, φ): size from R, shape from Y.
