---
title: From data to quantum states
area: qml
kind: lecture
order: 1
objectives: Explain what a feature map does | Write the angle-encoding state of a data point | Compute a quantum kernel as an overlap of states
math: 02-vectors-and-dirac-notation, 07-tensor-products, 09-matrix-exponentials
---
# From data to quantum states

Quantum machine learning starts with a question: how does a data point, a row of numbers, get into a quantum computer? The answer is a **feature map**: a circuit $U(x)$ whose angles are set by the data, turning each point $x$ into a quantum state $|\varphi(x)\rangle = U(x)|0\dots0\rangle$.

## Angle encoding

The simplest feature map gives each feature its own qubit and turns it by that much:

$$|\varphi(x)\rangle = R_Y(x_1)|0\rangle \otimes R_Y(x_2)|0\rangle \otimes \dots \otimes R_Y(x_n)|0\rangle$$

Each qubit ends up as $\cos\frac{x_i}{2}|0\rangle + \sin\frac{x_i}{2}|1\rangle$. With features scaled to $[0, \pi]$, every value maps to a different point on the qubit's Bloch sphere, from $|0\rangle$ (at 0) to $|1\rangle$ (at $\pi$). That is why QuantumScope's datasets are scaled to $[0, \pi]$.

The state is a **product state**: each qubit carries one feature, and they never interact.

## The ZZ feature map

The **ZZ feature map** of Havlíček et al. (2019) adds entanglement. After Hadamards on every qubit it applies phases that depend on single features and on **pairs** of features:

$$U(x) = \exp(i \sum_k x_k Z_k + i \sum_{j<k} (\pi - x_j)(\pi - x_k)\, Z_j Z_k)\, H^{\otimes n}$$

repeated for a chosen number of **repetitions**. The pair terms entangle the qubits, so the state is no longer a product: its amplitudes mix the features in ways that are hard to compute classically for many qubits.

## The quantum kernel

A classifier needs to know how **similar** two data points are. Two states can be compared by their overlap, the **quantum kernel**:

$$K(x, x') = |\langle \varphi(x) | \varphi(x') \rangle|^2$$

It is 1 for the same point and close to 0 for very different states. For angle encoding it has a simple form:

$$K(x, x') = \prod_k \cos^2\frac{x_k - x'_k}{2}$$

On a quantum computer, $K$ is measured, not calculated: run $U(x)$ followed by $U(x')^\dagger$ and count how often all qubits read 0. With $N$ shots, that frequency estimates $K$ with a statistical error of about $\sqrt{K(1-K)/N}$.

[Try it: the Quantum Kernel Classifier (its kernel heatmap compares every pair of points)](qs:open/qml_kernel)

## Check your understanding

```quiz
Q: Angle encoding with features in [0, π]: what state does the value π give a qubit?
- |0⟩
* |1⟩
- |+⟩
E: RY(π)|0⟩ = cos(π/2)|0⟩ + sin(π/2)|1⟩ = |1⟩.
```

```quiz
Q: What is K(x, x) for any feature map?
* 1
- 0
- It depends on x
E: K(x, x) = |⟨φ(x)|φ(x)⟩|² = 1, since |φ(x)⟩ is normalized.
```

## Summary

- A feature map $U(x)$ turns a data point into a state $|\varphi(x)\rangle$.
- Angle encoding gives a product state; the ZZ map entangles features in pairs.
- The quantum kernel $K(x, x') = |\langle \varphi(x)|\varphi(x')\rangle|^2$ measures similarity, estimated from shots on hardware.
