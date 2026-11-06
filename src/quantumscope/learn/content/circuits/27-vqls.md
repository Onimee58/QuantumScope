---
title: The variational quantum linear solver
area: circuits
kind: lecture
order: 27
objectives: Write a linear system as a quantum state problem | Explain the VQLS cost and why its minimum is the solution | Explain how the condition number affects the solve
math: 04-hermitian-and-unitary, 10-pauli-algebra, 12-gradients-and-optimization
---
# The variational quantum linear solver

Many problems in science and engineering come down to a **linear system** $A x = b$. Quantum algorithms approach it by preparing a state proportional to the solution, $|x\rangle \propto A^{-1}|b\rangle$. The famous HHL algorithm (Harrow, Hassidim and Lloyd, 2009) needs deep circuits; the **variational quantum linear solver** (VQLS; Bravo-Prieto et al., 2023) uses a short parameterized circuit and a classical optimizer instead.

## The idea

A parameterized circuit prepares $|x(\theta)\rangle$. The goal is to make $A|x\rangle$ point along $|b\rangle$: then $|x\rangle$ is the normalized solution. QuantumScope uses the cost

$$C(\theta) = \langle x(\theta)|\, A^\dagger (I - |b\rangle\langle b|)\, A\, |x(\theta)\rangle$$

The operator in the middle is Hermitian and never negative, and $C = 0$ exactly when $A|x\rangle$ has no part orthogonal to $|b\rangle$, that is, at the solution (for an invertible $A$). So minimizing $C$ is a VQE-style problem: QuantumScope writes the operator as a Pauli sum and uses it as the circuit's observable, and **Optimize**, the landscape and **Best of N** work as for VQE.

## The systems

In **Algorithms → Variational quantum linear solver**, the matrix $A$ is a sum of Pauli terms, as in the original paper:

$$A = 1 + 0.2\, X_0 Z_1 + 0.2\, X_0, \qquad |b\rangle = |{+}{+}{+}\rangle$$

You can also enter your own $A$ on 1 to 3 qubits, with $|b\rangle$ = |0…0⟩, |+…+⟩ or |1…1⟩. QuantumScope rejects a matrix that is not invertible, since then $A x = b$ has no unique solution. **Show the solution** compares the circuit's amplitudes with the classical solution $A^{-1}b$ as you optimize.

## The condition number

How hard a system is depends on its **condition number** $\kappa = \sigma_{\max}/\sigma_{\min}$, the ratio of the largest to the smallest singular value of $A$. The standard system has $\kappa \approx 2.3$; the worse-conditioned one, with 0.45 instead of 0.2, has $\kappa = 19$. Its cost landscape is flatter near the solution, and the optimizer needs about twice as many steps. For real VQLS on hardware, the number of measurements also grows with $\kappa$.

## On hardware

A quantum computer cannot read $C$ directly. VQLS estimates the terms with **Hadamard tests**: circuits with one extra qubit that controls the Pauli terms of $A$. QuantumScope computes $C$ exactly instead, to show the method itself clearly.

[Try it: solve a 1-qubit system with VQLS](qs:algorithm/vqls?problem=single&layers=1)

## Check your understanding

```quiz
Q: Why is the minimum of the VQLS cost exactly the solution?
* C = 0 only when A|x⟩ points along |b⟩, which for an invertible A means |x⟩ ∝ A⁻¹|b⟩
- Because the optimizer always finds the global minimum
- Because A is unitary
E: The cost measures the part of A|x⟩ orthogonal to |b⟩; it vanishes only when A|x⟩ ∝ |b⟩.
```

```quiz
Q: A system has condition number 19 instead of 2.3. What changes?
- Nothing: the solution is exact either way
* The cost landscape is flatter, so the solve takes more optimizer steps (and, on hardware, more measurements)
- The system has no solution
E: A large condition number means A nearly loses a direction, which makes the solution harder to pin down.
```

## Summary

- VQLS prepares $|x\rangle \propto A^{-1}|b\rangle$ with a parameterized circuit.
- The cost $\langle x| A^\dagger(I - |b\rangle\langle b|)A |x\rangle$ is 0 exactly at the solution.
- The condition number $\kappa$ measures how hard the system is.
