---
title: Mid-circuit measurement and classical bits
area: circuits
kind: lecture
order: 12
objectives: Measure a qubit in the middle of a circuit and store the result | Describe the branches a measurement creates | Explain why the averaged state is a density matrix
---
# Mid-circuit measurement and classical bits

## Two kinds of measurement

So far, measurement came at the very end: the **M** gates read out the final state. Many protocols need more: they measure *during* the circuit and use the result later. QuantumScope's **M→c** (in the Classical palette) measures a qubit at any point and stores the result in a **classical bit** c0, c1, …

| | M | M→c |
|---|---|---|
| Where | at the end only | anywhere |
| Result | the final readout (histogram) | stored in a classical bit for later use |
| Afterwards | nothing | the circuit continues with the collapsed qubit |

## Branches

Measuring q0 of $\alpha|0\rangle + \beta|1\rangle$ gives 0 with probability $|\alpha|^2$ and 1 with probability $|\beta|^2$, and the qubit collapses to the outcome. A circuit with mid-circuit measurements therefore splits into **branches**, one per possible record of the classical bits:

$$\rho \rightarrow \sum_{m} p_m\,\rho_m, \qquad p_m = \mathrm{Tr}(P_m\,\rho\,P_m), \quad \rho_m = \frac{P_m\,\rho\,P_m}{p_m}$$

where $P_0 = |0\rangle\langle 0|$ and $P_1 = |1\rangle\langle 1|$ act on the measured qubit. QuantumScope follows every branch exactly — the State Inspector's **Branches** tab lists each record, its probability, and the state in that branch.

## The averaged state

Someone who does not look at the classical bits describes the system by the average over the branches, $\sum_m p_m \rho_m$. Measuring and *forgetting* the result is a channel: it removes the coherences between $|0\rangle$ and $|1\rangle$ of the measured qubit — exactly phase damping with $\lambda = 1$. That is why a circuit with mid-circuit measurements is shown as a mixed state.

[Try it: a Bell pair with q0 measured mid-circuit](qs:circuit?n=2&gates=H:0;CX:0,1&measures=0:2:0&inspector=1)

In the Branches tab, the two records each have probability ½, and in each branch q1 has collapsed to the same value as q0: the measurement on q0 fixed q1 too.

## Check your understanding

```quiz
Q: q0 is in |+⟩ and is measured mid-circuit into c0. How many branches are there afterwards?
- 1
* 2
- 4
E: The result is 0 or 1, each with probability ½: two classical records, two branches.
```

```quiz
Q: What is the averaged state of a |+⟩ qubit after it is measured and the result is ignored?
- |+⟩
- |0⟩
* The maximally mixed state I/2
E: Each outcome has probability ½, and averaging |0⟩⟨0| and |1⟩⟨1| gives I/2: the coherence is gone.
```

## Summary

- M→c measures mid-circuit and stores the result in a classical bit; M remains the final readout.
- Each possible classical record is a branch with its own probability and state.
- Averaging over unread results gives a density matrix: measurement acts like complete dephasing.
