# QuantumScope 0.2.0 — Workspaces and circuit simulator

## Workspace organization

Three top-level categories: **Hydrogen**, **Quantum Principles**, and **Quantum Circuits**. The Hydrogen group contains Explorer and both Dynamics experiments. Quantum Principles contains Double-Slit, Superposition, and Entanglement. Quantum Circuits hosts the gate simulator. Each nonpermanent experiment opens in a reusable, closable child tab.

## Circuit simulator

- Ideal, exact statevector simulator, currently capped at **10 qubits** to keep interactions responsive.
- Gate palette and drop target grid (H, X, Y, Z, S, T, RX, RY, RZ, CX, CZ, SWAP). Gate placement also works by selecting a gate and clicking a wire cell. Right-click removes it.
- Use the second-qubit selector to specify the target of two-qubit gates. Column order is execution order, and row order breaks ties within the same column.
- Step slider lets you inspect the state after each operation, including each qubit's *reduced* Bloch vector. A vector shorter than 1 indicates a mixed reduced state (which can occur due to entanglement).
- Sampling of the final state for repeated fresh preparations. Ideal model: no noise or real-hardware back end.
- Restricted **OpenQASM 2** import/export. The importer accepts one qreg, qelib1.inc, and listed gates; it rejects measurements, conditionals and unsupported statements rather than silently interpreting them. Imported files are not executed on a quantum processor.
- Bloch vectors reside in a scrolling panel on narrow windows; scientific graphics preserve their aspect ratio during resize.

## Limitations

Do not interpret single-qubit reduced Bloch vectors as a full depiction of multi-qubit entanglement. The basis probability readout and circuit steps complement the reduced-state views.

Run `PYTHONPATH=src python -m pytest -q` from the project directory. Test the drag/drop visuals on both Ubuntu and Windows before publishing installers.
