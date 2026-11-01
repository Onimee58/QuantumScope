---
title: "Lab: reset by feed-forward"
area: circuits
kind: lab
order: 98
objectives: Condition a gate on a measurement | Reset a qubit to the zero state from any starting state
---
# Lab: reset by feed-forward

Starting from $|+\rangle$, you will force the qubit into $|0\rangle$ using a measurement and a classically controlled X.

[Start with q0 in |+⟩](qs:circuit?n=1&states=%2B)

```step
title: Measure
text: Drag M→c onto q0 in the first column. There are now two branches: in one the qubit is |0⟩, in the other |1⟩.
check: measures >= 1
check: branches = 2
```

```step
title: Correct the 1s
text: Put an X on q0 in the next column, right-click it and choose Run only if… → c0 = 1. In every branch the qubit is now |0⟩.
hint: The X must be in a later column than the measurement.
check: conditions >= 1
check: settles 0 0
```

```step
title: Do it in one step
text: Delete the measurement and the X, and drag Reset from the Classical palette onto q0 instead. Same result, no classical bit.
check: measures = 0
check: conditions = 0
check: settles 0 0
```

```quiz
Q: Would "measure, then X if c0 = 1" also reset a qubit that starts in |1⟩?
* Yes: the measurement gives 1 for certain, and the X turns |1⟩ into |0⟩
- No, it only works for |+⟩
E: Feed-forward reset works for every starting state.
```
