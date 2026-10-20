# QuantumScope — Quantum Circuit Workspace (v0.2.0)

The application now groups experiments under **Hydrogen**, **Quantum Principles**, and **Quantum Circuits**. Hydrogen contains the Explorer and 2D/3D Dynamics; Quantum Principles contains Double-Slit, Superposition, and Entanglement; Quantum Circuits contains the Gate Circuit Simulator.

## Using the circuit simulator

- **Qubits:** choose 1–10. The simulator holds a `2^n` complex statevector in RAM and evaluates the circuit exactly using NumPy (no quantum hardware, no noise).
- **Edit gates:** select a gate in the gate dropdown and click a circuit cell, or drag the gate from the palette onto the grid. For two-qubit gates (CX, CZ, SWAP), select the second qubit in the top toolbar before placing the gate. Right-click a cell to remove its gate. Use **Clear** to start over or **Bell example** for H→CX.
- **Step through:** move the step slider to inspect the output after each gate. The local Bloch vectors and computational-basis probabilities update for that stage.
- **Bloch displays:** these are fixed-view, three-dimensional *projections* of each qubit's **reduced density matrix**; vectors inside the sphere correctly represent mixed local states (including maximally entangled Bell-pair subsystems). Each label displays the vector length.
- **Measure all:** draw ideal computational-basis outcomes from freshly prepared full circuits. These are simulated samples and do not change the saved circuit.

## OpenQASM support

Import/export uses a **strict subset of OpenQASM 2.0**: `OPENQASM 2.0;`, optional `include "qelib1.inc";`, exactly one `qreg`, one-qubit gates `h x y z s t rx ry rz`, two-qubit gates `cx cz swap`, and ignored barrier statements. Rotations accept simple numeric and `pi` arithmetic. Each imported operation is represented as one sequential column. Measurement directives, classical registers, conditionals, user-defined gates, OpenQASM 3, and other unsupported syntax are **rejected with an explicit error** rather than silently misinterpreted.

The circuit simulator is intended for education and small ideal statevector experiments, not large-scale or noisy quantum-hardware emulation. Qubits are stored in the order `|q0 q1 ...⟩`.
