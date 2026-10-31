---
title: Multi-qubit gates and tensor products
area: circuits
kind: lecture
order: 3
objectives: Apply a single-qubit gate inside a larger register | Read the matrices of CX, CZ, SWAP and CP | Explain why a controlled gate is not a product of two single-qubit gates
---
# Multi-qubit gates and tensor products

## A single-qubit gate in a bigger register

On two qubits, applying $H$ to q0 and nothing to q1 is the $4\times 4$ matrix $H\otimes I$. With q0 written first, the tensor product places a copy of the second factor in each entry of the first:

$$H\otimes I = \frac{1}{\sqrt{2}}\begin{pmatrix}1 & 0 & 1 & 0\\ 0 & 1 & 0 & 1\\ 1 & 0 & -1 & 0\\ 0 & 1 & 0 & -1\end{pmatrix}$$

Gates on different qubits in the same column act at the same time and their order does not matter: $(A\otimes I)(I\otimes B) = A\otimes B$.

## Controlled gates

A **controlled** gate applies an operation to a target only when the control is $|1\rangle$. The controlled-NOT, with control q0 and target q1, is

$$CX = \begin{pmatrix}1 & 0 & 0 & 0\\ 0 & 1 & 0 & 0\\ 0 & 0 & 0 & 1\\ 0 & 0 & 1 & 0\end{pmatrix}$$

It maps $|10\rangle \to |11\rangle$ and $|11\rangle \to |10\rangle$ and leaves the other basis states alone: classically, the target becomes target ⊕ control.

No matrix of the form $A\otimes B$ equals CX, because what happens to q1 depends on q0. That dependence is exactly how two-qubit gates create entanglement.

[Try it: CX in the Gate Explorer](qs:gate/CX)

## Phase-type two-qubit gates

$$CZ = \mathrm{diag}(1, 1, 1, -1), \quad CP(\lambda) = \mathrm{diag}(1, 1, 1, e^{i\lambda})$$

Both add a phase only to $|11\rangle$, so it does not matter which qubit you call the control: they are **symmetric**. CZ is CP(π). These gates are the building blocks of the quantum Fourier transform.

A useful identity links the two families: $(I\otimes H)\,CX\,(I\otimes H) = CZ$. Hadamards on the target turn a bit flip into a phase flip.

[Try it: CZ between two |+⟩ qubits](qs:circuit?n=2&gates=CZ:0,1&states=%2B,%2B&inspector=1)

## SWAP and three-qubit gates

SWAP exchanges two qubits: $|01\rangle \leftrightarrow |10\rangle$. It can be built from three CX gates with alternating directions.

On three qubits, the **Toffoli** gate CCX flips the target when both controls are 1, and the **Fredkin** gate CSWAP swaps two qubits when the control is 1. Both are reversible versions of classical logic, as the lecture on reversible logic shows.

## Check your understanding

```quiz
Q: What does CX (control q0, target q1) do to |10⟩?
- Leaves it unchanged
* Changes it to |11⟩
- Changes it to |01⟩
- Multiplies it by −1
E: q0 is 1, so the target q1 is flipped from 0 to 1.
```

```quiz
Q: Why is CZ called symmetric?
* It only adds a phase to |11⟩, which treats both qubits the same way
- It is its own inverse
- Its matrix has only real entries
E: Swapping the roles of control and target leaves diag(1, 1, 1, −1) unchanged. Being its own inverse is true too, but that is a different property.
```

## Summary

- A gate on some qubits of a register is a tensor product with identities on the others.
- Controlled gates act on a target depending on a control and cannot be written as a product of single-qubit gates.
- CZ and CP add a phase to |11⟩ and are symmetric; SWAP, CCX and CSWAP complete the gate set.
