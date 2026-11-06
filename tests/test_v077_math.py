"""v0.7.7: Learn → Mathematics, "Math you need", and the glossary's mathematics terms."""
import re

import pytest

from quantumscope.learn import actions
from quantumscope.learn import glossary as G
from quantumscope.learn.lessons import builtin_lessons, math_titles, parse
from quantumscope.learn.render import to_html

LESSONS = {l.key: l for l in builtin_lessons()}
MATH = [l for l in LESSONS.values() if l.area == 'math']


def test_twelve_mathematics_lessons_in_order_with_quizzes_and_valid_links():
    assert [l.order for l in MATH] == list(range(1, 13)) and all(l.kind == 'lecture' for l in MATH)
    assert len(math_titles()) == 12 and math_titles()['math/07-tensor-products'] == 'Tensor products'
    for lesson in MATH:
        assert lesson.objectives and lesson.body.count('```quiz') >= 2 and '## Summary' in lesson.body
        links = re.findall(r'\]\((qs:[^)]+)\)', lesson.body)
        assert links, lesson.key                                                 # every lesson has a Try it
        for link in links:
            assert actions.parse(link) is not None, (lesson.key, link)


def test_every_physics_lecture_says_what_math_it_needs():
    for lesson in LESSONS.values():
        if lesson.kind != 'lecture' or lesson.area == 'math':
            continue
        assert lesson.math, lesson.key
        assert all(key in LESSONS and LESSONS[key].area == 'math' for key in lesson.math), lesson.key
        markup = to_html(lesson, 'dark')
        box = re.search(r'Math you need:</b>(.*?)</div>', markup).group(1)
        assert box.count('qs:lesson/math/') == len(lesson.math)
        assert actions.parse(f'qs:lesson/{lesson.math[0]}') is not None
    assert 'Math you need' not in to_html(MATH[0], 'dark')                       # math lessons have none


def test_math_header_field():
    lesson = parse('---\ntitle: T\nmath: 07-tensor-products, 05-eigenvalues\n---\nText.\n', 'course/t', '.')
    assert lesson.math == ('math/07-tensor-products', 'math/05-eigenvalues')
    assert parse('---\ntitle: T\n---\nText.\n', 'course/t', '.').math == ()


def test_glossary_points_linear_algebra_to_mathematics_and_has_the_new_terms():
    g = G.builtin()
    expected = {'Hermitian': 'math/04-hermitian-and-unitary', 'Unitary': 'math/04-hermitian-and-unitary',
                'Eigenvalue': 'math/05-eigenvalues', 'Tensor product': 'math/07-tensor-products',
                'Pauli matrices': 'math/10-pauli-algebra', 'Dirac notation': 'math/02-vectors-and-dirac-notation'}
    for name, lesson in expected.items():
        assert g.terms[name].lesson == lesson
    new = ['Complex number', 'Conjugate transpose', 'Inner product', 'Outer product', 'Projector', 'Trace',
           'Partial trace', 'Matrix exponential', 'Commutator', 'Gradient']
    assert all(g.terms[n].group == 'Mathematics' and g.terms[n].lesson.startswith('math/') for n in new)
    used = set()
    out = g.link('<p>the partial trace and the trace, a reduced density matrix, gradient descent</p>', used)
    assert re.findall(r'glossary:([^"]+)', out) == ['Partial trace', 'Trace', 'Gradient'] or \
        {'Partial trace', 'Trace', 'Gradient'} <= used
