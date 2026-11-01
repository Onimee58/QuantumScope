"""Automatic checks for lab steps (no Qt).

Each `check:` line in a ```step``` block is one condition on the student's
current circuit; a step is done when all of its checks pass:

    qubits 2                         the circuit has exactly 2 qubits
    state H:0;CX:0,1                 the final state equals this circuit's (from |0…0⟩), up to global phase
    probability 00=0.5 11=0.5        measurement probabilities of whole-register outcomes (q0 first)
    entangled 0                      qubit 0 is (maximally) entangled with the rest: reduced entropy ≥ 0.99 bit
    gates <= 4                       at most 4 gates (blocks count their real gates)
    uses H,CX                        the circuit contains these gate types
    starts 0:-                       qubit 0 starts in |−⟩ (initial state preset)
    noise depolarizing               a noise channel of this kind is placed in the circuit
    fidelity <= 0.8                  fidelity of the (noisy) final state with the ideal one (also >=)
    purity <= 0.9                    purity Tr(ρ²) of the (noisy) final state (also >=)
    measures >= 2                    number of mid-circuit measurements (M→c) (also <=, =)
    conditions >= 1                  number of classically conditioned gates (also <=, =)
    branches = 4                     number of measurement branches at the end (also <=, >=)
    record 00=0.25 11=0.75           probabilities of classical records (c0 first)
    teleports 0 2                    in every branch, qubit 2 ends in qubit 0's starting state
    settles 0 0                      in every branch, qubit 0 ends in |0⟩ (or |1⟩ with "settles 0 1")
"""
import numpy as np

from quantumscope.physics.circuits import evolution
from quantumscope.physics.initial_states import InitialState

TOL = 1e-6


def _final_state(model):
    return model.simulate().column_states[-1]


def check(model, condition):
    """(passed?, explanation) for one condition against an editor model."""
    words = condition.split(None, 1)
    if not words:
        return False, 'Empty check'
    kind, rest = words[0].lower(), (words[1] if len(words) > 1 else '').strip()
    if kind == 'qubits':
        return model.n == int(rest), f'needs {rest} qubits'
    if kind == 'state':
        from .actions import _gates
        try:
            target = evolution(model.n, _gates(rest, model.n))[-1]
        except ValueError:                       # e.g. the expected circuit needs more qubits than this one has
            return False, 'the circuit does not have the qubits this step needs'
        fidelity = abs(np.vdot(target, _final_state(model))) ** 2
        return fidelity > 1 - TOL, 'the final state is not the expected one yet'
    if kind == 'probability':
        probs = np.abs(_final_state(model)) ** 2
        for item in rest.split():
            bits, _, value = item.partition('=')
            if len(bits) != model.n:
                return False, f'this step needs {len(bits)} qubits'
            if abs(probs[int(bits, 2)] - float(value)) > 1e-6:
                return False, f'P({bits}) should be {value}'
        return True, ''
    if kind == 'entangled':
        from quantumscope.physics.state_analysis import reduced_summary
        if int(rest) >= model.n or model.n < 2:
            return False, f'needs a qubit q{rest} and at least one other'
        info = reduced_summary(_final_state(model), model.n, [int(rest)])
        return info['entropy'] > 0.99, f'q{rest} is not entangled yet'
    if kind == 'gates':
        op, value = rest.split()
        count = len(model.ordered())
        ok = {'<=': count <= int(value), '>=': count >= int(value), '=': count == int(value)}[op]
        return ok, f'uses {count} gates (needs {op} {value})'
    if kind == 'uses':
        present = {g.name for g in model.ordered()}
        missing = [name for name in rest.replace(' ', '').upper().split(',') if name not in present]
        return not missing, f'add {", ".join(missing)}' if missing else ''
    if kind == 'starts':
        qubit, _, preset = rest.partition(':')
        q = int(qubit)
        return q < model.n and model.initial_states[q] == InitialState.preset(preset), f'q{q} should start in |{preset}⟩'
    if kind == 'noise':
        present = {e.kind for e in model.noise.values()}
        return rest.strip() in present, f'place a {rest.strip().replace("_", " ")} channel'
    if kind in ('fidelity', 'purity'):
        from quantumscope.physics import noise as N
        op, value = rest.split()
        ideal = _final_state(model)
        rho = model.simulate_noisy(store=False)[1][-1] if model.noisy else N.density(ideal)
        measure = N.fidelity_with_pure(rho, ideal) if kind == 'fidelity' else N.purity(rho)
        ok = {'<=': measure <= float(value) + 1e-9, '>=': measure >= float(value) - 1e-9}[op]
        return ok, f'{kind} is {measure:.3f} (needs {op} {value})'
    if kind in ('measures', 'conditions', 'branches'):
        from quantumscope.physics.dynamic import Measure
        op, value = rest.split()
        if kind == 'measures':
            count = sum(isinstance(v, Measure) for v in model.wires.values())
        elif kind == 'conditions':
            count = len(model.conditions)
        else:
            count = len(model.simulate_branches(store=False)[1][-1])
        ok = {'<=': count <= int(value), '>=': count >= int(value), '=': count == int(value)}[op]
        return ok, f'{kind}: {count} (needs {op} {value})'
    if kind == 'record':
        from quantumscope.physics.dynamic import record_distribution
        record = record_distribution(model.simulate_branches(store=False)[1][-1])
        for item in rest.split():
            bits, _, value = item.partition('=')
            if abs(record.get(bits, 0.0) - float(value)) > 1e-6:
                return False, f'P(record {bits}) should be {value}'
        return True, ''
    if kind in ('teleports', 'settles'):
        from quantumscope.physics import noise as N
        a, b = (int(x) for x in rest.split())
        if max(a, b if kind == 'teleports' else a) >= model.n:
            return False, 'the circuit does not have these qubits'
        branches = model.simulate_branches(store=False)[1][-1]
        if kind == 'teleports':
            target = model.initial_states[a].vector()
            target_q = b
        else:
            target = np.array([1, 0] if b == 0 else [0, 1], complex)
            target_q = a
        worst = min(float(np.real(np.vdot(target, N.partial_trace(br.rho, model.n, [target_q]) @ target)))
                    for br in branches)
        return worst > 1 - 1e-6, f'q{target_q} does not match in every branch yet (worst fidelity {worst:.3f})'
    raise ValueError(f'Unknown check: {kind}')


def step_done(model, step):
    """(done?, first unmet explanation) for a parsed step."""
    for condition in step['checks']:
        ok, why = check(model, condition)
        if not ok:
            return False, why
    return bool(step['checks']), ''


def progress(model, steps):
    """{step number: done?} for a lab. Labs build on themselves, so a step also
    counts as done once any later step passes (adding the CX of a Bell pair
    rightly breaks step 1's "q1 is still 0" check)."""
    raw = [step_done(model, step)[0] for step in steps]
    done, later = {}, False
    for i in range(len(raw) - 1, -1, -1):
        later = later or raw[i]
        done[i] = later
    return done
