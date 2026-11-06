---
title: Outer products, projectors and density matrices
area: math
kind: lecture
order: 8
objectives: Build outer products and projectors | Compute a trace and the purity of a state | Use the partial trace to find one qubit's own state
---
# Outer products, projectors and density matrices

State vectors describe states we know exactly. To include uncertainty, noise, or one half of an entangled pair, quantum physics uses **density matrices**, built from outer products.

## Outer products and projectors

The inner product $\langle\varphi|\psi\rangle$ is a number. Reversed, the **outer product** $|\psi\rangle\langle\varphi|$ is a matrix: a column times a row.

$$|0\rangle\langle 0| = \begin{pmatrix} 1 \\ 0 \end{pmatrix}\begin{pmatrix} 1 & 0 \end{pmatrix} = \begin{pmatrix} 1 & 0 \\ 0 & 0 \end{pmatrix}$$

For a normalized state, $P = |\psi\rangle\langle\psi|$ is a **projector**: it keeps the part of a vector along $|\psi\rangle$ and removes the rest, so applying it twice changes nothing more, $P^2 = P$. Measurements are built from projectors: the probability of result $\psi$ is $\langle\varphi|P|\varphi\rangle$ for a state $|\varphi\rangle$.

## The trace

The **trace** of a square matrix is the sum of its diagonal:

$$\mathrm{Tr}\begin{pmatrix} a & b \\ c & d \end{pmatrix} = a + d$$

It does not depend on the basis, and $\mathrm{Tr}(AB) = \mathrm{Tr}(BA)$.

## Density matrices

A pure state $|\psi\rangle$ has the density matrix $\rho = |\psi\rangle\langle\psi|$. If a source prepares $|\psi_k\rangle$ with probability $p_k$, the density matrix is the mixture

$$\rho = \sum_k p_k\, |\psi_k\rangle\langle\psi_k|$$

Every density matrix is Hermitian, has trace 1, and has a diagonal that holds the measurement probabilities. Expectation values become $\langle A \rangle = \mathrm{Tr}(\rho A)$.

**Purity** tells pure states from mixtures:

$$\mathrm{Tr}(\rho^2) = 1 \text{ for a pure state}, \qquad \mathrm{Tr}(\rho^2) = \frac{1}{2} \text{ for a completely random qubit}$$

The completely random qubit is $\rho = \frac{1}{2} I$. On the Bloch sphere, pure states lie on the surface, mixtures inside, and $\frac{1}{2}I$ at the center.

## The partial trace: one qubit's own state

For two qubits, the state of the first qubit alone is found by the **partial trace** over the second, written $\rho_A = \mathrm{Tr}_B\,\rho$: sum over the second qubit's basis states. For the Bell state $\frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)$:

$$\rho_A = \frac{1}{2}|0\rangle\langle 0| + \frac{1}{2}|1\rangle\langle 1| = \frac{1}{2} I$$

The pair is in a definite pure state, yet each qubit on its own is **completely random**. That is why the Entanglement experiment shows "random" on both spheres.

[Try it: each half of a Bell pair is completely random](qs:open/entanglement)

## Check your understanding

```quiz
Q: What is the purity Tr(ρ²) of ρ = ½ I?
- 1
* ½
- 0
E: ρ² = ¼ I, whose trace is ¼ + ¼ = ½: the most mixed a qubit can be.
```

```quiz
Q: A pair is in a pure entangled state. What is each qubit's own state?
- Also pure
* Mixed: its partial trace has purity below 1
- Undefined
E: For an entangled pure pair, the partial trace gives a mixed state; for a Bell state, completely random.
```

## Summary

- $|\psi\rangle\langle\psi|$ is a projector: $P^2 = P$.
- Density matrices: Hermitian, trace 1; mixtures have purity $\mathrm{Tr}\,\rho^2 < 1$.
- The partial trace gives one part's own state; halves of a Bell pair are completely random.
