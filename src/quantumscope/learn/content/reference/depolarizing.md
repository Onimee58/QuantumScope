---
title: Depolarizing
---
# Depolarizing

With probability $p$ the qubit's state is replaced by the maximally mixed state $I/2$:

$$\rho \rightarrow (1-p)\,\rho + p\,\frac{I}{2}$$

## Kraus operators

The same channel applies $X$, $Y$ or $Z$ with probability $p/4$ each:

$$K_0 = \sqrt{1-\frac{3p}{4}}\,I, \quad K_{1,2,3} = \frac{\sqrt{p}}{2}\,X,\ Y,\ Z$$

## Effect on the Bloch sphere

Every direction shrinks equally:

$$(x,\ y,\ z) \rightarrow (1-p)\,(x,\ y,\ z)$$

The Bloch vector keeps its direction and loses length. The purity becomes $\frac{1}{2}\left(1 + (1-p)^2|\vec r|^2\right)$.

## Where it comes from

Depolarizing noise treats all errors alike, so it is the usual summary of an imperfect gate: QuantumScope's global noise applies it after every gate. On two qubits, the same idea replaces the pair's state by $I/4$ with probability $p$.
