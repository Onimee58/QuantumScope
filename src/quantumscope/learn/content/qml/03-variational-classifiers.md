---
title: Variational classifiers
area: qml
kind: lecture
order: 3
objectives: Describe a variational classifier's circuit and output | Explain how it is trained with exact gradients | Compare it with a kernel classifier
math: 06-probability, 12-gradients-and-optimization
---
# Variational classifiers

A kernel classifier uses the quantum computer only to compare data points. A **variational classifier** goes further: the circuit itself is the model, and training tunes its gates.

## The circuit

For a data point $x$ the circuit applies the feature map $U(x)$, then a trainable part $W(\theta)$: layers of $R_Y(\theta_k)$ on every qubit, each followed by a ring of CNOTs. The model's output is the expectation value of $Z$ on the first qubit, plus a bias:

$$f(x) = \langle \varphi(x)|\, W(\theta)^\dagger Z_0\, W(\theta)\, |\varphi(x)\rangle + b$$

It lies between $-1 + b$ and $1 + b$, and the predicted class is $\mathrm{sign}\, f(x)$. On hardware, $\langle Z_0\rangle$ is estimated by measuring the first qubit many times.

## Training

Training lowers the **loss**, here the mean squared error between outputs and labels:

$$L(\theta, b) = \frac{1}{2N} \sum_{i=1}^{N} (f(x_i) - y_i)^2$$

Because every $\theta_k$ sits in an $R_Y$ gate, the **parameter-shift rule** gives exact derivatives from two extra circuit runs per parameter:

$$\frac{\partial f}{\partial \theta_k} = \frac{f(\theta_k + \frac{\pi}{2}) - f(\theta_k - \frac{\pi}{2})}{2}$$

QuantumScope trains with **BFGS** (fast, using these exact gradients) or **Adam** (steady, small steps), and draws the loss and the training accuracy at every step.

## Kernels or circuits?

| | Kernel classifier | Variational classifier |
|---|---|---|
| Quantum part | the kernel matrix: one circuit per pair of points | one circuit per point and step |
| Training | classical, with a guaranteed best solution (convex) | gradient descent, which can stop in a local minimum |
| Cost as data grows | grows like $N^2$ | grows like $N$ per step |

The two are closely related: a variational classifier with a fixed feature map is a linear model in the same space of states that the kernel works in (Schuld and Killoran, 2019).

[Try it: train a variational classifier on the moons](qs:open/qml_variational)

## Check your understanding

```quiz
Q: The output is f(x) = ⟨Z₀⟩ + b = −0.4. Which class is predicted?
- +1
* −1
E: The prediction is sign f(x), and −0.4 is negative.
```

```quiz
Q: Why can training a variational classifier end at a worse result than an SVM on the same kernel?
* Gradient descent can stop in a local minimum; the SVM's problem has one best solution
- Variational circuits cannot be differentiated
- Kernels use more qubits
E: The SVM solves a convex problem; a variational loss landscape can have many valleys, which is why restarts from other seeds help.
```

## Summary

- A variational classifier is a trainable circuit: $f(x) = \langle Z_0\rangle + b$, class $\mathrm{sign}\, f$.
- It is trained on the mean squared error with exact parameter-shift gradients.
- Kernels need $N^2$ circuits but train to a guaranteed best; variational models scale better but can get stuck.
