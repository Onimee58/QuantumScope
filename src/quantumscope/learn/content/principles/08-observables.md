---
title: Observables and expectation values
area: principles
kind: lecture
order: 8
objectives: Read an observable written as a sum of Pauli terms | Compute an expectation value for simple states | State the variational principle
math: 04-hermitian-and-unitary, 05-eigenvalues, 10-pauli-algebra
---
# Observables and expectation values

## A quantity you could measure

An **observable** is a physical quantity — an energy, a magnetization, a parity. In quantum mechanics it is a Hermitian operator, and on qubits every observable can be written as a weighted sum of **Pauli terms**:

| Term | Meaning | Value for \|0⟩ | Value for \|1⟩ |
|---|---|---|---|
| $Z_k$ | is qubit $k$ 0 or 1? | +1 | −1 |
| $Z_0 Z_1$ | do q0 and q1 agree? | +1 if equal | −1 if different |
| $X_k$ | qubit $k$ along $x$ | +1 for \|+⟩ | −1 for \|−⟩ |

For example $Z_0 Z_1 + 0.5\,X_0$ adds "agreement" and half of q0's $x$-value.

## Expectation values

A single measurement gives one of the operator's eigenvalues. Averaged over many measurements of the same state $|\psi\rangle$ the result is the **expectation value**

$$\langle O \rangle = \langle \psi | O | \psi \rangle$$

For $|+\rangle$, measuring $Z$ gives +1 and −1 equally often, so $\langle Z \rangle = 0$, while $\langle X \rangle = 1$. For the Bell state $\frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)$ the two qubits always agree: $\langle Z_0 Z_1 \rangle = 1$.

[Try it: the observable panel (a Bell pair with Z0 Z1)](qs:circuit?n=2&gates=H:0;CX:0,1&observable=Z0%20Z1)

## The lowest possible value

No state can do better than the smallest eigenvalue $E_0$ of $O$:

$$\langle \psi | O | \psi \rangle \geq E_0 \quad \text{for every } |\psi\rangle$$

This **variational principle** is the basis of the variational algorithms in the Circuits lectures: lower ⟨O⟩ as far as possible, and you approach $E_0$. QuantumScope shows the exact $E_0$ next to ⟨O⟩, computed by diagonalizing the observable.

## Check your understanding

```quiz
Q: What is ⟨Z0 Z1⟩ for |01⟩?
- +1
* −1
- 0
E: q0 = 0 and q1 = 1 differ, so Z0 Z1 gives −1 every time.
```

```quiz
Q: Can a state give ⟨O⟩ below the smallest eigenvalue of O?
- Yes, with enough entanglement
* No: the smallest eigenvalue is a lower bound for every state
E: ⟨O⟩ is a weighted average of eigenvalues, so it can never fall below the smallest one.
```

## Summary

- Observables on qubits are weighted sums of Pauli terms.
- ⟨O⟩ is the average of many measurements of the same state.
- The smallest eigenvalue bounds ⟨O⟩ from below: the variational principle.
