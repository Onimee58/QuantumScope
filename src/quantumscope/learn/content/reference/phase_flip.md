---
title: Phase flip
---
# Phase flip

With probability $p$ the qubit's phase is flipped by $Z$:

$$\rho \rightarrow (1-p)\,\rho + p\,Z\rho Z$$

## Kraus operators

$$K_0 = \sqrt{1-p}\,I, \quad K_1 = \sqrt{p}\,Z$$

## Effect on the Bloch sphere

$$(x,\ y,\ z) \rightarrow ((1-2p)\,x,\ (1-2p)\,y,\ z)$$

The probabilities of $|0\rangle$ and $|1\rangle$ never change, but the off-diagonal terms of $\rho$ — the **coherences** that make interference possible — shrink by $1-2p$. At $p = \frac{1}{2}$ the state $|+\rangle$ becomes the maximally mixed state: indistinguishable from a coin toss.

## Where it comes from

A phase flip has no classical counterpart. It is the simplest model of **dephasing**, the loss of phase information caused by fluctuating fields, and is usually the dominant error in real qubits.
