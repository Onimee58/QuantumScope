"""v0.5.2 patch 2b: the Learn system and its built-in content."""
import os
import re

import pytest

from quantumscope.editor.circuit_model import CircuitModel
from quantumscope.learn import actions, labs
from quantumscope.learn.equations import THEME_COLORS, equations_in, image_name
from quantumscope.learn.lessons import builtin_lessons, content_folder, course_lessons, parse, search
from quantumscope.learn.render import parse_step, steps_of, to_html

LESSONS = builtin_lessons()
EQ = os.path.join(content_folder(), 'eq')


def test_builtin_lessons_have_titles_objectives_and_kinds():
    assert len(LESSONS) >= 3
    for lesson in LESSONS:
        assert lesson.title and lesson.objectives and lesson.kind in ('lecture', 'lab')
        assert lesson.area in ('circuits', 'principles', 'hydrogen')


@pytest.mark.parametrize('lesson', LESSONS, ids=[l.key for l in LESSONS])
def test_every_equation_has_images_for_both_themes(lesson):
    for tex, kind in equations_in(lesson.body):
        for theme in THEME_COLORS:
            assert os.path.exists(os.path.join(EQ, image_name(tex, kind, theme))), f'{tex!r}: run tools/render_equations.py'


def test_no_stale_equation_images():
    from quantumscope.learn.lessons import reference_pages
    wanted = {image_name(tex, kind, theme) for l in LESSONS + reference_pages()
              for tex, kind in equations_in(l.body) for theme in THEME_COLORS}
    unused = [n for n in os.listdir(EQ) if n.endswith('.png') and n not in wanted]
    assert not unused, 'run tools/render_equations.py --prune'


@pytest.mark.parametrize('lesson', LESSONS, ids=[l.key for l in LESSONS])
@pytest.mark.parametrize('theme', ['dark', 'light'])
def test_every_lesson_renders_without_fallbacks(lesson, theme):
    html = to_html(lesson, theme, EQ, revealed=range(20))
    assert '<h2>' in html and 'font-family:monospace' not in html     # every equation found its image


@pytest.mark.parametrize('lesson', LESSONS, ids=[l.key for l in LESSONS])
def test_every_try_it_link_is_valid(lesson):
    links = re.findall(r'\]\((qs:[^)\s]+)\)', lesson.body)
    for link in links:
        action = actions.parse(link)
        if action.kind == 'lesson':
            assert any(l.key == action.target for l in LESSONS)


@pytest.mark.parametrize('lesson', LESSONS, ids=[l.key for l in LESSONS])
def test_every_quiz_has_exactly_one_correct_answer_and_an_explanation(lesson):
    for block in re.findall(r'```quiz\n(.*?)```', lesson.body, re.S):
        lines = block.strip().splitlines()
        assert sum(l.startswith('* ') for l in lines) == 1 and any(l.startswith('Q:') for l in lines)
        assert sum(l.startswith(('- ', '* ')) for l in lines) >= 2 and any(l.startswith('E:') for l in lines)


@pytest.mark.parametrize('lesson', [l for l in LESSONS if l.kind == 'lab'], ids=lambda l: l.key)
def test_lab_checks_are_well_formed(lesson):
    steps = steps_of(lesson.body)
    assert steps and all(s['title'] and s['checks'] for s in steps)
    m = CircuitModel(2)
    for step in steps:
        for condition in step['checks']:
            labs.check(m, condition)                     # raises for an unknown check


def test_bell_lab_can_be_completed_step_by_step():
    lab = next(l for l in LESSONS if l.key == 'circuits/90-lab-bell-pair')
    steps = steps_of(lab.body)
    m = CircuitModel(2)
    assert labs.progress(m, steps) == {0: False, 1: False, 2: False}
    m.place('H', 0, 0)
    assert labs.progress(m, steps) == {0: True, 1: False, 2: False}
    m.place('CX', 1, 1)
    m.add_operand(0, 1)
    assert labs.progress(m, steps) == {0: True, 1: True, 2: True}   # step 1 stays done after the CX
    m.place('X', 0, 2)                                   # an extra gate breaks the Bell state again
    assert labs.progress(m, steps)[1] is False


def test_lab_check_types():
    m = CircuitModel(2)
    m.place('H', 0, 0)
    assert labs.check(m, 'qubits 2')[0] and labs.check(m, 'uses H')[0] and not labs.check(m, 'uses CX')[0]
    assert labs.check(m, 'probability 00=0.5 10=0.5')[0] and labs.check(m, 'gates <= 1')[0]
    assert not labs.check(m, 'entangled 0')[0]
    from quantumscope.physics.initial_states import InitialState
    m.set_initial_state(1, InitialState.preset('-'))
    assert labs.check(m, 'starts 1:-')[0]
    with pytest.raises(ValueError):
        labs.check(m, 'teleport 0')


@pytest.mark.parametrize('link,kind', [('qs:circuit?n=2&gates=H:0;CX:0,1&states=+,0', 'circuit'),
                                       ('qs:algorithm/grover?n=2&marked=11', 'algorithm'),
                                       ('qs:example/Full adder', 'example'), ('qs:example/Full%20adder', 'example'),
                                       ('qs:gate/h', 'gate'), ('qs:try/CX', 'try'), ('qs:inspector', 'inspector'),
                                       ('qs:open/dynamics3d', 'open'), ('qs:lesson/circuits/01-qubits', 'lesson')])
def test_action_links(link, kind):
    assert actions.parse(link).kind == kind


def test_plus_state_survives_link_parsing():
    assert actions.parse('qs:circuit?n=1&states=+').params['states'][0].label == '|+⟩'
    assert actions.parse('qs:circuit?n=1&states=%2B').params['states'][0].label == '|+⟩'
    assert actions.parse('qs:circuit?n=1&gates=RY:0:pi/2').params['gates'][0].angle == pytest.approx(1.5707963)


@pytest.mark.parametrize('link', ['qs:circuit?n=2&gates=CX:0', 'qs:circuit?n=2&gates=FOO:0', 'qs:circuit?n=2&gates=H:5',
                                  'qs:circuit?n=2&states=+', 'qs:algorithm/grover?n=9', 'qs:example/Nope',
                                  'qs:open/kitchen', 'qs:teleport', 'https://example.com'])
def test_bad_links_are_rejected(link):
    with pytest.raises(ValueError):
        actions.parse(link)


def test_course_lessons_with_and_without_headers(tmp_path):
    (tmp_path / 'week1.md').write_text('# Week 1: Spin\nSome text.', encoding='utf-8')
    (tmp_path / 'week2.md').write_text('---\ntitle: Week 2\norder: 1\nkind: lab\n---\nBody', encoding='utf-8')
    (tmp_path / 'notes.txt').write_text('ignored', encoding='utf-8')
    lessons = course_lessons(str(tmp_path))
    assert [l.title for l in lessons] == ['Week 2', 'Week 1: Spin'] and lessons[0].kind == 'lab'
    assert all(l.area == 'course' and not l.builtin for l in lessons)
    assert course_lessons(str(tmp_path / 'missing')) == []


def test_course_lessons_cannot_inject_html_and_show_unrendered_math(tmp_path):
    lesson = parse('# T\n<script>alert(1)</script> and $x^2$ and <b>bold</b>', 'course/t.md', str(tmp_path))
    html = to_html(lesson, 'dark', EQ)
    assert '<script>' not in html and '&lt;script&gt;' in html and '&lt;b&gt;' in html
    assert 'x^2' in html                                 # no pre-rendered image: shown as source


def test_tables_with_escaped_bars():
    lesson = parse('# T\n| a | b |\n|---|---|\n| \\|0⟩ | x |', 'course/t.md', '.')
    html = to_html(lesson, 'light', EQ)
    assert '<td>|0⟩</td>' in html and '<th>a</th>' in html


def test_search():
    results = search(LESSONS, 'hadamard')
    assert results and results[0].key == 'circuits/02-single-qubit-gates'
    assert search(LESSONS, '') == [] and search(LESSONS, 'zzzunusedword') == []


def test_step_parsing():
    step = parse_step('title: A\ntext: do this\nhint: try that\ncheck: qubits 2\ncheck: uses H')
    assert (step['title'], step['text'].strip(), step['hint']) == ('A', 'do this', 'try that')
    assert step['checks'] == ['qubits 2', 'uses H']


def test_lab_checks_on_a_circuit_of_the_wrong_size_are_simply_not_done():
    m = CircuitModel(1)
    for condition in ('state H:0;CX:0,1', 'probability 00=0.5 11=0.5', 'entangled 0', 'entangled 3', 'qubits 2'):
        assert labs.check(m, condition)[0] is False


# ---- every lab can be completed -------------------------------------------------------------

from quantumscope.physics.circuits import Gate  # noqa: E402
from quantumscope.physics.initial_states import InitialState  # noqa: E402

LAB_SOLUTIONS = {
    'circuits/90-lab-bell-pair': (2, [Gate('H', (0,)), Gate('CX', (0, 1))], '00'),
    'circuits/91-lab-ghz': (3, [Gate('H', (0,)), Gate('CX', (0, 1)), Gate('CX', (1, 2))], '000'),
    'circuits/92-lab-phase-kickback': (2, [Gate('CX', (0, 1)), Gate('H', (0,))], '+-'),
    'circuits/93-lab-grover-by-hand': (2, [Gate('H', (0,)), Gate('H', (1,)), Gate('CZ', (0, 1)),
                                           Gate('H', (0,)), Gate('H', (1,)), Gate('X', (0,)), Gate('X', (1,)),
                                           Gate('CZ', (0, 1)), Gate('X', (0,)), Gate('X', (1,)),
                                           Gate('H', (0,)), Gate('H', (1,))], '00'),
    'circuits/94-lab-half-adder': (3, [Gate('CCX', (0, 1, 2)), Gate('CX', (0, 1))], '110'),
    'circuits/95-lab-qft': (2, [Gate('H', (0,)), Gate('CP', (1, 0), 3.141592653589793 / 2), Gate('H', (1,)),
                                Gate('SWAP', (0, 1))], '01'),
    'circuits/96-lab-bell-decoherence': (2, [Gate('H', (0,)), Gate('CX', (0, 1))], '00',
                                         [('depolarizing', 1, 2, 1.0)]),
}


def test_every_lab_has_a_tested_solution():
    labs_present = {l.key for l in LESSONS if l.kind == 'lab'}
    assert labs_present == set(LAB_SOLUTIONS)


@pytest.mark.parametrize('key', sorted(LAB_SOLUTIONS))
def test_lab_solution_completes_every_step(key):
    lesson = next(l for l in LESSONS if l.key == key)
    n, gates, starts, *extra = LAB_SOLUTIONS[key]
    from quantumscope.physics.noise import NoiseElement
    noise = [(NoiseElement(kind, q, p), c) for kind, q, c, p in (extra[0] if extra else [])]
    states = []
    for ch in starts:
        states.append(InitialState.preset({'0': '0', '1': '1', '+': '+', '-': '-'}[ch]))
    m = CircuitModel(n)
    m.set_circuit(n, gates, initial_states=states, noise=noise)
    assert all(labs.progress(m, steps_of(lesson.body)).values())


# ---- numbers quoted in the lessons match the app's physics -------------------------------------

def lesson_text(key):
    return next(l for l in LESSONS if l.key == key).body


def test_hydrogen_energies_and_lines_match_the_model():
    from scipy import constants as c
    from quantumscope.physics.hydrogen import HydrogenAtom
    atom, text = HydrogenAtom(), lesson_text('hydrogen/04-energy-levels-and-spectra')
    for n in (1, 2, 3, 4):
        assert f'{atom.state(n, 0, 0).energy_ev:.3f}'.replace('-', '−') in text
    for (ni, nf), shown in (((2, 1), '121.6 nm'), ((3, 1), '102.6 nm'), ((3, 2), '656.5 nm')):
        de = atom.state(ni, 0, 0).energy_ev - atom.state(nf, 0, 0).energy_ev
        assert f'{c.h * c.c / (de * c.e) * 1e9:.1f} nm' == shown and shown in text


def test_beat_periods_match_the_model():
    from quantumscope.physics.dynamics import HydrogenSuperposition
    from quantumscope.physics.hydrogen import HydrogenAtom
    atom, text = HydrogenAtom(), lesson_text('hydrogen/05-superposition-and-quantum-beats')
    for a, b in (((1, 0, 0), (2, 1, 0)), ((1, 0, 0), (3, 2, 0))):
        period = HydrogenSuperposition(atom.state(*a), atom.state(*b)).beat_period_fs
        assert f'{period:.4f} fs' in text


def test_radii_quoted_in_lessons():
    import numpy as np
    from quantumscope.physics.dynamics import enclosing_radius
    from quantumscope.physics.hydrogen import HydrogenAtom
    atom = HydrogenAtom()
    r = np.linspace(0, 80, 400001)
    integrate = getattr(np, 'trapezoid', None) or np.trapz
    for (n, l), mean in (((1, 0), 1.5), ((2, 0), 6), ((2, 1), 5), ((3, 2), 10.5)):
        p = atom.state(n, l, 0).radial_probability(r)
        assert integrate(r * p, r) / integrate(p, r) == pytest.approx(mean, abs=1e-3)
    assert f'{enclosing_radius(atom.state(1, 0, 0)):.2f}' == '4.64'
    assert '4.64' in lesson_text('hydrogen/03-probability-density')


def test_grover_table_matches_the_formula():
    from quantumscope.physics.algorithms import grover_optimal_iterations, grover_success
    text = lesson_text('circuits/08-grover-search')
    for n, shown in ((2, '| 4 | 30° | 1 | 1 |'), (3, '| 8 | 20.7° | 2 | 0.945 |'), (4, '| 16 | 14.5° | 3 | 0.961 |')):
        k = grover_optimal_iterations(n)
        assert shown in text and f'| {k} |' in shown
        assert f'{grover_success(n, k):.3f}'.rstrip('0').rstrip('.') in shown


def test_every_area_has_lessons():
    areas = {l.area for l in LESSONS}
    assert areas == {'circuits', 'principles', 'hydrogen'}
    assert sum(l.kind == 'lab' for l in LESSONS) == 7 and len(LESSONS) == 30


def test_png_size_matches_the_image_and_needs_no_qt():
    from PIL import Image
    from quantumscope.learn.render import png_size
    name = sorted(os.listdir(EQ))[0]
    assert png_size(os.path.join(EQ, name)) == Image.open(os.path.join(EQ, name)).size


def test_objectives_are_not_split_inside_kets():
    # '|' separates objectives, so a ket like |1⟩ in an objective would be cut in pieces.
    for lesson in LESSONS:
        for objective in lesson.objectives:
            assert '⟩' not in objective and not objective.startswith(('1⟩', '0⟩')), (lesson.key, objective)


def test_noise_lecture_numbers_match_the_simulator():
    from quantumscope.physics import noise as N
    from quantumscope.physics.circuits import evolution
    text = lesson_text('circuits/11-noise-and-decoherence')
    for key, values, shown in (('grover', {'n': 3, 'marked': '101', 'iterations': -1}, 'about 0.577'),
                               ('bernstein_vazirani', {'n': 3, 's': '101'}, 'probability 0.919')):
        m = CircuitModel()
        m.load_library(key, values)
        m.set_noise_model(N.PRESETS['Moderate'])
        assert f'{m.noisy_verification()[0][0].probability:.3f}' in shown and shown in text
    bell = evolution(2, [Gate('H', (0,)), Gate('CX', (0, 1))])[-1]
    for p, shown in ((0.2, '0.85'), (0.4, '0.7')):
        rho = N.depolarize(N.density(bell), 2, p, (1,))
        assert f'{N.fidelity_with_pure(rho, bell):g}' == shown


def test_bell_decoherence_lab_steps_follow_the_strength():
    from quantumscope.physics.noise import NoiseElement
    lab = next(l for l in LESSONS if l.key == 'circuits/96-lab-bell-decoherence')
    steps = steps_of(lab.body)
    m = CircuitModel(2)
    m.set_circuit(2, [Gate('H', (0,)), Gate('CX', (0, 1))])
    assert labs.progress(m, steps) == {0: True, 1: False, 2: False}
    m.set_circuit(2, [Gate('H', (0,)), Gate('CX', (0, 1))], noise=[(NoiseElement('depolarizing', 1, 0.4), 2)])
    assert labs.progress(m, steps) == {0: True, 1: True, 2: False}


@pytest.mark.parametrize('link', ['qs:circuit?n=2&noise=Loud', 'qs:circuit?n=2&elements=depolarizing:5:0:0.1',
                                  'qs:circuit?n=2&elements=depolarizing:0:0', 'qs:circuit?n=2&elements=boom:0:0:0.1',
                                  'qs:algorithm/grover?n=2&marked=11&noise=Loud'])
def test_bad_noise_links_are_rejected(link):
    with pytest.raises(ValueError):
        actions.parse(link)


def test_noise_lab_checks():
    from quantumscope.physics.noise import NoiseElement
    m = CircuitModel(2)
    m.set_circuit(2, [Gate('H', (0,)), Gate('CX', (0, 1))])
    assert labs.check(m, 'fidelity >= 1')[0] and labs.check(m, 'purity >= 1')[0] and not labs.check(m, 'noise bit_flip')[0]
    m.set_circuit(2, [Gate('H', (0,)), Gate('CX', (0, 1))], noise=[(NoiseElement('bit_flip', 0, 0.5), 2)])
    assert labs.check(m, 'noise bit_flip')[0] and labs.check(m, 'purity <= 0.6')[0]


def test_quiz_rendering_states():
    from quantumscope.learn.lessons import parse
    lesson = parse('# T\n```quiz\nQ: 1 + 1?\n- 3\n* 2\nE: Because.\n```', 'course/t.md', '.')
    fresh = to_html(lesson, 'dark', EQ)
    assert 'qsquiz:0:0' in fresh and 'qsquiz:0:1' in fresh and 'Show answer' in fresh
    wrong = to_html(lesson, 'dark', EQ, answers={0: 0})
    assert 'Not quite' in wrong and 'qsquiz:0:1' in wrong and 'Because.' not in wrong
    right = to_html(lesson, 'light', EQ, answers={0: 1})
    assert 'Correct!' in right and 'Because.' in right and 'qsquiz:0:' not in right
    revealed = to_html(lesson, 'dark', EQ, revealed={0})
    assert 'Because.' in revealed and 'Correct!' not in revealed


def test_quiz_feedback_colors_are_readable():
    from quantumscope.gui.theme import contrast_ratio
    from quantumscope.learn.render import PALETTES
    for name in ('dark', 'light'):
        p = PALETTES[name]
        assert contrast_ratio(p['wrong'], p['note_bg']) >= 4.5 and contrast_ratio(p['answer'], p['note_bg']) >= 4.5
