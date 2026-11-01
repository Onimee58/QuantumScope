---
title: The deferred-measurement principle
area: circuits
kind: lecture
order: 16
objectives: State the deferred-measurement principle | Rewrite feed-forward with quantum controls | Judge when mid-circuit measurement is really needed
---
# The deferred-measurement principle

## The principle

A measurement followed by a gate controlled by its result has exactly the same effect as a **quantum** controlled gate followed by the measurement:

$$\text{measure } q_a \text{ then (if } c = 1\text{) } U \text{ on } q_b \quad\equiv\quad CU_{a \rightarrow b} \text{ then measure } q_a$$

Measurements can therefore always be moved to the end of a circuit, replacing classical control by quantum control.

## Teleportation without feed-forward

Replace Bob's corrections "X if c1 = 1" and "Z if c0 = 1" by a CX from q1 to q2 and a CZ from q0 to q2. No measurement is needed mid-circuit at all, and q2 still ends in the input state — although now Alice's and Bob's qubits stay entangled until the final measurement.

[Try it: teleportation with quantum controls](qs:circuit?n=3&gates=H:1;CX:1,2;CX:0,1;H:0;CX:1,2;CZ:0,2&states=%2Bi,0,0&inspector=1)

## What the principle does — and does not — say

- **It does:** any circuit's final measurement statistics can be produced with all measurements at the end. Hardware without fast feed-forward can still run such algorithms.
- **It does not** say feed-forward is useless. The deferred version needs the measured qubits to stay coherent until the end, and it cannot *reuse* a qubit after measuring and resetting it. In teleportation it also needs Alice's and Bob's qubits to interact directly — impossible if they are far apart. Error correction relies on genuine mid-circuit measurement for the same reasons.

## Check your understanding

```quiz
Q: By the deferred-measurement principle, "measure q0, then X on q1 if the result is 1" equals …
- X on q1, then measure q0
* CX from q0 to q1, then measure q0
- Measure q1, then X on q0
E: The classical control becomes a quantum control from the qubit that would have been measured.
```

```quiz
Q: Why is real teleportation still done with mid-circuit measurement?
- The deferred version gives a different result
* The deferred version needs a direct quantum interaction between Alice's and Bob's distant qubits
- QuantumScope cannot simulate CZ
E: The CX and CZ would have to act across the distance; classical bits can travel instead.
```

## Summary

- Measure-then-control equals control-then-measure.
- All measurements can be moved to the end, at the cost of keeping qubits coherent longer.
- Mid-circuit measurement remains essential for qubit reuse, distributed protocols and error correction.
