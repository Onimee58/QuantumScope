"""The teleportation protocol as a story in five steps (Qt-free), for the Quantum Principles
experiment. It runs the same branch engine as the circuit simulator, so both views agree.

q0: the qubit Alice wants to send · q1: Alice's half of a Bell pair · q2: Bob's half
"""
import numpy as np

from .circuits import Gate
from .dynamic import Conditioned, Measure, record_distribution, simulate
from .noise import NoiseModel, bloch, partial_trace, purity

STEPS = (
    ('Ready', 'Alice holds the qubit q0 she wants to send. Bob is far away. They will share a Bell pair.'),
    ('Share a Bell pair', 'q1 and q2 are entangled into a Bell pair: Alice keeps q1, Bob takes q2. On its own, '
                          'Bob\'s qubit is completely random (its arrow has length 0).'),
    ('Alice entangles', 'Alice applies CX from q0 to q1, then H to q0. Her qubits are now entangled with Bob\'s, '
                        'but nothing has changed for Bob yet: his qubit is still completely random.'),
    ('Alice measures', 'Alice measures q0 and q1, getting two classical bits. Her original state is destroyed. '
                       'For each result, Bob\'s qubit is the input rotated in a different way — but Bob does not '
                       'know which yet, so to him it is still random.'),
    ('Bob corrects', 'The two bits travel to Bob by an ordinary (light-speed) channel. Bob applies X if c1 = 1 '
                     'and Z if c0 = 1. Now his qubit is exactly Alice\'s original state, for every result.'),
)

_COLUMNS = (
    [],
    [[Gate('H', (1,))], [Gate('CX', (1, 2))]],
    [[Gate('CX', (0, 1))], [Gate('H', (0,))]],
    [[Measure(0, 0), Measure(1, 1)]],
    [[Conditioned(Gate('X', (2,)), 1, 1)], [Conditioned(Gate('Z', (2,)), 0, 1)]],
)


def columns_through(step):
    return [column for chunk in _COLUMNS[:step + 1] for column in chunk]


CLASSICAL_LIMIT = 2 / 3     # the best average fidelity without entanglement (measure, then rebuild)


def expected_fidelity(visibility=1.0, correct=True):
    """Average fidelity for a pair with `visibility` (1 = clean): (1 + v)/2 with Bob's correction,
    1/2 without it (his qubit is then, on average, completely random)."""
    return (1 + visibility) / 2 if correct else 0.5


def _columns(step, correct):
    columns = columns_through(step)
    if step >= 4 and not correct:                       # Bob skips the conditioned X and Z
        columns = columns_through(3)
    return columns


def state_at(input_vector, step, record=None, visibility=1.0, correct=True):
    """What the experiment shows after `step` (0–4).

    record: None for the view of someone who does not know the measurement result
    (the average over all branches), or a string like '01' for one result (from step 3).
    visibility < 1: the shared pair is noisy, v·(Bell pair) + (1 − v)·(completely random pair);
    correct=False: Bob skips his correction in step 4.
    Returns blochs (q0, q1, q2), Bob's purity and fidelity with the input, the
    probabilities of the four results, and the record shown.
    """
    a = np.asarray(input_vector, complex)
    a = a / np.linalg.norm(a)
    v = float(min(1.0, max(0.0, visibility)))
    # A completely random pair is the average over the four starting pairs |jk⟩ (H then CX turns
    # them into the four Bell states); the protocol is linear, so the noisy pair is a weighted mix.
    starts = [(v + (1 - v) / 4, 0)] + [((1 - v) / 4, k) for k in (1, 2, 3)] if v < 1 else [(1.0, 0)]
    sigmas, probabilities = {}, {}
    for weight, pair in starts:
        if weight <= 0:
            continue
        start = np.kron(a, np.eye(4, dtype=complex)[pair])
        for branch in simulate(3, _columns(step, correct), start, NoiseModel(), 0.0, False)[-1]:
            key = ''.join(map(str, branch.bits)) if step >= 3 else ''
            sigmas[key] = sigmas.get(key, 0) + weight * branch.sigma
    if step >= 3:
        probabilities = {key: float(np.real(np.trace(sigma))) for key, sigma in sigmas.items()}
    if record is not None and step >= 3:
        if record not in sigmas:
            raise ValueError(f'No measurement result {record}')
        rho = sigmas[record] / probabilities[record]
    else:
        rho = sum(sigmas.values())
        record = None
    bob = partial_trace(rho, 3, [2])
    return {'blochs': [bloch(partial_trace(rho, 3, [q])) for q in range(3)],
            'bob_purity': purity(bob), 'bob_fidelity': float(np.real(np.vdot(a, bob @ a))),
            'probabilities': probabilities, 'record': record}


def teleport_once(input_vector, visibility=1.0, correct=True, rng=None):
    """One complete run: (record, Bob's fidelity with the input)."""
    rng = rng or np.random.default_rng()
    probabilities = state_at(input_vector, 3, visibility=visibility)['probabilities']
    keys = sorted(probabilities)
    weights = np.array([probabilities[k] for k in keys])
    record = keys[int(rng.choice(len(keys), p=weights / weights.sum()))]
    return record, state_at(input_vector, 4, record, visibility, correct)['bob_fidelity']


def random_record(rng=None):
    """One measurement result; all four are equally likely for every input state."""
    rng = rng or np.random.default_rng()
    return format(int(rng.integers(4)), '02b')
