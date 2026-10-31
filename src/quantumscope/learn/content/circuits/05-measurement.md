---
title: Measurement in circuits
area: circuits
kind: lecture
order: 5
objectives: Predict measurement probabilities from amplitudes | Compute the outcome distribution of measuring some of the qubits | Explain why finite shots only estimate probabilities
---
# Measurement in circuits

## Measuring every qubit

Measuring all qubits of $|\psi\rangle = \sum_x c_x|x\rangle$ gives the bit string $x$ with probability $|c_x|^2$. The state afterwards is $|x\rangle$: measurement **collapses** the superposition, which is why QuantumScope only allows measurements at the end of a circuit (mid-circuit measurement arrives in a later version).

## Measuring some of the qubits

If you measure only q0, the probability of outcome $b$ adds up every basis state in which q0 equals $b$:

$$P(q_0 = b) = \sum_{x:\ x_0 = b} |c_x|^2$$

For the Bell pair, $P(q_0 = 0) = P(q_0 = 1) = \frac{1}{2}$, even though the pair is in a single, definite (pure) state. Put **M** gates only on the qubits you want to measure; the histogram then shows just those outcomes.

[Try it: a Bell pair, measuring q0 only](qs:circuit?n=2&gates=H:0;CX:0,1)

## Shots and statistics

A real experiment repeats the circuit many times (**shots**) and counts outcomes. With $N$ shots, an outcome of probability $p$ appears about $Np$ times, with a typical fluctuation of

$$\sqrt{Np(1-p)}$$

For $p = \frac{1}{2}$ and $N = 1024$ that is about 16 counts, so seeing 497 instead of 512 is perfectly normal. **Run measurement shots** in the circuit tab samples from the exact probabilities, so the counts fluctuate the same way.

## Check your understanding

```quiz
Q: A 2-qubit state has amplitudes 1/2 on each of |00⟩, |01⟩, |10⟩, |11⟩. What is P(q0 = 1)?
- 1/4
* 1/2
- 3/4
- 1
E: Add the probabilities of |10⟩ and |11⟩: 1/4 + 1/4 = 1/2.
```

```quiz
Q: You run 100 shots of a circuit with P(0) = 0.5. Which result is most suspicious?
- 46 zeros
- 55 zeros
* 80 zeros
E: The expected spread is √(100 · 0.5 · 0.5) = 5 counts, so 80 is six spreads away from 50.
```

## Summary

- Measuring all qubits gives x with probability |cₓ|², and the state collapses to |x⟩.
- Measuring some qubits sums the probabilities over the unmeasured ones.
- Finite shots estimate probabilities, with fluctuations of about √(Np(1−p)).
