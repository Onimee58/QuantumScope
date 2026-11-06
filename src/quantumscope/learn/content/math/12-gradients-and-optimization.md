---
title: Gradients and optimization
area: math
kind: lecture
order: 12
objectives: Compute derivatives and gradients of simple functions | Describe gradient descent and its pitfalls | Explain why the parameter-shift rule gives exact derivatives
---
# Gradients and optimization

Variational algorithms tune circuit parameters to make a quantity as small as possible. The tools are classical calculus: **derivatives**, **gradients** and **gradient descent**.

## Derivatives

The derivative $f'(\theta)$ is the slope of $f$ at $\theta$: how fast $f$ changes when $\theta$ changes a little. Two rules cover most circuits:

$$\frac{d}{d\theta}\cos\theta = -\sin\theta, \qquad \frac{d}{d\theta}\sin\theta = \cos\theta$$

At a minimum the slope is zero, which is the condition optimizers look for.

## Gradients

With several parameters $\theta_1, \dots, \theta_k$, the **gradient** collects the slopes along each one (the partial derivatives):

$$\nabla f = \left( \frac{\partial f}{\partial \theta_1}, \dots, \frac{\partial f}{\partial \theta_k} \right)$$

It points uphill, in the direction of steepest increase.

## Gradient descent

**Gradient descent** repeatedly takes a small step downhill:

$$\theta \leftarrow \theta - \eta\, \nabla f(\theta)$$

where $\eta$ is the step size. Too large a step overshoots the valley; too small a step crawls. QuantumScope's gradient descent shortens the step whenever it would go uphill, so it never makes things worse.

Two pitfalls appear in the energy landscapes:

- **Local minima:** a valley that is not the lowest one. Descent stops there, which is why starting again from random parameters ("best of N starts") helps.
- **Barren plateaus:** large flat regions where the gradient is nearly zero in every direction, so there is no downhill to follow.

## The parameter-shift rule

A circuit's expectation value depends on a rotation angle like $f(\theta) = A + B\cos\theta + C\sin\theta$. For such a function, the derivative is **exactly**

$$f'(\theta) = \frac{f(\theta + \frac{\pi}{2}) - f(\theta - \frac{\pi}{2})}{2}$$

Check it: $\cos(\theta + \frac{\pi}{2}) - \cos(\theta - \frac{\pi}{2}) = -2\sin\theta$, giving $-B\sin\theta$, and the $\sin$ term gives $C\cos\theta$ the same way. Unlike a numerical difference with a tiny step, this uses two large shifts and has no approximation error, so a quantum computer can measure gradients with just two extra circuit runs per parameter.

[Try it: VQE for H₂ — press Optimize, then open the landscape](qs:algorithm/vqe?problem=h2&layers=1)

## Check your understanding

```quiz
Q: f(θ) = cos θ. What does the parameter-shift rule give at θ = 0?
- 1
* 0
- −1
E: [cos(π/2) − cos(−π/2)]/2 = (0 − 0)/2 = 0, exactly f′(0) = −sin 0 = 0.
```

```quiz
Q: Gradient descent stops at a valley that is not the lowest. What helps?
- A smaller step size
* Starting again from other (random) parameters
- Measuring more shots
E: A local minimum traps descent from that side; other starting points can reach other valleys.
```

## Summary

- The gradient collects partial derivatives and points uphill; descent steps against it.
- Local minima and barren plateaus are the main obstacles; random restarts help with the first.
- The parameter-shift rule gives exact derivatives from two shifted circuit runs.
