---
title: Optimizers, landscapes and plateaus
area: circuits
kind: lecture
order: 25
objectives: Compare gradient-based and gradient-free optimizers | Read an energy landscape | Recognize step-size problems, plateaus and local minima
---
# Optimizers, landscapes and plateaus

## The landscape

⟨H⟩ as a function of the parameters is an **energy landscape**. **Landscape…** in the Parameters panel draws it over one or two parameters (others fixed): blue valleys are low, yellow hills high, and the optimizer's path is drawn on top.

## Gradient descent and the step size

The simplest method steps downhill: $\theta \leftarrow \theta - \eta\,\nabla \langle H \rangle$. Its step size $\eta$ matters: too large, and each step overshoots the valley so the energy bounces up and down; too small, and progress crawls. QuantumScope uses a **backtracking line search**: a step that would raise ⟨H⟩ is rejected and the step halved, so gradient descent never goes uphill.

## Better methods

| Method | Uses | Character |
|---|---|---|
| Gradient descent | parameter-shift gradients | simple; slow on flat regions |
| BFGS | parameter-shift gradients | learns the curvature; few steps |
| COBYLA, Nelder–Mead | only ⟨H⟩ values | no gradients; try many probe points |

The optimizer reports both its **steps** and its **circuit evaluations**: BFGS takes few steps but each needs a full gradient, while gradient-free methods discard most probes.

## Plateaus and local minima

- On a **plateau** the gradient is nearly zero and gradient descent crawls. In large random circuits these *barren plateaus* (McClean and colleagues, 2018) make training very hard.
- A **local minimum** is a valley that is not the lowest. "No step lowered ⟨H⟩" can mean you are at the best the circuit can do — or only at a local valley: try other starting values.

[Try it: compare methods on a 4-spin Ising chain](qs:algorithm/vqe?problem=ising-4&layers=3)

## Check your understanding

```quiz
Q: Gradient descent's energy bounces up and down. What is the likely cause?
* The step size is too large
- The gradient is exact
- The circuit has too many layers
E: Too large a step overshoots the valley on every step.
```

```quiz
Q: Why does BFGS report many circuit evaluations despite few steps?
* Each step needs a full parameter-shift gradient: two runs per bound gate
- BFGS repeats every step twice
- It counts measurement shots
E: Steps are cheap to count, but every gradient costs two circuit runs per gate.
```

## Summary

- The landscape shows ⟨H⟩ over the parameters; optimizers walk downhill on it.
- Step size matters; a line search keeps gradient descent from overshooting.
- Plateaus slow optimizers down; local minima can stop them early.
