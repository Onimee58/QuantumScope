# Contributing

Please open an issue to discuss larger changes. Keep the numerical physics backend independent of GUI/VTK packages. Add unit tests for changes to physics calculations and describe any approximations or unit conventions. Run `python -m pytest -q` before submitting a pull request. Use descriptive commits and keep individual PRs focused.

## Code layout

- `src/quantumscope/physics/` — simulation, file formats, examples and verification. No Qt.
- `src/quantumscope/editor/` — `CircuitModel`, the circuit editor's state and editing rules (placement, moving, columns, measurements, undo/redo). No Qt.
- `src/quantumscope/gui/` — PySide6 widgets. Widgets translate input into model calls and draw the result; put new editing rules in the model, with unit tests, not in the widget.

GUI checks are opt-in because CI has no display: `QUANTUMSCOPE_GUI_TESTS=1 QT_QPA_PLATFORM=offscreen python -m pytest -q`.
