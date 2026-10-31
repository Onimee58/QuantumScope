---
title: Grover search
area: circuits
kind: lecture
order: 8
objectives: Describe the oracle and diffusion steps | Use the geometric picture of Grover rotations | Choose the number of iterations and recognize overshooting
---
# Grover search

## The problem

Among $N = 2^n$ items, one is **marked**, and an oracle recognizes it. Classically you need about $N/2$ guesses on average. Grover's algorithm needs about $\frac{\pi}{4}\sqrt{N}$ oracle queries.

## The two steps

Start in the uniform superposition $|s\rangle = H^{\otimes n}|0\rangle$ and repeat:

1. **Oracle:** flip the sign of the marked state $|w\rangle$.
2. **Diffusion:** reflect every amplitude about the average, $D = 2|s\rangle\langle s| - I$.

The diffusion is built as H on every qubit, X on every qubit, a multi-controlled Z, then X and H again.

## The geometric picture

Every state the algorithm visits lies in the plane spanned by $|w\rangle$ and the unmarked states. If $\sin\theta = 1/\sqrt{N}$, each oracle-plus-diffusion rotates the state by $2\theta$ towards $|w\rangle$, so after $k$ iterations

$$P(w) = \sin^2\left((2k+1)\theta\right)$$

| N | θ | Best k | P(w) at best k |
|---|---|---|---|
| 4 | 30° | 1 | 1 |
| 8 | 20.7° | 2 | 0.945 |
| 16 | 14.5° | 3 | 0.961 |

Going past the best $k$ rotates *past* $|w\rangle$, and the success probability falls again — the algorithm **overshoots**.

[Try it: Grover with 3 qubits](qs:algorithm/grover?n=3&marked=101&iterations=-1&inspector=1)

Remove one Oracle and Diffusion pair: the verification panel checks the new probability against the same formula with the smaller $k$.

## Check your understanding

```quiz
Q: How many iterations maximize success for N = 4?
* 1
- 2
- 4
E: θ = 30°, so after one iteration (2k + 1)θ = 90° and P = 1.
```

```quiz
Q: What happens if you run more iterations than the optimum?
- Success stays at its maximum
* Success decreases again
- The circuit fails to run
E: Each iteration rotates by 2θ; past the marked state, the overlap shrinks.
```

## Summary

- Grover alternates an oracle (sign flip) and a diffusion (reflection about the mean).
- Each iteration rotates by 2θ with sin θ = 1/√N, giving P = sin²((2k+1)θ).
- About (π/4)√N iterations are optimal; more makes it worse.
