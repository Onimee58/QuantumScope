---
title: Measurement and the Born rule
area: principles
kind: lecture
order: 2
objectives: Compute measurement probabilities along any axis | Describe the state after a measurement | Explain why repeated measurements are needed to learn a state
---
# Measurement and the Born rule

## The Born rule

Measuring a state $|\psi\rangle$ in a basis $\{|b\rangle\}$ gives outcome $b$ with probability

$$P(b) = |\langle b|\psi\rangle|^2$$

and leaves the system in $|b\rangle$. The probabilities add up to one because the state is normalized.

## Measuring along any axis

Measuring a spin along a direction $\hat n$ gives "up" with probability

$$P(\uparrow_{\hat n}) = \frac{1 + \vec r\cdot\hat n}{2}$$

where $\vec r$ is the Bloch vector. A state pointing along $\hat n$ is always "up"; one pointing the opposite way is always "down"; one at right angles is 50:50.

[Try it: measure spin along different axes](qs:open/superposition)

## Collapse and repetition

After the measurement the state *is* the outcome, so measuring again along the same axis repeats the result. The original amplitudes cannot be read from a single measurement; they are estimated by preparing the same state many times — the shots in a circuit simulation.

## Measuring in other bases with gates

Circuits measure in the computational ($z$) basis. To measure along $x$, apply H first; to measure along $y$, apply S† and then H. Gates rotate the state so that the axis you care about lines up with $z$.

[Try it: |+⟩ is certain along x](qs:circuit?n=1&gates=H:0;H:0&inspector=1)

## Check your understanding

```quiz
Q: A spin points along +x. You measure along +z. What is P(up)?
- 0
* 1/2
- 1
E: r·n = 0 for perpendicular directions, so P = (1 + 0)/2 = 1/2.
```

```quiz
Q: How do you measure a qubit along x in a circuit?
* Apply H, then measure
- Apply X, then measure
- Measure twice
E: H swaps the x and z axes, so the x-basis states |+⟩ and |−⟩ become |0⟩ and |1⟩.
```

## Summary

- P(b) = |⟨b|ψ⟩|²; afterwards the state is |b⟩.
- Along an axis n̂, P(up) = (1 + r·n̂)/2.
- One measurement reveals one outcome; probabilities need many repetitions.
- Gates before measurement select the measurement basis.
