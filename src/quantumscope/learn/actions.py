"""Lesson actions: links of the form qs:… that set up an experiment ("Try it").

    qs:circuit?n=2&gates=H:0;CX:0,1&states=0,0&inspector=1
    qs:circuit?n=2&gates=H:0;CX:0,1&noise=Moderate&elements=depolarizing:1:2:0.4
                                     (noise: a preset; elements: channel:qubit:column:strength)
    qs:algorithm/grover?n=3&marked=101&iterations=-1
    qs:example/Full adder            (any title from the Examples menu)
    qs:gate/H                        (open the Gate Explorer)
    qs:try/CX                        (the Gate Explorer's "Try it" circuit)
    qs:inspector                     (open the State Inspector)
    qs:open/<view>                   (circuits, converter, orbital, dynamics2d, dynamics3d,
                                      doubleslit, superposition, entanglement)
    qs:lesson/<key>                  (another lesson, e.g. circuits/02-single-qubit-gates)

Gates in circuit links: NAME:q[,q…][:angle[,phi,lam]] separated by ';'.
Angles accept expressions such as pi/2. Parsing is pure, so every link in
the built-in lessons is tested.
"""
from dataclasses import dataclass, field
from urllib.parse import unquote

from quantumscope.physics.circuits import ALL, DUAL, TRIPLE, MAX_QUBITS, Gate
from quantumscope.physics.expressions import parse_angle
from quantumscope.physics.initial_states import PRESETS, InitialState

VIEWS = ('circuits', 'converter', 'orbital', 'dynamics2d', 'dynamics3d', 'doubleslit', 'superposition', 'entanglement',
         'teleportation')


@dataclass(frozen=True)
class Action:
    kind: str
    target: str = ''
    params: dict = field(default_factory=dict)


def _gates(spec, n):
    gates = []
    for token in filter(None, (t.strip() for t in spec.split(';'))):
        parts = token.split(':')
        name = parts[0].upper()
        if name not in ALL:
            raise ValueError(f'Unknown gate {parts[0]}')
        if len(parts) < 2:
            raise ValueError(f'{name} needs qubits')
        qubits = tuple(int(q) for q in parts[1].split(','))
        size = 3 if name in TRIPLE else 2 if name in DUAL else 1
        if len(qubits) != size or len(set(qubits)) != size or not all(0 <= q < n for q in qubits):
            raise ValueError(f'Invalid qubits for {name}: {parts[1]}')
        angles = [parse_angle(a) for a in parts[2].split(',')] if len(parts) > 2 else []
        gates.append(Gate(name, qubits, *(angles + [0.0] * (3 - len(angles)))[:3]))
    return gates


def parse(link):
    """An Action from a qs: link; raises ValueError for anything malformed."""
    link = link.strip()
    if not link.startswith('qs:'):
        raise ValueError('Not a QuantumScope action')
    path, _, query = link[3:].partition('?')
    path = unquote(path)
    # Decode %-escapes only: a literal + must stay + (it names the |+⟩ state).
    params = {}
    for pair in filter(None, query.split('&')):
        name, _, value = pair.partition('=')
        params[unquote(name)] = unquote(value)
    kind, _, target = path.partition('/')
    if kind == 'circuit':
        n = int(params.get('n', 2))
        if not 1 <= n <= MAX_QUBITS:
            raise ValueError('Qubits out of range')
        gates = _gates(params.get('gates', ''), n)
        states = [s.strip() for s in params.get('states', '').split(',') if s.strip()] or ['0'] * n
        if len(states) != n or not all(s in PRESETS for s in states):
            raise ValueError('states must give one preset (0, 1, +, -, +i, -i) per qubit')
        from quantumscope.physics.noise import PRESETS as NOISE_PRESETS, NoiseElement
        preset = params.get('noise')
        if preset is not None and preset not in NOISE_PRESETS:
            raise ValueError(f'Unknown noise preset {preset}')
        elements = []
        for token in filter(None, (t.strip() for t in params.get('elements', '').split(';'))):
            parts = token.split(':')
            if len(parts) != 4:
                raise ValueError('elements need channel:qubit:column:strength')
            element = NoiseElement(parts[0], int(parts[1]), float(parts[3]))
            if not 0 <= element.qubit < n or int(parts[2]) < 0:
                raise ValueError(f'Noise element outside the circuit: {token}')
            elements.append((element, int(parts[2])))
        from quantumscope.physics.dynamic import Measure, Reset
        for token in filter(None, (t.strip() for t in params.get('measures', '').split(';'))):
            q, col, cbit = (int(x) for x in token.split(':'))            # qubit:column:classical bit
            if not 0 <= q < n:
                raise ValueError(f'Measurement outside the circuit: {token}')
            elements.append((Measure(q, cbit), col))
        for token in filter(None, (t.strip() for t in params.get('resets', '').split(';'))):
            q, col = (int(x) for x in token.split(':'))
            if not 0 <= q < n:
                raise ValueError(f'Reset outside the circuit: {token}')
            elements.append((Reset(q), col))
        return Action('circuit', '', {'n': n, 'gates': gates, 'states': [InitialState.preset(s) for s in states],
                                      'inspector': params.get('inspector') == '1',
                                      'noise_model': NOISE_PRESETS[preset] if preset else None, 'elements': elements})
    if kind == 'algorithm':
        from quantumscope.physics.algorithms import ENTRIES, validate_params
        if target not in ENTRIES:
            raise ValueError(f'Unknown algorithm {target}')
        values = {}
        for p in ENTRIES[target].params:
            if p.key in params:
                values[p.key] = int(params[p.key]) if p.kind == 'int' or (
                    p.kind == 'choice' and isinstance(p.default, int)) else params[p.key]
        validate_params(ENTRIES[target].params, values)
        from quantumscope.physics.noise import PRESETS as NOISE_PRESETS
        preset = params.get('noise')
        if preset is not None and preset not in NOISE_PRESETS:
            raise ValueError(f'Unknown noise preset {preset}')
        return Action('algorithm', target, {'values': values, 'inspector': params.get('inspector') == '1',
                                            'noise_model': NOISE_PRESETS[preset] if preset else None})
    if kind == 'example':
        from quantumscope.physics.algorithms import LIBRARY
        from quantumscope.physics.circuit_examples import EXAMPLE_NAMES
        titles = list(EXAMPLE_NAMES) + [e.title for e in LIBRARY if e.menu == 'Examples']
        if target not in titles:
            raise ValueError(f'Unknown example {target}')
        return Action('example', target, {'inspector': params.get('inspector') == '1'})
    if kind in ('gate', 'try'):
        if target.upper() not in ALL + ('M',):
            raise ValueError(f'Unknown gate {target}')
        return Action(kind, target.upper())
    if kind == 'inspector':
        return Action('inspector')
    if kind == 'open':
        if target not in VIEWS:
            raise ValueError(f'Unknown view {target}')
        return Action('open', target)
    if kind == 'lesson':
        if not target:
            raise ValueError('lesson needs a key')
        return Action('lesson', target)
    raise ValueError(f'Unknown action {kind}')
