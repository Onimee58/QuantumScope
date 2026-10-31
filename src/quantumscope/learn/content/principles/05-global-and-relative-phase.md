---
title: Global and relative phase
area: principles
kind: lecture
order: 5
objectives: Explain why a global phase is unobservable | Show how a relative phase changes measurement results after interference | Recognize phase on the Bloch sphere
---
# Global and relative phase

## Global phase

The states $|\psi\rangle$ and $e^{i\gamma}|\psi\rangle$ give identical probabilities for every possible measurement, because $|e^{i\gamma}|^2 = 1$. They are the same physical state. This is why the Bloch sphere needs only two angles, and why QuantumScope can "remove the global phase" without changing anything physical.

## Relative phase

A phase on *one* component is different:

$$|+\rangle = \frac{1}{\sqrt{2}}(|0\rangle + |1\rangle), \qquad |-\rangle = \frac{1}{\sqrt{2}}(|0\rangle - |1\rangle)$$

Measured in the $z$ basis, both give 50:50. But after a Hadamard, $|+\rangle \to |0\rangle$ and $|-\rangle \to |1\rangle$: completely different outcomes. A relative phase is invisible to one measurement and decisive for another.

[Try it: a relative phase revealed by H](qs:circuit?n=1&gates=H:0;Z:0;H:0&inspector=1)

## Phase on the Bloch sphere

The relative phase $\varphi$ is the **azimuthal angle** around the $z$ axis. Phase gates such as S, T and $R_Z$ rotate the state around that axis: they leave $z$-measurement probabilities unchanged but move the state between, for example, $|+\rangle$, $|+i\rangle$ and $|-\rangle$.

## Why phase matters

Every quantum algorithm works by arranging relative phases so that wrong answers cancel and right answers reinforce. Phase kickback, Grover's oracle and the QFT are all ways of writing information into phases.

## Check your understanding

```quiz
Q: Which pair of states can be told apart by some measurement?
- |0⟩ and −|0⟩
- |+⟩ and i|+⟩
* |+⟩ and |−⟩
E: The first two pairs differ only by a global phase. |+⟩ and |−⟩ differ by a relative phase, which H turns into different outcomes.
```

```quiz
Q: What does an RZ gate do to the z-basis measurement probabilities?
* Nothing
- Swaps them
- Makes them equal
E: RZ only rotates around the z axis, changing the relative phase, not |α|² or |β|².
```

## Summary

- Global phase is unobservable; relative phase is physical.
- Relative phase is the azimuthal angle on the Bloch sphere, changed by phase gates.
- Interference turns relative phase into measurable differences — the engine of quantum algorithms.
