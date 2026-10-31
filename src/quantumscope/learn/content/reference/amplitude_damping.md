---
title: Amplitude damping
---
# Amplitude damping

An excited qubit loses its energy: $|1\rangle$ decays to $|0\rangle$ with probability $\gamma$.

## Kraus operators

$$K_0 = \begin{pmatrix}1 & 0\\ 0 & \sqrt{1-\gamma}\end{pmatrix}, \quad K_1 = \begin{pmatrix}0 & \sqrt{\gamma}\\ 0 & 0\end{pmatrix}$$

$K_1$ is the decay $|1\rangle \rightarrow |0\rangle$; $K_0$ describes what happens when no decay occurs.

## Effect on the Bloch sphere

$$(x,\ y,\ z) \rightarrow \left(\sqrt{1-\gamma}\,x,\ \sqrt{1-\gamma}\,y,\ \gamma + (1-\gamma)\,z\right)$$

Unlike the other channels, this one does not shrink towards the center: every state is pulled towards the north pole $|0\rangle$, which is a fixed point. Repeated damping gives exponential decay, $P(1) \propto (1-\gamma)^k$.

## Where it comes from

This is spontaneous emission and energy relaxation. Its time scale is the qubit's **T₁** time; over a time $t$, $\gamma = 1 - e^{-t/T_1}$.
