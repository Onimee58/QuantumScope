---
title: "Lab: build a GHZ state"
area: circuits
kind: lab
order: 91
objectives: Extend a Bell pair to three qubits | Check three-way correlations
---
# Lab: build a GHZ state

The goal is $|GHZ\rangle = \frac{1}{\sqrt{2}}(|000\rangle + |111\rangle)$: three qubits that are all 0 or all 1.

[Start with an empty 3-qubit circuit](qs:circuit?n=3)

```step
title: Superposition on q0
text: Put an H gate on q0.
check: qubits 3
check: probability 000=0.5 100=0.5
```

```step
title: Entangle q1
text: Add a CX with control q0 and target q1.
hint: You now have a Bell pair on q0 and q1, with q2 still 0.
check: probability 000=0.5 110=0.5
```

```step
title: Entangle q2
text: Add a CX with control q1 (or q0) and target q2.
check: probability 000=0.5 111=0.5
check: entangled 2
```

```quiz
Q: In the GHZ state, you measure q2 and get 0. What do q0 and q1 give?
* Both 0, with certainty
- Each 0 or 1 with probability ½
- Both 1
E: Only |000⟩ and |111⟩ appear, so all three results always agree.
```
