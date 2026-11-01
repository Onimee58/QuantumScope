"""Logical error rate of an error-correcting circuit (Qt-free, shared by the chart and the explorer).

The sweep sets every noise box in the circuit to the same strength p and measures how far
the data qubits end up from the noiseless result, in the worst case over the six standard
starting states of q0: the logical failure rate.
"""
import copy

import numpy as np

from quantumscope.physics import noise as N
from quantumscope.physics.dynamic import averaged
from quantumscope.physics.initial_states import InitialState

INPUTS = ('0', '1', '+', '-', '+i', '-i')


def _data_state(model, data):
    return N.partial_trace(averaged(model.simulate_branches(store=False)[1][-1]), model.n, list(data))


def logical_failure(model, p, data=(0, 1, 2)):
    """Worst-case (over q0's six standard inputs) infidelity of the data qubits at noise strength p."""
    noisy = copy.deepcopy(model)
    clean = copy.deepcopy(model)
    for key, item in list(model.wires.items()):
        if isinstance(item, N.NoiseElement):
            noisy.wires[key] = N.NoiseElement(item.kind, item.qubit, p)
            del clean.wires[key]
    worst = 0.0
    for key in INPUTS:
        for m in (noisy, clean):
            m.initial_states = [InitialState.preset(key)] + list(model.initial_states[1:])
        ideal = _data_state(clean, data)
        target = np.linalg.eigh(ideal)[1][:, -1]                  # the noiseless result is pure
        fidelity = float(np.real(np.vdot(target, _data_state(noisy, data) @ target)))
        worst = max(worst, 1 - fidelity)
    return worst


def curve(model, ps, data=(0, 1, 2)):
    return [logical_failure(model, p, data) for p in ps]


def noise_kind(model):
    kinds = {e.kind for e in model.wires.values() if isinstance(e, N.NoiseElement)}
    return kinds.pop() if len(kinds) == 1 else None


def example_model(code, channel, p=0.1):
    """A ready-made circuit: the code ('none', 'bit_flip', 'phase_flip') with noise boxes of `channel`."""
    from quantumscope.editor.circuit_model import CircuitModel
    from quantumscope.physics.circuits import Gate
    from quantumscope.physics.qec import build_repetition
    m = CircuitModel()
    if code == 'none':
        m.set_circuit(1, [], noise=[(N.NoiseElement(channel, 0, p), 0)])
        return m, (0,)
    n, items, states = build_repetition(code, '0', 'none')
    # the channel acts on every data qubit right after encoding
    from quantumscope.physics.algorithms import Built
    encode = 2 + (3 if code == 'phase_flip' else 0)
    items = items[:encode] + [N.NoiseElement(channel, q, p) for q in (0, 1, 2)] + items[encode:]
    _load(m, Built(n, items, states))
    return m, (0, 1, 2)


def _load(model, built):
    from quantumscope.physics import algorithms
    algorithms.ENTRIES['_qec_tmp'] = algorithms.Entry('_qec_tmp', 'Examples', '', (), lambda p: built,
                                                     lambda p, v: ([], ''), '')
    try:
        model.load_library('_qec_tmp', {})
        model.active_entry = None
    finally:
        del algorithms.ENTRIES['_qec_tmp']
