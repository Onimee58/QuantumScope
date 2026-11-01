---
title: Quantum teleportation
area: circuits
kind: lecture
order: 14
objectives: Follow the teleportation protocol step by step | Explain the four measurement results and their corrections | Explain why teleportation is neither faster than light nor cloning
---
# Quantum teleportation

## The task

Alice has a qubit in an unknown state $|\psi\rangle = \alpha|0\rangle + \beta|1\rangle$ and wants Bob, far away, to have it. She cannot measure $\alpha$ and $\beta$ — one measurement reveals one bit and destroys the state — and she cannot copy it. Teleportation moves the state using a shared Bell pair and **two classical bits**.

## The protocol

1. Alice (q1) and Bob (q2) share a Bell pair $|\Phi^+\rangle$.
2. Alice applies CX from q0 to q1, then H to q0.
3. Alice measures q0 into c0 and q1 into c1, and sends both bits to Bob.
4. Bob applies X if c1 = 1, then Z if c0 = 1.

Before the measurement, the three-qubit state can be rewritten as

$$\frac{1}{2}\sum_{a,b\,\in\,\{0,1\}} |a\,b\rangle\;X^{b}Z^{a}|\psi\rangle$$

so each of the four results $(a, b)$ leaves Bob with $|\psi\rangle$ rotated by a known Pauli operator, which his correction undoes:

| c0 c1 | Bob's qubit before correcting | Correction |
|---|---|---|
| 00 | $\vert \psi\rangle$ | none |
| 01 | $X\vert \psi\rangle$ | X |
| 10 | $Z\vert \psi\rangle$ | Z |
| 11 | $XZ\vert \psi\rangle$ | X then Z |

[Try it: the Teleportation experiment](qs:open/teleportation)

[Try it: teleportation as a circuit](qs:example/Quantum%20teleportation)

## No faster-than-light signalling

All four results are equally likely, whatever $|\psi\rangle$ is. Until Bob receives the two bits, his qubit is the average of the four rotated states — the maximally mixed state $I/2$ — and carries no information at all. The bits travel at most at the speed of light, so nothing is transmitted faster.

## No cloning

Alice's measurement collapses q0 to $|a\rangle$: her copy is destroyed as Bob's appears. Teleportation moves a state; it never duplicates one, consistent with the no-cloning theorem.

## Check your understanding

```quiz
Q: Alice's measurement gives c0c1 = 01. What must Bob do?
- Nothing
* Apply X
- Apply Z
- Apply X then Z
E: Result 01 leaves Bob with X|ψ⟩, so X restores |ψ⟩.
```

```quiz
Q: Why can't Bob learn anything before the bits arrive?
* All four results are equally likely, so his qubit is the maximally mixed state I/2
- Because his qubit is still |0⟩
- Because Alice's measurement has not happened yet
E: Averaged over the four equally likely results, Bob's qubit is I/2 for every input state.
```

## Summary

- One Bell pair plus two classical bits teleports one qubit state.
- Each of the four results needs its own Pauli correction.
- No signal travels faster than light, and the original is destroyed: no cloning.
