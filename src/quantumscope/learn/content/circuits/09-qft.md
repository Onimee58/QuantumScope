---
title: The quantum Fourier transform
area: circuits
kind: lecture
order: 9
objectives: State what the QFT does to a basis state | Build the QFT from H, controlled-phase and SWAP gates | Recognize the QFT's phase pattern in the State Inspector
---
# The quantum Fourier transform

## Definition

On $n$ qubits with $N = 2^n$, the **quantum Fourier transform** maps each basis state to an evenly spread superposition whose phases rotate at a rate set by $x$:

$$QFT\,|x\rangle = \frac{1}{\sqrt{N}}\sum_{y=0}^{N-1} e^{2\pi i\,xy/N}\,|y\rangle$$

Here $x$ and $y$ are read as binary numbers with q0 as the most significant bit. Every outcome is equally likely; all the information is in the **phases**.

## The circuit

For each qubit in turn, from q0 down:

1. Apply H.
2. Apply a controlled phase $CP(\pi/2^k)$ from each lower qubit, where $k$ is the distance between them.

Finally, SWAP the qubits to reverse their order. On three qubits this takes 3 H gates, 3 CP gates and 1 SWAP. In general it needs about $n^2/2$ gates, far fewer than the $N^2$ operations of a direct matrix product.

## Seeing the phases

For $|x\rangle = |001\rangle$ on 3 qubits ($x = 1$), the amplitude of $|y\rangle$ has phase $2\pi y/8$: the phases step around the circle in eighths. The State Inspector's color swatches show this as a rainbow. For $x = 2$ they step in quarters, twice as fast.

[Try it: QFT of |001⟩ with the State Inspector](qs:algorithm/qft?n=3&x=1&inverse=no&inspector=1)

The inverse transform QFT† undoes the QFT exactly; it is a key step of phase estimation.

[Try it: QFT followed by QFT†](qs:algorithm/qft?n=3&x=5&inverse=yes&inspector=1)

## Check your understanding

```quiz
Q: After the QFT of a basis state, what is the probability of each outcome?
- It depends on x
* 1/N for every outcome
- 1 for y = x and 0 otherwise
E: Every amplitude has magnitude 1/√N; x only changes the phases.
```

```quiz
Q: Why does the QFT end with SWAP gates?
- To undo the controlled phases
* The H-and-phase stages produce the output with its qubits in reverse order
- They are needed to make the circuit unitary
E: Without the SWAPs, the result is correct but with q0 and q(n−1) exchanged, and so on.
```

## Summary

- The QFT spreads a basis state evenly, encoding x in phases e^{2πixy/N}.
- It uses H, CP(π/2^k) and a final reversal by SWAPs: about n²/2 gates.
- QFT† undoes it; both are blocks in the Algorithms menu.
