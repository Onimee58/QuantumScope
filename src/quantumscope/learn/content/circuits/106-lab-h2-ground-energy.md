---
title: "Lab: find H₂'s ground energy"
area: circuits
kind: lab
order: 106
objectives: Run VQE on a molecular Hamiltonian | Compare the result with the exact ground energy
---
# Lab: find H₂'s ground energy

[Open VQE for H₂](qs:algorithm/vqe?problem=h2&layers=1)

```step
title: Look at the setup
text: The circuit has an RY parameter on each qubit before and after a CX, and the observable is H₂'s Hamiltonian. ⟨O⟩ starts well above the exact ground energy, −1.137306 Hartree.
check: parameters >= 4
check: observable
```

```step
title: Optimize
text: Press Optimize in the Parameters panel (BFGS). Watch ⟨H⟩ fall onto the dashed exact minimum; the example's check now passes.
check: reaches 0.001
check: verified
```

```quiz
Q: Why can VQE's ⟨H⟩ never go below −1.137306 Hartree here?
* That is the smallest eigenvalue of H: the variational principle
- The optimizer stops early
- The molecule has only two electrons
E: Every ⟨H⟩ is an upper bound on the ground energy.
```
