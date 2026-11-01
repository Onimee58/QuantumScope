---
title: "Error correction: the phase-flip code"
area: circuits
kind: lecture
order: 18
objectives: Protect a qubit against phase flips by changing basis | Explain why the bit-flip code fails against phase errors
---
# Error correction: the phase-flip code

## A blind spot of the bit-flip code

A Z error on any data qubit of $\alpha|000\rangle + \beta|111\rangle$ gives $\alpha|000\rangle - \beta|111\rangle$: a logical phase flip. The syndrome is 00 — the bit-flip code cannot even see it. Worse, any of the three qubits can cause it, so the code makes phase errors *three times* as likely.

## Change the basis

Z flips $|+\rangle \leftrightarrow |-\rangle$ just as X flips $|0\rangle \leftrightarrow |1\rangle$. So encode in the $|\pm\rangle$ basis: after the two CX gates, apply H to all three qubits,

$$\alpha|0\rangle + \beta|1\rangle \;\rightarrow\; \alpha|{+}{+}{+}\rangle + \beta|{-}{-}{-}\rangle$$

To read the syndrome, apply H to the data qubits, measure the same parities as before, and apply H again. A Z error now shows up exactly like an X error did, and is corrected by a **Z** on the flagged qubit.

[Try it: the phase-flip code with an error on q2](qs:algorithm/phase_flip_code?logical=%2B&error=q2&p=0.1)

## One code per error type

| Code | Corrects | Blind to |
|---|---|---|
| Bit-flip | one X error | Z errors |
| Phase-flip | one Z error | X errors |

Real qubits suffer both — the Shor code combines the two.

[Try it: compare the codes in the Error-correction explorer](qs:open/qec)

## Check your understanding

```quiz
Q: A Z error hits q1 of the bit-flip code α|000⟩ + β|111⟩. What does the syndrome show?
* 00: the error is invisible
- 11
- 10
E: Z leaves the parities unchanged; it only changes the relative sign, a logical phase error.
```

```quiz
Q: How does the phase-flip code correct the qubit it flags?
- With an X gate
* With a Z gate
- With a measurement
E: In the |±⟩ basis the error is a Z, so the correction is a Z on that qubit.
```

## Summary

- Z errors are invisible to the bit-flip code, which even multiplies them by three.
- Hadamards turn the bit-flip code into the phase-flip code, which corrects one Z error.
- Each repetition code handles one error type.
