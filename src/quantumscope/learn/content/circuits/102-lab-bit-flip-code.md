---
title: "Lab: build the bit-flip code"
area: circuits
kind: lab
order: 102
objectives: Encode a logical qubit in three data qubits | Measure the syndrome with two ancillas | Correct the error with a two-bit condition | Label the qubits of your own design
---
# Lab: build the bit-flip code

You will protect $|1\rangle$ against a bit flip, find the error with a syndrome measurement, and correct it. q0–q2 are data, q3 and q4 are syndrome ancillas.

[Start: q0 in |1⟩, four more qubits in |0⟩](qs:circuit?n=5&states=1,0,0,0,0)

```step
title: Name your qubits
text: Click q3's label and choose Label this qubit…, and name it syndrome. Do the same for q4.
check: labeled 3 syndrome
check: labeled 4 syndrome
```

```step
title: Encode
text: Add a CX from q0 to q1 and a CX from q0 to q2. The three data qubits now hold |111⟩: one logical 1.
check: qubits 5
check: probability 11100=1
```

```step
title: An error strikes
text: Put an X on q1 — a bit flip.
check: probability 10100=1
```

```step
title: Measure the syndrome
text: Add CX q0→q3, CX q1→q3, CX q1→q4, CX q2→q4, then M→c on q3 (into c0) and on q4 (into c1). The record is 11: the error is on q1.
hint: q3 holds q0 ⊕ q1 and q4 holds q1 ⊕ q2.
check: measures >= 2
check: record 11=1
```

```step
title: Correct it
text: Add X on q1, right-click it and choose Run only if… → Several bits… → c0 = 1, c1 = 1. All three data qubits are 1 again.
check: conditions >= 1
check: settles 0 1
check: settles 1 1
check: settles 2 1
```

```quiz
Q: Why does the correction need both bits?
- One bit is enough to locate any error
* The syndrome 11 points to q1, but 10 and 01 point to q0 and q2: only both bits together identify the qubit
E: Each single-qubit error has its own two-bit syndrome.
```
