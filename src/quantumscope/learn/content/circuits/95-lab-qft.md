---
title: "Lab: QFT of a basis state"
area: circuits
kind: lab
order: 95
objectives: Build the 2-qubit QFT gate by gate | Read the resulting phases
---
# Lab: QFT of a basis state

You will build the quantum Fourier transform of $|01\rangle$ ($x = 1$) on two qubits. The result is

$$\frac{1}{2}(|00\rangle + i|01\rangle - |10\rangle - i|11\rangle)$$

[Start with an empty 2-qubit circuit](qs:circuit?n=2)

```step
title: Prepare |01⟩
text: Set q1 to start in |1⟩.
check: qubits 2
check: starts 1:1
```

```step
title: H on q0
text: Put an H on q0.
check: state X:1;H:0
```

```step
title: Controlled phase
text: Add a CP gate between q1 and q0 with angle π/2 (set the new-gate angle to 90° before placing it).
hint: Drop CP on q0, then click q1.
check: state X:1;H:0;CP:1,0:pi/2
```

```step
title: H on q1, then reverse
text: Put an H on q1, then a SWAP between q0 and q1. Check the phases in the State Inspector: 1, i, −1, −i.
check: state X:1;H:0;CP:1,0:pi/2;H:1;SWAP:0,1
```

```quiz
Q: What is the probability of measuring |10⟩ after the QFT?
- 0
* 1/4
- 1/2
E: All four amplitudes have magnitude 1/2, so each outcome has probability 1/4; x only sets the phases.
```
