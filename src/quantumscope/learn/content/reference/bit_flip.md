---
title: Bit flip
---
# Bit flip

With probability $p$ the qubit is flipped by $X$; otherwise it is left alone:

$$\rho \rightarrow (1-p)\,\rho + p\,X\rho X$$

## Kraus operators

$$K_0 = \sqrt{1-p}\,I, \quad K_1 = \sqrt{p}\,X$$

## Effect on the Bloch sphere

The $x$ component is untouched; $y$ and $z$ shrink:

$$(x,\ y,\ z) \rightarrow (x,\ (1-2p)\,y,\ (1-2p)\,z)$$

States along the $x$ axis, $|+\rangle$ and $|-\rangle$, are immune, because $X$ leaves them unchanged (up to a sign). At $p = \frac{1}{2}$ every state is squeezed onto the $x$ axis.

## Where it comes from

Bit flips are the quantum version of the errors classical memory suffers. Real hardware rarely produces pure bit flips, but they are the starting point for error correction: the three-qubit repetition code protects against exactly this channel.
