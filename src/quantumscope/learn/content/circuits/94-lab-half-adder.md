---
title: "Lab: build a half adder"
area: circuits
kind: lab
order: 94
objectives: Compute a carry with a Toffoli | Compute a sum with a CX
---
# Lab: build a half adder

You will add $a = 1$ and $b = 1$: the sum bit is 0 and the carry is 1. The inputs are set with initial states.

[Start with an empty 3-qubit circuit](qs:circuit?n=3)

```step
title: Set the inputs
text: Set q0 (a) and q1 (b) to start in |1⟩ by clicking their labels. q2 holds the carry and stays |0⟩.
check: qubits 3
check: starts 0:1
check: starts 1:1
```

```step
title: The carry
text: Add a Toffoli (CCX) with controls q0, q1 and target q2: drop CCX on q2, then click q0 and q1.
hint: The carry is a AND b, written into q2.
check: probability 111=1
```

```step
title: The sum
text: Add a CX with control q0 and target q1. q1 becomes a XOR b.
check: probability 101=1
check: uses CCX,CX
```

```quiz
Q: What do q1 and q2 hold at the end?
* q1 = sum = 0, q2 = carry = 1
- q1 = 1, q2 = 0
- q1 = carry, q2 = sum
E: 1 + 1 = 10 in binary: sum bit 0 (in q1) and carry 1 (in q2).
```
