"""How basis states and numbers are shown (display only; the physics never changes).

The GUI sets these from Settings; physics code formats labels through
`ket`/`bits` and amplitudes through gate_education.format_amplitude.

bit_order:
  'q0_left'  — |q0 q1 … q(n−1)⟩, the textbook convention (default)
  'q0_right' — |q(n−1) … q1 q0⟩, the convention used by Qiskit
number_format: 'exact' (1/√2, i/2 …) or 'decimal' (0.7071 …), with `decimals` places.
"""

OPTIONS = {'bit_order': 'q0_left', 'number_format': 'exact', 'decimals': 4}
_ALLOWED = {'bit_order': ('q0_left', 'q0_right'), 'number_format': ('exact', 'decimal')}


def configure(**options):
    for key, value in options.items():
        if key not in OPTIONS:
            raise KeyError(key)
        if key in _ALLOWED and value not in _ALLOWED[key]:
            raise ValueError(f'Invalid {key}: {value}')
        if key == 'decimals' and not (isinstance(value, int) and 1 <= value <= 12):
            raise ValueError('decimals must be 1–12')
        OPTIONS[key] = value


def bits(index, n):
    """Basis index as a bit string in the chosen display order (index uses q0 as the MSB)."""
    text = format(int(index), f'0{n}b') if n else ''
    return text[::-1] if OPTIONS['bit_order'] == 'q0_right' else text


def ket(index, n, ascii=False):
    return f'|{bits(index, n)}{">" if ascii else "⟩"}'


def order_note(n=None):
    """Short phrase describing the current bit order, for labels and tooltips."""
    if OPTIONS['bit_order'] == 'q0_right':
        return 'q0 is the rightmost bit (Qiskit order)'
    return 'q0 is the leftmost bit'
