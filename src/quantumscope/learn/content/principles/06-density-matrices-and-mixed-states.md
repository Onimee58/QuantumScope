---
title: Density matrices and mixed states
area: principles
kind: lecture
order: 6
objectives: Write the density matrix of a pure state and of a mixture | Read probabilities and coherences from ρ | Use purity and the Bloch ball to tell pure from mixed states
---
# Density matrices and mixed states

## When a state vector is not enough

A state vector $|\psi\rangle$ describes a system we know completely. Often we do not: a qubit may have been prepared in one of several states at random, or it may be entangled with something we cannot see, or noise may have disturbed it. All of these are described by a **density matrix** $\rho$.

## Pure states and mixtures

For a pure state, $\rho = |\psi\rangle\langle\psi|$. If the system is in state $|\psi_i\rangle$ with probability $p_i$, then

$$\rho = \sum_i p_i\,|\psi_i\rangle\langle\psi_i|$$

Every density matrix is Hermitian, has trace 1, and has no negative eigenvalues.

## Reading a density matrix

$$\rho = \begin{pmatrix}\rho_{00} & \rho_{01}\\ \rho_{10} & \rho_{11}\end{pmatrix}$$

- The **diagonal** entries are probabilities: $P(0) = \rho_{00}$ and $P(1) = \rho_{11}$.
- The **off-diagonal** entries are **coherences**: they record the phase relationship that makes interference possible.

For $|+\rangle$, every entry is $\frac{1}{2}$. For a coin toss between $|0\rangle$ and $|1\rangle$, the diagonal is the same but the coherences are 0 — and that is the whole difference between a superposition and ignorance.

## Purity

$$\mathrm{Tr}(\rho^2) = 1 \text{ for a pure state}, \qquad \mathrm{Tr}(\rho^2) = \frac{1}{d} \text{ for the maximally mixed state } \frac{I}{d}$$

so purity measures how much is still known about the state.

## The Bloch ball

Every single-qubit density matrix can be written with a Bloch vector $\vec r$:

$$\rho = \frac{1}{2}\left(I + r_x X + r_y Y + r_z Z\right), \qquad |\vec r| \leq 1$$

Pure states lie on the surface ($|\vec r| = 1$); mixed states fill the inside. The purity is $\frac{1}{2}(1 + |\vec r|^2)$. This is why QuantumScope's Bloch arrows shrink when noise is on.

## Two routes to the same mixed state

A 50:50 mixture of $|0\rangle$ and $|1\rangle$ and a 50:50 mixture of $|+\rangle$ and $|-\rangle$ have the same density matrix, $I/2$. No measurement can tell them apart: $\rho$ contains everything that can be observed. The same $I/2$ is also what one qubit of a Bell pair looks like on its own.

[Try it: one qubit of a Bell pair](qs:circuit?n=2&gates=H:0;CX:0,1&inspector=1)

[Try it: a Bell pair with noise](qs:circuit?n=2&gates=H:0;CX:0,1&noise=Moderate&inspector=1)

## Check your understanding

```quiz
Q: A qubit has ρ with diagonal (0.7, 0.3) and off-diagonal entries 0. What is it?
- The pure state √0.7|0⟩ + √0.3|1⟩
* A mixture: |0⟩ with probability 0.7 and |1⟩ with probability 0.3
- The maximally mixed state
E: Zero coherences means no superposition; the diagonal gives the probabilities. The pure state would have off-diagonal entries √0.21 ≈ 0.46.
```

```quiz
Q: What is the purity of the maximally mixed state of one qubit?
- 0
* 1/2
- 1
E: Tr((I/2)²) = Tr(I/4) = 1/2, which is 1/d for d = 2.
```

## Summary

- A density matrix describes pure states, mixtures and parts of entangled systems.
- Diagonal entries are probabilities; off-diagonal entries are coherences.
- Purity Tr(ρ²) runs from 1 (pure) to 1/d (maximally mixed); single-qubit states fill the Bloch ball.
