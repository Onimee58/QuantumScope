"""Equations in lessons: written as $$…$$ (display) or $…$ (inline), pre-rendered to images.

Rendering needs matplotlib and Pillow, which only authors need: run
`python tools/render_equations.py` after editing lessons. The app itself only
loads the ready-made images (one per theme), so installers stay small.
Matrices (\\begin{pmatrix}…\\end{pmatrix}) are drawn here, since matplotlib's
math renderer does not support them.
"""
import hashlib
import os
import re

THEME_COLORS = {'dark': '#e3f2ff', 'light': '#1b364e'}
SCALE = 2                     # images are rendered at 2× and shown at half size (crisp on HiDPI)
SIZES = {'display': 18, 'inline': 15}    # ≈ pixels on screen; body text is 15 px
DISPLAY = re.compile(r'\$\$(.+?)\$\$', re.S)
INLINE = re.compile(r'(?<![\\$])\$(?!\$)([^$\n]+?)\$(?!\$)')
MATRIX = re.compile(r'\\begin\{pmatrix\}(.*?)\\end\{pmatrix\}', re.S)


def key(tex, kind):
    return hashlib.sha1(f'{kind}\n{tex.strip()}'.encode('utf-8')).hexdigest()[:14]


def image_name(tex, kind, theme):
    return f'{key(tex, kind)}-{theme}.png'


def equations_in(text):
    """[(tex, kind)] for every equation in a lesson body, display first then inline."""
    found = [(m.group(1).strip(), 'display') for m in DISPLAY.finditer(text)]
    stripped = DISPLAY.sub(' ', text)
    stripped = re.sub(r'```.*?```', ' ', stripped, flags=re.S)        # code blocks contain no math
    found += [(m.group(1).strip(), 'inline') for m in INLINE.finditer(stripped)]
    return found


# ---- build-time rendering (authors only) ------------------------------------------------------

def _mathtext(tex, color, size):
    """Render math text on a transparent background (math_to_image saves an opaque one)."""
    import io
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib.figure import Figure
    from PIL import Image
    fig = Figure(figsize=(0.01, 0.01))
    fig.text(0, 0, f'${tex}$', fontsize=size, color=color)
    buffer = io.BytesIO()
    fig.savefig(buffer, dpi=72 * SCALE, format='png', transparent=True, bbox_inches='tight', pad_inches=0.02)
    buffer.seek(0)
    image = Image.open(buffer).convert('RGBA')
    box = image.getbbox()                      # trim to the ink
    return image.crop(box) if box else image


def _matrix(body, color, size):
    from PIL import Image, ImageDraw
    rows = [r for r in re.split(r'\\\\', body) if r.strip()]
    cells = [[_mathtext(c.strip() or r'\ ', color, size) for c in r.split('&')] for r in rows]
    ncol = max(len(r) for r in cells)
    pad = 10 * SCALE
    widths = [max(r[c].width if c < len(r) else 0 for r in cells) for c in range(ncol)]
    heights = [max(im.height for im in r) for r in cells]
    bracket = 9 * SCALE
    width = sum(widths) + pad * (ncol - 1) + 2 * bracket + 2 * pad // 2
    height = sum(heights) + (pad // 2) * (len(rows) - 1) + 2 * SCALE
    out = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    y = SCALE
    for r, row in enumerate(cells):
        x = bracket + pad // 2
        for c in range(ncol):
            if c < len(row):
                im = row[c]
                out.alpha_composite(im, (x + (widths[c] - im.width) // 2, y + (heights[r] - im.height) // 2))
            x += widths[c] + pad
        y += heights[r] + pad // 2
    draw = ImageDraw.Draw(out)
    line = max(2, SCALE + 1)
    draw.arc((0, 0, 2 * bracket, height - 1), 100, 260, fill=color, width=line)
    draw.arc((width - 2 * bracket - 1, 0, width - 1, height - 1), -80, 80, fill=color, width=line)
    return out


def render(tex, kind, color):
    """A transparent PIL image of the equation (matrices supported)."""
    from PIL import Image
    size = SIZES[kind]
    parts = []
    pos = 0
    for m in MATRIX.finditer(tex):
        if tex[pos:m.start()].strip():
            parts.append(_mathtext(tex[pos:m.start()], color, size))
        parts.append(_matrix(m.group(1), color, size))
        pos = m.end()
    if tex[pos:].strip():
        parts.append(_mathtext(tex[pos:], color, size))
    gap = 3 * SCALE
    width = sum(p.width for p in parts) + gap * (len(parts) - 1)
    height = max(p.height for p in parts)
    out = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    x = 0
    for p in parts:
        out.alpha_composite(p, (x, (height - p.height) // 2))
        x += p.width + gap
    return out


def render_all(lesson_texts, folder, force=False):
    """Render every equation found in the texts into folder; returns (rendered, kept, unused files)."""
    os.makedirs(folder, exist_ok=True)
    wanted = set()
    rendered = kept = 0
    for text in lesson_texts:
        for tex, kind in equations_in(text):
            for theme, color in THEME_COLORS.items():
                name = image_name(tex, kind, theme)
                wanted.add(name)
                path = os.path.join(folder, name)
                if os.path.exists(path) and not force:
                    kept += 1
                    continue
                render(tex, kind, color).save(path, optimize=True)
                rendered += 1
    unused = sorted(n for n in os.listdir(folder) if n.endswith('.png') and n not in wanted)
    return rendered, kept, unused
