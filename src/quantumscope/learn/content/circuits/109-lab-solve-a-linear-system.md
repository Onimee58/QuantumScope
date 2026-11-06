---
title: "Lab: solve a linear system"
area: circuits
kind: lab
order: 109
objectives: Solve A x = b with VQLS | See how the condition number affects the solve
---
# Lab: solve a linear system

[Open VQLS for a 1-qubit system](qs:algorithm/vqls?problem=single&layers=1)

```step
title: Look at the setup
text: The circuit has RY parameters, and the observable is the VQLS cost for A = 1 + 0.5 X with b = |0⟩. Open Show the solution beside the verification table to compare the circuit's state with A⁻¹b.
check: parameters >= 2
check: observable
```

```step
title: Optimize
text: Press Optimize in the Parameters panel. The cost falls to 0, the bars in Show the solution meet, and the example's check passes.
check: reaches 0.001
check: verified
```

```quiz
Q: What does a cost of exactly 0 tell you?
* A|x⟩ points along |b⟩: the circuit prepares the solution A⁻¹b, normalized
- The circuit has no parameters left
- The matrix A is singular
E: The VQLS cost is 0 exactly at the solution.
```
