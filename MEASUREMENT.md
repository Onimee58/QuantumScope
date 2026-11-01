# Mid-circuit measurement, feed-forward and reset

QuantumScope can measure qubits **during** a circuit, store the results in classical bits, and use them later in the same run. These circuits are called *dynamic circuits*.

## The Classical palette

| Item | What it does |
|---|---|
| **M→c** | Measures the qubit at this point and stores the result in a classical bit. q0 uses c0 by default, q1 uses c1, and so on; right-click → **Store result in** to choose c0–c9. |
| **Reset** | Returns the qubit to \|0⟩ at this point, without recording anything. |

**M** (in the Gates palette) is still the **final readout**: it can only go at the end, and its results fill the histogram. **M→c** can go anywhere, and its result can control later gates.

## Classically controlled gates

Right-click a gate and choose **Run only if… → c1 = 1** (or = 0). The gate then shows a **c1=1** badge and runs only in runs where that bit has that value. Within one column, gates act before measurements, so a condition always uses results from earlier columns. Conditions apply to single bits; conditions on whole registers (such as `c = 3`) are planned for a later version.

## Branches

A dynamic circuit is simulated exactly, with no random sampling. Every possible classical record (for example c0c1 = 01) is followed as a separate **branch**, with its probability and the state of the qubits in that branch.

- **The step view** shows the average over all branches, a density matrix, together with each record's probability.
- **The State Inspector's Branches tab** lists every record with its probability, purity and each qubit's Bloch vector. For example, it shows how teleportation's correction makes Bob's qubit agree across all four branches.
- **Shots:** without final M gates, the histogram shows the classical record (c0c1…), sampled from the exact probabilities.

Noise from Settings and the Noise palette works inside every branch. With readout error on, a mid-circuit result may be *recorded* wrongly while the qubit still collapses to the true outcome.

## Examples and the Teleportation experiment

- **Examples → Quantum teleportation:** choose the state to send. The check tests your current circuit on ten inputs (the six standard states plus four random ones), and q2 must equal the input in every branch.
- **Examples → Superdense coding:** choose two bits; the check confirms they arrive with certainty.
- **Quantum Principles → + → Quantum Teleportation:** the same protocol told with Alice, Bob and a classical channel, in five steps, using the same engine.

## Files and OpenQASM

- **`.qscope` files:** circuits with mid-circuit operations are saved as schema version 5. Older versions refuse these files.
- **OpenQASM 2 export:** each classical bit becomes its own one-bit register, `creg m0[1];`, so single-bit conditions are exact: `measure q[0] -> m0[0];`, `if(m1==1) x q[2];`, `reset q[0];`.
- **OpenQASM 2 import:** accepts measurements anywhere, `if` on one-bit registers, and `reset`. Operations are placed in the earliest valid column, and a conditioned gate is always placed after the measurement it depends on.

## What is not available for dynamic circuits

Simplify, Check equivalence and the noisy-success notes compare fixed unitaries, so they explain that they need circuits without measurements, resets or conditions.

## Learn more

- **Lectures:** *Mid-circuit measurement and classical bits*, *Classical control, feed-forward and reset*, *Quantum teleportation*, *Superdense coding*, *The deferred-measurement principle*, and (in Quantum Principles) *Measurement, information and no-cloning*.
- **Labs:** *Measure in the middle*, *Reset by feed-forward*, *Teleport a qubit*, *Send two bits with one qubit*, *Defer the measurement*.
