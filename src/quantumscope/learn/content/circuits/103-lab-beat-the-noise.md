---
title: "Lab: beat the noise"
area: circuits
kind: lab
order: 103
objectives: Measure a code's logical error rate | See what each correction contributes
---
# Lab: beat the noise

Every data qubit now suffers a random bit flip with probability $p$.

[Open the bit-flip code with random errors (p = 0.1)](qs:algorithm/bit_flip_code?logical=0&error=random&p=0.1)

```step
title: Look at the noisy code
text: The data qubits each have a dashed noise box. Press Plot logical error rate in the verification panel: the code's curve lies far below the unprotected line. At p = 0.1 it fails 2.8% of the time instead of 10%.
check: noise bit_flip
check: measures >= 2
check: conditions = 3
```

```step
title: Remove a correction
text: Delete the correction gate on q1 (the X with c0c1=11) and plot again. The curve rises: errors on q1 are no longer fixed.
check: conditions = 2
```

```step
title: Restore it
text: Use Undo to bring the correction back, and plot once more.
check: conditions = 3
```

```quiz
Q: At p = 0.1, how much less often does the full code fail than an unprotected qubit?
- About 1.2 times
* About 3.6 times
- About 10 times
E: 0.1 / 0.028 ≈ 3.6, since the code fails with probability 3p² − 2p³ = 0.028.
```
