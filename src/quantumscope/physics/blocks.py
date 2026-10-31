"""Blocks: a named group of real gates that the editor treats as one operation.

A block acts on a set of qubits and reserves the whole wire span from its
lowest to its highest qubit. Collapsed it occupies one column; expanded, its
gates are laid out over several columns (packed so gates on separate qubits
share a column). Simulation always uses the real gates, so collapsed and
expanded blocks behave identically.
"""
from dataclasses import dataclass
import math

from .circuits import ALL, DUAL, TRIPLE, MAX_QUBITS, Gate
from .circuit_layout import pack_and_order


@dataclass(frozen=True)
class Block:
    kind: str                 # builder key, e.g. 'grover_oracle'; used by Edit block
    label: str                # shown on the box, e.g. 'Oracle'
    qubits: tuple             # every qubit the block may act on (including work qubits)
    gates: tuple              # the real gates, absolute qubit indices, in circuit order
    params: tuple = ()        # ((name, value), ...) the block was built with

    def __post_init__(self):
        qubits = tuple(sorted(set(int(q) for q in self.qubits)))
        if not qubits:
            raise ValueError('A block needs at least one qubit')
        if not isinstance(self.label, str) or not self.label.strip() or len(self.label) > 40:
            raise ValueError('Invalid block label')
        gates = tuple(self.gates)
        for g in gates:
            if not isinstance(g, Gate) or g.name not in ALL:
                raise ValueError('Blocks may contain only supported gates')
            size = 3 if g.name in TRIPLE else 2 if g.name in DUAL else 1
            if len(g.targets) != size or len(set(g.targets)) != size:
                raise ValueError(f'Invalid operands for {g.name} in block {self.label}')
            if not set(g.targets) <= set(qubits):
                raise ValueError(f'Block {self.label} has a gate outside its qubits')
            if not all(math.isfinite(v) for v in (g.angle, g.phi, g.lam)):
                raise ValueError('Gate parameters must be finite')
        object.__setattr__(self, 'qubits', qubits)
        object.__setattr__(self, 'gates', gates)
        object.__setattr__(self, 'params', tuple((str(k), v) for k, v in self.params))

    # ---- geometry --------------------------------------------------------------------
    @property
    def low(self):
        return self.qubits[0]

    @property
    def high(self):
        return self.qubits[-1]

    @property
    def span(self):
        """Every wire the block reserves, including wires between its qubits."""
        return range(self.low, self.high + 1)

    def expanded_layout(self):
        """(gates, relative columns) when expanded; column 0 is the block's own column."""
        if not self.gates:
            return [], []
        return pack_and_order(self.high + 1, list(self.gates))

    @property
    def expanded_width(self):
        _, cols = self.expanded_layout()
        return max(cols) + 1 if cols else 1

    def param(self, name, default=None):
        return dict(self.params).get(name, default)

    def shifted(self, delta):
        """The same block moved `delta` wires down (negative: up)."""
        return Block(self.kind, self.label, tuple(q + delta for q in self.qubits),
                     tuple(Gate(g.name, tuple(q + delta for q in g.targets), g.angle, g.phi, g.lam)
                           for g in self.gates), self.params)

    # ---- files -------------------------------------------------------------------------
    def to_record(self):
        return {'kind': self.kind, 'label': self.label, 'qubits': list(self.qubits),
                'params': {k: v for k, v in self.params},
                'gates': [{'gate': g.name, 'targets': list(g.targets),
                           **({'angle_radians': g.angle} if g.name in ('RX', 'RY', 'RZ', 'P', 'CP') else {}),
                           **({'theta_radians': g.angle, 'phi_radians': g.phi, 'lambda_radians': g.lam}
                              if g.name == 'U' else {})} for g in self.gates]}

    @classmethod
    def from_record(cls, record, n):
        if not isinstance(record, dict):
            raise ValueError('Invalid block record')
        qubits = record.get('qubits')
        if not isinstance(qubits, list) or not all(type(q) is int and 0 <= q < n for q in qubits):
            raise ValueError('Invalid block qubits')
        params = record.get('params', {})
        if not isinstance(params, dict) or not all(isinstance(v, (int, float, str)) for v in params.values()):
            raise ValueError('Invalid block parameters')
        gates = []
        for g in record.get('gates', []):
            if not isinstance(g, dict) or g.get('gate') not in ALL or not isinstance(g.get('targets'), list):
                raise ValueError('Invalid gate in block')
            if g['gate'] == 'U':
                angle, phi, lam = (g.get('theta_radians', 0.0), g.get('phi_radians', 0.0), g.get('lambda_radians', 0.0))
            else:
                angle, phi, lam = g.get('angle_radians', 0.0), 0.0, 0.0
            if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (angle, phi, lam)):
                raise ValueError('Invalid gate parameter in block')
            gates.append(Gate(g['gate'], tuple(g['targets']), float(angle), float(phi), float(lam)))
        if len(gates) > 10000 or len(qubits) > MAX_QUBITS:
            raise ValueError('Block too large')
        return cls(str(record.get('kind', 'custom')), str(record.get('label', 'Block')), tuple(qubits),
                   tuple(gates), tuple(params.items()))


@dataclass(frozen=True)
class BlockPlacement:
    """A block in the circuit: its block, its first column and whether it is expanded."""
    block: Block
    col: int
    expanded: bool = False

    @property
    def width(self):
        return self.block.expanded_width if self.expanded else 1

    @property
    def end(self):
        """Last column the placement occupies."""
        return self.col + self.width - 1

    def covers(self, row, col):
        return self.block.low <= row <= self.block.high and self.col <= col <= self.end

    def placed_gates(self):
        """[(gate, absolute column)] in simulation order."""
        if not self.expanded:
            return [(g, self.col) for g in self.block.gates]
        gates, cols = self.block.expanded_layout()
        return [(g, self.col + c) for g, c in zip(gates, cols)]


def check_layout(n, gates, columns, placements):
    """Blocks must fit the register and not overlap gates or each other."""
    cells = {}
    for g, c in zip(gates, columns):
        for q in g.targets:
            cells[(q, c)] = g.name
    for pl in placements:
        if pl.col < 0 or pl.block.high >= n:
            raise ValueError(f'Block {pl.block.label} does not fit the circuit')
        for c in range(pl.col, pl.end + 1):
            for q in pl.block.span:
                if (q, c) in cells:
                    raise ValueError(f'Block {pl.block.label} overlaps another operation in column {c + 1}')
                cells[(q, c)] = pl.block.label


def placed_items(free, placements):
    """[(column, row, sequence, gate, placement or None)] in simulation order.

    free: iterable of (row, column, gate). A block's gates keep their internal
    order; nothing else shares the block's wire span in its columns.
    """
    items = [(c, r, 0, g, None) for r, c, g in free]
    for pl in placements:
        for seq, (g, c) in enumerate(pl.placed_gates()):
            items.append((c, pl.block.low, seq, g, pl))
    items.sort(key=lambda x: (x[0], x[1], x[2]))
    return items


def describe(block):
    params = ', '.join(f'{k}={v}' for k, v in block.params if k not in ('inputs', 'search', 'size'))
    qubits = ','.join(f'q{q}' for q in block.qubits)
    return f'block: {block.label} on {qubits}' + (f' ({params})' if params else '')


def flatten_with_comments(free, placements):
    """(gates in simulation order, {gate index: comment}) marking where each block starts."""
    gates, comments, seen = [], {}, set()
    for _, _, _, g, pl in placed_items(free, placements):
        if pl is not None and id(pl) not in seen:
            seen.add(id(pl))
            comments[len(gates)] = describe(pl.block)
        gates.append(g)
    return gates, comments
