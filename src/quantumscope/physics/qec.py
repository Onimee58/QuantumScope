"""Quantum error correction: repetition codes and the Shor code (Qt-free).

Builders return the same Built objects as the algorithm library, so the codes appear as
Examples. Repetition codes use 5 qubits: data q0–q2 and syndrome ancillas q3, q4 measured
mid-circuit into c0 (q0⊕q1) and c1 (q1⊕q2); corrections are conditioned on both bits.
"""
import numpy as np

from .circuits import Gate
from .dynamic import Conditioned, Measure
from .initial_states import InitialState
from .noise import NoiseElement

DATA = (0, 1, 2)
INPUTS = ('0', '1', '+', '-', '+i', '-i')
# syndrome c0c1 -> data qubit to correct
SYNDROME = {(1, 0): 0, (1, 1): 1, (0, 1): 2}
CHANNEL_OF = {'bit_flip': 'bit_flip', 'phase_flip': 'phase_flip', 'depolarizing': 'depolarizing'}


def _encode(code):
    gates = [Gate('CX', (0, 1)), Gate('CX', (0, 2))]                    # a|000⟩ + b|111⟩
    if code == 'phase_flip':
        gates += [Gate('H', (q,)) for q in DATA]                        # a|+++⟩ + b|−−−⟩
    return gates


def _syndrome(code):
    """Parity checks onto q3 (q0⊕q1) and q4 (q1⊕q2), measured into c0 and c1."""
    gates = [Gate('H', (q,)) for q in DATA] if code == 'phase_flip' else []      # X-parities for the phase code
    gates += [Gate('CX', (0, 3)), Gate('CX', (1, 3)), Gate('CX', (1, 4)), Gate('CX', (2, 4))]
    gates += [Gate('H', (q,)) for q in DATA] if code == 'phase_flip' else []
    return gates + [Measure(3, 0), Measure(4, 1)]


def _correct(code):
    fix = 'Z' if code == 'phase_flip' else 'X'
    return [Conditioned(Gate(fix, (q,)), (0, 1), bits) for bits, q in SYNDROME.items()]


def error_items(error, p=0.1, kind='X'):
    """Injected errors: 'none', 'q0'/'q1'/'q2', 'q0q1' (two errors), or 'random' (a noise box per data qubit)."""
    if error == 'none':
        return []
    if error == 'random':
        channel = {'X': 'bit_flip', 'Z': 'phase_flip'}.get(kind, 'depolarizing')
        return [NoiseElement(channel, q, p) for q in DATA]
    qubits = [int(ch) for ch in error.replace('q', '')]
    return [Gate(kind, (q,)) for q in qubits]


def build_repetition(code, logical, error, p=0.1):
    """Items for the bit-flip ('bit_flip') or phase-flip ('phase_flip') code."""
    kind = 'Z' if code == 'phase_flip' else 'X'
    items = _encode(code) + error_items(error, p, kind) + _syndrome(code) + _correct(code)
    states = [InitialState.preset(logical)] + [InitialState.preset('0')] * 4
    return 5, items, states


def logical_state(code, input_vector):
    """The ideal encoded 3-qubit state for a logical input a|0⟩ + b|1⟩."""
    a, b = input_vector
    if code == 'phase_flip':
        plus, minus = np.array([1, 1]) / np.sqrt(2), np.array([1, -1]) / np.sqrt(2)
        zero = np.kron(np.kron(plus, plus), plus)
        one = np.kron(np.kron(minus, minus), minus)
    else:
        zero, one = np.eye(8)[0], np.eye(8)[7]
    return a * zero + b * one


# ---- the Shor code (9 qubits, coherent correction) -----------------------------------------------

def build_shor(logical, error_qubit=None, error_kind='X'):
    """Shor's 9-qubit code, corrected coherently (Toffoli majority votes, no ancillas):
    the logical qubit ends back in q0 whatever single-qubit error occurred."""
    items = [Gate('CX', (0, 3)), Gate('CX', (0, 6))]
    items += [Gate('H', (q,)) for q in (0, 3, 6)]
    for top in (0, 3, 6):
        items += [Gate('CX', (top, top + 1)), Gate('CX', (top, top + 2))]
    if error_qubit is not None:
        for kind in ('X', 'Z') if error_kind == 'Y' else (error_kind,):
            items.append(Gate(kind, (error_qubit,)))
    for top in (0, 3, 6):                                                # bit-flip majority in each block
        items += [Gate('CX', (top, top + 1)), Gate('CX', (top, top + 2)), Gate('CCX', (top + 1, top + 2, top))]
    items += [Gate('H', (q,)) for q in (0, 3, 6)]
    items += [Gate('CX', (0, 3)), Gate('CX', (0, 6)), Gate('CCX', (3, 6, 0))]  # phase-flip majority across blocks
    return 9, items, [InitialState.preset(logical)] + [InitialState.preset('0')] * 8


# ---- exact failure rates for single-qubit channels (the comparison line and theory) -------------

def unprotected_failure(channel, p):
    """Worst-case infidelity of one qubit sent through the channel: bit/phase flip p, depolarizing p/2."""
    return p / 2 if channel == 'depolarizing' else p


def repetition_theory(code, channel, p):
    """Known closed forms (None when there is no simple one)."""
    if (code, channel) in (('bit_flip', 'bit_flip'), ('phase_flip', 'phase_flip')):
        return 3 * p ** 2 - 2 * p ** 3                                  # two or more errors defeat the code
    if (code, channel) in (('bit_flip', 'phase_flip'), ('phase_flip', 'bit_flip')):
        return (1 - (1 - 2 * p) ** 3) / 2                               # any odd number of errors flips the logical
    return None
