---
title: Superposition and the Bloch sphere
area: principles
kind: lecture
order: 1
objectives: Write any single-qubit pure state with two angles | Locate states on the Bloch sphere | Connect a spin-½ particle with a qubit
---
# Superposition and the Bloch sphere

## Two angles describe every pure state

Up to an unobservable global phase, every pure state of a two-level system can be written as

$$|\psi\rangle = \cos\frac{\theta}{2}|0\rangle + e^{i\varphi}\sin\frac{\theta}{2}|1\rangle$$

with $0 \leq \theta \leq \pi$ and $0 \leq \varphi < 2\pi$. These are the polar and azimuthal angles of a point on a sphere: the **Bloch sphere**. Its north pole is $|0\rangle$, its south pole $|1\rangle$, and the equator holds the equal superpositions such as $|+\rangle$ and $|+i\rangle$.

## The Bloch vector

The point's coordinates are the expectation values of the three Pauli operators:

$$\vec r = (\langle X\rangle, \langle Y\rangle, \langle Z\rangle) = (\sin\theta\cos\varphi,\ \sin\theta\sin\varphi,\ \cos\theta)$$

Pure states lie on the surface ($|\vec r| = 1$). Mixed states, such as one qubit of an entangled pair, lie inside; the maximally mixed state is the center.

[Try it: explore the Bloch sphere](qs:open/superposition)

## Spin-½

An electron's spin is a physical two-level system: "up" and "down" along any chosen axis. Spin up along $z$ corresponds to $|0\rangle$; spin up along $x$ corresponds to $|+\rangle$. The Bloch vector points along the direction in which the spin is definitely "up".

## Superposition is not ignorance

$|+\rangle$ is not "secretly 0 or secretly 1". A coin that is secretly heads or tails would give random results along *every* axis, but $|+\rangle$ gives a definite result when measured along $x$. Superposition is a definite state pointing in a different direction.

[Try it: a custom state on the Bloch sphere](qs:circuit?n=1&gates=RY:0:pi/3;RZ:0:pi/4&inspector=1)

## Check your understanding

```quiz
Q: Where on the Bloch sphere is |−i⟩ = (|0⟩ − i|1⟩)/√2?
- North pole
- On the equator, along +y
* On the equator, along −y
- At the center
E: θ = π/2 (equal weights) and φ = 3π/2 (the factor −i), which points along −y.
```

```quiz
Q: A qubit's Bloch vector has length 0.6. What can you say?
- It is a pure state
* It is mixed, for example entangled with something else
- It has been measured
E: Pure states lie on the surface (length 1); shorter vectors are mixed states.
```

## Summary

- Two angles θ, φ describe every pure qubit state: a point on the Bloch sphere.
- The Bloch vector is (⟨X⟩, ⟨Y⟩, ⟨Z⟩); mixed states lie inside the sphere.
- A spin-½ particle is a physical qubit; superposition is a definite state, not hidden ignorance.
