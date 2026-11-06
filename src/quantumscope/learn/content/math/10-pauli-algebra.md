---
title: Pauli algebra
area: math
kind: lecture
order: 10
objectives: Multiply Pauli matrices and use XY = iZ | Use commutators and anticommutators | Read observables as sums of Pauli strings
---
# Pauli algebra

The Pauli matrices are the alphabet of quantum computing: gates, errors, observables and stabilizers are all written with them.

## The three matrices

$$X = \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}, \qquad Y = \begin{pmatrix} 0 & -i \\ i & 0 \end{pmatrix}, \qquad Z = \begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}$$

Each is Hermitian and unitary, squares to the identity, and has eigenvalues $+1$ and $-1$.

## Multiplying them

Products of two different Paulis give the third, with a factor $\pm i$:

$$XY = iZ, \qquad YZ = iX, \qquad ZX = iY$$

and in the opposite order the sign flips: $YX = -iZ$. A memory aid: going around $X \to Y \to Z \to X$ gives $+i$, going backwards gives $-i$.

## Commutators and anticommutators

The **commutator** measures how much two matrices fail to commute:

$$[A, B] = AB - BA$$

For Paulis, $[X, Y] = 2iZ$, while the **anticommutator** $\{X, Y\} = XY + YX = 0$: two different Paulis anticommute. Matrices that commute can be measured together with definite results; $X$ and $Z$ cannot, which is the uncertainty principle for a qubit.

## Pauli strings

For several qubits, a **Pauli string** is a tensor product of Paulis, written compactly with qubit labels: $Z_0 Z_1$ means $Z \otimes Z$, and $X_0$ alone means $X \otimes I$. Two strings commute exactly when they **differ** (both non-identity, different letters) on an **even** number of qubits. So $X_0 X_1$ and $Z_0 Z_1$ commute, even though $X$ and $Z$ do not: the two sign flips cancel.

Every Hermitian matrix on $n$ qubits is a real-weighted sum of Pauli strings. That is how QuantumScope writes observables and Hamiltonians, for example

$$H = Z_0 Z_1 + 0.5\, X_0$$

and how error-correcting codes describe their stabilizers, such as $Z_0 Z_1$ and $Z_1 Z_2$ for the bit-flip code.

[Try it: the observable Z0 Z1 on a Bell pair](qs:circuit?n=2&gates=H:0;CX:0,1&observable=Z0%20Z1)

## Check your understanding

```quiz
Q: What is ZX?
- −iY
* iY
- X
E: Going around X → Y → Z → X: ZX = iY (and XZ = −iY).
```

```quiz
Q: Do Z0 Z1 and X0 X1 commute?
* Yes: they differ on two qubits, an even number
- No: X and Z anticommute
E: Each qubit contributes a sign flip; two flips cancel, so the strings commute.
```

## Summary

- $X, Y, Z$: Hermitian, unitary, square to $I$; $XY = iZ$ and cyclic, reversed order gives $-i$.
- Different Paulis anticommute; strings commute when they differ on an even number of qubits.
- Observables, Hamiltonians and stabilizers are weighted sums of Pauli strings.
