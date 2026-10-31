"""Lesson Markdown → HTML for the reader (a deliberate, small subset of Markdown).

Supported: # headings, paragraphs, **bold**, *italic*, `code`, - and 1. lists,
| tables |, > notes, ``` code ```, images, links, $$display$$ and $inline$
equations, ```quiz``` blocks and ```step``` blocks (labs). Links starting with
qs: are QuantumScope actions ("Try it"); see learn.actions.
"""
import html
import os
import re

from .equations import DISPLAY, INLINE, image_name

PALETTES = {
    'dark': {'text': '#dce7f7', 'muted': '#9fb4cb', 'link': '#6fd6ee', 'note_bg': '#16283b', 'note_border': '#3c6d93',
             'code_bg': '#0d1520', 'ok': '#77e6a1', 'todo': '#9fb4cb', 'answer': '#77e6a1', 'rule': '#304058'},
    'light': {'text': '#1b364e', 'muted': '#4d6a82', 'link': '#0b6f8f', 'note_bg': '#e8f2fa', 'note_border': '#7aa7c7',
              'code_bg': '#eef3f8', 'ok': '#17703a', 'todo': '#4d6a82', 'answer': '#17703a', 'rule': '#c4d6e4'},
}


def _inline(text, ctx):
    """Inline formatting for already-HTML-escaped text."""
    # Code spans first, so their content is left alone.
    pieces = re.split(r'(`[^`]+`)', text)
    out = []
    for piece in pieces:
        if piece.startswith('`') and piece.endswith('`') and len(piece) > 1:
            out.append(f'<code style="background:{ctx["p"]["code_bg"]}">{piece[1:-1]}</code>')
            continue
        piece = re.sub(r'!\[([^\]]*)\]\(([^)\s]+)\)', lambda m: _image(m, ctx), piece)
        piece = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', lambda m: _link(m, ctx), piece)
        piece = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', piece)
        piece = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<i>\1</i>', piece)
        out.append(piece)
    return ''.join(out)


def _image(m, ctx):
    alt, src = m.group(1), html.unescape(m.group(2))
    if not re.match(r'^[a-z]+:', src):
        src = os.path.join(ctx['folder'], src)
    return f'<img src="{html.escape(src)}" alt="{alt}">'


def _link(m, ctx):
    label, target = m.group(1), html.unescape(m.group(2))
    if target.startswith('qs:'):
        return f'<a href="{html.escape(target)}" style="color:{ctx["p"]["link"]}; font-weight:600">▶ {label}</a>'
    return f'<a href="{html.escape(target)}" style="color:{ctx["p"]["link"]}">{label}</a>'


def _equation(tex, kind, ctx):
    name = image_name(tex, kind, ctx['theme'])
    path = os.path.join(ctx['eq_folder'], name)
    if os.path.exists(path):
        from PySide6.QtGui import QImage            # only to read the size (shown at half: 2× renders)
        image = QImage(path)
        w, h = image.width() // 2, image.height() // 2
        align = ' align="middle"' if kind == 'inline' else ''
        return f'<img src="{html.escape(path)}" width="{w}" height="{h}"{align}>'
    # No pre-rendered image (e.g. a teacher's own lesson): show the source, readable.
    return f'<span style="font-family:monospace; color:{ctx["p"]["muted"]}">{html.escape(tex)}</span>'


def _protect_math(text, ctx, store):
    """Replace equations by placeholders before escaping, then restore them as images."""
    def display(m):
        store.append(f'<p align="center">{_equation(m.group(1).strip(), "display", ctx)}</p>')
        return f'\x00{len(store) - 1}\x00'

    def inline(m):
        store.append(_equation(m.group(1).strip(), 'inline', ctx))
        return f'\x00{len(store) - 1}\x00'
    text = DISPLAY.sub(display, text)
    return INLINE.sub(inline, text)


def _restore(text, store):
    return re.sub('\x00(\\d+)\x00', lambda m: store[int(m.group(1))], text)


def _quiz(body, number, ctx):
    lines = [line.rstrip() for line in body.strip().splitlines() if line.strip()]
    question, options, explanation = '', [], ''
    for line in lines:
        if line.startswith('Q:'):
            question = line[2:].strip()
        elif line.startswith(('- ', '* ')):
            options.append((line[:1] == '*', line[2:].strip()))
        elif line.startswith('E:'):
            explanation = line[2:].strip()
    shown = number in ctx['revealed']
    p = ctx['p']
    parts = [f'<div style="background:{p["note_bg"]}; border-left:3px solid {p["note_border"]}; padding:8px">',
             f'<p><b>Check your understanding {number + 1}.</b> {_inline(html.escape(question), ctx)}</p><ol type="A">']
    for correct, text in options:
        item = _inline(html.escape(text), ctx)
        if shown and correct:
            item = f'<b style="color:{p["answer"]}">{item}  ✓</b>'
        parts.append(f'<li>{item}</li>')
    parts.append('</ol>')
    if shown:
        parts.append(f'<p>{_inline(html.escape(explanation), ctx)}</p>' if explanation else '')
    else:
        parts.append(f'<p><a href="qsquiz:{number}" style="color:{p["link"]}">Show answer</a></p>')
    parts.append('</div>')
    return ''.join(parts)


def parse_step(body):
    """A lab step block → dict(title, text, hint, checks)."""
    step = {'title': '', 'text': '', 'hint': '', 'checks': []}
    for line in body.strip().splitlines():
        if ':' not in line:
            step['text'] += ' ' + line.strip()
            continue
        name, value = line.split(':', 1)
        name = name.strip().lower()
        if name == 'check':
            step['checks'].append(value.strip())
        elif name in step:
            step[name] = value.strip()
        else:
            step['text'] += ' ' + line.strip()
    return step


def _step(body, number, ctx):
    step = parse_step(body)
    p = ctx['p']
    status = ctx['steps'].get(number)
    mark = (f'<span style="color:{p["ok"]}">✓ Done</span>' if status else
            f'<span style="color:{p["todo"]}">○ Not yet</span>')
    hint = (f'<p style="color:{p["muted"]}"><i>Hint: {_inline(html.escape(step["hint"]), ctx)}</i></p>'
            if step['hint'] else '')
    return (f'<div style="border:1px solid {p["rule"]}; padding:8px"><p><b>Step {number + 1}: '
            f'{_inline(html.escape(step["title"]), ctx)}</b> — {mark}</p>'
            f'<p>{_inline(html.escape(step["text"].strip()), ctx)}</p>{hint}</div>')


def steps_of(body):
    """Lab steps in order (for checking)."""
    return [parse_step(m.group(1)) for m in re.finditer(r'```step\n(.*?)```', body, re.S)]


def to_html(lesson, theme='dark', eq_folder='', revealed=(), steps=None, font_size=15):
    """HTML for the reader. revealed: quiz numbers whose answers are shown; steps: {number: done?}."""
    p = PALETTES.get(theme, PALETTES['dark'])
    ctx = {'p': p, 'theme': theme, 'eq_folder': eq_folder, 'folder': lesson.folder,
           'revealed': set(revealed), 'steps': dict(steps or {})}
    out = [f'<html><body style="color:{p["text"]}; font-size:{font_size}px">']
    pending = {'objectives': ''}
    if lesson.objectives:
        pending['objectives'] = (f'<div style="background:{p["note_bg"]}; padding:8px"><b>In this {lesson.kind}, '
                                 f'you will:</b><ul>' + ''.join(f'<li>{html.escape(o)}</li>' for o in lesson.objectives)
                                 + '</ul></div>')
    if pending['objectives'] and not re.match(r'\s*#\s', lesson.body):
        out.append(pending['objectives'])         # no title heading: objectives come first
        pending['objectives'] = ''
    lines = lesson.body.splitlines()
    i = 0
    quiz = step = 0
    paragraph = []

    def flush():
        if paragraph:
            store = []
            text = _protect_math(' '.join(paragraph), ctx, store)
            out.append('<p>' + _restore(_inline(html.escape(text), ctx), store) + '</p>')
            paragraph.clear()

    def render_line(text):
        store = []
        return _restore(_inline(html.escape(_protect_math(text, ctx, store)), ctx), store)

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith('```'):
            flush()
            tag = stripped[3:].strip()
            block = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                block.append(lines[i])
                i += 1
            body = '\n'.join(block)
            if tag == 'quiz':
                out.append(_quiz(body, quiz, ctx))
                quiz += 1
            elif tag == 'step':
                out.append(_step(body, step, ctx))
                step += 1
            else:
                out.append(f'<pre style="background:{p["code_bg"]}; padding:6px">{html.escape(body)}</pre>')
        elif stripped.startswith('$$'):
            flush()                                   # a display equation, on one line or several
            block = [stripped]
            if not (len(stripped) > 2 and stripped.endswith('$$')):
                i += 1
                while i < len(lines) and '$$' not in lines[i]:
                    block.append(lines[i].strip())
                    i += 1
                if i < len(lines):
                    block.append(lines[i].strip())
            out.append(render_line(' '.join(block)))
        elif re.match(r'^#{1,4}\s', stripped):
            flush()
            level = len(stripped) - len(stripped.lstrip('#'))
            out.append(f'<h{level + 1}>{render_line(stripped[level:].strip())}</h{level + 1}>')
            if level == 1 and pending['objectives']:   # objectives right after the lesson's title
                out.append(pending['objectives'])
                pending['objectives'] = ''
        elif stripped.startswith('>'):
            flush()
            note = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                note.append(lines[i].strip()[1:].strip())
                i += 1
            i -= 1
            out.append(f'<div style="background:{p["note_bg"]}; border-left:3px solid {p["note_border"]}; '
                       f'padding:8px">{render_line(" ".join(note))}</div>')
        elif re.match(r'^([-*]|\d+\.)\s', stripped):
            flush()
            ordered = bool(re.match(r'^\d+\.', stripped))
            items = []
            while i < len(lines) and re.match(r'^\s*([-*]|\d+\.)\s', lines[i]):
                items.append(re.sub(r'^\s*([-*]|\d+\.)\s+', '', lines[i]))
                i += 1
            i -= 1
            tag = 'ol' if ordered else 'ul'
            out.append(f'<{tag}>' + ''.join(f'<li>{render_line(t)}</li>' for t in items) + f'</{tag}>')
        elif stripped.startswith('|'):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = re.split(r'(?<!\\)\|', lines[i].strip().strip('|'))   # an escaped \| is a literal bar
                rows.append([c.strip().replace('\\|', '|') for c in cells])
                i += 1
            i -= 1
            body_rows = [r for r in rows if not all(re.fullmatch(r':?-{2,}:?', c) for c in r)]
            table = [f'<table border="1" cellpadding="6" cellspacing="0" style="border-color:{p["rule"]}">']
            for r, row in enumerate(body_rows):
                cell = 'th' if r == 0 and len(rows) > 1 and len(body_rows) < len(rows) else 'td'
                table.append('<tr>' + ''.join(f'<{cell}>{render_line(c)}</{cell}>' for c in row) + '</tr>')
            out.append(''.join(table) + '</table>')
        elif stripped in ('---', '***'):
            flush()
            out.append('<hr>')
        elif not stripped:
            flush()
        else:
            paragraph.append(stripped)
        i += 1
    flush()
    out.append('</body></html>')
    return '\n'.join(out)
