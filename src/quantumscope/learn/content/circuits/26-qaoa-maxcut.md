---
title: QAOA and MaxCut
area: circuits
kind: lecture
order: 26
objectives: State the MaxCut problem as an energy | Build a QAOA circuit from cost and mixer layers | Interpret approximation ratios and the effect of symmetry
math: 10-pauli-algebra, 12-gradients-and-optimization
---
# QAOA and MaxCut

## MaxCut

Colour each node of a graph 0 or 1. An edge is **cut** when its ends differ. **MaxCut** asks for the colouring with the most cut edges — a hard problem in general. As an energy, with one qubit per node,

$$H = \sum_{(i,j)\,\in\,\text{edges}} \frac{1}{2}\left(Z_i Z_j - 1\right)$$

counts minus the cut edges, so its minimum is minus the maximum cut.

## The QAOA circuit

The **Quantum Approximate Optimization Algorithm** (Farhi, Goldstone and Gutmann, 2014) alternates two steps, $p$ times:

1. **Cost** $e^{-i\gamma H}$: for every edge, CX, RZ(−γ), CX.
2. **Mixer** $e^{-i\beta \sum X}$: RX(2β) on every node.

It starts from H on every qubit (all colourings equally likely) and optimizes the $2p$ angles γ and β.

[Try it: QAOA on a square — Optimize, then Show the graph](qs:algorithm/qaoa?graph=ring4&layers=1)

## How good is it?

The **approximation ratio** is the expected cut divided by the maximum cut. On rings with an even number of nodes, one layer reaches exactly **3/4**. With two layers the hexagon reaches **5/6**, while the square — small enough for two layers to cover it — is solved outright: the maximum cut is found with certainty. More layers help, at the cost of more parameters.

## Symmetry

QAOA treats equivalent nodes and edges alike. On the pentagon all five edges are equivalent, so ⟨Z₀Z₁⟩ equals the average over the edges. The best cut leaves 1 of the 5 edges uncut, so that average is at least

$$\frac{1 - 4}{5} = -0.6$$

even though the observable Z₀Z₁ alone could reach −1. The circuit's structure limits the states it can make.

## Check your understanding

```quiz
Q: What does one QAOA layer contain?
- Only CX gates
* A cost step on every edge and a mixer RX(2β) on every node
- A measurement of every qubit
E: Each layer applies the cost Hamiltonian (angle γ) and the mixer (angle β).
```

```quiz
Q: For an even ring with one layer, what approximation ratio does QAOA reach?
- 1/2
* 3/4
- 1
E: The known result for rings at p = 1 is 3/4.
```

## Summary

- MaxCut becomes an energy: minus the number of cut edges.
- QAOA alternates cost and mixer layers and optimizes γ and β.
- Even rings: 3/4 at one layer; the hexagon 5/6 at two; symmetry limits what QAOA can reach.
