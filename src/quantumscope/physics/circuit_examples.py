"""Built-in example circuits (Qt-free so they can be tested directly)."""
from .circuits import Gate

EXAMPLE_NAMES = ('Bell pair', 'GHZ', 'Half adder (a=1,b=1)', 'Half subtractor (a=1,b=1)',
                 '2-bit ripple-carry adder (1+1)')

# Examples with an arithmetic specification checked by verify_example.
VERIFIED_PREFIXES = ('Half adder', 'Half subtractor', '2-bit ripple-carry')


def example_circuit(name):
    """Return (n, gates) for a built-in example."""
    if name == 'Bell pair':
        return 2, [Gate('H', (0,)), Gate('CX', (0, 1))]
    if name == 'GHZ':
        return 3, [Gate('H', (0,)), Gate('CX', (0, 1)), Gate('CX', (1, 2))]
    if name == 'Half adder (a=1,b=1)':
        return 3, [Gate('X', (0,)), Gate('X', (1,)), Gate('CCX', (0, 1, 2)), Gate('CX', (0, 1))]
    if name == 'Half subtractor (a=1,b=1)':
        # Difference in q1 = a xor b, borrow in q2 = not(a) and b.
        return 3, [Gate('X', (0,)), Gate('X', (1,)), Gate('X', (0,)), Gate('CCX', (0, 1, 2)),
                   Gate('X', (0,)), Gate('CX', (0, 1))]
    if name == '2-bit ripple-carry adder (1+1)':
        # Input a=01 in q0,q1 and b=01 in q2,q3. Reversible 2-bit sum, q4/q5 are carry work bits.
        return 6, [Gate('X', (1,)), Gate('X', (3,)), Gate('CCX', (1, 3, 4)), Gate('CX', (3, 1)),
                   Gate('CCX', (0, 2, 5)), Gate('CX', (0, 2)), Gate('CCX', (2, 4, 5)), Gate('CX', (4, 2))]
    raise ValueError('Unknown example: ' + str(name))


def has_specification(name):
    return bool(name) and name.startswith(VERIFIED_PREFIXES)
