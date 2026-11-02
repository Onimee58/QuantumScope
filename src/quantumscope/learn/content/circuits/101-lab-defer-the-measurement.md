---
title: "Lab: defer the measurement"
area: circuits
kind: lab
order: 101
objectives: Replace classical corrections with quantum controls | Verify that teleportation still works
---
# Lab: defer the measurement

You will rebuild teleportation without any mid-circuit measurement, using the deferred-measurement principle.

[Start: q0 in |+i⟩, q1 and q2 in |0⟩](qs:circuit?n=3&states=%2Bi,0,0)

```step
title: Bell pair and Alice's gates
text: Put H on q1, CX from q1 to q2, CX from q0 to q1, then H on q0 — the same start as teleportation.
check: qubits 3
check: gates >= 4
```

```step
title: Quantum corrections
text: Instead of measuring, add a CX with control q1 and target q2, then a CZ between q0 and q2. q2 now holds |+i⟩, with no measurement at all.
hint: CX replaces "X if c1 = 1"; CZ replaces "Z if c0 = 1".
check: measures = 0
check: conditions = 0
check: uses CZ
check: teleports 0 2
```

```quiz
Q: Why can't Alice and Bob use this version when they are far apart?
* The CX and CZ need q1 and q0 to interact directly with Bob's distant q2
- It gives a different final state
- It needs more classical bits
E: The deferred version replaces two classical bits by two quantum interactions across the distance.
```
