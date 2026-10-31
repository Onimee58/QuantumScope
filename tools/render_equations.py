"""Render the equations in QuantumScope's built-in lessons (authors only).

Usage:  python tools/render_equations.py [--force] [--prune]
Needs matplotlib and Pillow (pip install matplotlib). Writes PNGs to
src/quantumscope/learn/content/eq/, one per equation and theme; --prune
removes images no lesson uses any more.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from quantumscope.learn.equations import render_all  # noqa: E402
from quantumscope.learn.lessons import builtin_lessons, content_folder, reference_pages  # noqa: E402


def main():
    folder = os.path.join(content_folder(), 'eq')
    texts = [lesson.body for lesson in builtin_lessons() + reference_pages()]
    rendered, kept, unused = render_all(texts, folder, force='--force' in sys.argv)
    if '--prune' in sys.argv:
        for name in unused:
            os.remove(os.path.join(folder, name))
    print(f'{rendered} rendered, {kept} up to date, {len(unused)} unused'
          + (' (removed)' if '--prune' in sys.argv and unused else ''))


if __name__ == '__main__':
    main()
