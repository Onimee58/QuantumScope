"""v0.4.2: theme canvas contrast (R-05) and Gate Explorer content.

The Gate Explorer is teaching material, so its identities, inverses and
classifications are verified numerically against the simulator's matrices.
"""
import math

import numpy as np
import pytest

from quantumscope.gui.theme import CANVAS, CONTRAST_REQUIREMENTS, canvas_hex, contrast_ratio
from quantumscope.physics.circuits import ALL, DUAL, TRIPLE, Gate, apply_gate
from quantumscope.physics.gate_education import (RELATED, format_amplitude, gate_information,
    gate_matrix, gate_properties, inverse_description, transformation_rows)

ANGLES = (0.0, math.pi / 3, math.pi / 2, -1.234, 2.5)


def same_up_to_phase(a, b):
    k = np.argmax(np.abs(b))
    if abs(b.flat[k]) < 1e-12:
        return np.allclose(a, b)
    phase = a.flat[k] / b.flat[k]
    return abs(abs(phase) - 1) < 1e-9 and np.allclose(a, phase * b, atol=1e-9)


def product(*mats):
    out = np.eye(mats[0].shape[0], dtype=complex)
    for m in mats:
        out = out @ m
    return out


# R-05: theme contrast ------------------------------------------------------------

def test_both_themes_define_the_same_roles():
    assert set(CANVAS['dark']) == set(CANVAS['light'])


@pytest.mark.parametrize('theme', ['dark', 'light'])
@pytest.mark.parametrize('foreground,background,minimum', CONTRAST_REQUIREMENTS)
def test_canvas_colors_meet_wcag_contrast(theme, foreground, background, minimum):
    ratio = contrast_ratio(canvas_hex(foreground, theme), canvas_hex(background, theme))
    assert ratio >= minimum, f'{theme}: {foreground} on {background} is {ratio:.2f}:1'


def test_contrast_ratio_reference_values():
    assert contrast_ratio('#000000', '#ffffff') == pytest.approx(21.0)
    assert contrast_ratio('#777777', '#777777') == pytest.approx(1.0)


def test_light_mode_control_dots_are_now_visible():
    # v0.4.1 painted dark-theme '#d5f5ff' dots on the light table (1.08:1).
    assert contrast_ratio('#d5f5ff', CANVAS['light']['surface']) < 1.2
    assert contrast_ratio(CANVAS['light']['control'], CANVAS['light']['surface']) > 7


# Gate Explorer: matrices, inverses and properties ----------------------------------

@pytest.mark.parametrize('name', ALL)
def test_explorer_matrix_matches_simulator(name):
    n = 3 if name in TRIPLE else 2 if name in DUAL else 1
    u = gate_matrix(name, 0.7, 0.3, -0.4)
    for index in range(1 << n):
        v = np.zeros(1 << n, complex)
        v[index] = 1
        assert np.allclose(u[:, index], apply_gate(v, n, Gate(name, tuple(range(n)), 0.7, 0.3, -0.4)))


@pytest.mark.parametrize('name', ALL)
@pytest.mark.parametrize('angle', ANGLES)
def test_stated_inverse_really_inverts(name, angle):
    phi, lam = 0.4, -0.9
    n = gate_information(name)['qubits']
    _, gates = inverse_description(name, angle, phi, lam)
    inverse = product(*[gate_matrix(g.name, g.angle, g.phi, g.lam) for g in reversed(gates)])
    assert np.allclose(inverse @ gate_matrix(name, angle, phi, lam), np.eye(1 << n), atol=1e-9)


@pytest.mark.parametrize('name', ALL)
def test_properties_are_consistent(name):
    props = gate_properties(name, 0.9, 0.2, 0.3)
    u = gate_matrix(name, 0.9, 0.2, 0.3)
    assert props['unitary'] is True
    assert props['hermitian'] == bool(np.allclose(u, u.conj().T))
    assert all(r in ALL for r in props['related'])


def test_known_hermitian_gates():
    for name in ('H', 'X', 'Y', 'Z', 'CX', 'CZ', 'SWAP', 'CCX', 'CSWAP'):
        assert gate_properties(name)['self_inverse'] is True
    for name in ('S', 'T', 'SX'):
        assert gate_properties(name)['self_inverse'] is False


@pytest.mark.parametrize('name,angle,clifford', [('RZ', math.pi / 2, True), ('RX', math.pi, True),
                                                  ('P', math.pi / 4, False), ('RY', 0.3, False)])
def test_rotation_clifford_classification(name, angle, clifford):
    assert gate_properties(name, angle)['clifford'].startswith('Yes') is clifford


def test_measurement_has_no_unitary_properties():
    props = gate_properties('M')
    assert props['unitary'] is False and 'irreversible' in props['inverse']


def test_bloch_vector_of_gate_applied_to_zero():
    assert gate_properties('H')['on_zero'] == pytest.approx((1, 0, 0))
    assert gate_properties('X')['on_zero'] == pytest.approx((0, 0, -1))
    assert gate_properties('RX', math.pi / 2)['on_zero'] == pytest.approx((0, -1, 0))


def test_related_gates_cover_every_unitary():
    assert set(RELATED) == set(ALL)


# The identities displayed in the explorer must hold (up to global phase).

def M(name, angle=0.0, phi=0.0, lam=0.0):
    return gate_matrix(name, angle, phi, lam)


I2 = np.eye(2)
H2 = np.kron(I2, M('H'))


@pytest.mark.parametrize('left,right', [
    (product(M('H'), M('X'), M('H')), M('Z')),
    (product(M('H'), M('Z'), M('H')), M('X')),
    (product(M('X'), M('X')), I2),
    (1j * product(M('X'), M('Z')), M('Y')),
    (product(M('S'), M('S')), M('Z')),
    (product(M('T'), M('T')), M('S')),
    (np.linalg.matrix_power(M('T'), 8), I2),
    (product(M('SX'), M('SX')), M('X')),
    (M('P', math.pi), M('Z')),
    (M('P', math.pi / 2), M('S')),
    (M('P', math.pi / 4), M('T')),
    (M('RZ', 0.8), np.exp(-0.4j) * M('P', 0.8)),
    (M('U', 0.8, -math.pi / 2, math.pi / 2), M('RX', 0.8)),
    (M('U', 0.8, 0, 0), M('RY', 0.8)),
    (product(H2, M('CX'), H2), M('CZ')),
])
def test_displayed_identities_hold(left, right):
    assert same_up_to_phase(left, right)


def test_swap_from_three_cx():
    cx_01 = M('CX')
    swap_basis = M('SWAP')
    cx_10 = swap_basis @ cx_01 @ swap_basis
    assert np.allclose(product(cx_01, cx_10, cx_01), swap_basis)


def test_fredkin_conserves_number_of_ones():
    u = M('CSWAP')
    for index in range(8):
        out = int(np.argmax(np.abs(u[:, index])))
        assert bin(out).count('1') == bin(index).count('1')


# Readable amplitudes -----------------------------------------------------------------

@pytest.mark.parametrize('z,text', [(0, '0'), (1, '1'), (-1, '-1'), (1j, 'i'), (-1j, '-i'),
                                    (1 / math.sqrt(2), '1/√2'), (-0.5j, '-i/2'),
                                    (complex(0.5, 0.5), '1/2 + i/2'), (complex(0.5, -0.5), '1/2 - i/2'),
                                    (complex(0.3, 0.123456), '0.3 + 0.1235i')])
def test_format_amplitude(z, text):
    assert format_amplitude(complex(z)) == text


def test_transformation_rows_accept_u_angles():
    rows = transformation_rows('U', math.pi, math.pi / 2, 0.0)
    assert rows[0][1] == '(i)|1>'


@pytest.mark.parametrize('x,text', [(0, '0'), (math.pi, 'π'), (-math.pi / 2, '-π/2'),
                                    (3 * math.pi / 4, '3π/4'), (2 * math.pi / 3, '2π/3'), (1.0, '1.0000')])
def test_angle_text(x, text):
    from quantumscope.physics.gate_education import angle_text
    assert angle_text(x) == text
