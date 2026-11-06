---
title: Vectors and Dirac notation
area: math
kind: lecture
order: 2
objectives: Write qubit states as column vectors and kets | Normalize a state | Compute inner products and recognize orthogonal states
---
# Vectors and Dirac notation

A qubit's state is a **vector** of two complex amplitudes. Physicists write such vectors in **Dirac notation**: compact, and the same for one qubit or ten.

## States as column vectors

The two basis states of a qubit are

$$|0\rangle = \begin{pmatrix} 1 \\ 0 \end{pmatrix}, \qquad |1\rangle = \begin{pmatrix} 0 \\ 1 \end{pmatrix}$$

Every state is a combination of them:

$$|\psi\rangle = \alpha|0\rangle + \beta|1\rangle = \begin{pmatrix} \alpha \\ \beta \end{pmatrix}$$

The symbol $|\psi\rangle$ is called a **ket**. It is just a name for a column vector.

## Normalization

The amplitudes give probabilities $|\alpha|^2$ and $|\beta|^2$, which must add up to 1:

$$|\alpha|^2 + |\beta|^2 = 1$$

A vector with this property is **normalized**. To normalize any nonzero vector, divide it by its length. For example $|0\rangle + |1\rangle$ has length $\sqrt{2}$, so the normalized state is

$$|+\rangle = \frac{1}{\sqrt{2}}\left(|0\rangle + |1\rangle\right)$$

## Bras and inner products

The **bra** $\langle\psi|$ is the conjugate transpose of the ket: a row vector with conjugated entries.

$$\langle\psi| = \begin{pmatrix} \bar{\alpha} & \bar{\beta} \end{pmatrix}$$

Putting a bra and a ket together gives the **inner product**, a single complex number:

$$\langle\varphi|\psi\rangle = \bar{\gamma}\,\alpha + \bar{\delta}\,\beta \qquad \text{for } |\varphi\rangle = \gamma|0\rangle + \delta|1\rangle$$

It measures how much two states overlap:

- $\langle\psi|\psi\rangle = |\alpha|^2 + |\beta|^2 = 1$ for a normalized state.
- $\langle 0|1\rangle = 0$: the two states are **orthogonal**, completely distinguishable.
- $|\langle\varphi|\psi\rangle|^2$ is the probability of finding $|\varphi\rangle$ when the system is in $|\psi\rangle$. This is the **fidelity** between two pure states.

For example $\langle 0|+\rangle = \frac{1}{\sqrt{2}}$, so a $|+\rangle$ qubit is found in $|0\rangle$ with probability $\frac{1}{2}$.

## Bases

Two orthogonal, normalized states form a **basis**: every state can be written as a combination of them. Besides $|0\rangle, |1\rangle$, the most useful basis is

$$|\pm\rangle = \frac{1}{\sqrt{2}}\left(|0\rangle \pm |1\rangle\right)$$

Measuring "along $x$" means measuring in this basis.

[Try it: inspect amplitudes and probabilities in the State Inspector (a |+⟩ qubit)](qs:circuit?n=1&gates=H:0)

## Check your understanding

```quiz
Q: Which vector is normalized?
- (1, 1)
* (0.6, 0.8i)
- (0.5, 0.5)
E: |0.6|² + |0.8i|² = 0.36 + 0.64 = 1. The others give 2 and 0.5.
```

```quiz
Q: What is ⟨+|−⟩?
* 0
- 1
- 1/2
E: ⟨+|−⟩ = ½(1·1 + 1·(−1)) = 0: |+⟩ and |−⟩ are orthogonal, so they form a basis.
```

## Summary

- A ket $|\psi\rangle$ is a column vector of amplitudes; its bra $\langle\psi|$ is the conjugate row vector.
- States are normalized: the squared amplitudes add up to 1.
- $\langle\varphi|\psi\rangle$ measures overlap; $|\langle\varphi|\psi\rangle|^2$ is a probability, and 0 means orthogonal.
