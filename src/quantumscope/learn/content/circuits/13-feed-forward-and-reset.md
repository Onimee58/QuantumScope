---
title: Classical control, feed-forward and reset
area: circuits
kind: lecture
order: 13
objectives: Condition a gate on a classical bit | Reset a qubit with measurement and feed-forward | Explain when the order of operations in a column matters
---
# Classical control, feed-forward and reset

## Gates that depend on a measurement

A **classically controlled** gate runs only when a classical bit has a given value — "apply X to q2 if c1 = 1". Using measurement results later in the same run is called **feed-forward**. In QuantumScope, right-click any gate and choose **Run only if… → c1 = 1**; the gate shows a **c1=1** badge.

Within one column, gates act first and measurements after, so a condition always uses results from *earlier* columns.

## Reset by feed-forward

Measuring a qubit and then applying X if the result was 1 leaves it in $|0\rangle$ whatever it was before:

| Measured | Then | Result |
|---|---|---|
| 0 | nothing | \|0⟩ |
| 1 | X | \|0⟩ |

This **active reset** lets a circuit reuse a qubit, for example as a fresh work qubit. QuantumScope's **Reset** element does the same in one step, $\rho \rightarrow |0\rangle\langle 0|$ on that qubit, without recording a bit.

[Try it: reset |+⟩ by measurement and feed-forward](qs:circuit?n=1&gates=X:0&cols=1&states=%2B&measures=0:0:0&conditions=0:1:0:1&inspector=1)

## Why feed-forward is hard on real hardware

The measurement result has to be read, processed classically and used to control a gate while the other qubits wait — and waiting qubits decohere. Fast classical control is one of the engineering challenges of real quantum computers, and one reason the deferred-measurement principle (a later lecture) is useful.

## Check your understanding

```quiz
Q: A qubit is measured into c0, and then X is applied if c0 = 1. What is the final state?
- The same state as before the measurement
* |0⟩, whatever the starting state
- |1⟩
E: Outcome 0 leaves |0⟩; outcome 1 leaves |1⟩, which X turns into |0⟩.
```

```quiz
Q: A conditioned gate and the measurement it depends on are in the same column. What happens?
- The gate uses the new result
* The gate uses the bit's earlier value, because gates act before measurements in a column
- The circuit is rejected
E: Within a column, gates come first; put the conditioned gate in a later column to use the new result.
```

## Summary

- Classically controlled gates run only for a chosen value of a classical bit: feed-forward.
- Measurement plus a conditional X resets any qubit to |0⟩; Reset does it in one step.
- Fast classical control is demanding for real hardware.
