---
title: "Circuit cost: depth, T-count and Clifford gates"
area: circuits
kind: lecture
order: 10
objectives: Distinguish gate count, depth and minimum depth | Explain why T gates are expensive in fault-tolerant computing | Identify Clifford gates
---
# Circuit cost: depth, T-count and Clifford gates

## Counting gates

The simplest cost is the number of gates, with two-qubit gates usually weighted more heavily: on real hardware they are slower and noisier than single-qubit gates.

## Depth

**Depth** counts layers: gates on different qubits can run at the same time. QuantumScope reports two depths in the State Inspector's Circuit tab:

- **Drawn depth:** the occupied columns, as you laid out the circuit.
- **Minimum depth:** the fewest layers if every gate ran as early as possible.

A large gap means the drawing spreads out gates that could run in parallel. Depth matters because qubits lose their quantum information over time, so shallower circuits suffer less noise.

## Clifford gates and the T gate

**Clifford gates** map Pauli operators to Pauli operators. They include H, S, X, Y, Z, CX, CZ and SWAP. Circuits made only of Clifford gates can be simulated efficiently on a classical computer, so they cannot give a quantum speed-up on their own.

Adding the **T gate** ($\pi/4$ phase) makes the gate set universal. In error-corrected (fault-tolerant) computers, T gates are by far the most expensive to implement, so the **T-count** — the number of T and T† gates — is a standard cost measure. A Toffoli needs 7 T gates in its standard decomposition.

[Try it: Grover's circuit statistics](qs:algorithm/grover?n=3&marked=101&iterations=-1&inspector=1)

Open the Circuit tab to see gate counts, depths and Clifford counts. Collapsed blocks never hide their real gates in these statistics.

## Making circuits cheaper

**Tools → Simplify circuit** removes gates that cancel (such as H·H or S·S†) and merges consecutive rotations, verifying that the circuit's unitary is unchanged.

## Check your understanding

```quiz
Q: Which gate is NOT a Clifford gate?
- H
- S
- CX
* T
E: T is a π/4 phase; it maps X to a combination that is not a Pauli operator. It makes the gate set universal.
```

```quiz
Q: Four single-qubit gates act on four different qubits in four different columns. What is the minimum depth?
* 1
- 2
- 4
E: They act on different qubits, so they can all run in the same layer.
```

## Summary

- Costs include gate counts, two-qubit gate counts and depth; minimum depth packs parallel gates.
- Clifford circuits are classically simulable; T gates add universality and dominate fault-tolerant cost.
- Simplify removes redundant gates without changing the unitary.
