"""The Learn glossary: terms such as Hermitian or Hamiltonian, linked from lessons (no Qt).

Terms live in content/glossary.md. In a lesson, the first occurrence of each term (or one of its
aliases) is linked automatically, longest terms first ("phase flip" before "phase"), and never
inside headings, links, code or equations. Authors write [[Term]] or [[shown text|Term]] for an
explicit link, and "noglossary: Term, Term" in a lesson's header to switch terms off there.
"""
from dataclasses import dataclass
import functools
import html
import os
import re

from .lessons import content_folder


@dataclass(frozen=True)
class Term:
    name: str
    aliases: tuple
    lesson: str
    see: tuple
    definition: str
    group: str


def _case_sensitive(word):
    """Acronyms and words with inner capitals (QFT, VQE, MaxCut) match exactly; other words in any case."""
    return any(ch.isupper() for ch in word[1:]) or (len(word) <= 5 and word.isupper())


class Glossary:
    def __init__(self, terms):
        self.terms = {t.name: t for t in terms}
        self._lookup_exact, self._lookup_lower = {}, {}
        alternatives = []
        for term in terms:
            for word in (term.name,) + term.aliases:
                if _case_sensitive(word):
                    self._lookup_exact[word] = term.name
                    alternatives.append((len(word), re.escape(word)))
                else:
                    self._lookup_lower[word.lower()] = term.name
                    alternatives.append((len(word), f'(?i:{re.escape(word)})'))
        alternatives.sort(key=lambda a: -a[0])                     # longest first
        self._pattern = re.compile(r'(?<![\w\-])(' + '|'.join(a for _, a in alternatives) + r')(?![\w\-])') \
            if alternatives else None

    def term_for(self, text):
        return self._lookup_exact.get(text) or self._lookup_lower.get(text.lower())

    def resolve(self, name):
        """A term by its name or any alias (for [[...]] links), or None."""
        found = self.terms.get(name) or self.terms.get(self.term_for(name) or '')
        return found

    def link(self, markup, used, exclude=(), style=''):
        """Link first occurrences in the text parts of HTML `markup`.
        `used` (a set) collects linked term names across a whole lesson."""
        if self._pattern is None:
            return markup
        out, skip = [], 0
        for part in re.split(r'(<[^>]+>)', markup):
            if part.startswith('<'):
                tag = re.match(r'</?\s*(\w+)', part)
                if tag and tag.group(1).lower() in ('a', 'code', 'pre'):
                    skip += -1 if part.startswith('</') else 1
                out.append(part)
                continue
            if skip > 0 or not part:
                out.append(part)
                continue

            def replace(m):
                name = self.term_for(m.group(1))
                if name is None or name in used or name in exclude:
                    return m.group(1)
                used.add(name)
                return f'<a href="glossary:{html.escape(name)}" style="{style}">{m.group(1)}</a>'
            out.append(self._pattern.sub(replace, part))
        return ''.join(out)

    def page_markdown(self):
        """The Glossary page: every term, grouped, with related terms and Learn more links."""
        lines = ['# Glossary', '',
                 'Every term below is also linked from the lessons: click one wherever it appears.', '']
        groups = []
        for term in self.terms.values():
            if term.group not in groups:
                groups.append(term.group)
        for group in groups:
            lines += [f'## {group}', '']
            for term in sorted((t for t in self.terms.values() if t.group == group), key=lambda t: t.name.lower()):
                extra = ''
                if term.see:
                    extra += ' *Related:* ' + ', '.join(f'[[{s}]]' for s in term.see) + '.'
                if term.lesson:
                    extra += f' [Learn more](qs:lesson/{term.lesson})'
                lines += [f'**{term.name}** — {term.definition}{extra}', '']
        return '\n'.join(lines)


def parse(text):
    terms, group, current = [], '', None

    def finish():
        if current is not None:
            terms.append(Term(current['name'], tuple(current['aliases']), current['lesson'], tuple(current['see']),
                              ' '.join(current['text']).strip(), current['group']))
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith('### '):
            finish()
            current = {'name': line[4:].strip(), 'aliases': [], 'lesson': '', 'see': [], 'text': [], 'group': group}
        elif line.startswith('## '):
            finish()
            current, group = None, line[3:].strip()
        elif current is None or not line or line.startswith('# '):
            continue
        elif re.match(r'^(aliases|lesson|see):', line):
            key, value = line.split(':', 1)
            if key == 'lesson':
                current['lesson'] = value.strip()
            else:
                current[key] = [v.strip() for v in value.split(',') if v.strip()]
        else:
            current['text'].append(line)
    finish()
    return terms


@functools.lru_cache(maxsize=1)
def builtin():
    with open(os.path.join(content_folder(), 'glossary.md'), encoding='utf-8') as handle:
        return Glossary(parse(handle.read()))
