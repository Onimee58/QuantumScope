---
title: Phase kickback and oracles
area: circuits
kind: lecture
order: 7
objectives: Explain phase kickback with the target in the minus state | Describe a phase oracle | Follow the Deutsch, Deutsch–Jozsa and Bernstein–Vazirani algorithms
---
# Phase kickback and oracles

## Phase kickback

$|-\rangle$ is an eigenstate of X with eigenvalue −1: $X|-\rangle = -|-\rangle$. So if a CX has its target in $|-\rangle$ and its control in $|x\rangle$,

$$CX\,|x\rangle|-\rangle = (-1)^x\,|x\rangle|-\rangle$$

The target is unchanged; instead, a phase appears on the *control*. With the control in superposition, that phase becomes a relative phase — for example $|+\rangle$ becomes $|-\rangle$.

[Try it: CX with the target in |−⟩](qs:circuit?n=2&gates=CX:0,1&states=%2B,-&inspector=1)

## Oracles

An **oracle** for a Boolean function $f$ is a reversible circuit $U_f|x\rangle|y\rangle = |x\rangle|y\oplus f(x)\rangle$. With the last qubit in $|-\rangle$, kickback turns it into a **phase oracle**:

$$U_f\,|x\rangle|-\rangle = (-1)^{f(x)}\,|x\rangle|-\rangle$$

In QuantumScope's Algorithms menu, oracles are blocks: double-click one to see its gates.

## Deutsch–Jozsa

Suppose $f$ on $n$ bits is promised to be either **constant** or **balanced** (0 for exactly half of the inputs). Classically you may need $2^{n-1}+1$ queries to be sure. The quantum algorithm needs one:

1. Apply H to every input qubit (ancilla in $|-\rangle$).
2. Query the phase oracle once.
3. Apply H to the inputs again and measure.

The result is $|0\cdots0\rangle$ with certainty if $f$ is constant, and never if it is balanced.

[Try it: Deutsch–Jozsa with a balanced function](qs:algorithm/deutsch_jozsa?n=3&function=balanced&s=101)

## Bernstein–Vazirani

If $f(x) = s\cdot x\ (\mathrm{mod}\ 2)$ for a hidden string $s$, the same circuit outputs $s$ itself with certainty, again after one query; classically you would need $n$ queries.

[Try it: Bernstein–Vazirani with s = 1011](qs:algorithm/bernstein_vazirani?n=4&s=1011&inspector=1)

## Check your understanding

```quiz
Q: In phase kickback with CX, where does the phase (−1)^x end up?
- On the target qubit
* On the control qubit's state
- It disappears
E: The target stays |−⟩; the factor (−1)^x multiplies the control's basis state, a relative phase when the control is in superposition.
```

```quiz
Q: Deutsch–Jozsa measures |000⟩. What can you conclude?
* f is constant
- f is balanced
- Nothing, the run must be repeated
E: For a balanced f the probability of |0…0⟩ is exactly zero, so one run decides.
```

## Summary

- A target in |−⟩ turns bit flips into phases on the control: phase kickback.
- A phase oracle multiplies |x⟩ by (−1)^f(x).
- Deutsch–Jozsa and Bernstein–Vazirani solve their problems with a single oracle query.
