---
title: "Lab: see phase kickback"
area: circuits
kind: lab
order: 92
objectives: Prepare a target in the minus state | Watch a CX change its control instead of its target
---
# Lab: see phase kickback

You will watch a CX gate change its **control** qubit. Open the State Inspector and keep it beside the circuit.

[Start with an empty 2-qubit circuit](qs:circuit?n=2)

```step
title: Target in |−⟩
text: Click the label of q1 at the left of its wire and choose |−⟩.
hint: q1 will be the CX target.
check: qubits 2
check: starts 1:-
```

```step
title: Control in |+⟩
text: Set q0's initial state to |+⟩ the same way.
check: starts 0:+
```

```step
title: Apply the CX
text: Add a CX with control q0 and target q1. In the Inspector's Reduced state tab, q1 is still |−⟩ — but q0 has turned from |+⟩ into |−⟩.
check: state H:0;X:1;H:1;CX:0,1
```

```step
title: Read the phase out
text: Add an H on q0. A |−⟩ becomes |1⟩, so q0 now measures 1 with certainty.
check: probability 10=0.5 11=0.5
check: uses CX,H
```

```quiz
Q: Which qubit did the CX change?
- The target q1
* The control q0
- Neither
E: X|−⟩ = −|−⟩, so the target is untouched and the sign lands on the control's |1⟩ part, turning |+⟩ into |−⟩.
```
