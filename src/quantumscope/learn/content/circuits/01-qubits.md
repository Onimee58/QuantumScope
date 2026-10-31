---
title: Qubits, state vectors and bit order
area: circuits
kind: lecture
order: 1
objectives: Write a single-qubit state as a vector | Explain what the amplitudes mean when you measure | Build the state of several qubits with the tensor product | Read basis labels in either bit order
---
# Qubits, state vectors and bit order

## One qubit

A classical bit is either 0 or 1. A **qubit** has two basis states, written $|0\rangle$ and $|1\rangle$, and can be in any **superposition** of them:

$$|\psi\rangle = \alpha|0\rangle + \beta|1\rangle$$

The numbers $\alpha$ and $\beta$ are complex **amplitudes**. As column vectors, the basis states are

$$|0\rangle = \begin{pmatrix}1\\0\end{pmatrix}, \quad |1\rangle = \begin{pmatrix}0\\1\end{pmatrix}, \quad |\psi\rangle = \begin{pmatrix}\alpha\\ \beta\end{pmatrix}$$

## What the amplitudes mean

Measuring the qubit in the computational basis gives 0 with probability $|\alpha|^2$ and 1 with probability $|\beta|^2$ (the **Born rule**). The probabilities must add up to one, so every state is **normalized**:

$$|\alpha|^2 + |\beta|^2 = 1$$

For example, $|+\rangle = \frac{1}{\sqrt{2}}(|0\rangle + |1\rangle)$ gives 0 or 1 with probability ½ each. So does $|-\rangle = \frac{1}{\sqrt{2}}(|0\rangle - |1\rangle)$: the minus sign is a **relative phase**, invisible to this measurement but very visible to interference, as later lectures show.

> Multiplying the whole state by a number of size one, $e^{i\varphi}|\psi\rangle$, changes nothing you can ever measure. This is a **global phase**, and QuantumScope's State Inspector can hide it ("Remove global phase").

[Try it: |+⟩ in the State Inspector](qs:circuit?n=1&gates=H:0&inspector=1)

## Several qubits

Two qubits have four basis states, $|00\rangle, |01\rangle, |10\rangle, |11\rangle$, and a general state is a superposition of all four. In general, $n$ qubits need $2^n$ amplitudes, which is why simulating many qubits on a classical computer quickly becomes expensive.

When the qubits are independent, the joint state is the **tensor product** of the individual states:

$$|a\rangle\otimes|b\rangle = \begin{pmatrix}a_0\\a_1\end{pmatrix}\otimes\begin{pmatrix}b_0\\b_1\end{pmatrix} = \begin{pmatrix}a_0 b_0\\a_0 b_1\\a_1 b_0\\a_1 b_1\end{pmatrix}$$

For example, $|1\rangle\otimes|0\rangle = |10\rangle$. States that *cannot* be written as such a product are **entangled**; you will meet them in "Entanglement in circuits".

## Bit order: which qubit is written first?

A label such as $|10\rangle$ only makes sense once you know which qubit each digit belongs to. QuantumScope, like most textbooks, writes **q0 first (leftmost)**: $|10\rangle$ means q0 is 1 and q1 is 0, and the amplitudes are listed in the order $|00\rangle, |01\rangle, |10\rangle, |11\rangle$.

Some software, including Qiskit, writes **q0 last (rightmost)**. Both describe the same physics; only the labels differ.

| Situation | q0 leftmost (textbook) | q0 rightmost (Qiskit) |
|---|---|---|
| q0 = 1, q1 = 0, q2 = 0 | \|100⟩ | \|001⟩ |
| q0 = 0, q1 = 1, q2 = 1 | \|011⟩ | \|110⟩ |

You can switch QuantumScope's labels in **Settings → Circuits → Bit order in labels**. Algorithm parameters and exported CSV data always list q0 first.

[Try it: X on q0 of three qubits](qs:circuit?n=3&gates=X:0&inspector=1)

## Check your understanding

```quiz
Q: A qubit is in the state (1/2)|0⟩ + (√3/2)|1⟩. What is the probability of measuring 1?
- 1/2
- √3/2
* 3/4
- 1/4
E: The probability is the squared magnitude of the amplitude: (√3/2)² = 3/4. The two probabilities, 1/4 and 3/4, add up to one.
```

```quiz
Q: How many amplitudes does the state of 10 qubits have?
- 10
- 20
- 100
* 1024
E: n qubits have 2ⁿ basis states, so 2¹⁰ = 1024 amplitudes.
```

```quiz
Q: In textbook order (q0 leftmost), which label means "q0 = 0 and q1 = 1"?
* |01⟩
- |10⟩
- |11⟩
- |00⟩
E: The first digit belongs to q0 and the second to q1. In Qiskit order the same state would be written |10⟩.
```

## Summary

- A qubit's state is a normalized vector of two complex amplitudes; the Born rule turns amplitudes into probabilities.
- Global phase is unobservable; relative phase matters.
- $n$ qubits have $2^n$ amplitudes, and independent qubits combine by the tensor product.
- Basis labels need a bit-order convention; QuantumScope uses q0 leftmost unless you choose otherwise.
