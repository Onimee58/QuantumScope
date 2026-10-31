---
title: "Lab: make a Bell pair"
area: circuits
kind: lab
order: 90
objectives: Build an entangled two-qubit state from gates | Confirm entanglement with the State Inspector
---
# Lab: make a Bell pair

In this lab you build the Bell state

$$|\Phi^+\rangle = \frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)$$

step by step. Keep this window open next to the circuit: each step turns **✓ Done** as soon as your circuit satisfies it.

[Start with an empty 2-qubit circuit](qs:circuit?n=2)

```step
title: Put q0 in superposition
text: Drag an H gate onto q0 in the first column. q0 should now be equally likely to be 0 or 1, with q1 still 0.
hint: H turns |0⟩ into (|0⟩ + |1⟩)/√2.
check: qubits 2
check: probability 00=0.5 10=0.5
```

```step
title: Entangle q1 with q0
text: Add a CX gate with q0 as the control and q1 as the target, in the next column: drop CX on q1, then click q0.
hint: CX flips q1 only when q0 is 1, so |10⟩ becomes |11⟩ while |00⟩ is unchanged.
check: state H:0;CX:0,1
```

```step
title: Confirm the entanglement
text: Open the State Inspector, choose the Reduced state tab and tick q0 only. Its entropy is 1 bit: on its own, q0 is completely random, even though the pair together is a pure state.
check: entangled 0
check: gates <= 2
```

## What you built

Measuring either qubit gives 0 or 1 with probability ½ — but the two results always agree. No product state $|a\rangle\otimes|b\rangle$ can do this, which is exactly what entanglement means.

```quiz
Q: You measure q0 of the Bell pair and get 1. What will q1 give?
- 0 or 1 with probability ½ each
* 1 with certainty
- 0 with certainty
E: Only |00⟩ and |11⟩ appear in the state, so the outcomes are perfectly correlated.
```
