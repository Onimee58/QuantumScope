---
title: The discrete Fourier transform
area: math
kind: lecture
order: 11
objectives: Work with roots of unity | Write the DFT matrix for small sizes | Explain why the quantum Fourier transform is unitary
---
# The discrete Fourier transform

The **quantum Fourier transform** at the heart of phase estimation and Shor's algorithm is the ordinary discrete Fourier transform, applied to amplitudes.

## Roots of unity

The $N$-th **roots of unity** are the $N$ complex numbers with $\omega^N = 1$. They are evenly spaced around the unit circle:

$$\omega = e^{2\pi i/N}, \qquad 1, \omega, \omega^2, \dots, \omega^{N-1}$$

For $N = 4$: $1, i, -1, -i$. Added together, the roots of unity always give 0: they cancel around the circle. This cancellation is what makes the transform work.

## The DFT matrix

The discrete Fourier transform of size $N$ is the $N \times N$ matrix with entries

$$F_{jk} = \frac{1}{\sqrt{N}}\, \omega^{jk} \qquad (j, k = 0, \dots, N-1)$$

For $N = 2$, $\omega = -1$ and $F$ is exactly the Hadamard gate $H$. For $N = 4$:

$$F = \frac{1}{2}\begin{pmatrix} 1 & 1 & 1 & 1 \\ 1 & i & -1 & -i \\ 1 & -1 & 1 & -1 \\ 1 & -i & -1 & i \end{pmatrix}$$

## Why it is unitary

Two different columns $k$ and $l$ of $F$ have inner product

$$\frac{1}{N}\sum_{j=0}^{N-1} \omega^{j(l - k)} = 0$$

because the terms are roots of unity that cancel. Each column has length 1, so the columns are orthonormal and $F^\dagger F = I$: the Fourier transform is a valid quantum gate. Its inverse $F^\dagger$ simply uses $\omega^{-jk}$.

## What it does

The DFT turns a **phase that grows step by step** into a **single peak**. The state

$$\frac{1}{\sqrt{N}}\sum_{j} e^{2\pi i\, j\varphi}\, |j\rangle$$

is turned by $F^\dagger$ into a state concentrated on $|k\rangle$ with $k/N \approx \varphi$. Phase estimation prepares exactly this state with **phase kickback**, then reads $\varphi$ off as a binary number. On $n$ qubits, $N = 2^n$, and the quantum circuit needs only about $n^2$ gates, far fewer than the $N^2 = 4^n$ entries of the matrix.

[Try it: phase estimation reads φ = 3/8 exactly with 3 counting qubits](qs:algorithm/qpe?t=3&phase=3/8)

## Check your understanding

```quiz
Q: What are the 4th roots of unity?
* 1, i, −1, −i
- 1, 2, 3, 4
- 0, 1, 2, 3
E: e^{2πik/4} for k = 0…3: the points 1, i, −1, −i on the unit circle.
```

```quiz
Q: Which gate is the DFT of size 2?
- X
* H
- Z
E: For N = 2, ω = −1, so F = (1/√2)[[1, 1], [1, −1]], the Hadamard gate.
```

## Summary

- The $N$-th roots of unity $\omega^k$, $\omega = e^{2\pi i/N}$, sum to 0.
- $F_{jk} = \omega^{jk}/\sqrt{N}$ has orthonormal columns, so it is unitary; for $N = 2$ it is $H$.
- $F^\dagger$ turns a steadily growing phase into a peak: the core of phase estimation.
