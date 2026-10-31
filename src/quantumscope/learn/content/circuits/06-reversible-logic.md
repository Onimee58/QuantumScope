---
title: Reversible logic
area: circuits
kind: lecture
order: 6
objectives: Explain why quantum gates must be reversible | Compute AND, XOR and copies with Toffoli and CX gates | Use work qubits and uncompute them
---
# Reversible logic

## Why reversibility?

Quantum gates are unitary, so every gate can be undone. Ordinary logic is not like that: from the output of AND you cannot tell whether the input was 00, 01 or 10. To compute such functions on a quantum computer, we keep enough information to run the computation backwards.

## The basic building blocks

| Gate | Inputs → outputs | Classical meaning |
|---|---|---|
| X | a → NOT a | NOT |
| CX | (a, b) → (a, a ⊕ b) | XOR into b; copy a when b = 0 |
| CCX (Toffoli) | (a, b, c) → (a, b, c ⊕ ab) | AND into c when c = 0 |
| CSWAP (Fredkin) | (s, x, y) → swap x, y if s = 1 | a controlled multiplexer |

The Toffoli gate alone is **universal** for reversible logic: any classical function can be computed with Toffolis and extra bits set to 0 or 1.

## A half adder

Adding two bits gives a sum $a\oplus b$ and a carry $ab$:

1. Toffoli with controls a, b writes the carry into a fresh qubit.
2. CX from a to b turns b into the sum $a\oplus b$.

[Try it: the half adder example](qs:example/Half%20adder%20%28a%3D1%2Cb%3D1%29)

## Work qubits and uncomputing

Larger circuits need temporary **work qubits** (ancillas) for intermediate results. Leaving them with junk entangles them with the answer and spoils interference later, so good reversible circuits **uncompute** them: they repeat the steps that wrote the junk, in reverse order, returning the work qubits to $|0\rangle$. QuantumScope's 2-bit comparator does exactly this with q6.

[Try it: the comparator example](qs:example/2-bit%20comparator)

## Check your understanding

```quiz
Q: A Toffoli gate acts on (a, b, c) = (1, 1, 1). What is the output?
- (1, 1, 1)
* (1, 1, 0)
- (0, 0, 1)
E: c becomes c ⊕ ab = 1 ⊕ 1 = 0; the controls are unchanged.
```

```quiz
Q: Why uncompute work qubits?
- To save memory
* So they are not left entangled with the result
- Because gates cannot be applied to them twice
E: Leftover junk entangles the work qubits with the answer, which destroys the interference algorithms rely on.
```

## Summary

- Quantum gates are reversible, so classical logic must keep its inputs.
- CX computes XOR, the Toffoli computes AND, and the Fredkin is a controlled swap.
- Work qubits hold intermediate results and should be uncomputed back to |0⟩.
