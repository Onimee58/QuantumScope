"""v0.8.0: the user guide PDF's structure, its references, and the builder's figure floats."""
import os
import re
import sys

import pytest

ROOT = os.path.join(os.path.dirname(__file__), '..')
PDF = os.path.join(ROOT, 'src', 'quantumscope', 'assets', 'QuantumScope-User-Guide.pdf')
REFS = os.path.join(ROOT, 'docs', 'references.md')


def test_references_are_numbered_and_well_formed():
    text = open(REFS, encoding='utf-8').read()
    numbers = [int(n) for n in re.findall(r'^(\d+)\. ', text, re.M)]
    assert numbers == list(range(1, len(numbers) + 1)) and len(numbers) >= 41
    for doi in re.findall(r'https://doi\.org/(\S+)', text):
        assert re.match(r'^10\.\d{4,5}/\S+[^.,;]$', doi), doi                    # a DOI, no trailing punctuation
    for must in ('Havlíček', 'Bravo-Prieto', 'Thanasilp', 'Cortes, C. & Vapnik', 'Fisher, R. (1936)', 'MNIST'):
        assert must in text, must


def test_the_pdf_has_a_title_page_bookmarks_links_and_page_numbers():
    pypdf = pytest.importorskip('pypdf')
    reader = pypdf.PdfReader(PDF)
    texts = [re.sub(r'\s+', ' ', page.extract_text() or '') for page in reader.pages]
    assert texts[0].strip() == 'Md. Saif Hassan Onim, PhD'                         # only the logo and the author
    assert texts[1].startswith('Contents') and 'List of figures' in ' '.join(texts[2:4])

    def walk(items):
        for item in items:
            if isinstance(item, list):
                yield from walk(item)
            else:
                yield item.title, reader.get_destination_page_number(item)
    marks = list(walk(reader.outline))
    titles = [t for t, _ in marks]
    for chapter in ('Quantum ML', 'Quantum Circuits', 'References'):
        assert any(chapter in t for t in titles), chapter
    norm = lambda t: re.sub(r'[^a-z0-9]', '', t.lower())                           # noqa: E731
    assert all(norm(t)[:25] in norm(texts[p]) for t, p in marks)                  # each bookmark on its page
    links = [a.get_object() for page in reader.pages[:4] for a in (page.get('/Annots') or [])]
    assert len(links) >= len(marks) - 2 and all(reader.get_page_number(a['/Dest'][0].get_object()) is not None
                                                 for a in links)
    assert all(re.search(rf'(^|\s){k + 1}\s*$', texts[k]) for k in range(1, len(texts)))   # footers


def test_figures_float_within_their_section_only():
    sys.path.insert(0, os.path.join(ROOT, 'tools'))
    from guide_pdf import _float_figures
    markdown = '## A\n\n![one](a.png)\n\nText 1.\n\nText 2.\n\n## B\n\nText 3.\n'
    assert _float_figures(markdown, {0: 1}).index('![one]') > _float_figures(markdown, {0: 1}).index('Text 1.')
    far = _float_figures(markdown, {0: 9})
    assert far.index('Text 2.') < far.index('![one]') < far.index('## B')          # never past the next heading
