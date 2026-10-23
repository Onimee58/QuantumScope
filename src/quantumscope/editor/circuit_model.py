"""Qt-free model of the circuit editor.

Holds the editable circuit (gates by grid cell, terminal measurements, column
layout), undo/redo, multi-qubit placement, example verification state and
per-column simulation. The GUI widget only translates user input into these
calls and renders the result, so every editing rule here is unit-tested
without a display.

Cells are (row, column). A gate is stored under its anchor cell
(row = the qubit it was placed on, column = its operation column) and
occupies every qubit in Gate.targets within that column.
"""
from dataclasses import dataclass

from quantumscope.physics.circuits import ALL, DUAL, TRIPLE, MAX_QUBITS, Gate, apply_gate, evolution
from quantumscope.physics.circuit_examples import example_circuit, has_specification
from quantumscope.physics.circuit_layout import pack_and_order, validate_columns
from quantumscope.physics.circuit_verification import inspect_basis, verify_example
from quantumscope.physics.initial_states import DEFAULT, InitialState, all_default, defaults, product_state
from quantumscope.physics.state_analysis import analyze_circuit

PARAMETERIZED = ('RX', 'RY', 'RZ', 'P', 'U')
UNDO_LIMIT = 80


class EditorError(ValueError):
    """An edit was rejected; the message is shown to the user as status text."""


@dataclass(frozen=True)
class Simulation:
    occupied_columns: list
    column_states: list   # state before any column, then after each occupied column
    states: list          # state after each gate, from physics.circuits.evolution


def operand_count(name):
    return 3 if name in TRIPLE else 2 if name in DUAL else 1


class CircuitModel:
    def __init__(self, n=3):
        if not 1 <= n <= MAX_QUBITS:
            raise ValueError('Qubit count out of range')
        self.n = n
        self.gates = {}            # (row, col) -> Gate
        self.measurements = {}     # qubit -> terminal measurement column
        self.reserved_columns = 2  # columns kept even when trailing columns are empty
        self.active_example = None
        self.example_ops = None    # example's original gate order, to detect edits
        self.pending = None        # (name, col, operand rows) during multi-qubit placement
        self.initial_states = defaults(n)   # per-qubit starting state, |0⟩ by default
        self.undo_stack = []
        self.redo_stack = []

    # ---- layout ---------------------------------------------------------------
    @property
    def columns(self):
        """Visible columns: always one spare after the last operation (two when empty)."""
        last = max([c for _, c in self.gates] + list(self.measurements.values()), default=-1)
        return max(2, last + 2, self.reserved_columns)

    def ordered(self):
        """Gates in simulation order: by column, then row."""
        return [g for _, g in sorted(self.gates.items(), key=lambda x: (x[0][1], x[0][0]))]

    def layout(self):
        """(gates, columns, measurement column, total columns) for saving."""
        items = sorted(self.gates.items(), key=lambda x: (x[0][1], x[0][0]))
        return ([g for _, g in items], [c for (_, c), _ in items],
                min(self.measurements.values()) if self.measurements else None, self.reserved_columns)

    def operation_at(self, row, col):
        """('gate', key, gate), ('measurement', (row, col), None) or None."""
        for key, gate in self.gates.items():
            if key[1] == col and row in gate.targets:
                return ('gate', key, gate)
        if self.measurements.get(row) == col:
            return ('measurement', (row, col), None)
        return None

    # ---- undo/redo ------------------------------------------------------------
    def _record(self):
        return (self.n, self.reserved_columns, dict(self.gates), dict(self.measurements),
                self.active_example, self.example_ops, tuple(self.initial_states))

    def snapshot(self):
        self.undo_stack.append(self._record())
        self.undo_stack = self.undo_stack[-UNDO_LIMIT:]
        self.redo_stack.clear()

    def _restore(self, record):
        (self.n, self.reserved_columns, gates, measurements,
         self.active_example, self.example_ops, states) = record
        self.gates, self.measurements = dict(gates), dict(measurements)
        self.initial_states = list(states)
        self.pending = None

    def undo(self):
        if not self.undo_stack:
            return False
        self.redo_stack.append(self._record())
        self._restore(self.undo_stack.pop())
        return True

    def redo(self):
        if not self.redo_stack:
            return False
        self.undo_stack.append(self._record())
        self._restore(self.redo_stack.pop())
        return True

    # ---- whole-circuit operations --------------------------------------------
    def clear(self):
        self.snapshot()
        self.active_example = self.example_ops = self.pending = None
        self.gates, self.measurements = {}, {}
        self.reserved_columns = 2
        self.initial_states = defaults(self.n)

    def load_bell(self):
        """The quick 'Bell example' button (not a verified example)."""
        if self.n < 2:
            self.resize(2)
        self.snapshot()
        self.active_example, self.example_ops, self.pending = 'Bell pair', None, None
        self.gates = {(0, 0): Gate('H', (0,)), (0, 1): Gate('CX', (0, 1))}
        self.measurements = {}
        self.initial_states = defaults(self.n)

    def set_circuit(self, n, ops, columns=None, measured=(), measurement_column=None, total_columns=None,
                    initial_states=None):
        """Replace the circuit. Without columns, gates are packed (simulation unchanged).
        initial_states defaults to |0⟩ on every qubit."""
        from quantumscope.physics.circuit_files import validate
        ops = list(ops)
        validate(n, ops)
        if columns is None:
            ops, columns = pack_and_order(n, ops)
        else:
            columns = list(columns)
            validate_columns(ops, columns)
        last = max(columns, default=-1)
        if measurement_column is None or measurement_column <= last:
            measurement_column = last + 1
        states = defaults(n) if initial_states is None else list(initial_states)
        if len(states) != n or not all(isinstance(s, InitialState) for s in states):
            raise ValueError('Need one initial state per qubit')
        self.snapshot()
        self.active_example = self.example_ops = self.pending = None
        self.n = n
        self.gates = {(g.targets[0], c): g for g, c in zip(ops, columns)}
        self.measurements = {q: measurement_column for q in measured}
        self.reserved_columns = max(2, total_columns or 0)
        self.initial_states = states

    def load_example(self, name):
        n, ops = example_circuit(name)
        self.set_circuit(n, ops)
        self.active_example = name
        self.example_ops = tuple(self.ordered())

    def removes_gates(self, n):
        """True if shrinking to n qubits would delete gates (the GUI asks first)."""
        return n < self.n and any(any(q >= n for q in g.targets) for g in self.gates.values())

    def resize(self, n):
        if not 1 <= n <= MAX_QUBITS:
            raise EditorError(f'Choose between 1 and {MAX_QUBITS} qubits')
        self.snapshot()
        self.gates = {pos: g for pos, g in self.gates.items() if all(q < n for q in g.targets)}
        self.measurements = {q: c for q, c in self.measurements.items() if q < n}
        self.n = n
        self.initial_states = (self.initial_states + defaults(n))[:n]
        if self.pending and any(q >= n for q in self.pending[2]):
            self.pending = None

    # ---- initial states -----------------------------------------------------------
    def set_initial_state(self, qubit, state):
        """Set a qubit's starting state. Returns False if it is unchanged."""
        if not 0 <= qubit < self.n:
            raise EditorError('No such qubit')
        if not isinstance(state, InitialState):
            raise EditorError('Invalid initial state')
        if self.initial_states[qubit] == state:
            return False
        self.snapshot()
        self.initial_states[qubit] = state
        return True

    def initial_vector(self):
        return product_state(self.initial_states)

    # ---- placement --------------------------------------------------------------
    def place(self, name, row, col, operands=None, angle=0.0, phi=0.0, lam=0.0):
        """Place a gate or terminal measurement.

        A multi-qubit gate without operands starts a pending placement anchored
        on (row, col) and returns a status message; complete it with
        add_operand(). Returns True when committed, False when the drop is
        ignored (outside the grid or an unknown gate name). Raises EditorError
        when the edit breaks an editor rule.
        """
        if not (0 <= row < self.n and 0 <= col < self.columns):
            return False
        if name in DUAL + TRIPLE and operands is None:
            if self.n < operand_count(name):
                raise EditorError('Not enough qubits for this gate')
            if self.operation_at(row, col):
                raise EditorError('Choose an empty cell for the first operand')
            self.pending = (name, col, (row,))
            return f'{name}: target anchored on q{row}; select remaining qubit(s) in column {col + 1} (Esc to cancel)'
        if (row, col) in self.gates or self.measurements.get(row) == col:
            raise EditorError('Cell occupied: select or remove the existing gate first')
        if name == 'M':
            if row in self.measurements:
                raise EditorError('This qubit already has a terminal measurement')
            if any(c >= col for (_, c) in self.gates):
                raise EditorError('M must be terminal on its measured qubit')
            if self.measurements and any(c != col for c in self.measurements.values()):
                raise EditorError('All measurement gates must be in the final circuit column')
            self.snapshot()
            self.measurements[row] = col
            return True
        if name not in ALL:
            return False
        if row in self.measurements:
            raise EditorError('Remove this qubit’s terminal measurement before adding gates')
        if self.measurements and col >= min(self.measurements.values()):
            raise EditorError('Unitary gates must be before terminal measurements')
        ids = tuple(operands) if operands is not None else (row,)
        if len(ids) != operand_count(name) or len(set(ids)) != len(ids):
            raise EditorError('Select distinct operand qubits')
        for (r, c), gate in self.gates.items():
            if c == col and (r, c) != (row, col) and set(gate.targets) & set(ids):
                raise EditorError('Qubit collision in column; choose another column')
        self.snapshot()
        param = name in PARAMETERIZED
        self.gates[(row, col)] = Gate(name, ids, angle if param else 0.0,
                                      phi if name == 'U' else 0.0, lam if name == 'U' else 0.0)
        return True

    def add_operand(self, row, col):
        """Add a qubit to the pending multi-qubit placement.

        Returns a status message while more operands are needed, otherwise
        place()'s result (True when committed); None if nothing is pending.
        Raises EditorError for an invalid choice; an invalid final operand
        rule (e.g. a column collision) also ends the placement.
        """
        if not self.pending:
            return None
        name, pcol, ids = self.pending
        if col != pcol:
            raise EditorError(f'Select a qubit in column {pcol + 1}, or press Esc')
        if row in ids:
            raise EditorError('Choose another qubit')
        if self.operation_at(row, col):
            raise EditorError('Qubit occupied in this column')
        ids = ids + (row,)
        if len(ids) < operand_count(name):
            self.pending = (name, pcol, ids)
            return f'{name}: select final qubit in column {pcol + 1}'
        self.pending = None
        # CX/CCX are anchored target-first in the editor, control-first in Gate.targets.
        ordered = ids[1:] + ids[:1] if name in ('CX', 'CCX') else ids
        return self.place(name, ids[0], pcol, ordered)

    def cancel_pending(self):
        had = self.pending is not None
        self.pending = None
        return had

    # ---- editing ----------------------------------------------------------------
    def move(self, src_row, src_col, dst_row, dst_col):
        """Move the operation found at (src_row, src_col). Returns True if moved."""
        found = self.operation_at(src_row, src_col)
        if not found or (src_row, src_col) == (dst_row, dst_col):
            return False
        if not (0 <= dst_row < self.n and 0 <= dst_col < self.columns):
            return False
        kind, key, gate = found
        if kind == 'gate':
            delta = dst_row - src_row
            targets = tuple(q + delta for q in gate.targets)
            if any(q < 0 or q >= self.n for q in targets):
                raise EditorError('Cannot move operation outside available qubits')
            others = {k: v for k, v in self.gates.items() if k != key}
            if any(c == dst_col and set(v.targets) & set(targets) for (_, c), v in others.items()):
                raise EditorError('Destination occupied by another operation')
            if any(q in self.measurements for q in targets) or (
                    self.measurements and dst_col >= min(self.measurements.values())):
                raise EditorError('Cannot move unitary past terminal measurements')
            self.snapshot()
            self.gates.pop(key)
            self.gates[(targets[0], dst_col)] = Gate(gate.name, targets, gate.angle, gate.phi, gate.lam)
        else:
            if dst_row in self.measurements and dst_row != src_row:
                raise EditorError('Target qubit already measured')
            if any(c >= dst_col for (_, c) in self.gates):
                raise EditorError('Measurement must follow all unitary columns')
            if any(c != dst_col for q, c in self.measurements.items() if q != src_row):
                raise EditorError('Measurements must occupy a shared terminal column')
            self.snapshot()
            self.measurements.pop(src_row)
            self.measurements[dst_row] = dst_col
        return True

    def insert_column(self, index):
        if not 0 <= index <= self.columns:
            return False
        self.snapshot()
        self.gates = {(r, c + 1 if c >= index else c): g for (r, c), g in self.gates.items()}
        self.measurements = {r: c + 1 if c >= index else c for r, c in self.measurements.items()}
        self.reserved_columns = max(self.reserved_columns + 1, index + 2)
        return True

    def delete_empty_column(self, index):
        if not 0 <= index < self.columns:
            return False
        if any(c == index for _, c in self.gates) or index in self.measurements.values():
            raise EditorError('Delete the gates in this column first')
        self.snapshot()
        self.gates = {(r, c - 1 if c > index else c): g for (r, c), g in self.gates.items()}
        self.measurements = {r: c - 1 if c > index else c for r, c in self.measurements.items()}
        self.reserved_columns = max(2, self.reserved_columns - 1)
        return True

    def remove(self, row, col):
        """Remove the gate or measurement covering (row, col), from any of its wires."""
        found = self.operation_at(row, col)
        if not found:
            return False
        self.snapshot()
        kind, key, _ = found
        if kind == 'gate':
            self.gates.pop(key)
        else:
            self.measurements.pop(row)
        return True

    def editable_gate(self, row, col):
        """The parameterized gate covering (row, col), or None."""
        found = self.operation_at(row, col)
        if found and found[0] == 'gate' and found[2].name in PARAMETERIZED:
            return found[1], found[2]
        return None

    def edit_parameters(self, row, col, angle, phi=None, lam=None):
        found = self.editable_gate(row, col)
        if not found:
            raise EditorError('Only RX, RY, RZ, P and U gates have editable parameters')
        key, gate = found
        self.snapshot()
        self.gates[key] = Gate(gate.name, gate.targets, angle,
                               gate.phi if phi is None else phi, gate.lam if lam is None else lam)

    # ---- analysis ---------------------------------------------------------------
    def is_edited_example(self):
        return self.example_ops is not None and tuple(self.ordered()) != self.example_ops

    def verification(self):
        """(rows, note) for the verification table."""
        if has_specification(self.active_example):
            rows, note = verify_example(self.active_example, self.n, self.ordered())
            if self.is_edited_example():
                note = f'Edited {self.active_example}: checking against the original specification. ' + note
        else:
            rows, note = inspect_basis(self.n, self.ordered())
        if not all_default(self.initial_states):
            note += ' The table checks the gate logic for each basis input; it does not use the chosen initial states.'
        return rows, note

    def analysis(self):
        """Gate statistics for the State Inspector's Circuit tab."""
        gates, columns, _, _ = self.layout()
        return analyze_circuit(self.n, gates, columns, sorted(self.measurements))

    def simulate(self):
        """Exact state before and after each occupied column (parallel gates commute)."""
        column_ops = {}
        for (_, c), g in sorted(self.gates.items(), key=lambda item: (item[0][1], item[0][0])):
            column_ops.setdefault(c, []).append(g)
        occupied = sorted(column_ops)
        start = self.initial_vector()
        states = evolution(self.n, [g for c in occupied for g in column_ops[c]], start)
        state = start
        column_states = [state]
        for c in occupied:
            for g in column_ops[c]:
                state = apply_gate(state, self.n, g)
            column_states.append(state)
        return Simulation(occupied, column_states, states)
