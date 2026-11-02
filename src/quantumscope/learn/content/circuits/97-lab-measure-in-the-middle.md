---
title: "Lab: measure in the middle"
area: circuits
kind: lab
order: 97
objectives: Place mid-circuit measurements | Read branches and classical records
---
# Lab: measure in the middle

You will measure a Bell pair mid-circuit and watch the branches. Open the State Inspector and choose its **Branches** tab.

[Start with an empty 2-qubit circuit](qs:circuit?n=2)

```step
title: Make a Bell pair
text: Put H on q0, then a CX with control q0 and target q1.
check: qubits 2
check: state H:0;CX:0,1
```

```step
title: Measure q0 mid-circuit
text: From the Classical palette, drag M→c onto q0 after the CX. It records into c0. The Branches tab now lists two records, each with probability ½.
hint: M→c is different from M: it can go anywhere and stores its result in a classical bit.
check: measures >= 1
check: branches = 2
check: record 0=0.5 1=0.5
```

```step
title: Measure q1 too
text: Drag M→c onto q1 in the same column; it records into c1. Only the records 00 and 11 appear: the results are perfectly correlated.
check: measures >= 2
check: record 00=0.5 11=0.5
```

```quiz
Q: Why do the records 01 and 10 never appear?
* In the Bell pair, q1 always agrees with q0
- The second measurement failed
- Because c1 is measured after c0
E: (|00⟩ + |11⟩)/√2 only contains equal values, so the two measured bits always agree.
```
