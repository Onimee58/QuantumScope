---
title: Quantum phase estimation
area: circuits
kind: lecture
order: 21
objectives: State what phase estimation computes | Follow the circuit from controlled powers to the inverse QFT | Predict the result when the phase is not an exact binary fraction
---
# Quantum phase estimation

## The problem

A unitary $U$ with an eigenstate $|u\rangle$ satisfies

$$U|u\rangle = e^{2\pi i\varphi}|u\rangle$$

for some phase $\varphi$ between 0 and 1. **Phase estimation** finds $\varphi$ to $t$ binary digits. It is the engine inside Shor's factoring algorithm and inside quantum algorithms for chemistry, which estimate energies as phases.

## The circuit

1. Put $t$ **counting** qubits in superposition with H, and the target in $|u\rangle$.
2. Counting qubit $j$ controls $U^{2^{t-1-j}}$. By **phase kickback**, each counting qubit picks up the phase $e^{2\pi i\,\varphi\,2^{t-1-j}}$ on its $|1\rangle$ part — the target never changes.
3. The counting register now holds the quantum Fourier transform of the number $2^t\varphi$ — exactly so when that number is whole — so the **inverse QFT** turns it back into that number, or into its closest neighbours.
4. Measure the counting qubits: the result $m$ gives $\varphi \approx m/2^t$.

In QuantumScope, $U = P(2\pi\varphi)$ and $|u\rangle = |1\rangle$, so the controlled powers are controlled-phase gates.

[Try it: estimate φ = 5/16 with 4 counting qubits](qs:algorithm/qpe?t=4&phase=5/16)

## Exact and inexact phases

If $2^t\varphi$ is a whole number, the result is certain. Otherwise the probability spreads over neighbouring values, but the closest $t$-bit estimate still wins with probability at least

$$\frac{4}{\pi^2} \approx 0.405$$

and more counting qubits sharpen the estimate: each one adds a binary digit.

[Try it: estimate φ = 1/3 with 4 counting qubits](qs:algorithm/qpe?t=4&phase=1/3)

## Check your understanding

```quiz
Q: With t = 3 counting qubits and φ = 3/8, what is measured?
- 011 with probability 4/π²
* 011 with certainty
- A uniform spread
E: 2³ · 3/8 = 3 exactly, so the counting register ends in |011⟩.
```

```quiz
Q: Why does the target qubit stay unchanged?
* It is an eigenstate of U; the phase kicks back onto the counting qubits
- The controlled gates never act on it
- It is measured first
E: Controlled-U on an eigenstate only multiplies the control's |1⟩ part by the eigenphase.
```

## Summary

- Phase estimation finds φ in U|u⟩ = e^{2πiφ}|u⟩ to t bits.
- Controlled powers of U kick the phase back onto counting qubits; the inverse QFT reads it out.
- Exact binary fractions are found with certainty; otherwise the closest estimate wins with probability at least 4/π².
