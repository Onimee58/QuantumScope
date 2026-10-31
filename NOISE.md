# Noise and mixed states

QuantumScope can simulate circuits with noise. It switches from the exact statevector to a **density matrix** ρ, which can describe the mixed states noise creates. With no noise present, nothing changes: the circuit is simulated exactly, as before.

## Two ways to add noise

**1. Global noise: the Noise button.** Noise follows *every* gate. The settings are:

| Setting | What it means |
|---|---|
| Single-qubit gate error | depolarizing probability after each 1-qubit gate |
| Two-qubit gate error | depolarizing probability after each multi-qubit gate (2-qubit depolarizing on 2-qubit gates; on 3-qubit gates, 1-qubit depolarizing on each of their qubits) |
| Amplitude damping γ | energy relaxation (T₁-like) on each qubit a gate acts on |
| Dephasing λ | phase loss (T₂-like) on each qubit a gate acts on |
| Readout error | probability that a measured bit is reported wrongly |
| Idle noise | damping and dephasing also act on qubits waiting in a column |

The presets **Ideal**, **Gentle**, **Moderate** and **Very noisy** are illustrative teaching levels, not measurements of any particular device.

**2. Noise elements: the Noise palette.** Drag **Bit flip**, **Phase flip**, **Depolarize**, **Amp. damp** or **Dephase** onto a wire to apply that channel at one point. Noise elements are drawn as orange dashed boxes, so they are never mistaken for gates.
- **Edit:** double-click a box to set its strength.
- **Menu:** right-click it to edit, remove, or open **About this channel…**.

## The Noise Explorer

Double-click a noise channel in the palette to open its Noise Explorer.
- **About this channel:** the channel's equation, its Kraus operators, its exact effect on the Bloch sphere, and the physics behind it.
- **Effect at this strength:** a slider for p, γ or λ, with a live table of where |0⟩, |1⟩, |+⟩ and |+i⟩ end up, and the Kraus matrices with numbers filled in.
- **Try it in the circuit:** loads a one-qubit demonstration circuit.

## What changes when noise is on

- **Results:** the probability bars come from the density matrix, the **Bloch arrows shrink** inside the sphere, and the result line shows **purity** and **fidelity with the ideal state**.
- **Shots:** samples come from the noisy distribution, including readout error on the measured qubits.
- **State Inspector:**
  - the tabs become **Probabilities** (noisy and ideal side by side) and **Density matrix** (ρ for up to 3 qubits, with purity and fidelity);
  - **Reduced state** is computed from the noisy ρ;
  - copying the statevector is disabled, since a mixed state has none.
- **Algorithm checks:** PASS/FAIL still judges the ideal circuit, and a note reports the noisy success (for example "With noise: P(101) = 0.577").

## Limits and files

- Up to 8 qubits, every column is stored for the step slider. Larger noisy circuits are computed at the final column only, taking about 2–3 seconds at 10 qubits.
- Circuits with noise are saved as `.qscope` **schema version 4**. Older QuantumScope versions refuse these files rather than silently ignoring the noise.
- OpenQASM 2 cannot describe noise, so QASM export writes the ideal circuit with a comment saying so.

## Learn more

- **Lectures:** *Density matrices and mixed states* (Quantum Principles) and *Noise and decoherence* (Quantum Circuits).
- **Lab:** *Watch a Bell pair decohere*.
