---
title: Entanglement and Bell states
area: principles
kind: lecture
order: 4
objectives: Describe the spin singlet and its correlations | State what a Bell inequality tests | Explain why entanglement cannot send signals
---
# Entanglement and Bell states

## The singlet

Two spin-½ particles can share the **singlet** state

$$|\Psi^-\rangle = \frac{1}{\sqrt{2}}(|\uparrow\downarrow\rangle - |\downarrow\uparrow\rangle)$$

Measured along the same axis — any axis — the two always give opposite results. Each result on its own is completely random.

[Try it: entangled electron spins](qs:open/entanglement)

## Correlations at different angles

If the two spins are measured along directions at an angle $\alpha$ to each other, the average product of the results ($\pm 1$ each) is

$$E(\alpha) = -\cos\alpha$$

## Bell's inequality

Any theory where each particle carries pre-set answers ("local hidden variables") obeys the CHSH inequality, which combines four correlations:

$$|E(a,b) - E(a,b') + E(a',b) + E(a',b')| \leq 2$$

For the singlet, quantum mechanics predicts up to $2\sqrt{2} \approx 2.83$ for suitable angles, and experiments agree. No pre-set answers can explain entanglement.

## No signalling

Measuring one particle does not change the other's statistics: on its own, each particle is maximally mixed whatever is done to its partner. The correlation only appears when the two lists of results are compared, which needs ordinary communication. Entanglement cannot send messages.

[Try it: a Bell pair in the State Inspector](qs:circuit?n=2&gates=X:1;H:0;CX:0,1;Z:0&inspector=1)

## Check your understanding

```quiz
Q: For the singlet, both spins are measured along the same axis. What is the correlation E?
* −1: always opposite
- 0: uncorrelated
- +1: always equal
E: E(0°) = −cos 0 = −1.
```

```quiz
Q: What does a CHSH value of 2.7 tell you?
- The particles exchanged a signal
* No local hidden-variable model can explain the results
- The measurement was faulty
E: Local hidden variables obey |S| ≤ 2; quantum entanglement allows up to 2√2.
```

## Summary

- The singlet gives perfectly opposite results along any common axis.
- Correlations follow −cos α; Bell inequalities show no local hidden variables can reproduce them.
- Entanglement creates correlations, not communication.
