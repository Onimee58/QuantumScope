---
title: The parameter-shift rule
area: circuits
kind: lecture
order: 23
objectives: State the parameter-shift rule | Verify it for RY and Z | Explain why it gives exact gradients on hardware
---
# The parameter-shift rule

## Gradients without calculus on the circuit

To lower ⟨O⟩ efficiently we want its **gradient**: how fast ⟨O⟩ changes with each parameter. On a quantum computer we cannot differentiate the circuit symbolically, and finite differences ($f(\theta + \epsilon) - f(\theta)$ for a tiny $\epsilon$) drown in measurement noise.

## The rule

For gates $e^{-i\theta G}$ whose generator $G$ has eigenvalues $\pm\frac{1}{2}$ — RX, RY and RZ, and with a gap of 1 also P, CP and U's angles — the derivative is **exactly**

$$\frac{\partial f}{\partial \theta} = \frac{f(\theta + \frac{\pi}{2}) - f(\theta - \frac{\pi}{2})}{2}$$

Two runs of the *same* circuit, with the angle shifted by ±π/2, give the exact gradient — large shifts, so the result is robust to noise.

## A check

For $R_Y(\theta)|0\rangle$ and $Z$, $f(\theta) = \cos\theta$:

$$\frac{\cos(\theta + \frac{\pi}{2}) - \cos(\theta - \frac{\pi}{2})}{2} = \frac{-\sin\theta - \sin\theta}{2} = -\sin\theta$$

which is exactly $f'(\theta)$.

## Several gates, one parameter

When a parameter drives several gates, its gradient is the sum of each gate's shift, multiplied by that gate's factor. QuantumScope's **BFGS** and **gradient descent** use this rule; the cost is two circuit runs per bound gate, which is why the optimizer reports how many circuit evaluations it used.

## Check your understanding

```quiz
Q: How many circuit runs does the parameter-shift rule need per gate?
- 1
* 2
- One per measurement shot
E: f(θ + π/2) and f(θ − π/2): two runs, then half their difference.
```

```quiz
Q: Why not use a tiny finite difference instead?
* On hardware, f is estimated from measurements, and the noise swamps a tiny difference
- Finite differences are always exactly zero
- Quantum circuits have no derivatives
E: The shifts of ±π/2 are large, so the difference is far above the measurement noise.
```

## Summary

- For rotation gates, the gradient is exact from two shifted runs: [f(θ + π/2) − f(θ − π/2)] / 2.
- Gradients add over gates that share a parameter, each times its factor.
