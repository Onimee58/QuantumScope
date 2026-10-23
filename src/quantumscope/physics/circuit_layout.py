"""Column layout for circuit operations, independent of the GUI.

Simulation order is column order (then row within a column). Gates sharing a
column must act on disjoint qubits, so they commute and the layout never
changes the circuit's unitary.
"""


def span(gate):
    """Wires a gate occupies visually, including those its connector crosses."""
    return range(min(gate.targets), max(gate.targets) + 1)


def pack_columns(n, gates, fences=()):
    """Place each gate in the earliest column after every earlier gate it touches.

    A gate reserves every wire between its outermost operands, so connector
    lines never cross another gate in the same column. fences are gate indices
    (e.g. from QASM barriers) before which no earlier column may be reused.
    Gate order is preserved for any two gates that share a wire.
    """
    free = [0] * n
    floor = 0
    fences = set(fences)
    columns = []
    for index, gate in enumerate(gates):
        if index in fences:
            floor = max(free + [floor])
        wires = span(gate)
        col = max([floor] + [free[q] for q in wires])
        for q in wires:
            free[q] = col + 1
        columns.append(col)
    return columns


def validate_columns(gates, columns):
    """Check a stored layout is consistent with its operation list.

    The stored operation order must be column order, so that the circuit a
    file describes is the same whether or not a reader honours the layout.
    """
    if len(columns) != len(gates):
        raise ValueError('Layout column count does not match operations')
    if any(type(c) is not int or c < 0 or c > 100000 for c in columns):
        raise ValueError('Invalid layout column')
    if any(b < a for a, b in zip(columns, columns[1:])):
        raise ValueError('Operations must be stored in column order')
    used = {}
    for gate, col in zip(gates, columns):
        wires = used.setdefault(col, set())
        if wires & set(gate.targets):
            raise ValueError(f'Two operations share a qubit in column {col + 1}')
        wires.update(gate.targets)


def pack_and_order(n, gates, fences=()):
    """Pack gates and return (gates, columns) sorted into column order.

    Reordering is safe: a gate can only move ahead of earlier gates in a later
    column, and a gate sharing a wire with an earlier one always lands in a
    later column, so only commuting (disjoint) gates change relative order.
    """
    columns = pack_columns(n, gates, fences)
    order = sorted(range(len(gates)), key=lambda i: (columns[i], min(gates[i].targets), i))
    return [gates[i] for i in order], [columns[i] for i in order]
