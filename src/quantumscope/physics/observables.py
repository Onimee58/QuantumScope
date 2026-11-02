"""Observables written as Pauli sums, e.g. "Z0 Z1 + 0.5 X0 - 1.2 Y1 Y2" (no Qt).

Each term is a real coefficient times a product of Pauli operators on distinct qubits.
Expectation values are exact, for pure states and density matrices alike; the matrix
form gives exact ground energies by diagonalization, so variational results can be checked.
"""
import re

import numpy as np

_PAULI = {'I': np.eye(2), 'X': np.array([[0, 1], [1, 0]], complex),
          'Y': np.array([[0, -1j], [1j, 0]], complex), 'Z': np.array([[1, 0], [0, -1]], complex)}
_FACTOR = re.compile(r'([IXYZ])\s*(\d+)', re.I)


def parse(text, n=None):
    """[(coefficient, ((qubit, 'X'|'Y'|'Z'), …)), …]; raises ValueError with a readable message."""
    source = str(text).strip()
    if not source:
        raise ValueError('Enter an observable, e.g. Z0 Z1 + 0.5 X0')
    source = source.replace('−', '-').replace('·', ' ').replace('*', ' ')
    terms = []
    for sign, body in re.findall(r'([+-]?)\s*([^+-]+)', source):
        body = body.strip()
        if not body:
            continue
        match = re.match(r'^(\d+(?:\.\d*)?|\.\d+)?\s*(.*)$', body)
        coefficient = float(match.group(1)) if match.group(1) else 1.0
        rest = match.group(2).strip()
        factors = _FACTOR.findall(rest)
        if _FACTOR.sub('', rest).strip():
            raise ValueError(f'Cannot read "{body}": use terms like 0.5 X0 Z1')
        ops = {}
        for letter, qubit in factors:
            q = int(qubit)
            if q in ops:
                raise ValueError(f'Qubit {q} appears twice in the term "{body}"')
            if n is not None and q >= n:
                raise ValueError(f'The circuit has no qubit q{q}')
            if letter.upper() != 'I':
                ops[q] = letter.upper()
        terms.append(((-1 if sign == '-' else 1) * coefficient, tuple(sorted(ops.items()))))
    if not terms:
        raise ValueError('Enter an observable, e.g. Z0 Z1 + 0.5 X0')
    return terms


def text(terms):
    """A readable form of parsed terms."""
    parts = []
    for coefficient, ops in terms:
        body = ' '.join(f'{p}{q}' for q, p in ops) or 'I'
        magnitude = abs(coefficient)
        number = '' if abs(magnitude - 1) < 1e-12 and ops else f'{magnitude:g} '
        parts.append(('- ' if coefficient < 0 else '+ ') + number + body)
    joined = ' '.join(parts)
    return joined[2:] if joined.startswith('+ ') else '-' + joined[2:]


def _apply_term(state, n, ops):
    t = np.asarray(state, complex).reshape((2,) * n)
    for q, p in ops:
        t = np.moveaxis(np.tensordot(_PAULI[p], t, axes=([1], [q])), 0, q)
    return t.reshape(-1)


def expectation(state, n, terms):
    """⟨O⟩ for a state vector, or Tr(ρO) for a density matrix (always real)."""
    state = np.asarray(state, complex)
    if state.ndim == 2:
        return float(sum(c * np.real(np.trace(_apply_rows(state, n, ops))) for c, ops in terms))
    return float(sum(c * np.real(np.vdot(state, _apply_term(state, n, ops))) for c, ops in terms))


def _apply_rows(rho, n, ops):
    """O_term · ρ, transforming every column at once."""
    dim = rho.shape[0]
    t = np.asarray(rho, complex).reshape((2,) * n + (dim,))
    for q, p in ops:
        t = np.moveaxis(np.tensordot(_PAULI[p], t, axes=([1], [q])), 0, q)
    return t.reshape(dim, dim)


def matrix(n, terms):
    """The 2^n × 2^n Hermitian matrix (q0 is the most significant qubit)."""
    total = np.zeros((2 ** n, 2 ** n), complex)
    for coefficient, ops in terms:
        factors = dict(ops)
        term = np.array([[1.0 + 0j]])
        for q in range(n):
            term = np.kron(term, _PAULI[factors.get(q, 'I')])
        total += coefficient * term
    return total


def ground_energy(n, terms):
    return float(np.linalg.eigvalsh(matrix(n, terms))[0])
