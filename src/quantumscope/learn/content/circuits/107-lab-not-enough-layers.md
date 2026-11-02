---
title: "Lab: not enough layers"
area: circuits
kind: lab
order: 107
objectives: Recognize when an ansatz cannot express the ground state | Fix it by adding layers
---
# Lab: not enough layers

[Open VQE for a 3-spin Heisenberg chain, one layer](qs:algorithm/vqe?problem=heisenberg-3&layers=1)

```step
title: Optimize with one layer
text: Press Optimize. ⟨H⟩ stops near −3.83, well above the exact −4 — and running longer does not help.
check: expectation <= -3.8
```

```step
title: Add a layer
text: In the title bar choose Change parameters… and set 2 entangling layers, then Optimize again. Now ⟨H⟩ reaches −4.
check: reaches 0.001
```

```quiz
Q: Why did one layer stop at about −3.83?
- The optimizer was too slow
* The circuit cannot represent the ground state, so no parameters reach −4
- The Hamiltonian changed
E: With one layer the lowest reachable value is −(1 + 2√2) ≈ −3.83.
```
