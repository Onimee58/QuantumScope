---
title: The Shor code and stabilizers
area: circuits
kind: lecture
order: 20
objectives: Combine the bit-flip and phase-flip codes into Shor's 9-qubit code | Explain why correcting X and Z corrects every single-qubit error | Describe codes by their stabilizers
---
# The Shor code and stabilizers

## Concatenating two codes

Shor's code (1995), the first quantum error-correcting code, nests the two repetition codes: the phase-flip code across three blocks, and the bit-flip code inside each block. One logical qubit uses nine physical qubits:

$$|0_L\rangle = \frac{(|000\rangle + |111\rangle)^{\otimes 3}}{2\sqrt{2}}, \qquad |1_L\rangle = \frac{(|000\rangle - |111\rangle)^{\otimes 3}}{2\sqrt{2}}$$

Within a block, a bit flip is corrected by majority; a phase flip on any qubit flips the sign of its whole block, which the phase-flip code across the blocks corrects.

## Every single-qubit error

Any error on one qubit is a combination $aI + bX + cY + dZ$, and $Y = iXZ$. Measuring the syndrome forces the qubit into one of these possibilities — the error is **discretized** — and correcting X and Z handles each of them. So the Shor code corrects *any* single-qubit error, even a tiny continuous rotation.

In QuantumScope's example, correction is done coherently with Toffoli majority votes instead of measured syndromes, so it fits into nine qubits (measured syndromes would need eight more).

[Try it: the Shor code with a Y error on q4](qs:algorithm/shor_code?logical=%2Bi&error=Y4)

## Stabilizers

A compact way to describe a code is by the operators that leave every code state unchanged — its **stabilizers**. For the bit-flip code they are $Z_0Z_1$ and $Z_1Z_2$: exactly the parities the syndrome measures. For the phase-flip code they are $X_0X_1$ and $X_1X_2$. An error that anticommutes with a stabilizer flips its measured value, which is how the syndrome locates it. Most modern codes, including the surface code, are stabilizer codes.

## Check your understanding

```quiz
Q: Why does correcting X and Z errors also correct Y errors?
* Y = iXZ, so a Y error is an X error and a Z error on the same qubit (up to a global phase)
- Y errors never happen
- The Shor code measures Y separately
E: The bit-flip layer fixes the X part and the phase-flip layer fixes the Z part.
```

```quiz
Q: What are the stabilizers of the 3-qubit bit-flip code?
- X0X1 and X1X2
* Z0Z1 and Z1Z2
- Z0, Z1 and Z2
E: Both code states have even parity on q0q1 and on q1q2; those parity operators are Z0Z1 and Z1Z2.
```

## Summary

- The Shor code nests the phase-flip and bit-flip codes: 9 qubits for 1 logical qubit.
- Measuring a syndrome discretizes errors, so correcting X and Z corrects any single-qubit error.
- Codes are described by stabilizers; the syndrome is the measured value of each stabilizer.
