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
from quantumscope.physics.blocks import Block, BlockPlacement, check_layout, flatten_with_comments, placed_items

from quantumscope.physics.circuits import PARAMETERIZED  # noqa: E402  (includes CP)
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
        self.blocks = {}           # block id -> BlockPlacement (collapsed or expanded)
        self._next_block = 1
        self.active_entry = None   # (library key, ((param, value), ...)) for algorithms and new examples
        self.undo_stack = []
        self.redo_stack = []

    # ---- layout ---------------------------------------------------------------
    @property
    def columns(self):
        """Visible columns: always one spare after the last operation (two when empty)."""
        last = max([c for _, c in self.gates] + list(self.measurements.values())
                   + [pl.end for pl in self.blocks.values()], default=-1)
        return max(2, last + 2, self.reserved_columns)

    def _placed(self):
        """[(column, row, sequence, gate)] for every real gate, sorted into simulation order.

        Free gates are ordered by column then row, as always. A block's gates sit
        at its column(s) and keep their internal order; nothing else can share the
        block's wire span in those columns, so the result is well defined.
        """
        return [item[:4] for item in placed_items(((r, c, g) for (r, c), g in self.gates.items()),
                                                    self.blocks.values())]

    def qasm_items(self):
        """(gates, {index: comment}) for QASM export: blocks marked by comments."""
        return flatten_with_comments(((r, c, g) for (r, c), g in self.gates.items()), self.blocks.values())

    def ordered(self):
        """Gates in simulation order: by column, then row (blocks contribute their real gates)."""
        return [g for _, _, _, g in self._placed()]

    def flat_layout(self):
        """(gates, columns) for every real gate, including those inside blocks."""
        placed = self._placed()
        return [g for _, _, _, g in placed], [c for c, _, _, _ in placed]

    def layout(self):
        """(gates, columns, measurement column, total columns) for saving."""
        items = sorted(self.gates.items(), key=lambda x: (x[0][1], x[0][0]))
        return ([g for _, g in items], [c for (_, c), _ in items],
                min(self.measurements.values()) if self.measurements else None, self.reserved_columns)

    def operation_at(self, row, col):
        """('gate', key, gate), ('block', id, placement), ('measurement', (row, col), None) or None."""
        for bid, pl in self.blocks.items():
            if pl.covers(row, col):
                return ('block', bid, pl)
        for key, gate in self.gates.items():
            if key[1] == col and row in gate.targets:
                return ('gate', key, gate)
        if self.measurements.get(row) == col:
            return ('measurement', (row, col), None)
        return None

    # ---- undo/redo ------------------------------------------------------------
    def _record(self):
        return (self.n, self.reserved_columns, dict(self.gates), dict(self.measurements),
                self.active_example, self.example_ops, tuple(self.initial_states),
                dict(self.blocks), self.active_entry)

    def snapshot(self):
        self.undo_stack.append(self._record())
        self.undo_stack = self.undo_stack[-UNDO_LIMIT:]
        self.redo_stack.clear()

    def _restore(self, record):
        (self.n, self.reserved_columns, gates, measurements,
         self.active_example, self.example_ops, states, blocks, self.active_entry) = record
        self.gates, self.measurements = dict(gates), dict(measurements)
        self.initial_states = list(states)
        self.blocks = dict(blocks)
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
        self.blocks, self.active_entry = {}, None

    def load_bell(self):
        """The quick 'Bell example' button (not a verified example)."""
        if self.n < 2:
            self.resize(2)
        self.snapshot()
        self.active_example, self.example_ops, self.pending = 'Bell pair', None, None
        self.gates = {(0, 0): Gate('H', (0,)), (0, 1): Gate('CX', (0, 1))}
        self.measurements = {}
        self.initial_states = defaults(self.n)
        self.blocks, self.active_entry = {}, None

    def set_circuit(self, n, ops, columns=None, measured=(), measurement_column=None, total_columns=None,
                    initial_states=None, blocks=()):
        """Replace the circuit. Without columns, gates are packed (simulation unchanged).
        initial_states defaults to |0⟩ on every qubit. blocks is a list of
        (Block, column, expanded) placed alongside the gates."""
        from quantumscope.physics.circuit_files import validate
        ops = list(ops)
        validate(n, ops)
        if columns is None:
            ops, columns = pack_and_order(n, ops)
        else:
            columns = list(columns)
            validate_columns(ops, columns)
        placements = [BlockPlacement(b, c, bool(e)) for b, c, e in blocks]
        check_layout(n, ops, columns, placements)
        last = max(list(columns) + [pl.end for pl in placements], default=-1)
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
        self.blocks = {}
        self.active_entry = None
        for pl in placements:
            self.blocks[self._next_block] = pl
            self._next_block += 1

    def load_example(self, name):
        n, ops = example_circuit(name)
        self.set_circuit(n, ops)
        self.active_example = name
        self.example_ops = tuple(self.ordered())

    def load_library(self, key, values=None):
        """Build an algorithm or example from the library and load it.

        Gates and (collapsed) blocks are placed in the earliest free column; a
        block reserves its whole wire span. Measurements go after everything.
        """
        from quantumscope.physics.algorithms import build
        params, built = build(key, values)
        free = [0] * built.n
        ops, cols, placed = [], [], []
        for item in built.items:
            wires = item.span if isinstance(item, Block) else range(min(item.targets), max(item.targets) + 1)
            col = max(free[q] for q in wires)
            for q in wires:
                free[q] = col + 1
            if isinstance(item, Block):
                placed.append((item, col, False))
            else:
                ops.append(item)
                cols.append(col)
        order = sorted(range(len(ops)), key=lambda i: (cols[i], min(ops[i].targets)))
        self.set_circuit(built.n, [ops[i] for i in order], [cols[i] for i in order], built.measured,
                         initial_states=built.initial_states, blocks=placed)
        self.active_entry = (key, tuple(sorted(params.items())))
        return built.note

    def removes_gates(self, n):
        """True if shrinking to n qubits would delete gates or blocks (the GUI asks first)."""
        return n < self.n and (any(any(q >= n for q in g.targets) for g in self.gates.values())
                               or any(pl.block.high >= n for pl in self.blocks.values()))

    def resize(self, n):
        if not 1 <= n <= MAX_QUBITS:
            raise EditorError(f'Choose between 1 and {MAX_QUBITS} qubits')
        self.snapshot()
        self.gates = {pos: g for pos, g in self.gates.items() if all(q < n for q in g.targets)}
        self.measurements = {q: c for q, c in self.measurements.items() if q < n}
        self.blocks = {bid: pl for bid, pl in self.blocks.items() if pl.block.high < n}
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
            self._pending_params = (angle, phi, lam)     # CP keeps its angle until committed
            return f'{name}: target anchored on q{row}; select remaining qubit(s) in column {col + 1} (Esc to cancel)'
        if (row, col) in self.gates or self.measurements.get(row) == col:
            raise EditorError('Cell occupied: select or remove the existing gate first')
        inside = self._block_covering(row, col)
        if inside is not None:
            raise EditorError(f'Part of block {inside.block.label}: place gates outside it, or ungroup it first')
        if name == 'M':
            if row in self.measurements:
                raise EditorError('This qubit already has a terminal measurement')
            if any(c >= col for (_, c) in self.gates) or any(pl.end >= col for pl in self.blocks.values()):
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
        for q in ids:
            inside = self._block_covering(q, col)
            if inside is not None:
                raise EditorError(f'Qubit q{q} is inside block {inside.block.label} in this column')
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
        angle, phi, lam = getattr(self, '_pending_params', (0.0, 0.0, 0.0))
        return self.place(name, ids[0], pcol, ordered, angle, phi, lam)

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
        if kind == 'block':
            return self._move_block(key, src_row, src_col, dst_row, dst_col)
        if kind == 'gate':
            delta = dst_row - src_row
            targets = tuple(q + delta for q in gate.targets)
            if any(q < 0 or q >= self.n for q in targets):
                raise EditorError('Cannot move operation outside available qubits')
            others = {k: v for k, v in self.gates.items() if k != key}
            if any(c == dst_col and set(v.targets) & set(targets) for (_, c), v in others.items()) or any(
                    self._block_covering(q, dst_col) is not None for q in targets):
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
            if any(c >= dst_col for (_, c) in self.gates) or any(pl.end >= dst_col for pl in self.blocks.values()):
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
        for pl in self.blocks.values():
            if pl.col < index <= pl.end:
                raise EditorError(f'Cannot insert a column inside block {pl.block.label}')
        self.snapshot()
        self._shift_columns(index, 1)
        self.reserved_columns = max(self.reserved_columns + 1, index + 2)
        return True

    def _shift_columns(self, start, delta):
        """Move every operation at column ≥ start by delta columns (no snapshot)."""
        self.gates = {(r, c + delta if c >= start else c): g for (r, c), g in self.gates.items()}
        self.measurements = {r: c + delta if c >= start else c for r, c in self.measurements.items()}
        self.blocks = {bid: (BlockPlacement(pl.block, pl.col + delta, pl.expanded) if pl.col >= start else pl)
                       for bid, pl in self.blocks.items()}

    def _column_empty(self, index):
        return (not any(c == index for _, c in self.gates) and index not in self.measurements.values()
                and not any(pl.col <= index <= pl.end for pl in self.blocks.values()))

    def delete_empty_column(self, index):
        if not 0 <= index < self.columns:
            return False
        if not self._column_empty(index):
            raise EditorError('Delete the gates in this column first')
        self.snapshot()
        self._shift_columns(index + 1, -1)
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
        elif kind == 'block':
            self.blocks.pop(key)
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
            raise EditorError('Only RX, RY, RZ, P, U and CP gates have editable parameters')
        key, gate = found
        self.snapshot()
        self.gates[key] = Gate(gate.name, gate.targets, angle,
                               gate.phi if phi is None else phi, gate.lam if lam is None else lam)

    # ---- blocks -------------------------------------------------------------------
    def _block_covering(self, row, col, ignore=None):
        for bid, pl in self.blocks.items():
            if bid != ignore and pl.covers(row, col):
                return pl
        return None

    def block(self, bid):
        if bid not in self.blocks:
            raise EditorError('No such block')
        return self.blocks[bid]

    def _footprint_free(self, block, col, width, ignore=None):
        """Raise EditorError unless the block's span is free in columns col..col+width−1."""
        if col < 0 or block.low < 0 or block.high >= self.n:
            raise EditorError('Cannot move the block outside the circuit')
        for c in range(col, col + width):
            for q in block.span:
                if self._block_covering(q, c, ignore) is not None or self.measurements.get(q) == c or any(
                        gc == c and q in g.targets for (_, gc), g in self.gates.items()):
                    raise EditorError('Destination occupied by another operation')
        if any(q in self.measurements for q in block.qubits) or (
                self.measurements and col + width - 1 >= min(self.measurements.values())):
            raise EditorError('Cannot move a block past terminal measurements')

    def add_block(self, block, col):
        """Place a collapsed block (used by the library and by tests)."""
        self._footprint_free(block, col, 1)
        self.snapshot()
        bid = self._next_block
        self._next_block += 1
        self.blocks[bid] = BlockPlacement(block, col, False)
        return bid

    def _move_block(self, bid, src_row, src_col, dst_row, dst_col):
        pl = self.blocks[bid]
        moved = pl.block.shifted(dst_row - src_row)
        col = pl.col + (dst_col - src_col)
        if moved.low < 0 or moved.high >= self.n:
            raise EditorError('Cannot move the block outside the circuit')
        if col < 0 or col >= self.columns:
            return False
        self._footprint_free(moved, col, pl.width, ignore=bid)
        self.snapshot()
        self.blocks[bid] = BlockPlacement(moved, col, pl.expanded)
        return True

    def _expand(self, bid):
        pl = self.blocks[bid]
        if pl.expanded:
            return False
        extra = pl.block.expanded_width - 1
        if extra:
            # Make room: everything after the block's column moves right.
            self._shift_columns(pl.col + 1, extra)
        self.blocks[bid] = BlockPlacement(pl.block, pl.col, True)
        return True

    def _collapse(self, bid):
        pl = self.blocks[bid]
        if not pl.expanded:
            return False
        self.blocks[bid] = BlockPlacement(pl.block, pl.col, False)
        # Remove the columns the expansion added, where they are still empty.
        for c in range(pl.end, pl.col, -1):
            if self._column_empty(c):
                self._shift_columns(c + 1, -1)
        return True

    def expand_block(self, bid):
        self.block(bid)
        if self.blocks[bid].expanded:
            return False
        self.snapshot()
        return self._expand(bid)

    def collapse_block(self, bid):
        self.block(bid)
        if not self.blocks[bid].expanded:
            return False
        self.snapshot()
        return self._collapse(bid)

    def ungroup_block(self, bid):
        """Turn a block into ordinary editable gates (expanding it first if needed)."""
        self.block(bid)
        self.snapshot()
        self._expand(bid)
        pl = self.blocks.pop(bid)
        for g, c in pl.placed_gates():
            self.gates[(g.targets[0], c)] = g
        return True

    def edit_block(self, bid, values):
        """Rebuild a block with new parameters, keeping its place and expanded state."""
        from quantumscope.physics.algorithms import rebuild_block
        pl = self.block(bid)
        try:
            new = rebuild_block(pl.block, values)
        except ValueError as exc:
            raise EditorError(str(exc)) from exc
        if new == pl.block:
            return False
        self.snapshot()
        was_expanded = pl.expanded
        self._collapse(bid)
        self.blocks[bid] = BlockPlacement(new, self.blocks[bid].col, False)
        if was_expanded:
            self._expand(bid)
        return True

    def block_summary(self):
        """[(id, label, gate count, expanded)] for display."""
        return [(bid, pl.block.label, len(pl.block.gates), pl.expanded)
                for bid, pl in sorted(self.blocks.items(), key=lambda x: (x[1].col, x[1].block.low))]

    # ---- circuit tools --------------------------------------------------------------
    def _optimizable_items(self):
        """Simulation-order items for physics.optimize: editable gates, and blocks as barriers."""
        items = []
        for c, r, seq, g, pl in placed_items(((r, c, g) for (r, c), g in self.gates.items()), self.blocks.values()):
            if pl is None:
                items.append(('gate', (r, c), g))
            else:
                items.append(('barrier', ('block', pl.col, pl.block.low, seq), tuple(pl.block.span)))
        return items

    def simplification(self):
        """(kept gates by key, list of changes, equivalent?, global phase) — nothing is changed yet.

        Gates inside blocks are never changed; blocks act as barriers.
        """
        from quantumscope.physics.optimize import equivalent, simplify_sequence
        items = self._optimizable_items()
        kept, changes = simplify_sequence(items)
        if not changes:
            return kept, [], True, 1.0
        before = self.ordered()
        # Rebuild the full order, block gates included, for the equivalence check.
        flat_after = []
        gi = 0
        survivors = [kept[key] if key in kept else None for kind, key, _ in items if kind == 'gate']
        for c, r, seq, g, pl in placed_items(((r, c, g) for (r, c), g in self.gates.items()), self.blocks.values()):
            if pl is None:
                if survivors[gi] is not None:
                    flat_after.append(survivors[gi])
                gi += 1
            else:
                flat_after.append(g)
        ok, phase, _ = equivalent(self.n, before, flat_after)
        return kept, changes, ok, phase

    def apply_simplification(self, kept):
        """Replace the editable gates with the simplified set (one undo step)."""
        if set(kept) - set(self.gates):
            raise EditorError('Simplification no longer matches the circuit')
        self.snapshot()
        self.gates = {key: gate for key, gate in kept.items()}
        return True

    # ---- analysis ---------------------------------------------------------------
    def is_edited_example(self):
        return self.example_ops is not None and tuple(self.ordered()) != self.example_ops

    def circuit_view(self):
        from quantumscope.physics.algorithms import CircuitView
        gates = self.ordered()
        start = self.initial_vector()
        final = evolution(self.n, gates, start)[-1]
        return CircuitView(self.n, gates, start, [pl.block for pl in self.blocks.values()],
                           tuple(sorted(self.measurements)), final)

    def verification(self):
        """(rows, note) for the verification table."""
        if self.active_entry is not None:
            from quantumscope.physics.algorithms import entry
            key, params = self.active_entry
            return entry(key).spec(dict(params), self.circuit_view())
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
        """Gate statistics for the State Inspector's Circuit tab (blocks count their real gates)."""
        gates, columns = self.flat_layout()
        stats = analyze_circuit(self.n, gates, columns, sorted(self.measurements))
        stats['blocks'] = [(label, count, expanded) for _, label, count, expanded in self.block_summary()]
        return stats

    def simulate(self):
        """Exact state before and after each occupied column (parallel gates commute)."""
        column_ops = {}
        for c, _, _, g in self._placed():
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
