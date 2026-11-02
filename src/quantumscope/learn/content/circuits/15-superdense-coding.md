---
title: Superdense coding
area: circuits
kind: lecture
order: 15
objectives: Send two classical bits by transmitting one qubit | Decode with a Bell measurement | Compare superdense coding with teleportation
---
# Superdense coding

## Two bits in one qubit

On its own, one qubit can carry at most one bit of classical information (the Holevo bound). With a shared Bell pair, Alice can send **two** bits by transmitting just her one qubit.

## Encoding

Alice and Bob share $|\Phi^+\rangle = \frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)$, Alice holding q0. To send the bits $b_0 b_1$, she applies $X$ if $b_1 = 1$ and $Z$ if $b_0 = 1$ to her qubit:

| Message | Alice applies | Resulting Bell state |
|---|---|---|
| 00 | nothing | $\frac{1}{\sqrt{2}}(\vert 00\rangle + \vert 11\rangle)$ |
| 01 | X | $\frac{1}{\sqrt{2}}(\vert 10\rangle + \vert 01\rangle)$ |
| 10 | Z | $\frac{1}{\sqrt{2}}(\vert 00\rangle - \vert 11\rangle)$ |
| 11 | X, then Z | $\frac{1}{\sqrt{2}}(\vert 01\rangle - \vert 10\rangle)$ (up to a sign) |

The four results are the four Bell states, which are perfectly distinguishable.

## Decoding

Alice sends q0 to Bob. He applies CX from q0 to q1, then H to q0, and measures both: the result is exactly $b_0 b_1$.

[Try it: superdense coding](qs:example/Superdense%20coding)

## Teleportation in reverse

| Protocol | Uses | Sends |
|---|---|---|
| Teleportation | 1 Bell pair + 2 classical bits | 1 qubit state |
| Superdense coding | 1 Bell pair + 1 qubit | 2 classical bits |

Both show that shared entanglement is a resource that can be traded against communication.

## Check your understanding

```quiz
Q: To send 10, what does Alice apply to her qubit?
- X
* Z
- X then Z
E: b0 = 1 means Z, and b1 = 0 means no X.
```

```quiz
Q: Can one qubit without shared entanglement carry two classical bits?
- Yes, using a superposition
* No: at most one bit (the Holevo bound)
E: Superdense coding needs the Bell pair; a lone qubit carries at most one bit.
```

## Summary

- With a shared Bell pair, transmitting one qubit sends two classical bits.
- Alice encodes with I, X, Z or XZ; Bob decodes with CX, H and two measurements.
- Superdense coding and teleportation are mirror images.
