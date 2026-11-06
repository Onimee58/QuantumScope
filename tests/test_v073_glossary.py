"""v0.7.3: the Learn glossary (Qt-free parts)."""
import re

import pytest

from quantumscope.learn import glossary as G
from quantumscope.learn.lessons import builtin_lessons, parse
from quantumscope.learn.render import to_html

GLOSSARY = G.builtin()
LESSONS = {l.key: l for l in builtin_lessons()}


def links(markup):
    return re.findall(r'href="glossary:([^"]+)"[^>]*>([^<]+)<', markup)


def test_the_glossary_is_complete_and_consistent():
    terms = GLOSSARY.terms
    assert len(terms) == 105                                                   # + 10 Mathematics (0.7.7), + 14 Quantum ML (0.8.0)
    for term in terms.values():
        assert term.definition and term.group, term.name
        assert term.lesson in LESSONS, (term.name, term.lesson)               # Learn more opens a real lesson
        assert all(s in terms for s in term.see), (term.name, term.see)       # related terms exist
    words = [w.lower() for t in terms.values() for w in (t.name,) + t.aliases]
    assert len(words) == len(set(words))                                       # no alias belongs to two terms


def test_first_occurrence_longest_first_and_case_rules():
    used = set()
    out = GLOSSARY.link('<p>a phase flip and a phase; the QFT, not qft; then phase flip again</p>', used)
    assert links(out) == [('Phase flip', 'phase flip'), ('Phase', 'phase'), ('Quantum Fourier transform', 'QFT')]
    assert 'qft' in out and used == {'Phase flip', 'Phase', 'Quantum Fourier transform'}


def test_never_inside_links_code_or_partial_words():
    out = GLOSSARY.link('<p><a href="x">qubit</a> <code>qubit</code> qubitness bit-flip-ish phase-flip</p>', set())
    assert links(out) == []


def test_every_lecture_links_each_term_once_and_never_in_headings():
    for lesson in LESSONS.values():
        markup = to_html(lesson, 'dark', glossary=GLOSSARY)
        names = [name for name, _ in links(markup)]
        assert len(names) == len(set(names)), lesson.key
        assert not re.search(r'<h\d>(?:(?!</h\d>).)*glossary:', markup), lesson.key
    total = sum(len(links(to_html(l, 'dark', glossary=GLOSSARY))) for l in LESSONS.values() if l.kind == 'lecture')
    assert total > 200


def test_author_controls_noglossary_and_explicit_links():
    text = ('---\ntitle: T\nnoglossary: Phase\n---\nThe phase here is not ours, but the [[Hermitian]] and '
            '[[these|Hamiltonian]] and [[nothing real]] links.\n')
    lesson = parse(text, 'course/t', '.')
    assert lesson.noglossary == ('Phase',)
    out = to_html(lesson, 'dark', glossary=GLOSSARY)
    assert ('Hermitian', 'Hermitian') in links(out) and ('Hamiltonian', 'these') in links(out)
    assert all(name != 'Phase' for name, _ in links(out)) and 'nothing real' in out and '[[' not in out


def test_orbital_is_linked_in_its_proper_sense():
    out = to_html(LESSONS['hydrogen/02-quantum-numbers-and-orbitals'], 'dark', glossary=GLOSSARY)
    assert ('Orbital', 'orbitals') in links(out) and 'orbital angular momentum' in out


def test_without_a_glossary_lessons_render_as_before():
    assert 'glossary:' not in to_html(LESSONS['principles/08-observables'], 'dark')


def test_glossary_page_markdown():
    page = GLOSSARY.page_markdown()
    assert page.startswith('# Glossary') and page.count('**') == 2 * 105 and '[[Eigenvalue]]' in page
    assert '(qs:lesson/math/04-hermitian-and-unitary)' in page
