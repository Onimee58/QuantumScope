---
title: "Lab: phase estimation precision"
area: circuits
kind: lab
order: 104
objectives: Read a phase from the counting register | See how more counting qubits sharpen an inexact estimate
---
# Lab: phase estimation precision

You will estimate $\varphi = \frac{1}{3}$, which no finite binary fraction represents exactly.

[Open phase estimation with 3 counting qubits and φ = 1/3](qs:algorithm/qpe?t=3&phase=1/3)

```step
title: Three counting qubits
text: Run measurement shots. The most likely result is 011 = 3/8 = 0.375, the closest 3-bit value to 1/3, but other results appear too.
check: qubits 4
```

```step
title: Six counting qubits
text: Choose Change parameters… in the title bar and set 6 counting qubits. The peak is now 010101 = 21/64 ≈ 0.328 — much closer to 1/3, and sharper.
check: qubits 7
```

```quiz
Q: What does each extra counting qubit add?
* One more binary digit of precision
- A higher success probability of exactly 1
- Nothing for inexact phases
E: t counting qubits estimate φ to t bits; for inexact phases the closest estimate still wins with probability at least 4/π².
```
