---
title: Parameterized circuits
area: circuits
kind: lecture
order: 22
objectives: Build a circuit whose gate angles are parameters | Share one parameter among several gates | Explore how an expectation value depends on the parameters
math: 09-matrix-exponentials
---
# Parameterized circuits

## Angles as knobs

A **parameterized circuit** has gate angles that are not fixed numbers but parameters $\theta_0, \theta_1, \dots$ Changing a parameter changes the state the circuit prepares, and with it every expectation value. Variational algorithms (VQE, QAOA) and quantum machine learning are all built on such circuits.

## In QuantumScope

- Double-click a rotation gate (RX, RY, RZ, P, CP or U) and type a **parameter name** as its angle: `a`, or a Greek letter written as in LaTeX, `\theta` for θ.
- A **factor** ties several gates to one parameter: typing `2*\theta` makes that angle twice θ. The gate shows its parameter under its name.
- The **Parameters** panel has a slider for each parameter, and an **observable** whose ⟨O⟩ updates as you move the sliders.

[Try it: one parameter, one observable](qs:circuit?n=1&gates=RY:0:0.4&bind=0:0:%5Ctheta&observable=Z0)

For $R_Y(\theta)|0\rangle$, the expectation value is

$$\langle Z \rangle = \cos\theta$$

so it moves from +1 at θ = 0 to −1 at θ = π.

## Why share parameters

Sharing a parameter encodes structure: in QAOA every edge of a graph uses the same angle γ, and every node the same β. Fewer parameters are easier to optimize, and the structure can reflect symmetries of the problem.

## Check your understanding

```quiz
Q: A gate's angle is bound as 2·θ. θ is set to 0.3. What is the angle?
- 0.3
* 0.6
- 2.3
E: The angle is the factor times the parameter: 2 × 0.3 = 0.6.
```

```quiz
Q: What is ⟨Z⟩ for RY(θ)|0⟩ at θ = π/2?
* 0
- 1
- −1
E: cos(π/2) = 0: the state is |+⟩, equally likely to give +1 or −1.
```

## Summary

- Parameters turn gate angles into knobs; one parameter can drive several gates with factors.
- ⟨O⟩ is a function of the parameters — the landscape that variational algorithms explore.
