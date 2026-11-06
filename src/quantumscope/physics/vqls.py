"""The variational quantum linear solver, VQLS (Bravo-Prieto et al.), exactly (no Qt).

To solve A x = b, a parameterized circuit prepares |x(θ)⟩, and θ is tuned until A|x⟩ points along
|b⟩. The cost used here is the expectation of the Hermitian operator

    H = A† (I − |b⟩⟨b|) A,

which is never negative and is 0 exactly when A|x⟩ ∝ |b⟩, i.e. at the normalized solution
A⁻¹|b⟩/‖A⁻¹|b⟩‖ (A invertible). H is written as a Pauli sum, so QuantumScope's observable panel,
optimizer and landscape work on it unchanged. On a quantum computer the cost is estimated with
Hadamard-test circuits; here it is computed exactly.
"""
import itertools

import numpy as np

from .observables import matrix as pauli_matrix
from .observables import parse

PRESETS = {
    'standard': (3, '1 + 0.2 X0 Z1 + 0.2 X0', 'plus',
                 'the standard 3-qubit system A = 1 + 0.2 X0 Z1 + 0.2 X0 with b = |+++⟩'),
    'harder': (3, '1 + 0.45 X0 Z1 + 0.45 X0', 'plus',
               'a worse-conditioned system A = 1 + 0.45 X0 Z1 + 0.45 X0 with b = |+++⟩'),
    'single': (1, '1 + 0.5 X0', 'zeros', 'a 1-qubit system A = 1 + 0.5 X with b = |0⟩'),
}
B_STATES = (('|0…0⟩', 'zeros'), ('|+…+⟩ (H on every qubit)', 'plus'), ('|1…1⟩', 'ones'))
MAX_QUBITS = 3


def b_vector(kind, n):
    if kind == 'zeros':
        v = np.zeros(2 ** n, complex)
        v[0] = 1
    elif kind == 'ones':
        v = np.zeros(2 ** n, complex)
        v[-1] = 1
    elif kind == 'plus':
        v = np.ones(2 ** n, complex) / np.sqrt(2 ** n)
    else:
        raise ValueError(f'Unknown b {kind!r}')
    return v


def a_matrix(text, n):
    """A from a Pauli sum such as '1 + 0.2 X0 Z1' (raises ValueError if unreadable or not invertible)."""
    if not 1 <= n <= MAX_QUBITS:
        raise ValueError(f'VQLS here uses 1 to {MAX_QUBITS} qubits')
    try:
        A = pauli_matrix(n, parse(text, n))
    except ValueError as exc:
        raise ValueError(f'A: {exc}') from None
    singular = np.linalg.svd(A, compute_uv=False)
    if singular[-1] < 1e-9 * max(1.0, singular[0]):
        raise ValueError('A is not invertible (singular), so A x = b has no unique solution.')
    return A


def system(p):
    """(qubits, A, b, A as text, description) for the parameters of the VQLS example."""
    if p.get('problem', 'standard') in PRESETS:
        n, text, b, about = PRESETS[p.get('problem', 'standard')]
    else:
        n, text, b = int(p['qubits']), str(p['matrix']), p['b']
        about = f'the system A = {text} with b = {dict((v, k) for k, v in B_STATES)[b].split(" ")[0]}'
    return n, a_matrix(text, n), b_vector(b, n), text, about


def condition_number(A):
    s = np.linalg.svd(A, compute_uv=False)
    return float(s[0] / s[-1])


def classical_solution(A, b):
    x = np.linalg.solve(A, b)
    return x / np.linalg.norm(x)


def cost_operator(A, b):
    """H = A†(I − |b⟩⟨b|)A as a matrix."""
    projector = np.outer(b, b.conj())
    return A.conj().T @ (np.eye(len(b)) - projector) @ A


def pauli_text(H, n, digits=6):
    """A Hermitian matrix as a Pauli sum the observable parser reads (fixed decimals, no exponents)."""
    labels = {'I': np.eye(2), 'X': np.array([[0, 1], [1, 0]]), 'Y': np.array([[0, -1j], [1j, 0]]),
              'Z': np.diag([1, -1])}
    terms = []
    for word in itertools.product('IXYZ', repeat=n):
        P = labels[word[0]]
        for letter in word[1:]:
            P = np.kron(P, labels[letter])
        c = float(np.real(np.trace(P @ H))) / 2 ** n
        if abs(c) < 10 ** -digits:
            continue
        body = ' '.join(f'{letter}{q}' for q, letter in enumerate(word) if letter != 'I')
        terms.append((c, body))
    if not terms:
        return '0'
    out = ''
    for k, (c, body) in enumerate(terms):
        number = f'{abs(c):.{digits}f}'.rstrip('0').rstrip('.')
        piece = f'{number} {body}'.strip() if body else number
        out += (('-' if c < 0 else '') + piece) if k == 0 else ((' - ' if c < 0 else ' + ') + piece)
    return out


def normalized_cost(A, b, state):
    """1 − |⟨b|A|x⟩|² / ⟨x|A†A|x⟩: 0 at the solution, at most 1."""
    Ax = A @ state
    return float(1 - abs(np.vdot(b, Ax)) ** 2 / max(1e-300, np.real(np.vdot(Ax, Ax))))


def fidelity(A, b, state):
    """|⟨x_true|x⟩|² with the normalized classical solution."""
    return float(abs(np.vdot(classical_solution(A, b), state)) ** 2)
