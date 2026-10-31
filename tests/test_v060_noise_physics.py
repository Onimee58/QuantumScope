"""v0.6.0 (6a): noise channels and the density-matrix engine."""
import math

import numpy as np
import pytest

from quantumscope.physics import noise as N
from quantumscope.physics.circuits import ALL, DUAL, TRIPLE, Gate, evolution

RNG = np.random.default_rng(7)


def random_state(n):
    psi = RNG.normal(size=2 ** n) + 1j * RNG.normal(size=2 ** n)
    return psi / np.linalg.norm(psi)


def zero(n):
    psi = np.zeros(2 ** n, complex)
    psi[0] = 1
    return psi


def random_gates(n, count):
    gates = []
    for _ in range(count):
        name = ALL[RNG.integers(len(ALL))]
        k = 3 if name in TRIPLE else 2 if name in DUAL else 1
        if k <= n:
            gates.append(Gate(name, tuple(int(q) for q in RNG.permutation(n)[:k]), *map(float, RNG.normal(size=3))))
    return gates


# ---- channels ------------------------------------------------------------------------------

@pytest.mark.parametrize('kind', sorted(N.CHANNELS))
@pytest.mark.parametrize('p', [0.0, 0.13, 0.5, 1.0])
def test_channels_are_trace_preserving(kind, p):
    ops = N.kraus(kind, p)
    assert np.allclose(sum(k.conj().T @ k for k in ops), np.eye(2))


@pytest.mark.parametrize('kind', sorted(N.CHANNELS))
def test_channels_keep_states_physical(kind):
    rho = N.density(random_state(3))
    out = N.apply_channel(rho, 3, N.kraus(kind, 0.37), (1,))
    assert np.isclose(np.trace(out), 1) and np.allclose(out, out.conj().T)
    assert np.linalg.eigvalsh(out).min() > -1e-12             # positive


def test_two_qubit_depolarizing_is_trace_preserving():
    ops = N.kraus('depolarizing', 0.4, 2)
    assert len(ops) == 16 and np.allclose(sum(k.conj().T @ k for k in ops), np.eye(4))


@pytest.mark.parametrize('bad', [-0.1, 1.5, float('nan')])
def test_invalid_strengths(bad):
    with pytest.raises(ValueError):
        N.kraus('bit_flip', bad)


@pytest.mark.parametrize('targets', [(0,), (2,), (0, 2), (3, 1)])
def test_closed_form_depolarizing_equals_kraus_and_textbook_formula(targets):
    n = 4
    rho = N.density(random_state(n))
    closed = N.depolarize(rho, n, 0.3, targets)
    assert np.allclose(closed, N.apply_channel(rho, n, N.kraus('depolarizing', 0.3, len(targets)), targets))
    if len(targets) == n:
        assert np.allclose(closed, 0.7 * rho + 0.3 * np.eye(2 ** n) / 2 ** n)


@pytest.mark.parametrize('q', [0, 1, 2])
def test_closed_form_damping_equals_kraus(q):
    rho = N.density(random_state(3))
    expected = N.apply_channel(N.apply_channel(rho, 3, N.kraus('amplitude_damping', 0.3), (q,)), 3,
                               N.kraus('phase_damping', 0.4), (q,))
    assert np.allclose(N.relax(rho, 3, q, 0.3, 0.4), expected)
    assert np.allclose(N.damp(rho, 3, 0.3, q), N.apply_channel(rho, 3, N.kraus('amplitude_damping', 0.3), (q,)))
    assert np.allclose(N.dephase(rho, 3, 0.4, q), N.apply_channel(rho, 3, N.kraus('phase_damping', 0.4), (q,)))


def test_relax_does_not_change_its_input():
    rho = N.density(random_state(2))
    copy = rho.copy()
    N.relax(rho, 2, 1, 0.5, 0.5)
    assert np.array_equal(rho, copy)


# ---- textbook results ------------------------------------------------------------------------

def test_amplitude_damping_decays_the_excited_state():
    rho = N.density(np.array([0, 1], complex))
    for _ in range(3):
        rho = N.damp(rho, 1, 0.2, 0)
    assert rho[1, 1].real == pytest.approx(0.8 ** 3)          # exponential (T1-like) decay


def test_dephasing_kills_coherence_but_not_populations():
    plus = N.density(np.array([1, 1], complex) / math.sqrt(2))
    out = N.dephase(plus, 1, 1.0, 0)
    assert np.allclose(np.diag(out), [0.5, 0.5]) and abs(out[0, 1]) < 1e-12


def test_bell_fidelity_under_depolarizing():
    bell = evolution(2, [Gate('H', (0,)), Gate('CX', (0, 1))])[-1]
    for p in (0.1, 0.2, 0.5):
        rho = N.depolarize(N.density(bell), 2, p, (1,))
        assert N.fidelity_with_pure(rho, bell) == pytest.approx(1 - 3 * p / 4)


def test_purity_and_bloch_shrink_under_depolarizing():
    rho = N.density(np.array([1, 0], complex))
    out = N.depolarize(rho, 1, 0.4, (0,))
    assert N.bloch(out) == pytest.approx((0, 0, 0.6))          # length 1 − p
    assert N.purity(out) == pytest.approx((1 + 0.6 ** 2) / 2)


def test_partial_trace_matches_state_analysis():
    from quantumscope.physics.state_analysis import reduced_density_matrix
    psi = random_state(4)
    for keep in ([0], [1, 3], [2, 0]):
        assert np.allclose(N.partial_trace(N.density(psi), 4, keep), reduced_density_matrix(psi, 4, keep))


# ---- simulation ------------------------------------------------------------------------------------

def test_noiseless_density_simulation_equals_statevector():
    for _ in range(15):
        n = int(RNG.integers(1, 5))
        gates = random_gates(n, 10)
        start = random_state(n)
        history = N.simulate(n, [[g] for g in gates], start, N.NoiseModel(False))
        assert np.allclose(history[-1], N.density(evolution(n, gates, start)[-1]))
        assert len(history) == len(gates) + 1


def test_noisy_simulation_stays_physical_and_loses_purity():
    n = 3
    gates = random_gates(n, 12)
    history = N.simulate(n, [[g] for g in gates], zero(n), N.PRESETS['Very noisy'])
    final = history[-1]
    assert np.isclose(np.trace(final), 1) and np.linalg.eigvalsh(final).min() > -1e-10
    assert N.purity(final) < 0.999


def test_noise_elements_and_idle_noise():
    columns = [[Gate('H', (0,))], [N.NoiseElement('phase_flip', 0, 0.5)]]
    final = N.simulate(1, columns, zero(1), N.NoiseModel(False))[-1]
    assert abs(final[0, 1]) < 1e-12                            # p = ½ phase flip erases |+⟩'s coherence
    idle = N.NoiseModel(True, damping=0.5, idle=True)
    state = np.array([0, 1, 0, 0], complex)                     # |01⟩: q1 excited, idle in this column
    rho = N.simulate(2, [[Gate('X', (0,)), Gate('X', (0,))]], state, idle)[-1]
    assert N.partial_trace(rho, 2, [1])[1, 1].real < 1          # waiting qubit decayed
    no_idle = N.NoiseModel(True, damping=0.5, idle=False)
    rho = N.simulate(2, [[Gate('X', (0,)), Gate('X', (0,))]], state, no_idle)[-1]
    assert N.partial_trace(rho, 2, [1])[1, 1].real == pytest.approx(1)


def test_large_registers_keep_only_the_final_state():
    n = N.MAX_STORED_QUBITS + 1
    history = N.simulate(n, [[Gate('H', (q,))] for q in range(3)], zero(n), N.PRESETS['Gentle'])
    assert len(history) == 2


# ---- model, elements, readout --------------------------------------------------------------------------

def test_noise_model_records_and_presets():
    for model in N.PRESETS.values():
        assert N.NoiseModel.from_record(model.to_record()) == model
    assert not N.PRESETS['Ideal'].active and N.PRESETS['Moderate'].active
    assert not N.NoiseModel(True).active                       # enabled but all rates zero
    with pytest.raises(ValueError):
        N.NoiseModel(True, single=1.5)


def test_noise_element_records():
    element = N.NoiseElement('amplitude_damping', 2, 0.25)
    assert N.NoiseElement.from_record(element.to_record()) == element and 'γ=0.25' in element.label
    for bad in ({'channel': 'boom', 'qubit': 0, 'p': 0.1}, {'channel': 'bit_flip', 'qubit': 0, 'p': 2},
                {'channel': 'bit_flip', 'qubit': 'q0', 'p': 0.1}):
        with pytest.raises(ValueError):
            N.NoiseElement.from_record(bad)


def test_readout_error():
    probs = N.apply_readout([1, 0, 0, 0], 2, [0, 1], 0.1)
    assert probs == pytest.approx([0.81, 0.09, 0.09, 0.01])
    assert N.apply_readout([0.25] * 4, 2, [0], 0.3) == pytest.approx([0.25] * 4)
    assert sum(N.apply_readout(np.abs(random_state(3)) ** 2, 3, [0, 2], 0.2)) == pytest.approx(1)
