---
title: Single-qubit gates
area: circuits
kind: lecture
order: 2
objectives: Describe a gate as a unitary matrix | Use the Pauli, Hadamard and phase gates | Picture single-qubit gates as rotations of the Bloch sphere | Distinguish global from relative phase in practice
---
# Single-qubit gates

## Gates are unitary matrices

A quantum gate on one qubit is a $2\times 2$ **unitary** matrix $U$: it satisfies $U^\dagger U = I$, which guarantees that a normalized state stays normalized. Applying the gate means multiplying the state vector by $U$, and every gate can be undone by applying $U^\dagger$.

## The Pauli gates

$$X = \begin{pmatrix}0 & 1\\ 1 & 0\end{pmatrix}, \quad Y = \begin{pmatrix}0 & -i\\ i & 0\end{pmatrix}, \quad Z = \begin{pmatrix}1 & 0\\ 0 & -1\end{pmatrix}$$

- $X$ is the quantum NOT: $X|0\rangle = |1\rangle$ and $X|1\rangle = |0\rangle$.
- $Z$ leaves $|0\rangle$ alone and flips the sign of $|1\rangle$: a **phase flip**.
- $Y = iXZ$ does both.

Each Pauli gate is its own inverse: $X^2 = Y^2 = Z^2 = I$.

## The Hadamard gate

$$H = \frac{1}{\sqrt{2}}\begin{pmatrix}1 & 1\\ 1 & -1\end{pmatrix}$$

The Hadamard creates superpositions, $H|0\rangle = |+\rangle$ and $H|1\rangle = |-\rangle$, and is also its own inverse. A useful identity: $HZH = X$ and $HXH = Z$. The Gate Explorer's **Worked identity** tab follows each basis state through $H$, $Z$, $H$ step by step.

[Try it: open the Hadamard in the Gate Explorer](qs:gate/H)

## Phase gates

$$S = \begin{pmatrix}1 & 0\\ 0 & i\end{pmatrix}, \quad T = \begin{pmatrix}1 & 0\\ 0 & e^{i\pi/4}\end{pmatrix}, \quad P(\lambda) = \begin{pmatrix}1 & 0\\ 0 & e^{i\lambda}\end{pmatrix}$$

These change only the phase of $|1\rangle$, so $S^2 = Z$ and $T^2 = S$. On $|0\rangle$ or $|1\rangle$ alone their effect is a global phase and cannot be seen; on $|+\rangle$ the relative phase changes, which you can see as a rotation on the Bloch sphere.

[Try it: T acting on |+⟩](qs:circuit?n=1&gates=T:0&states=%2B&inspector=1)

## Gates as rotations

Every single-qubit state is a point on the **Bloch sphere**, and every single-qubit gate is a rotation of it (up to a global phase). The rotation gates make this explicit:

$$R_X(\theta) = e^{-i\theta X/2}, \quad R_Y(\theta) = e^{-i\theta Y/2}, \quad R_Z(\theta) = e^{-i\theta Z/2}$$

$R_Y(\theta)$ rotates by $\theta$ about the $y$ axis, so $R_Y(\pi/2)|0\rangle = |+\rangle$. Note the half angle in the exponent: a full turn, $R_Z(2\pi) = -I$, is the identity only up to a global phase. QuantumScope's **Tools → Simplify** removes such gates and says so.

[Try it: RY(π/2) on |0⟩](qs:circuit?n=1&gates=RY:0:pi/2&inspector=1)

## Check your understanding

```quiz
Q: What is HZH|0⟩?
- |0⟩
* |1⟩
- |+⟩
- −|0⟩
E: HZH = X, so HZH|0⟩ = X|0⟩ = |1⟩. Step by step: |0⟩ → |+⟩ → |−⟩ → |1⟩.
```

```quiz
Q: The S gate is applied to |0⟩. Which statement is true?
* Nothing observable changes: S|0⟩ = |0⟩.
- The qubit is now measured as 1 with probability ½.
- The qubit acquires a relative phase of i.
- The state becomes −|0⟩.
E: S multiplies only the |1⟩ amplitude by i; with no |1⟩ component, |0⟩ is unchanged. Start from |+⟩ to see S act.
```

```quiz
Q: Which of these gates is NOT its own inverse?
- X
- H
- Z
* S
E: S² = Z, not I. The inverse of S is S† (shown as SDG), with i replaced by −i.
```

## Summary

- Gates are unitary matrices; every gate can be undone.
- X flips bits, Z flips phases, H creates and removes superpositions; S, T and P adjust the relative phase.
- Single-qubit gates are rotations of the Bloch sphere; rotation gates use half angles, so a 2π turn gives −I.
