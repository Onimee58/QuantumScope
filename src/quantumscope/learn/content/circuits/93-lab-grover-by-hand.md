---
title: "Lab: Grover search by hand"
area: circuits
kind: lab
order: 93
objectives: Build Grover's oracle and diffusion from single gates | Find the marked item 11 with one query
---
# Lab: Grover search by hand

With two qubits there are four items. One Grover iteration finds the marked item $|11\rangle$ with certainty.

[Start with an empty 2-qubit circuit](qs:circuit?n=2)

```step
title: Uniform superposition
text: Put an H on both qubits.
check: qubits 2
check: probability 00=0.25 01=0.25 10=0.25 11=0.25
```

```step
title: The oracle
text: Add a CZ between q0 and q1. It flips the sign of |11⟩ only, so the probabilities do not change yet — look at the phases in the State Inspector.
check: state H:0;H:1;CZ:0,1
```

```step
title: The diffusion
text: Add H on both qubits, X on both, a CZ, then X on both and H on both.
hint: That is 9 gates in 5 columns: H H | X X | CZ | X X | H H.
check: probability 11=1
```

```quiz
Q: Why does one iteration suffice here?
* For N = 4, θ = 30°, and one iteration rotates by 2θ to 90°
- Two-qubit circuits are always exact
- The oracle measures the answer
E: sin θ = 1/√4 gives θ = 30°, so (2·1 + 1)·30° = 90° and P = sin² 90° = 1.
```
