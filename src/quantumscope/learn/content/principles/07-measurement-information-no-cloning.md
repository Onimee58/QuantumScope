---
title: Measurement, information and no-cloning
area: principles
kind: lecture
order: 7
objectives: Explain what a measurement does to a quantum state | State and prove the no-cloning theorem | Connect no-cloning to teleportation and secure communication
---
# Measurement, information and no-cloning

## Measurement changes what it measures

Measuring a qubit gives a classical result and leaves the qubit in the matching basis state. The information about the original amplitudes is lost: one measurement of $\alpha|0\rangle + \beta|1\rangle$ yields one bit, not $\alpha$ and $\beta$. To estimate them you need many identically prepared copies — which raises the question of whether copies can be made.

## The no-cloning theorem

No device can copy an unknown quantum state. Suppose a unitary $U$ did, for every state: $U|\psi\rangle|0\rangle = |\psi\rangle|\psi\rangle$. For two states $|\psi\rangle$ and $|\varphi\rangle$, inner products are preserved by $U$, so

$$\langle\psi|\varphi\rangle = \langle\psi|\varphi\rangle^2$$

which only holds if $\langle\psi|\varphi\rangle$ is 0 or 1: the states are identical or orthogonal. A copier can work for a set of mutually orthogonal states, such as $|0\rangle$ and $|1\rangle$ (a CX does it), but never for arbitrary states such as $|+\rangle$ as well.

## Consequences

- **No faster-than-light signalling.** If entangled states could be cloned, one could read out a partner's measurement choice instantly; no-cloning prevents it.
- **Teleportation moves, never copies.** Alice's original is destroyed by her measurement as Bob's appears.
- **Secure communication.** In quantum key distribution, an eavesdropper cannot copy the qubits in transit, and measuring them disturbs them detectably.

[Try it: watch the original collapse in the Teleportation experiment](qs:open/teleportation)

## Check your understanding

```quiz
Q: Why does a CX not violate the no-cloning theorem when it copies |0⟩ and |1⟩?
* |0⟩ and |1⟩ are orthogonal; CX does not copy superpositions such as |+⟩
- CX is not unitary
- The theorem only applies to two qubits
E: CX on |+⟩|0⟩ gives a Bell state, not |+⟩|+⟩.
```

```quiz
Q: What does one measurement of a qubit reveal?
- Both amplitudes α and β
* One classical bit, and the state collapses
- Nothing
E: The result is 0 or 1; amplitudes can only be estimated from many copies, which cannot be made from one unknown state.
```

## Summary

- Measurement yields one bit and collapses the state.
- No-cloning: unknown states cannot be copied; only mutually orthogonal sets can.
- No-cloning underlies teleportation's "move, not copy", no-signalling and quantum cryptography.
