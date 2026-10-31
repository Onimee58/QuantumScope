"""Lessons: Markdown files with a small header block.

    ---
    title: Qubits, state vectors and bit order
    area: circuits            # circuits, principles, hydrogen (or anything, for teachers' lessons)
    kind: lecture             # lecture or lab
    order: 1
    objectives: Write a qubit state | Read a basis label
    ---
    Markdown body…

Built-in lessons ship in quantumscope/learn/content/<area>/. Teachers' own
lessons are read from a folder chosen in Settings (shown under "My course");
their header is optional — the first "# Heading" becomes the title.
"""
from dataclasses import dataclass, field
from importlib.resources import files
import os
import re

AREAS = {'circuits': 'Quantum Circuits', 'principles': 'Quantum Principles', 'hydrogen': 'Hydrogen'}
COURSE = 'course'
MAX_LESSON_BYTES = 2_000_000


@dataclass(frozen=True)
class Lesson:
    key: str                  # 'circuits/01-qubits' or 'course/<file name>'
    title: str
    area: str
    kind: str                 # 'lecture' or 'lab'
    order: float
    body: str
    folder: str               # where relative images resolve
    objectives: tuple = field(default=())

    @property
    def builtin(self):
        return not self.key.startswith(COURSE + '/')


def parse(text, key, folder, default_area=COURSE):
    """Split the header from the body. Invalid or missing headers fall back to defaults."""
    meta = {}
    body = text
    match = re.match(r'\A---\s*\n(.*?)\n---\s*\n', text, re.S)
    if match:
        for line in match.group(1).splitlines():
            if ':' in line:
                name, value = line.split(':', 1)
                meta[name.strip().lower()] = value.split(' #', 1)[0].strip().strip('"').strip("'")
        body = text[match.end():]
    title = meta.get('title')
    if not title:
        heading = re.search(r'^#\s+(.+)$', body, re.M)
        title = heading.group(1).strip() if heading else os.path.splitext(os.path.basename(key))[0]
    try:
        order = float(meta.get('order', 999))
    except ValueError:
        order = 999.0
    kind = meta.get('kind', 'lecture').lower()
    objectives = tuple(o.strip() for o in meta.get('objectives', '').split('|') if o.strip())
    return Lesson(key, title, meta.get('area', default_area), kind if kind in ('lecture', 'lab') else 'lecture',
                  order, body, folder, objectives)


def content_folder():
    return str(files('quantumscope.learn').joinpath('content'))


def builtin_lessons():
    root = content_folder()
    lessons = []
    for area in AREAS:
        folder = os.path.join(root, area)
        if not os.path.isdir(folder):
            continue
        for name in sorted(os.listdir(folder)):
            if name.endswith('.md'):
                with open(os.path.join(folder, name), encoding='utf-8') as handle:
                    lessons.append(parse(handle.read(), f'{area}/{name[:-3]}', folder, area))
    return sorted(lessons, key=lambda l: (list(AREAS).index(l.area), l.order, l.title))


def course_lessons(folder):
    """Teachers' lessons: every .md file in the folder (not recursive). Unreadable files are skipped."""
    lessons = []
    if not folder or not os.path.isdir(folder):
        return lessons
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if not name.lower().endswith('.md') or not os.path.isfile(path) or os.path.getsize(path) > MAX_LESSON_BYTES:
            continue
        try:
            with open(path, encoding='utf-8') as handle:
                lesson = parse(handle.read(), f'{COURSE}/{name}', folder)
        except (OSError, UnicodeDecodeError):
            continue
        lessons.append(Lesson(lesson.key, lesson.title, COURSE, lesson.kind, lesson.order, lesson.body,
                              folder, lesson.objectives))
    return sorted(lessons, key=lambda l: (l.order, l.title.lower()))


def search(lessons, query, limit=30):
    """Lessons matching every word of the query, title matches first."""
    words = [w for w in re.findall(r'\w+', query.lower()) if w]
    if not words:
        return []
    scored = []
    for lesson in lessons:
        title, body = lesson.title.lower(), lesson.body.lower()
        if all(w in title or w in body for w in words):
            score = sum(3 for w in words if w in title) + sum(body.count(w) for w in words)
            scored.append((-score, lesson.title, lesson))
    return [item[2] for item in sorted(scored, key=lambda x: (x[0], x[1]))[:limit]]
