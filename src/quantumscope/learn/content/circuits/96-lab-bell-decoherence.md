---
title: "Lab: watch a Bell pair decohere"
area: circuits
kind: lab
order: 96
objectives: Add a noise channel to a circuit | Measure fidelity and purity | See entanglement disappear
---
# Lab: watch a Bell pair decohere

You will build a Bell pair, then damage it with noise and watch the State Inspector. Open the Inspector and keep it beside the circuit.

[Start with an empty 2-qubit circuit](qs:circuit?n=2)

```step
title: Build the Bell pair
text: Put H on q0, then a CX with control q0 and target q1. In the Inspector, the pair is pure and q0 alone is maximally mixed.
check: qubits 2
check: state H:0;CX:0,1
```

```step
title: Add depolarizing noise
text: Drag Depolarize from the Noise palette onto q1, after the CX. Double-click it and set the strength to 0.4. The tabs change to Probabilities and Density matrix: the pair is now a mixed state.
hint: The fidelity should drop to 1 − 3p/4 = 0.7.
check: noise depolarizing
check: fidelity <= 0.8
```

```step
title: Destroy the entanglement
text: Raise the strength to 1. q1 is now completely random, and the coherences in ρ are gone: what is left is just a pair of coin tosses.
check: fidelity <= 0.26
check: purity <= 0.26
```

## What you saw

As $p$ grows, the off-diagonal entries of $\rho$ shrink, the fidelity falls as $1 - \frac{3p}{4}$, and at $p = 1$ the state is $\frac{I}{2}\otimes\frac{I}{2}$, with fidelity $\frac{1}{4}$ and purity $\frac{1}{4}$.

```quiz
Q: At p = 1, are the two qubits still correlated?
- Yes, always equal
- Yes, always opposite
* No, they are independent coin tosses
E: The state is I/2 ⊗ I/2, a product of two maximally mixed qubits: no correlation and no entanglement remain.
```
