---
title: Entanglement in circuits
area: circuits
kind: lecture
order: 4
objectives: Build the four Bell states and a GHZ state | Decide whether a two-qubit state is entangled | Use the reduced state and its entropy as an entanglement measure
---
# Entanglement in circuits

## The Bell states

A Hadamard followed by a CX turns $|00\rangle$ into

$$|\Phi^+\rangle = \frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)$$

Starting from the other three basis states gives the other **Bell states**:

| Start | Result |
|---|---|
| \|00⟩ | (\|00⟩ + \|11⟩)/√2 |
| \|01⟩ | (\|01⟩ + \|10⟩)/√2 |
| \|10⟩ | (\|00⟩ − \|11⟩)/√2 |
| \|11⟩ | (\|01⟩ − \|10⟩)/√2 |

[Try it: the Bell pair](qs:circuit?n=2&gates=H:0;CX:0,1&inspector=1)

## What makes a state entangled

A two-qubit state is a **product state** if it can be written as $|a\rangle\otimes|b\rangle$; otherwise it is **entangled**. For $|\psi\rangle = c_{00}|00\rangle + c_{01}|01\rangle + c_{10}|10\rangle + c_{11}|11\rangle$ there is a quick test:

$$|\psi\rangle \text{ is a product state} \Leftrightarrow c_{00}c_{11} - c_{01}c_{10} = 0$$

For $|\Phi^+\rangle$, $c_{00}c_{11} = \frac{1}{2}$ while $c_{01}c_{10} = 0$, so it is entangled.

## Measuring entanglement with the reduced state

Ignoring q1 leaves q0 in a **reduced density matrix** $\rho_0$. For a product state, $\rho_0$ is pure; for an entangled state it is mixed. The **entanglement entropy**

$$S = -\mathrm{Tr}\,\rho_0 \log_2 \rho_0$$

is 0 for a product state and 1 bit for a Bell state, the maximum for one qubit. The State Inspector's **Reduced state** tab shows $\rho$, its purity and $S$.

## GHZ states

Adding a second CX spreads the entanglement to a third qubit:

$$|GHZ\rangle = \frac{1}{\sqrt{2}}(|000\rangle + |111\rangle)$$

Every single qubit of a GHZ state has entropy 1 bit, and so does every pair. Measuring any one qubit fixes the other two.

[Try it: GHZ with the State Inspector](qs:example/GHZ?inspector=1)

## Check your understanding

```quiz
Q: Is (|00⟩ + |01⟩)/√2 entangled?
- Yes
* No, it is |0⟩ ⊗ |+⟩
E: c00·c11 − c01·c10 = 0 − 0 = 0. The state factors as |0⟩ ⊗ (|0⟩ + |1⟩)/√2.
```

```quiz
Q: What is the entanglement entropy of one qubit of a Bell pair?
- 0 bits
- ½ bit
* 1 bit
- 2 bits
E: Its reduced state is I/2, maximally mixed, with entropy 1 bit.
```

## Summary

- H then CX creates a Bell state; different inputs give the four Bell states.
- A state is entangled when it is not a product; for two qubits, c00·c11 − c01·c10 ≠ 0.
- The reduced state's entropy measures entanglement: 0 for product states, 1 bit for Bell states.
