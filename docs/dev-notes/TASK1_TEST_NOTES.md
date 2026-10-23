# QuantumScope v0.3.0 - Circuit Editor Task 1 test build

This build keeps the application version at v0.3.0 and modifies the circuit workspace and a small, pure terminal-measurement helper in the physics module.

Changes:
- Drag-and-drop is the only way to add gates; clicking occupied cells cannot overwrite them.
- Start with two operation columns when empty. Maintain one additional column after the rightmost operation (including M); shrink when deleting operations.
- Disable automatic viewport panning during step changes and editor updates.
- When terminal measurement gates exist, the measured-outcome histogram and shot results show only measured qubits; full quantum state can still be inspected in step view.
- Preserve the fixed-height ten-qubit-capacity canvas, blank unused qubit area, and scrollable workspace from the previous Task 1 test build.

Testing: `PYTHONPATH=src python -m pytest -q` (81 passing tests: 77 original + 4 new).

Manual tests requested:
1. Click occupied gates after selecting a different palette gate: no overwrite. Drag a palette gate onto an empty cell: placement works.
2. Clear circuit: two operation columns. Occupy last column: one more appears. Remove rightmost gate using right-click: trailing columns shrink.
3. Add/delete, run playback, then check circuit no longer jumps right.
4. H q0; CX q0->q1; M q2: measurement histogram shows q2=0 with 100%, while full-state preview shows |000> and |110>.
5. Measure q0 and q1: histogram shows joint outcomes 00 and 11 with roughly 50% each.
6. Confirm page scrolling, pan/zoom and 10-qubit sizing on Windows and supported Ubuntu versions.

Note: Desktop PySide6 interactions must be checked locally; no desktop Qt runtime was available during packaging.
