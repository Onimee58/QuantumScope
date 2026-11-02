---
title: The variational quantum eigensolver
area: circuits
kind: lecture
order: 24
objectives: Explain how VQE finds a ground-state energy | Run VQE for the H₂ molecule | Recognize when a circuit cannot express the ground state
---
# The variational quantum eigensolver

## The idea

Many problems in chemistry and physics ask for the **ground-state energy** $E_0$ of a Hamiltonian $H$ — the smallest eigenvalue. The variational principle says $\langle H \rangle \geq E_0$ for every state, so:

1. Prepare a state with a parameterized circuit (the **ansatz**).
2. Measure $\langle H \rangle$.
3. Let a classical optimizer adjust the parameters to lower it, and repeat.

The quantum computer prepares states that may be hard to describe classically; the classical computer steers. VQE was introduced by Peruzzo and colleagues in 2014.

## H₂

QuantumScope's VQE example includes the hydrogen molecule at a bond length of 0.735 Å, reduced to two qubits. Its exact ground energy is

$$E_0 = -1.137306 \text{ Hartree}$$

and one layer of RY rotations with a CX already reaches it.

[Try it: VQE for H₂ — press Optimize](qs:algorithm/vqe?problem=h2&layers=1)

## Expressibility

The ansatz decides which states can be reached. For a 3-spin Heisenberg chain ($E_0 = -4$), one entangling layer gets no lower than $-(1 + 2\sqrt{2}) \approx -3.83$, however well it is optimized; two layers reach −4 exactly. When the optimizer stops above the exact value, the circuit may simply be unable to represent the ground state.

[Try it: the Heisenberg chain with one layer](qs:algorithm/vqe?problem=heisenberg-3&layers=1)

## Check your understanding

```quiz
Q: VQE reports ⟨H⟩ = −1.10 for H₂. What do you know about the true ground energy?
* It is at most −1.10
- It is exactly −1.10
- It is at least −1.10
E: By the variational principle every ⟨H⟩ is an upper bound on E₀.
```

```quiz
Q: The optimizer converges 0.17 above the exact energy. What is a sensible next step?
- Run the same optimizer longer
* Add layers to the ansatz, so it can represent more states
- Lower the exact energy
E: If the circuit cannot represent the ground state, no optimizer can reach it.
```

## Summary

- VQE lowers ⟨H⟩ over a parameterized circuit; every value is an upper bound on E₀.
- H₂ at 0.735 Å: E₀ = −1.137306 Hartree, reached with one layer.
- Too simple an ansatz stops above E₀: expressibility matters.
