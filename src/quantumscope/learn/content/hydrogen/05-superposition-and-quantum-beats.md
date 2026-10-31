---
title: Superposition and quantum beats
area: hydrogen
kind: lecture
order: 5
objectives: Explain why stationary states have time-independent densities | Compute the beat period of a two-state superposition | Interpret the Hydrogen Dynamics views correctly
---
# Superposition and quantum beats

## Stationary states

A single energy eigenstate evolves as $\psi(t) = \psi\,e^{-iEt/\hbar}$. The phase factor has magnitude one, so $|\psi(t)|^2$ never changes: that is why eigenstates are called **stationary**.

## Two states at once

A superposition of two levels,

$$\Psi(t) = \sqrt{p}\,\psi_a e^{-iE_a t/\hbar} + \sqrt{1-p}\,\psi_b e^{-iE_b t/\hbar}$$

has a density with a cross term oscillating at the energy difference. It repeats with the **beat period**

$$T = \frac{h}{|E_a - E_b|}$$

| States | Beat period |
|---|---|
| 1s + 2p | 0.4055 fs |
| 1s + 3d | 0.3421 fs |
| 2s + 2p | none (same energy: stationary) |

For 1s + 2p the cloud sloshes from one side of the nucleus to the other. A charge doing this radiates, which is how such a state emits light — but the 2p lifetime is about 1.6 ns, millions of beat periods, so the Dynamics views show the beating without the slow decay.

[Try it: Hydrogen Dynamics 3D](qs:open/dynamics3d)

## What the animation is — and is not

The animation shows the exact time-dependent probability density. It is **not** a trajectory: the electron is not a particle moving along a path inside the cloud. Only the density changes, and only because of the interference between the two states.

[Try it: Hydrogen Dynamics 2D](qs:open/dynamics2d)

## Check your understanding

```quiz
Q: Why does a 2s + 2p superposition not beat in this model?
* The two states have the same energy
- 2s is spherically symmetric
- The superposition is not normalized
E: T = h/|E_a − E_b| is infinite when the energies are equal, so the density stays constant.
```

```quiz
Q: What does the animated cloud represent?
- The electron's path around the nucleus
* How the probability density changes in time
- The shape of the emitted light
E: Quantum mechanics gives a probability density, not a trajectory.
```

## Summary

- Eigenstates have constant densities; superpositions of different energies beat.
- The beat period is h/|E_a − E_b|: 0.4055 fs for 1s + 2p.
- The animation shows probability density, not motion along a path.
