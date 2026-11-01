"""Algorithm and example library (no Qt).

Each entry builds a circuit from parameters: plain gates plus Blocks for
oracles and subroutines. Its specification checks the *current* circuit,
reading block parameters from the blocks actually present, so edits are
judged against the physics rather than against the original build.

Conventions: q0 is the most significant bit; registers are listed top-down.
"""
from dataclasses import dataclass, field
import math

import numpy as np

from .blocks import Block
from .circuits import Gate, apply_gate, distribution
from .circuit_verification import VerificationRow
from .initial_states import InitialState, defaults

TOL = 1e-9


# ---- parameters --------------------------------------------------------------------------

@dataclass(frozen=True)
class Param:
    key: str
    label: str
    kind: str                     # 'int', 'choice' or 'bits'
    default: object
    minimum: int = 0
    maximum: int = 0
    choices: tuple = ()           # ((label, value), ...) for 'choice'
    length_of: str = ''           # for 'bits': the int parameter giving the length
    help: str = ''


def validate_params(params_spec, values):
    """Complete and check parameter values; raises ValueError with a readable message."""
    out = {}
    for p in params_spec:
        v = values.get(p.key, p.default)
        if p.kind == 'int':
            if isinstance(v, bool) or not isinstance(v, int) or not p.minimum <= v <= p.maximum:
                raise ValueError(f'{p.label} must be an integer from {p.minimum} to {p.maximum}')
        elif p.kind == 'choice':
            if v not in [c[1] for c in p.choices]:
                raise ValueError(f'Invalid choice for {p.label}')
        elif p.kind == 'bits':
            length = out.get(p.length_of)
            if not isinstance(v, str) or any(ch not in '01' for ch in v) or (length is not None and len(v) != length):
                raise ValueError(f'{p.label} must be {length} bits of 0 and 1')
        out[p.key] = v
    return out


# ---- reusable gate patterns --------------------------------------------------------------------

def mcz(qubits, work=()):
    """Z on the all-ones state of `qubits`, using Toffolis and clean work qubits.

    1 qubit: Z. 2: CZ. 3: H·CCX·H. k ≥ 4: a V-chain needing k − 3 work
    qubits, which start in |0⟩ and are returned to |0⟩.
    """
    qubits, work = list(qubits), list(work)
    k = len(qubits)
    if k == 1:
        return [Gate('Z', (qubits[0],))]
    if k == 2:
        return [Gate('CZ', tuple(qubits))]
    target, controls = qubits[-1], qubits[:-1]
    if k == 3:
        return [Gate('H', (target,)), Gate('CCX', (controls[0], controls[1], target)), Gate('H', (target,))]
    need = k - 3
    if len(work) < need:
        raise ValueError(f'Multi-controlled Z on {k} qubits needs {need} work qubit(s)')
    w = work[:need]
    compute = [Gate('CCX', (controls[0], controls[1], w[0]))]
    for i in range(2, len(controls) - 1):
        compute.append(Gate('CCX', (controls[i], w[i - 2], w[i - 1])))
    middle = [Gate('H', (target,)), Gate('CCX', (controls[-1], w[-1], target)), Gate('H', (target,))]
    return compute + middle + list(reversed(compute))


def mcz_work_needed(k):
    return max(0, k - 3)


# ---- block builders (also used by "Edit block…") -------------------------------------------------

def parity_oracle(inputs, ancilla, s, c=0):
    """|x⟩|y⟩ → |x⟩|y ⊕ f(x)⟩ with f(x) = s·x ⊕ c. With the ancilla in |−⟩ this is a phase oracle."""
    gates = [Gate('CX', (q, ancilla)) for q, bit in zip(inputs, s) if bit == '1']
    if int(c):
        gates.append(Gate('X', (ancilla,)))
    return Block('parity_oracle', 'Oracle', tuple(inputs) + (ancilla,), tuple(gates),
                 (('s', s), ('c', int(c)), ('inputs', len(inputs))))


def grover_oracle(search, work, marked):
    """Phase −1 on the marked basis state of the search register."""
    flips = [Gate('X', (q,)) for q, bit in zip(search, marked) if bit == '0']
    gates = flips + mcz(search, work) + flips
    return Block('grover_oracle', 'Oracle', tuple(search) + tuple(work), tuple(gates),
                 (('marked', marked), ('search', len(search))))


def grover_diffusion(search, work):
    """Inversion about the mean: H X (multi-controlled Z) X H on the search register."""
    hs = [Gate('H', (q,)) for q in search]
    xs = [Gate('X', (q,)) for q in search]
    gates = hs + xs + mcz(search, work) + xs + hs
    return Block('grover_diffusion', 'Diffusion', tuple(search) + tuple(work), tuple(gates),
                 (('search', len(search)),))


def qft_gates(qubits):
    gates = []
    n = len(qubits)
    for j in range(n):
        gates.append(Gate('H', (qubits[j],)))
        for k in range(j + 1, n):
            gates.append(Gate('CP', (qubits[k], qubits[j]), math.pi / 2 ** (k - j)))
    for i in range(n // 2):
        gates.append(Gate('SWAP', (qubits[i], qubits[n - 1 - i])))
    return gates


def qft_block(qubits):
    return Block('qft', 'QFT', tuple(qubits), tuple(qft_gates(qubits)), (('size', len(qubits)),))


def iqft_block(qubits):
    inverse = [Gate(g.name, g.targets, -g.angle) for g in reversed(qft_gates(qubits))]
    return Block('iqft', 'QFT†', tuple(qubits), tuple(inverse), (('size', len(qubits)),))


# Parameters that "Edit block…" offers, and how to rebuild with new values.
def _rebuild_parity(block, values):
    n_inputs = block.param('inputs')
    return parity_oracle(block.qubits[:n_inputs], block.qubits[n_inputs], values['s'], values['c'])


def _rebuild_grover(block, values):
    k = block.param('search')
    return grover_oracle(block.qubits[:k], block.qubits[k:], values['marked'])


def block_edit_spec(block):
    """(params, rebuild) for blocks with editable parameters, or None."""
    if block.kind == 'parity_oracle':
        n = block.param('inputs')
        return ((Param('n', 'Input qubits', 'int', n, n, n),
                 Param('s', 'Hidden string s (f(x) = s·x ⊕ c)', 'bits', block.param('s'), length_of='n'),
                 Param('c', 'Constant c', 'choice', block.param('c'), choices=(('0', 0), ('1', 1))),),
                _rebuild_parity)
    if block.kind == 'grover_oracle':
        k = block.param('search')
        return ((Param('n', 'Search qubits', 'int', k, k, k),
                 Param('marked', 'Marked item', 'bits', block.param('marked'), length_of='n'),),
                _rebuild_grover)
    return None


def rebuild_block(block, values):
    spec = block_edit_spec(block)
    if spec is None:
        raise ValueError(f'{block.label} has no editable parameters')
    params, rebuild = spec
    checked = validate_params(params, {**dict(block.params), **values})
    new = rebuild(block, checked)
    return new


# ---- built circuits ---------------------------------------------------------------------------------

@dataclass
class Built:
    n: int
    items: list                       # Gate or Block, in circuit order
    initial_states: list
    measured: tuple = ()
    note: str = ''
    roles: tuple = ()                 # a short role per qubit, shown beside its label ('data', 'Bob', …)


@dataclass
class CircuitView:
    """What a specification may inspect: the current circuit, as simulated."""
    n: int
    gates: list                       # all real gates in simulation order (blocks flattened)
    initial_vector: np.ndarray
    blocks: list                      # Block objects present
    measured: tuple
    final_state: np.ndarray = field(default=None)
    branches: list = field(default=None)          # final branches (dynamic circuits)
    simulate: object = field(default=None)        # simulate(initial vector) -> final branches of this circuit


def marginal(state, n, qubits):
    """Probabilities of each bit string on `qubits` (listed in order), from a pure
    state vector or — under noise — a density matrix (its diagonal)."""
    probs = np.clip(np.real(np.diag(state)), 0, 1) if np.ndim(state) == 2 else distribution(state)
    out = {}
    for index, p in enumerate(probs):
        if p < 1e-15:
            continue
        key = ''.join(str((index >> (n - 1 - q)) & 1) for q in qubits)
        out[key] = out.get(key, 0.0) + float(p)
    return out


def _blocks_of(view, kind):
    return [b for b in view.blocks if b.kind == kind]


def _row(input_label, actual, expected, probability, passed):
    return VerificationRow(input_label, actual, expected, float(probability), passed)


# ---- algorithm entries -------------------------------------------------------------------------------

def _oracle_params(view, fallback_s, fallback_c):
    oracles = _blocks_of(view, 'parity_oracle')
    if len(oracles) == 1:
        return oracles[0].param('s'), int(oracles[0].param('c')), ''
    return fallback_s, fallback_c, ' The oracle is no longer a single block, so the originally chosen function is assumed.'


DEUTSCH_FUNCTIONS = (('f(x) = 0  (constant)', '0'), ('f(x) = 1  (constant)', '1'),
                     ('f(x) = x  (balanced)', 'x'), ('f(x) = NOT x  (balanced)', 'not'))
_DEUTSCH_SC = {'0': ('0', 0), '1': ('0', 1), 'x': ('1', 0), 'not': ('1', 1)}


def build_deutsch(p):
    s, c = _DEUTSCH_SC[p['function']]
    states = [InitialState.preset('0'), InitialState.preset('-')]
    return Built(2, [Gate('H', (0,)), parity_oracle([0], 1, s, c), Gate('H', (0,))], states, (0,),
                 'The ancilla q1 starts in |−⟩, so the oracle kicks the phase (−1)^f(x) back onto q0.')


def build_dj(p):
    n = p['n']
    s = '0' * n if p['function'] != 'balanced' else p['s']
    if p['function'] == 'balanced' and '1' not in s:
        raise ValueError('A balanced parity function needs at least one 1 in s')
    c = 1 if p['function'] == 'constant1' else 0
    hs = [Gate('H', (q,)) for q in range(n)]
    states = defaults(n) + [InitialState.preset('-')]
    return Built(n + 1, hs + [parity_oracle(list(range(n)), n, s, c)] + hs, states, tuple(range(n)),
                 'Constant f gives |0…0⟩ with certainty; balanced f never does.')


def spec_dj(p, view, n_inputs=None):
    n = n_inputs if n_inputs is not None else p['n']
    if p.get('function') in _DEUTSCH_SC:
        fs, fc = _DEUTSCH_SC[p['function']]
    else:
        fs = '0' * n if p['function'] != 'balanced' else p['s']
        fc = 1 if p['function'] == 'constant1' else 0
    s, c, note = _oracle_params(view, fs, fc)
    constant = '1' not in s
    p0 = marginal(view.final_state, view.n, list(range(n))).get('0' * n, 0.0)
    expected = 'P(' + '0' * n + ') = 1  (constant)' if constant else 'P(' + '0' * n + ') = 0  (balanced)'
    passed = abs(p0 - (1.0 if constant else 0.0)) < TOL
    verdict = 'constant' if p0 > 1 - TOL else 'balanced' if p0 < TOL else 'undetermined'
    row = _row(f'f(x) = {s}·x ⊕ {c}', f'P({"0" * n}) = {p0:.6f} → {verdict}', expected, p0 if constant else 1 - p0, passed)
    return [row], 'One oracle query decides constant versus balanced.' + note


def build_bv(p):
    n, s = p['n'], p['s']
    hs = [Gate('H', (q,)) for q in range(n)]
    states = defaults(n) + [InitialState.preset('-')]
    return Built(n + 1, hs + [parity_oracle(list(range(n)), n, s, 0)] + hs, states, tuple(range(n)),
                 'One query reveals the hidden string s.')


def spec_bv(p, view):
    n = p['n']
    s, _, note = _oracle_params(view, p['s'], 0)
    dist = marginal(view.final_state, view.n, list(range(n)))
    prob = dist.get(s, 0.0)
    top = max(dist, key=dist.get)
    row = _row(f's = {s}', f'most likely {top} (P = {dist[top]:.6f})', f'{s} with certainty', prob, abs(prob - 1) < TOL)
    return [row], 'The input register measures s with certainty.' + note


def grover_optimal_iterations(n):
    theta = math.asin(1 / math.sqrt(2 ** n))
    return max(0, round(math.pi / (4 * theta) - 0.5))


def grover_success(n, k):
    theta = math.asin(1 / math.sqrt(2 ** n))
    return math.sin((2 * k + 1) * theta) ** 2


def build_grover(p):
    n, marked = p['n'], p['marked']
    k = grover_optimal_iterations(n) if p['iterations'] < 0 else p['iterations']
    search = list(range(n))
    work = list(range(n, n + mcz_work_needed(n)))
    items = [Gate('H', (q,)) for q in search]
    for _ in range(k):
        items += [grover_oracle(search, work, marked), grover_diffusion(search, work)]
    total = n + len(work)
    note = f'{k} iteration(s); optimal for N = {2 ** n} is {grover_optimal_iterations(n)}.'
    if work:
        note += f' q{n}–q{total - 1} are work qubits for the multi-controlled Z; they start and end in |0⟩.'
    return Built(total, items, defaults(total), tuple(search), note)


def spec_grover(p, view):
    n = p['n']
    oracles = _blocks_of(view, 'grover_oracle')
    diffusions = _blocks_of(view, 'grover_diffusion')
    marks = {b.param('marked') for b in oracles}
    mixed = len(marks) > 1
    marked = next(iter(marks)) if len(marks) == 1 else p['marked']
    k = len(oracles)
    dist = marginal(view.final_state, view.n, list(range(n)))
    actual = dist.get(marked, 0.0)
    expected = grover_success(n, k)
    note = (f'{k} oracle/diffusion iteration(s): sin²((2k+1)θ) with sin θ = 1/√{2 ** n}. '
            f'Optimal: k = {grover_optimal_iterations(n)} (P = {grover_success(n, grover_optimal_iterations(n)):.4f}).')
    if mixed or len(diffusions) != k:
        passed = None
        note += ' The formula assumes one diffusion per oracle, all marking the same item.'
    else:
        passed = abs(actual - expected) < 1e-9
    row = _row(f'marked {marked}, k = {k}', f'P({marked}) = {actual:.6f}', f'sin²((2k+1)θ) = {expected:.6f}', actual, passed)
    return [row], note


def build_qft(p):
    n, x = p['n'], p['x']
    if not 0 <= x < 2 ** n:
        raise ValueError(f'Input value must be from 0 to {2 ** n - 1}')
    bits = format(x, f'0{n}b')
    states = [InitialState.preset(b) for b in bits]
    items = [qft_block(list(range(n)))]
    if p['inverse'] == 'yes':
        items.append(iqft_block(list(range(n))))
    return Built(n, items, states, (), 'The input |x⟩ is set by the initial states; click a wire label to change it.')


def dft_matrix(n):
    size = 2 ** n
    k = np.arange(size)
    return np.exp(2j * np.pi * np.outer(k, k) / size) / math.sqrt(size)


def spec_qft(p, view):
    n = p['n']
    qft = len(_blocks_of(view, 'qft'))
    inverse = len(_blocks_of(view, 'iqft'))
    f = dft_matrix(n)
    expected = np.linalg.matrix_power(f, qft) @ view.initial_vector
    expected = np.linalg.matrix_power(f.conj().T, inverse) @ expected if inverse else expected
    final = view.final_state
    fidelity = (float(np.real(np.vdot(expected, final @ expected))) if np.ndim(final) == 2   # noisy: ⟨e|ρ|e⟩
                else float(abs(np.vdot(expected, final)) ** 2))
    what = ('QFT' if qft else '') + (' then QFT†' if inverse else '')
    row = _row(f'{qft} QFT, {inverse} QFT† on the initial state', f'fidelity {fidelity:.9f}',
               f'{what.strip() or "identity"} of the input (DFT matrix)', fidelity, abs(fidelity - 1) < 1e-9)
    return [row], ('QFT|x⟩ = (1/√N) Σ_y e^{2πixy/N} |y⟩ with x, y read with q0 as the most significant bit. '
                   'Compared with the textbook DFT matrix.')


# ---- reversible examples (truth tables) ------------------------------------------------------------------

def truth_table(view, inputs, outputs, function, keep_inputs=True):
    """Check deterministic outputs for every basis input on `inputs` (others start in |0⟩).

    inputs: [(name, qubit)]; outputs: [(name, qubit)]; function(dict) -> dict of expected output bits.
    The chosen initial states are not used: every input combination is tested.
    """
    rows = []
    n = view.n
    for value in range(2 ** len(inputs)):
        bits = {name: (value >> (len(inputs) - 1 - i)) & 1 for i, (name, _) in enumerate(inputs)}
        state = np.zeros(2 ** n, complex)
        index = sum(bits[name] << (n - 1 - q) for name, q in inputs)
        state[index] = 1
        for g in view.gates:
            state = apply_gate(state, n, g)
        probs = distribution(state)
        top = int(np.argmax(probs))
        prob = float(probs[top])
        got = {name: (top >> (n - 1 - q)) & 1 for name, q in outputs}
        want = function(bits)
        ok = prob > 1 - TOL and all(got[k] == want[k] for k in want)
        if keep_inputs:
            # Inputs that are not also outputs must come back unchanged (reversible logic).
            output_qubits = {q for _, q in outputs}
            ok = ok and all(((top >> (n - 1 - q)) & 1) == bits[name] for name, q in inputs if q not in output_qubits)
        label = ' '.join(f'{k}={v}' for k, v in bits.items())
        rows.append(_row(label, ' '.join(f'{k}={v}' for k, v in got.items()) + ('' if prob > 1 - TOL else ' (not deterministic)'),
                         ' '.join(f'{k}={v}' for k, v in want.items()), prob, ok))
    return rows, 'Every input combination is checked; the truth table does not use the chosen initial states.'


def _inputs_from(p, names):
    return [InitialState.preset(str(p.get(k, 0))) for k in names]


# ---- dynamic examples (v0.6.1): mid-circuit measurement and feed-forward ---------------------

def build_teleport(p):
    from .dynamic import Conditioned, Measure
    items = [Gate('H', (1,)), Gate('CX', (1, 2)),                 # shared Bell pair between q1 and q2
             Gate('CX', (0, 1)), Gate('H', (0,)),                  # Bell measurement of q0 and q1 …
             Measure(0, 0), Measure(1, 1),                         # … recorded in c0 and c1
             Conditioned(Gate('X', (2,)), 1, 1), Conditioned(Gate('Z', (2,)), 0, 1)]   # corrections
    return Built(3, items, [InitialState.preset(p['input']), InitialState.preset('0'), InitialState.preset('0')],
                 note='Teleports q0\'s state to q2 using a Bell pair and two classical bits.',
                 roles=('Alice · input', 'Alice', 'Bob'))


TELEPORT_TESTS = ('0', '1', '+', '-', '+i', '-i')


def spec_teleport(p, view):
    """q2 must end in q0's starting state in every branch, for many inputs (not just the one shown)."""
    from .noise import partial_trace
    if view.n != 3 or view.simulate is None:
        return [], 'Teleportation needs 3 qubits.'
    rows = []
    inputs = [(InitialState.preset(k).label, InitialState.preset(k).vector()) for k in TELEPORT_TESTS]
    rng = np.random.default_rng(2026)
    for i in range(4):
        a = rng.normal(size=2) + 1j * rng.normal(size=2)
        inputs.append((f'random input {i + 1}', a / np.linalg.norm(a)))
    for label, a in inputs:
        start = np.kron(a, np.array([1, 0, 0, 0], complex))
        branches = view.simulate(start)
        fidelities = [float(np.real(np.vdot(a, partial_trace(b.rho, 3, [2]) @ a))) for b in branches]
        worst = min(fidelities)
        rows.append(_row(label, f'q2 fidelity {worst:.6f} in {len(branches)} branch(es)', 'q2 = input in every branch',
                         worst, worst > 1 - 1e-9))
    return rows, 'Each input is teleported from q0 to q2; every measurement branch must end with q2 equal to the input.'


def build_superdense(p):
    from .dynamic import Measure
    items = [Gate('H', (0,)), Gate('CX', (0, 1))]                 # shared Bell pair
    if p['b1']:
        items.append(Gate('X', (0,)))                              # encode: X for the second bit …
    if p['b0']:
        items.append(Gate('Z', (0,)))                              # … Z for the first
    items += [Gate('CX', (0, 1)), Gate('H', (0,)), Measure(0, 0), Measure(1, 1)]   # decode
    return Built(2, items, [InitialState.preset('0')] * 2,
                 note=f'Sends the two bits {p["b0"]}{p["b1"]} by transmitting only q0.', roles=('Alice', 'Bob'))


def spec_superdense(p, view):
    from .dynamic import record_distribution
    if not view.branches:
        return [], 'Superdense coding needs mid-circuit measurements into c0 and c1.'
    expected = f'{p["b0"]}{p["b1"]}'
    record = record_distribution(view.branches)
    probability = record.get(expected, 0.0)
    best = max(record, key=record.get)
    return [_row(f'message {expected}', f'received {best} (P = {record[best]:.6f})', f'received {expected}',
                 probability, probability > 1 - 1e-9)], 'The two classical bits c0c1 must equal the message.'


# ---- error correction (v0.6.2) ---------------------------------------------------------------

QEC_ERRORS = (('No error', 'none'), ('Error on q0', 'q0'), ('Error on q1', 'q1'), ('Error on q2', 'q2'),
              ('Two errors (q0 and q1)', 'q0q1'), ('Random errors on every data qubit', 'random'))
QEC_STRENGTHS = tuple((f'p = {v:g}', v) for v in (0.01, 0.05, 0.1, 0.2, 0.3))


def _repetition(code):
    def build(p):
        from .qec import build_repetition
        n, items, states = build_repetition(code, p['logical'], p['error'], p.get('p', 0.1))
        kind = 'Z (phase-flip)' if code == 'phase_flip' else 'X (bit-flip)'
        return Built(n, items, states, note=f'Data q0–q2 encode q0\'s starting state; {kind} errors are '
                                            'detected by q3, q4 (measured into c0, c1) and corrected.',
                     roles=('data', 'data', 'data', 'syndrome', 'syndrome'))
    return build


def _repetition_spec(code):
    def spec(p, view):
        """The data qubits must hold the encoded input after correction (for the six standard inputs)."""
        from .noise import partial_trace
        from .qec import logical_state
        if view.n != 5 or view.simulate is None:
            return [], 'This check needs the 5-qubit code with mid-circuit syndrome measurement.'
        rows = []
        for key in ('0', '1', '+', '-', '+i', '-i'):
            a = InitialState.preset(key).vector()
            start = np.kron(a, np.eye(16)[0])
            rho = partial_trace(sum(b.sigma for b in view.simulate(start)), 5, [0, 1, 2])
            target = logical_state(code, a)
            fidelity = float(np.real(np.vdot(target, rho @ target)))
            rows.append(_row(f'logical {InitialState.preset(key).label}', f'fidelity {fidelity:.6f}',
                             'encoded state restored', fidelity, fidelity > 1 - 1e-9))
        limit = (' Two errors are beyond what the code can correct, so some inputs fail: that is its limit.'
                 if p.get('error') == 'q0q1' else '')
        noisy = (' With random errors, fidelity below 1 is expected: use Plot logical error rate.'
                 if p.get('error') == 'random' else '')
        return rows, 'After correction, q0–q2 must hold the encoded input for every starting state.' + limit + noisy
    return spec


def build_shor_example(p):
    from .qec import build_shor
    error = p['error']
    qubit = None if error == 'none' else int(error[1:])
    n, items, states = build_shor(p['logical'], qubit, error[0] if error != 'none' else 'X')
    return Built(n, items, states, note='Shor\'s code spreads q0 over 9 qubits and corrects any single-qubit '
                                        'error coherently; the logical qubit ends back in q0.',
                 roles=('logical',) + ('code',) * 8)


def spec_shor(p, view):
    from .noise import density, partial_trace
    from .circuits import evolution
    rows = []
    for key in ('0', '1', '+', '-', '+i', '-i'):
        a = InitialState.preset(key).vector()
        final = evolution(9, view.gates, np.kron(a, np.eye(256)[0]))[-1]
        q0 = partial_trace(density(final), 9, [0])
        fidelity = float(np.real(np.vdot(a, q0 @ a)))
        rows.append(_row(f'input {InitialState.preset(key).label}', f'q0 fidelity {fidelity:.6f}', 'q0 = input',
                         fidelity, fidelity > 1 - 1e-9))
    return rows, 'q0 must end in its starting state whatever single-qubit error was injected.'


SHOR_ERRORS = (('No error', 'none'),) + tuple((f'{k} on q{q}', f'{k}{q}') for k in 'XYZ' for q in range(9))


# ---- quantum phase estimation (v0.6.2) ------------------------------------------------------

QPE_PHASES = (('3/8 (exact with 3 or more counting qubits)', '3/8'), ('1/4 (exact)', '1/4'),
              ('5/16 (exact with 4 or more)', '5/16'), ('1/3 (not exact)', '1/3'), ('0.3 (not exact)', '0.3'),
              ('0.1 (not exact)', '0.1'))


def _phase_value(text):
    if '/' in text:
        a, b = text.split('/')
        return int(a) / int(b)
    return float(text)


def build_qpe(p):
    """Estimate φ in U = P(2πφ), whose eigenstate |1⟩ sits in the last qubit."""
    t, phi = p['t'], _phase_value(p['phase'])
    target = t
    items = [Gate('H', (j,)) for j in range(t)]
    # counting qubit j controls U^(2^(t−1−j)): q0 holds the most significant bit of the estimate
    items += [Gate('CP', (j, target), 2 * math.pi * phi * 2 ** (t - 1 - j)) for j in range(t)]
    items.append(iqft_block(range(t)))
    states = [InitialState.preset('0')] * t + [InitialState.preset('1')]
    return Built(t + 1, items, states, measured=tuple(range(t)), roles=('count',) * t + ('eigenstate',),
                 note=f'q0–q{t - 1} read out the best {t}-bit estimate of φ = {p["phase"]}; the last qubit holds U\'s eigenstate |1⟩.')


def spec_qpe(p, view):
    t, phi = p['t'], _phase_value(p['phase'])
    if view.n != t + 1:
        return [], f'Phase estimation with {t} counting qubits needs {t + 1} qubits.'
    probs = marginal(view.final_state, view.n, list(range(t)))
    best = max(probs, key=probs.get)
    closest = round(phi * 2 ** t) % 2 ** t
    exact = abs(phi * 2 ** t - round(phi * 2 ** t)) < 1e-9
    target_bits = format(closest, f'0{t}b')
    p_best = probs.get(target_bits, 0.0)
    bound = 1.0 if exact else 4 / math.pi ** 2
    rows = [_row(f'φ = {p["phase"]}', f'most likely {best} → {int(best, 2) / 2 ** t:.4f}',
                 f'{target_bits} → {closest / 2 ** t:.4f}', p_best, best == target_bits and p_best >= bound - 1e-9)]
    note = ('φ has an exact t-bit expansion, so the estimate is certain.' if exact else
            f'φ is not a multiple of 1/{2 ** t}: the closest estimate wins with probability {p_best:.3f} '
            f'(at least 4/π² ≈ 0.405 in theory); more counting qubits sharpen it.')
    return rows, note


def build_full_adder(p):
    gates = [Gate('CCX', (0, 1, 3)), Gate('CX', (0, 1)), Gate('CCX', (1, 2, 3)), Gate('CX', (1, 2)), Gate('CX', (0, 1))]
    return Built(4, gates, _inputs_from(p, ('a', 'b', 'cin')) + [InitialState()], (2, 3),
                 'q0 = a, q1 = b (restored), q2 = cin → sum, q3 = cout. Click wire labels to change the inputs.')


def spec_full_adder(p, view):
    return truth_table(view, [('a', 0), ('b', 1), ('cin', 2)], [('sum', 2), ('cout', 3)],
                       lambda b: {'sum': b['a'] ^ b['b'] ^ b['cin'],
                                  'cout': (b['a'] & b['b']) | (b['cin'] & (b['a'] ^ b['b']))})


def build_comparator(p):
    a1, a0, b1, b0, eq, gt, w = range(7)
    gates = [Gate('CX', (a1, b1)), Gate('CX', (a0, b0)),                 # b becomes a ⊕ b
             Gate('X', (b1,)), Gate('X', (b0,)), Gate('CCX', (b1, b0, eq)), Gate('X', (b1,)), Gate('X', (b0,)),
             Gate('CCX', (a1, b1, gt)),                                    # a1 = 1, b1 = 0
             Gate('CCX', (a0, b0, w)), Gate('X', (b1,)), Gate('CCX', (b1, w, gt)), Gate('X', (b1,)),
             Gate('CCX', (a0, b0, w)),                                     # a1 = b1, a0 = 1, b0 = 0
             Gate('CX', (a0, b0)), Gate('CX', (a1, b1))]                   # restore b
    return Built(7, gates, _inputs_from(p, ('a1', 'a0', 'b1', 'b0')) + defaults(3), (4, 5),
                 'A = q0q1, B = q2q3 (restored); q4 = (A = B), q5 = (A > B); q6 is a work qubit.')


def spec_comparator(p, view):
    def f(b):
        a, bb = 2 * b['a1'] + b['a0'], 2 * b['b1'] + b['b0']
        return {'eq': int(a == bb), 'gt': int(a > bb), 'work': 0}
    return truth_table(view, [('a1', 0), ('a0', 1), ('b1', 2), ('b0', 3)], [('eq', 4), ('gt', 5), ('work', 6)], f)


def build_increment(p):
    gates = [Gate('CCX', (0, 2, 1)), Gate('CX', (0, 2))]
    return Built(3, gates, _inputs_from(p, ('c', 'x1', 'x0')), (1, 2),
                 'If the control q0 is 1, the 2-bit counter q1q2 increases by 1 (mod 4).')


def spec_increment(p, view):
    def f(b):
        value = (2 * b['x1'] + b['x0'] + b['c']) % 4
        return {'x1': value >> 1, 'x0': value & 1}
    return truth_table(view, [('c', 0), ('x1', 1), ('x0', 2)], [('x1', 1), ('x0', 2)], f)


def build_and(p):
    return Built(3, [Gate('CCX', (0, 1, 2))], _inputs_from(p, ('a', 'b')) + [InitialState()], (2,),
                 'A Toffoli writes a AND b into q2, which starts in |0⟩.')


def spec_and(p, view):
    return truth_table(view, [('a', 0), ('b', 1)], [('out', 2)], lambda b: {'out': b['a'] & b['b']})


def build_mux(p):
    return Built(3, [Gate('CSWAP', (0, 1, 2))], _inputs_from(p, ('s', 'x', 'y')), (1, 2),
                 'A Fredkin gate: if s = 1 it swaps x and y, so q1 = (s ? y : x).')


def spec_mux(p, view):
    return truth_table(view, [('s', 0), ('x', 1), ('y', 2)], [('out', 1), ('other', 2)],
                       lambda b: {'out': b['y'] if b['s'] else b['x'], 'other': b['x'] if b['s'] else b['y']})


# ---- the registry --------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Entry:
    key: str
    menu: str                     # 'Algorithms' or 'Examples'
    title: str
    params: tuple
    build: object
    spec: object
    description: str = ''


def _bit(key, label):
    return Param(key, label, 'choice', 1, choices=(('0', 0), ('1', 1)))


LIBRARY = (
    Entry('deutsch', 'Algorithms', 'Deutsch',
          (Param('function', 'Function f', 'choice', 'x', choices=DEUTSCH_FUNCTIONS),),
          build_deutsch, lambda p, v: spec_dj(p, v, 1),
          'Decide whether a 1-bit function is constant or balanced with a single query.'),
    Entry('deutsch_jozsa', 'Algorithms', 'Deutsch–Jozsa',
          (Param('n', 'Input qubits', 'int', 3, 1, 6),
           Param('function', 'Function', 'choice', 'balanced',
                 choices=(('Constant 0', 'constant0'), ('Constant 1', 'constant1'),
                          ('Balanced: parity of the bits chosen by s', 'balanced'))),
           Param('s', 'Bits used by the balanced function (s)', 'bits', '101', length_of='n')),
          build_dj, spec_dj, 'Constant or balanced for n input bits, with one query.'),
    Entry('bernstein_vazirani', 'Algorithms', 'Bernstein–Vazirani',
          (Param('n', 'Input qubits', 'int', 4, 1, 6),
           Param('s', 'Hidden string s', 'bits', '1011', length_of='n')),
          build_bv, spec_bv, 'Recover a hidden bit string s from f(x) = s·x in one query.'),
    Entry('grover', 'Algorithms', 'Grover search',
          (Param('n', 'Search qubits', 'int', 3, 2, 5),
           Param('marked', 'Marked item', 'bits', '101', length_of='n'),
           Param('iterations', 'Iterations (−1 = optimal)', 'int', -1, -1, 12)),
          build_grover, spec_grover, 'Amplify the marked item; success probability sin²((2k+1)θ).'),
    Entry('qft', 'Algorithms', 'Quantum Fourier transform',
          (Param('n', 'Qubits', 'int', 3, 1, 6), Param('x', 'Input value x', 'int', 5, 0, 63),
           Param('inverse', 'Follow with QFT†', 'choice', 'no', choices=(('No', 'no'), ('Yes', 'yes')))),
          build_qft, spec_qft, 'QFT of a basis state; phase patterns are visible in the State Inspector.'),
    Entry('teleportation', 'Examples', 'Quantum teleportation',
          (Param('input', 'State of q0 to teleport', 'choice', '+i',
                 choices=tuple((InitialState.preset(k).label, k) for k in TELEPORT_TESTS)),),
          build_teleport, spec_teleport, 'Mid-circuit measurement and classically controlled corrections'),
    Entry('superdense', 'Examples', 'Superdense coding', (_bit('b0', 'first bit'), _bit('b1', 'second bit')),
          build_superdense, spec_superdense, 'Two classical bits sent with one qubit and shared entanglement'),
    Entry('qpe', 'Algorithms', 'Quantum phase estimation',
          (Param('t', 'Counting qubits', 'int', 4, 1, 6), Param('phase', 'Phase φ of U = P(2πφ)', 'choice', '5/16',
                                                                choices=QPE_PHASES)),
          build_qpe, spec_qpe, 'Estimates an eigenphase with controlled powers of U and the inverse QFT'),
    Entry('bit_flip_code', 'Examples', 'Bit-flip code',
          (Param('logical', 'Logical state (q0)', 'choice', '1',
                 choices=tuple((InitialState.preset(k).label, k) for k in TELEPORT_TESTS)),
           Param('error', 'Error', 'choice', 'q1', choices=QEC_ERRORS),
           Param('p', 'Random error strength', 'choice', 0.1, choices=QEC_STRENGTHS)),
          _repetition('bit_flip'), _repetition_spec('bit_flip'), '3-qubit code with syndrome measurement and correction'),
    Entry('phase_flip_code', 'Examples', 'Phase-flip code',
          (Param('logical', 'Logical state (q0)', 'choice', '+',
                 choices=tuple((InitialState.preset(k).label, k) for k in TELEPORT_TESTS)),
           Param('error', 'Error', 'choice', 'q1', choices=QEC_ERRORS),
           Param('p', 'Random error strength', 'choice', 0.1, choices=QEC_STRENGTHS)),
          _repetition('phase_flip'), _repetition_spec('phase_flip'), 'The same code in the |±⟩ basis, for Z errors'),
    Entry('shor_code', 'Examples', 'Shor code (9 qubits)',
          (Param('logical', 'Logical state (q0)', 'choice', '+i',
                 choices=tuple((InitialState.preset(k).label, k) for k in TELEPORT_TESTS)),
           Param('error', 'Error', 'choice', 'Y4', choices=SHOR_ERRORS)),
          build_shor_example, spec_shor, 'Corrects any single-qubit error, coherently'),
    Entry('full_adder', 'Examples', 'Full adder', (_bit('a', 'a'), _bit('b', 'b'), _bit('cin', 'cin')),
          build_full_adder, spec_full_adder),
    Entry('comparator', 'Examples', '2-bit comparator',
          (_bit('a1', 'a1'), _bit('a0', 'a0'), Param('b1', 'b1', 'choice', 0, choices=(('0', 0), ('1', 1))), _bit('b0', 'b0')),
          build_comparator, spec_comparator),
    Entry('controlled_increment', 'Examples', 'Controlled increment (2-bit)',
          (_bit('c', 'c'), _bit('x1', 'x1'), Param('x0', 'x0', 'choice', 0, choices=(('0', 0), ('1', 1)))),
          build_increment, spec_increment),
    Entry('toffoli_and', 'Examples', 'Toffoli as AND', (_bit('a', 'a'), _bit('b', 'b')), build_and, spec_and),
    Entry('fredkin_mux', 'Examples', 'Fredkin multiplexer',
          (_bit('s', 's'), Param('x', 'x', 'choice', 0, choices=(('0', 0), ('1', 1))), _bit('y', 'y')),
          build_mux, spec_mux),
)

ENTRIES = {e.key: e for e in LIBRARY}


def entry(key):
    if key not in ENTRIES:
        raise ValueError('Unknown library entry: ' + str(key))
    return ENTRIES[key]


def build(key, values=None):
    e = entry(key)
    params = validate_params(e.params, dict(values or {}))
    return params, e.build(params)
