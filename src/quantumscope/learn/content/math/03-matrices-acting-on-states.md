---
title: Matrices acting on states
area: math
kind: lecture
order: 3
objectives: Multiply a matrix by a vector and by another matrix | Write X, Z and H as matrices | Explain why the order of gates matters
---
# Matrices acting on states

Every quantum gate is a **matrix**, and applying a gate means multiplying the state vector by it.

## Matrix times vector

A 2 × 2 matrix acts on a vector row by row:

$$\begin{pmatrix} a & b \\ c & d \end{pmatrix}\begin{pmatrix} \alpha \\ \beta \end{pmatrix} = \begin{pmatrix} a\alpha + b\beta \\ c\alpha + d\beta \end{pmatrix}$$

Each entry of the result is a row of the matrix multiplied entry by entry with the vector, then added up.

## Three gates as matrices

$$X = \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}, \qquad Z = \begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}, \qquad H = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}$$

- $X$ swaps the amplitudes: $X|0\rangle = |1\rangle$. It is the quantum NOT.
- $Z$ changes the sign of the $|1\rangle$ amplitude: a phase flip.
- $H$ makes superpositions: $H|0\rangle = |+\rangle$ and $H|1\rangle = |-\rangle$.

Worked example:

$$H|0\rangle = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}\begin{pmatrix} 1 \\ 0 \end{pmatrix} = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 \\ 1 \end{pmatrix} = |+\rangle$$

## Matrix times matrix

Applying gate $A$ and then gate $B$ gives $B(A|\psi\rangle) = (BA)|\psi\rangle$. The product $BA$ is a single matrix that does both. Its entries are rows of $B$ times columns of $A$.

The **identity** $I = \begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix}$ leaves every vector unchanged.

## Order matters: right to left

In a circuit, time runs **left to right**. In the matrix product, the first gate stands **on the right**, closest to the state. A circuit "$A$ then $B$" is the matrix $BA$.

Matrix products usually depend on the order. For example

$$XZ = \begin{pmatrix} 0 & -1 \\ 1 & 0 \end{pmatrix} \neq ZX = \begin{pmatrix} 0 & 1 \\ -1 & 0 \end{pmatrix}$$

so "Z then X" and "X then Z" are different gates; here they differ only by a sign, $XZ = -ZX$.

[Try it: H twice is the identity (the qubit returns to |0⟩)](qs:circuit?n=1&gates=H:0;H:0)

## Check your understanding

```quiz
Q: What is Z|+⟩?
* |−⟩
- |+⟩
- |1⟩
E: Z changes the sign of the |1⟩ amplitude: Z·(1, 1)/√2 = (1, −1)/√2 = |−⟩.
```

```quiz
Q: A circuit applies H, then X. Which matrix describes it?
- HX
* XH
- H + X
E: The first gate acts first, so it stands on the right, next to the state: X(H|ψ⟩) = (XH)|ψ⟩.
```

## Summary

- A gate is a matrix; applying it multiplies the state vector.
- Circuits read left to right, products right to left: "A then B" is $BA$.
- Matrix products depend on the order: $XZ \neq ZX$.
