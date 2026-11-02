# Parameterized circuits, VQE and QAOA

## Parameters

- **Making an angle a parameter:** double-click a rotation gate (RX, RY, RZ, P, CP or U) and type a **parameter name** as its angle.
  - A new name creates the parameter at the gate's current angle, so the circuit doesn't change.
  - **Greek letters** are typed as in LaTeX: `\theta` → θ, `\gamma0` → γ0, `\beta` → β. Plain names (`a`, `angle1`, `theta`) stay as typed, and `pi` is always the number π.
  - **Factors** share one parameter among gates: `2*\gamma` and `-\beta` become 2·γ and −β.
- **A bound gate shows its parameter** under its name (for example RY θ). Typing a plain number unbinds it again.
- **The Parameters panel** (under the circuit; it appears when used, or with the **Parameters** button) has a slider and an exact value for each parameter, how many gates use it, and **Delete**. Deleting a parameter keeps its gates at their current angles.
- **Undo:** one slider drag is one undo step.

## Observables

The **Observable** box takes a sum of Pauli terms, such as `Z0 Z1 + 0.5 X0 - 0.3`.

| Term | Meaning |
|---|---|
| `Zk` | +1 if qubit k is 0, −1 if it is 1 |
| `Z0 Z1` | +1 when q0 and q1 agree, −1 when they differ |
| `Xk` | +1 for \|+⟩, −1 for \|−⟩ |

- **What the panel shows:** **⟨O⟩** for the final state (with noise and mid-circuit measurements taken into account), and the **exact lowest possible value**, found by diagonalizing the observable.
- **Examples…** offers ready-made observables, explained in plain words.

## Optimize

| Method | Uses | Notes |
|---|---|---|
| **BFGS** (default) | exact **parameter-shift** gradients | few steps |
| **Gradient descent** | parameter-shift gradients, with a backtracking line search | never goes uphill; can crawl on plateaus |
| **COBYLA**, **Nelder–Mead** | only ⟨O⟩ values | no gradients; only improving steps are shown |

- **The optimization window** plots ⟨O⟩ against the steps, with the exact minimum dashed, and reports both the **steps** and the **circuit evaluations** used. It has a **Stop** button, and the whole optimization is one undo step.
- **Afterwards,** parameters are wrapped back into −π…π wherever that provably changes nothing (whole-number factors).
- **If no step lowers ⟨O⟩,** the window says so: the parameters are already at a minimum of what this circuit can do.

**Landscape…** draws ⟨O⟩ over one parameter (a curve) or two (a color map), with the other parameters held at their current values. The current point and the last optimization path are drawn on top.

## The variational quantum eigensolver (Algorithms → VQE)

- **Problems:** the H₂ molecule (two qubits, 0.735 Å; exact ground energy −1.137306 Hartree), transverse-field Ising chains with 2–4 spins, and Heisenberg chains with 2–3 spins.
- **The ansatz:** layers of RY gates, each with its own parameter, joined by CX chains (1–3 entangling layers).
- **The check** passes once ⟨H⟩ is within 0.001 of the exact ground energy. If the optimizer stops above it, the circuit may be unable to represent the ground state: add layers.

## QAOA for MaxCut (Algorithms → QAOA for MaxCut)

- **Graphs:** a square, a square with a diagonal, a pentagon, a hexagon, and a triangular prism.
- **The circuit:** 1–3 layers, each with a cost step (CX, RZ(−γ), CX on every edge) and a mixer (RX(2β) on every node).
- **The observable** is minus the number of cut edges.
- **Show the graph** (in the verification panel) colors the nodes by the likeliest measured result, highlights the cut edges, and shows the probability of each cut size. It updates live.
- **The check** passes when the likeliest result is a maximum cut, found by brute force.

## Files and exports

- **`.qscope` files:** parameters, bindings and the observable are saved as an optional field. Gates always store their current angles, so older versions open the circuit at the current values.
- **OpenQASM 2** has no symbols, so the parameters, bindings and observable are written as comments.

## Learn more

- **Lectures:** *Observables and expectation values* (Quantum Principles); *Parameterized circuits*; *The parameter-shift rule*; *The variational quantum eigensolver*; *Optimizers, landscapes and plateaus*; *QAOA and MaxCut*.
- **Labs:** *Tune a circuit by hand*; *Find H₂'s ground energy*; *Not enough layers*; *Cut a graph with QAOA*.
