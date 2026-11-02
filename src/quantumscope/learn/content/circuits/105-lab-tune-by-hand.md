---
title: "Lab: tune a circuit by hand"
area: circuits
kind: lab
order: 105
objectives: Turn a gate angle into a parameter | Set an observable | Lower the expectation value with a slider
---
# Lab: tune a circuit by hand

Before letting an optimizer do it, you will minimize an expectation value yourself.

[Start: one qubit with an RY gate](qs:circuit?n=1&gates=RY:0:0.4)

```step
title: Make the angle a parameter
text: Double-click the RY gate and type \theta as its angle. The gate now shows θ, and the Parameters panel appears with a slider for θ.
hint: The backslash makes the Greek letter, as in LaTeX.
check: parameters >= 1
check: bound >= 1
```

```step
title: Choose what to measure
text: In the Observable box type Z0 (or pick it from Examples…). ⟨O⟩ shows how likely q0 is to be 0 rather than 1.
check: observable Z0
```

```step
title: Find the minimum
text: Drag θ's slider until ⟨O⟩ is as low as it can go: −1, the exact minimum shown beside it.
hint: ⟨Z⟩ = cos θ for this circuit.
check: expectation <= -0.99
```

```quiz
Q: At which angle did ⟨Z0⟩ reach −1?
- θ = 0
- θ = π/2
* θ = π
E: cos π = −1: RY(π) turns |0⟩ into |1⟩.
```
