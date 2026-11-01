"""Dynamic circuits: mid-circuit measurement, classical bits, conditioned gates and reset (no Qt).

The simulation follows every measurement outcome as a *branch*: a classical
record (one value per classical bit) together with the unnormalized density
matrix σ of the qubits in that branch (its trace is the branch probability).
Branches with the same record are merged, so there are at most 2^bits of them.
The state averaged over all branches is Σσ — what an observer who does not
look at the classical bits would describe.

Everything is exact: no random sampling. Shots are drawn from the result.
"""
from dataclasses import dataclass

import numpy as np

from .circuits import Gate
from .noise import NoiseElement, apply_element, apply_unitary, density, gate_noise, idle_noise

MAX_BITS = 10
PRUNE = 1e-14                    # branches less likely than this are dropped


@dataclass(frozen=True)
class Measure:
    """Measure `qubit` in the computational basis and store the result in classical bit `cbit`."""
    qubit: int
    cbit: int

    def __post_init__(self):
        if not (isinstance(self.cbit, int) and 0 <= self.cbit < MAX_BITS):
            raise ValueError(f'Classical bit must be c0–c{MAX_BITS - 1}')

    @property
    def label(self):
        return f'Measure q{self.qubit} → c{self.cbit}'

    def to_record(self):
        return {'op': 'measure', 'qubit': self.qubit, 'cbit': self.cbit}


@dataclass(frozen=True)
class Reset:
    """Return `qubit` to |0⟩ (a measurement whose result is discarded, then X if it was 1)."""
    qubit: int

    @property
    def label(self):
        return f'Reset q{self.qubit} to |0⟩'

    def to_record(self):
        return {'op': 'reset', 'qubit': self.qubit}


@dataclass(frozen=True)
class Conditioned:
    """A gate applied only when classical bits have given values.

    Single bit: Conditioned(gate, 1, 1) means "if c1 = 1".
    Several bits: Conditioned(gate, (0, 1), (1, 0)) means "if c0c1 = 10".
    """
    gate: Gate
    cbit: object                 # an int, or a tuple of ints for a multi-bit condition
    value: object = 1            # an int, or a tuple of 0/1 values (one per bit)

    def __post_init__(self):
        bits, values = condition_parts(self.cbit, self.value)
        if not bits or len(set(bits)) != len(bits) or len(bits) != len(values):
            raise ValueError('Invalid classical condition')
        if not all(isinstance(b, int) and 0 <= b < MAX_BITS for b in bits) or not all(v in (0, 1) for v in values):
            raise ValueError('Invalid classical condition')

    @property
    def bits(self):
        return condition_parts(self.cbit, self.value)[0]

    @property
    def values(self):
        return condition_parts(self.cbit, self.value)[1]

    def holds(self, record):
        return all(record[b] == v for b, v in zip(self.bits, self.values))

    @property
    def label(self):
        return 'if ' + condition_text(self.cbit, self.value)


def condition_parts(cbit, value):
    """(bits, values) as tuples, for a single-bit or multi-bit condition."""
    if isinstance(cbit, (tuple, list)):
        values = tuple(value) if isinstance(value, (tuple, list)) else ()
        return tuple(cbit), values
    return (cbit,), (value,)


def condition_text(cbit, value):
    """'c1 = 1' or 'c0c1 = 10'."""
    bits, values = condition_parts(cbit, value)
    return ''.join(f'c{b}' for b in bits) + ' = ' + ''.join(str(v) for v in values)


def item_from_record(record):
    """A Measure or Reset from a file record (raises ValueError if invalid)."""
    if not isinstance(record, dict) or type(record.get('qubit')) is not int or record['qubit'] < 0:
        raise ValueError('Invalid classical operation')
    if record.get('op') == 'measure':
        if type(record.get('cbit')) is not int:
            raise ValueError('Invalid classical bit')
        return Measure(record['qubit'], record['cbit'])
    if record.get('op') == 'reset':
        return Reset(record['qubit'])
    raise ValueError('Unknown classical operation')


@dataclass
class Branch:
    bits: tuple                 # classical record, one 0/1 per classical bit
    sigma: np.ndarray           # unnormalized density matrix; trace = probability

    @property
    def probability(self):
        return float(np.real(np.trace(self.sigma)))

    @property
    def rho(self):
        p = self.probability
        return self.sigma / p if p > 0 else self.sigma


def _project(sigma, n, qubit, outcome):
    """P σ P for the projector onto |outcome⟩ of one qubit."""
    t = np.array(sigma, dtype=complex).reshape((2,) * (2 * n))
    keep = [slice(None)] * (2 * n)
    other = 1 - outcome
    index = list(keep)
    index[qubit] = other
    t[tuple(index)] = 0
    index = list(keep)
    index[qubit + n] = other
    t[tuple(index)] = 0
    return t.reshape(2 ** n, 2 ** n)


def _reset(sigma, n, qubit):
    """|0⟩⟨0|σ|0⟩⟨0| + |0⟩⟨1|σ|1⟩⟨0| on one qubit: everything moves to |0⟩, coherences are lost."""
    t = np.array(sigma, dtype=complex).reshape((2,) * (2 * n))
    out = np.zeros_like(t)
    a = [slice(None)] * (2 * n)
    def at(r, c):
        index = list(a)
        index[qubit], index[qubit + n] = r, c
        return tuple(index)
    out[at(0, 0)] = t[at(0, 0)] + t[at(1, 1)]
    return out.reshape(2 ** n, 2 ** n)


def _merge(branches):
    merged = {}
    for b in branches:
        if b.probability < PRUNE:
            continue
        if b.bits in merged:
            merged[b.bits].sigma = merged[b.bits].sigma + b.sigma
        else:
            merged[b.bits] = Branch(b.bits, b.sigma)
    return [merged[k] for k in sorted(merged)]


def bits_needed(columns):
    used = [-1]
    for column in columns:
        for item in column:
            if isinstance(item, Measure):
                used.append(item.cbit)
            elif isinstance(item, Conditioned):
                used.extend(item.bits)
    return max(used) + 1


def simulate(n, columns, initial_state, model, readout=0.0, store=True):
    """Branch-resolved simulation, column by column.

    columns: lists of Gate, Conditioned, NoiseElement, Measure or Reset.
    readout: probability that a mid-circuit result is recorded wrongly (the
    qubit still collapses to the true outcome).
    Returns a list (before the first column, then after each stored column) of
    lists of Branch; sum the branches' σ for the averaged state.
    """
    nbits = bits_needed(columns)
    branches = [Branch((0,) * nbits, density(initial_state))]
    history = [branches]
    for column in columns:
        busy = set()
        for item in column:
            if isinstance(item, Measure):
                split = []
                for b in branches:
                    s0, s1 = _project(b.sigma, n, item.qubit, 0), _project(b.sigma, n, item.qubit, 1)
                    for recorded in (0, 1):
                        # recorded value: the true outcome, or the other one with probability `readout`
                        sigma = (1 - readout) * (s0 if recorded == 0 else s1) + readout * (s1 if recorded == 0 else s0)
                        bits = list(b.bits)
                        bits[item.cbit] = recorded
                        split.append(Branch(tuple(bits), sigma))
                branches = _merge(split)
                busy.add(item.qubit)
            elif isinstance(item, Reset):
                branches = [Branch(b.bits, _reset(b.sigma, n, item.qubit)) for b in branches]
                busy.add(item.qubit)
            elif isinstance(item, NoiseElement):
                branches = [Branch(b.bits, apply_element(b.sigma, n, item)) for b in branches]
                busy.add(item.qubit)
            else:
                gate, condition = (item.gate, item) if isinstance(item, Conditioned) else (item, None)
                updated = []
                for b in branches:
                    if condition is None or condition.holds(b.bits):
                        sigma = gate_noise(apply_unitary(b.sigma, n, gate), n, gate, model)
                        updated.append(Branch(b.bits, sigma))
                    else:
                        updated.append(b)
                branches = updated
                busy.update(gate.targets)
        idle = [q for q in range(n) if q not in busy]
        if idle and model.active and model.idle:
            branches = [Branch(b.bits, idle_noise(np.array(b.sigma), n, idle, model)) for b in branches]
        if store:
            history.append([Branch(b.bits, b.sigma.copy()) for b in branches])
    if not store:
        history = [history[0], branches]
    return history


def averaged(branches):
    """The state averaged over all branches (a normalized density matrix)."""
    return sum(b.sigma for b in branches)


def record_distribution(branches):
    """{bits string 'c0c1…': probability} of the classical record."""
    return {''.join(map(str, b.bits)): b.probability for b in branches}
