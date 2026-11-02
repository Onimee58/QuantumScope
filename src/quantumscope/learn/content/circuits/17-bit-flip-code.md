---
title: "Error correction: the bit-flip code"
area: circuits
kind: lecture
order: 17
objectives: Explain why quantum error correction cannot simply copy qubits | Encode one qubit into three | Detect an error with syndrome measurements without disturbing the encoded state | Correct it with feed-forward on two bits
---
# Error correction: the bit-flip code

## Redundancy, the classical way

To protect a bit against flips, send it three times — 0 as 000, 1 as 111 — and take a majority vote. One flipped copy is outvoted; it takes two flips to fool the vote.

## Why quantum is harder

Three obstacles seem to block the same idea for qubits:

- **No cloning:** $|\psi\rangle$ cannot be copied into $|\psi\rangle|\psi\rangle|\psi\rangle$.
- **Measurement disturbs:** reading the copies to take a vote would collapse a superposition.
- **Errors are continuous:** a qubit can be slightly rotated, not just flipped.

All three are overcome. Instead of copies, we *entangle*; instead of reading the data, we read only **parities**; and measuring the parities turns any small error into either "no error" or a definite flip.

## Encoding

Two CX gates spread one qubit over three:

$$\alpha|0\rangle + \beta|1\rangle \;\rightarrow\; \alpha|000\rangle + \beta|111\rangle$$

This is not three copies of $|\psi\rangle$ — it is one *logical* qubit stored in three physical ones.

## The syndrome

Two **ancilla** qubits measure the parities $q_0 \oplus q_1$ and $q_1 \oplus q_2$ (each with two CX gates), mid-circuit, into c0 and c1. Both terms of the superposition have the same parities, so the measurement reveals only *where* an error is, never $\alpha$ or $\beta$:

| Error | c0 c1 | Correction |
|---|---|---|
| none | 00 | none |
| X on q0 | 10 | X on q0 |
| X on q1 | 11 | X on q1 |
| X on q2 | 01 | X on q2 |

Each correction is a gate conditioned on **both** bits — "X on q1 if c0c1 = 11" — which is why QuantumScope supports conditions on several bits. With single-bit conditions, an error on q1 would be "corrected" on q0 and q2 instead, flipping the logical qubit.

[Try it: the bit-flip code with an error on q1](qs:algorithm/bit_flip_code?logical=1&error=q1&p=0.1)

The qubits are labeled **data** and **syndrome**; in your own designs, click a qubit's label to name it the same way.

## The limit

Two flips give the same syndrome as one flip on the remaining qubit, so the "correction" completes a logical error instead. The code protects against **one** bit flip.

## Check your understanding

```quiz
Q: The syndrome is c0c1 = 01. Which qubit is corrected?
- q0
- q1
* q2
E: Only q2 differs from its neighbour in the second parity (q1 ⊕ q2) and not in the first.
```

```quiz
Q: Why does measuring the syndrome not destroy the superposition α|000⟩ + β|111⟩?
* Both terms have the same parities, so the measurement learns nothing about α and β
- Because the ancillas are measured very quickly
- Because the code uses three qubits
E: A parity measurement only distinguishes error patterns, which affect both terms alike.
```

## Summary

- Encode α|0⟩ + β|1⟩ as α|000⟩ + β|111⟩ — entangled, not copied.
- Parity checks on ancillas reveal the error location without revealing the data.
- Two-bit feed-forward corrects any single bit flip; two flips defeat the code.
