---
title: Probability for quantum experiments
area: math
kind: lecture
order: 6
objectives: Compute an expectation value and a variance | Explain why shot counts fluctuate | Estimate the standard error of an average
---
# Probability for quantum experiments

Every quantum measurement is random, so reading experiments means reading **statistics**: averages, spreads, and how both depend on the number of repetitions.

## Probabilities and averages

A measurement has results $x_k$ with probabilities $p_k$, where all $p_k \geq 0$ and $\sum_k p_k = 1$. The **expectation value** is the probability-weighted average:

$$\langle x \rangle = \sum_k p_k\, x_k$$

For a qubit measured along $z$ with results $+1$ and $-1$:

$$\langle Z \rangle = p_0 \cdot (+1) + p_1 \cdot (-1) = p_0 - p_1$$

So $\langle Z \rangle = 0$ for $|+\rangle$ (50/50), and $\langle Z \rangle = 1$ for $|0\rangle$.

## Variance: how much results spread

The **variance** measures the spread around the average:

$$\mathrm{Var}(x) = \langle x^2 \rangle - \langle x \rangle^2$$

For results $\pm 1$, $x^2 = 1$ always, so $\mathrm{Var} = 1 - \langle x \rangle^2$. An eigenstate has variance 0 (always the same result); $|+\rangle$ measured along $z$ has variance 1, the maximum.

## Many shots: why counts fluctuate

Repeat a measurement $N$ times ("shots") and average. The average approaches $\langle x \rangle$, but never exactly: its typical error, the **standard error**, is

$$\sigma_{\mathrm{mean}} = \sqrt{\frac{\mathrm{Var}(x)}{N}}$$

The error shrinks like $1/\sqrt{N}$: **4 times more shots halve the error**, and 100 times more shots make it 10 times smaller.

For counts, the same rule says that an outcome with probability $p$ appears about $Np$ times, give or take $\sqrt{Np(1-p)}$. With $N = 1024$ and $p = \frac{1}{2}$ that is about $512 \pm 16$, so seeing 497 is perfectly normal.

The Bell-test meter in the Entanglement experiment shows its result as $|S| \pm$ error: the error combines the standard errors of its four correlations.

[Try it: a |+⟩ qubit — press Run shots a few times and watch the counts vary around 512](qs:circuit?n=1&gates=H:0)

## Check your understanding

```quiz
Q: A qubit gives +1 with probability 0.75 and −1 otherwise. What is ⟨Z⟩?
- 0.75
* 0.5
- 0.25
E: ⟨Z⟩ = 0.75·(+1) + 0.25·(−1) = 0.5.
```

```quiz
Q: An average from 100 shots has an error of about 0.1. How many shots give an error of about 0.01?
- 1,000
* 10,000
- 200
E: The error shrinks like 1/√N: ten times smaller needs 10² = 100 times more shots.
```

## Summary

- Expectation value: $\langle x \rangle = \sum_k p_k x_k$; for $\pm 1$ results, $\langle Z \rangle = p_0 - p_1$.
- Variance $\langle x^2 \rangle - \langle x \rangle^2$ measures the spread; eigenstates have none.
- Averages of $N$ shots have errors that shrink like $1/\sqrt{N}$.
