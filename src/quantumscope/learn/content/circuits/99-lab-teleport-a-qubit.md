---
title: "Lab: teleport a qubit"
area: circuits
kind: lab
order: 99
objectives: Build the full teleportation protocol | Check it in every measurement branch
---
# Lab: teleport a qubit

q0 starts in $|+i\rangle$. You will teleport it to q2. Keep the State Inspector's **Branches** tab open.

[Start: q0 in |+i⟩, q1 and q2 in |0⟩](qs:circuit?n=3&states=%2Bi,0,0)

```step
title: Share a Bell pair
text: Put H on q1, then a CX with control q1 and target q2.
check: qubits 3
check: entangled 1
```

```step
title: Alice entangles
text: Add a CX with control q0 and target q1, then H on q0.
hint: These two gates prepare Alice's Bell measurement.
check: gates >= 4
check: uses H,CX
```

```step
title: Alice measures
text: In the next column, drag M→c onto q0 (into c0) and onto q1 (into c1). Four branches appear, each with probability ¼ — and in each, q2 is a differently rotated version of |+i⟩.
check: measures >= 2
check: branches = 4
```

```step
title: Bob corrects
text: Put X on q2 and set Run only if… → c1 = 1; then Z on q2 with Run only if… → c0 = 1. Now q2 is |+i⟩ in every branch.
hint: Compare q2's Bloch vector across the four rows of the Branches tab.
check: conditions = 2
check: teleports 0 2
```

```quiz
Q: Which branch needs no correction at all?
* c0c1 = 00
- c0c1 = 11
- Every branch needs both X and Z
E: For the result 00, Bob's qubit is already |ψ⟩.
```
