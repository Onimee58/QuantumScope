"""Build the user guide PDF from docs/user-guide.md and docs/references.md (an author's tool).

Layout is done by Qt (QTextDocument), page by page, so the builder knows exactly where every
heading and figure lands. That gives:
  - a title page (the logo and the author), then Contents and List of figures with page numbers;
  - figures numbered and captioned from their alt text;
  - blank-spot repair: an image that leaves a large gap at the bottom of a page is shrunk to fit
    it (down to 60%), and a heading stranded at the bottom of a page moves to the next one;
  - page numbers in the footer (not on the title page);
  - PDF bookmarks for every chapter and section, and clickable Contents entries (pypdf, BSD).
"""
import html as htmlmod
import os
import re

try:                                    # the layout needs Qt; the text helpers (figure floats) do not
    from PySide6.QtCore import QMarginsF, QRectF, QSizeF, Qt, QUrl
    from PySide6.QtGui import QFont, QImage, QPageLayout, QPageSize, QPainter, QTextDocument
    from PySide6.QtWidgets import QApplication
    from PySide6.QtPrintSupport import QPrinter
except ImportError:                     # e.g. a CI machine without graphics libraries
    QMarginsF = QRectF = QSizeF = Qt = QUrl = QFont = QImage = QPageLayout = QPageSize = None
    QPainter = QTextDocument = QApplication = QPrinter = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')
LOGO = os.path.join(ROOT, 'src', 'quantumscope', 'assets', 'quantumscope-512.png')
AUTHOR = 'Md. Saif Hassan Onim, PhD'
MAX_W, MAX_H = 640, 400                 # largest figure, in document units (96 per inch)
FOOTER = 26                             # room for the page number at the bottom of each page
GAP_LIMIT = 0.25                        # a page ending with more than this share empty is a "blank spot"
MIN_SCALE = 0.6                         # figures shrink at most to this to fill a gap


def _markdown():
    with open(os.path.join(DOCS, 'user-guide.md'), encoding='utf-8') as handle:
        guide = handle.read()
    with open(os.path.join(DOCS, 'references.md'), encoding='utf-8') as handle:
        refs = handle.read()
    number = len(re.findall(r'^## \d+\.', guide, re.M)) + 1
    refs = re.sub(r'^# References', f'## {number}. References', refs, count=1, flags=re.M)
    refs = re.sub(r'^## (?!\d)', '### ', refs, flags=re.M)               # groups become sections
    return guide.rstrip() + '\n\n' + refs


def _float_figures(markdown, floats):
    """Move figure k down past floats[k] paragraphs or lists, never past a heading (like LaTeX floats)."""
    blocks = re.split(r'\n\s*\n', markdown.strip())
    figure_blocks = [i for i, b in enumerate(blocks) if b.lstrip().startswith('![')]
    for k in sorted(floats, reverse=True):
        i = figure_blocks[k]
        steps = 0
        while steps < floats[k] and i + 1 < len(blocks) and not blocks[i + 1].lstrip().startswith(('#', '![')):
            blocks[i], blocks[i + 1] = blocks[i + 1], blocks[i]
            i += 1
            steps += 1
    return '\n\n'.join(blocks) + '\n'


def _can_float(markdown, floats, k):
    """Whether figure k can move one more block down within its section."""
    before = _float_figures(markdown, floats)
    after = _float_figures(markdown, {**floats, k: floats.get(k, 0) + 1})
    return before != after


def _body_html(markdown):
    """The guide as HTML, with numbered, captioned, sized figures. Returns (html, figures)."""
    figures = [(alt, src) for alt, src in re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', markdown)]
    doc = QTextDocument()
    doc.setMarkdown(markdown)
    html = doc.toHtml()
    html = html[html.index('<body'):]
    html = html[html.index('>') + 1:html.rindex('</body>')]
    count = [0]

    def figure(match):
        k = count[0]
        count[0] += 1
        alt, src = figures[k]
        image = QImage(os.path.join(DOCS, src))
        scale = min(1.0, MAX_W / image.width(), MAX_H / image.height())
        w, h = int(image.width() * scale), int(image.height() * scale)
        return (f'<p align="center" style="margin-top:8px; margin-bottom:12px;"><a name="figure-{k}"></a>'
                f'<img src="{src}" width="{w}" height="{h}" /><br />'
                f'<span style="font-size:9pt; color:#4a5568;"><b>Figure {k + 1}.</b> {htmlmod.escape(alt)}</span></p>')
    html = re.sub(r'<p[^>]*><img src="[^"]+"[^>]*/></p>', figure, html)
    assert count[0] == len(figures), 'every figure must be on its own paragraph'
    return html, figures


def _front(headings, figures, pages):
    """Title page, Contents and List of figures (page numbers from `pages`, or placeholders)."""
    def page(key):
        return str(pages.get(key, '000'))
    rows = []
    for k, (level, text) in enumerate(headings):
        indent, weight = (0, 600) if level == 2 else (22, 400)
        rows.append(f'<tr><td style="padding-left:{indent}px; font-weight:{weight};">{htmlmod.escape(text)}</td>'
                    f'<td align="right" style="font-weight:{weight};">{page(("h", k))}</td></tr>')
    fig_rows = [f'<tr><td>Figure {k + 1}. {htmlmod.escape(alt)}</td><td align="right">{page(("f", k))}</td></tr>'
                for k, (alt, _) in enumerate(figures)]
    table = '<table width="100%" cellspacing="0" cellpadding="3">{}</table>'
    return (f'<p align="center" style="margin-top:230px;"><img src="{QUrl.fromLocalFile(LOGO).toString()}" '
            f'width="230" height="230" /></p>'
            f'<p align="center" style="margin-top:40px; font-size:20pt; font-weight:600; page-break-after:always;">'
            f'{AUTHOR}</p>'
            '<h1>Contents</h1>' + table.format(''.join(rows)) +
            '<p style="page-break-after:always;"></p>'
            '<h1>List of figures</h1>' + table.format(''.join(fig_rows)) +
            '<p style="page-break-after:always;"></p>')


class Guide:
    def __init__(self):
        QApplication.instance() or QApplication([])
        self.printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        self.printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        self.printer.setPageLayout(QPageLayout(QPageSize(QPageSize.PageSizeId.Letter), QPageLayout.Orientation.Portrait,
                                               QMarginsF(18, 18, 18, 18), QPageLayout.Unit.Millimeter))
        area = self.printer.pageLayout().paintRect(QPageLayout.Unit.Inch)
        self.W, self.H = area.width() * 96.0, area.height() * 96.0 - FOOTER
        self.markdown = _markdown()
        self.breaks = set()                       # heading numbers that start a new page
        self.shrink = {}                          # figure number → scale
        self.floats = {}                          # figure number → paragraphs it moves down
        self._rebuild()

    def _rebuild(self):
        self.body, self.figures = _body_html(_float_figures(self.markdown, self.floats))

    def _document(self, pages):
        body = self.body
        for k, scale in self.shrink.items():      # shrink chosen figures
            body = re.sub(rf'(<a name="figure-{k}"></a><img src="[^"]+" width=")(\d+)(" height=")(\d+)',
                          lambda m: f'{m.group(1)}{int(int(m.group(2)) * scale)}{m.group(3)}{int(int(m.group(4)) * scale)}',
                          body)
        heads = list(re.finditer(r'<h([23])([^>]*)>', body))
        for k in sorted(self.breaks, reverse=True):
            m = heads[k]
            body = body[:m.start()] + f'<h{m.group(1)}{m.group(2)} style="page-break-before:always;"' + \
                body[m.start() + 3 + len(m.group(2)):]
        doc = QTextDocument()
        font = QFont(doc.defaultFont())
        font.setPointSizeF(10.5)
        doc.setDefaultFont(font)
        doc.setBaseUrl(QUrl.fromLocalFile(DOCS + os.sep))
        headings = [(int(m.group(1)), htmlmod.unescape(re.sub(r'<[^>]+>', '', m.group(2))).strip())
                    for m in re.finditer(r'<h([23])[^>]*>(.*?)</h\1>', body, re.S)]
        doc.setHtml('<html><body>' + _front(headings, self.figures, pages) + body + '</body></html>')
        doc.setPageSize(QSizeF(self.W, self.H))
        doc.documentLayout().documentSize()                    # lay it out
        return doc, headings

    def _scan(self, doc):
        """Where every block is: (page, top, bottom, kind, index) in layout order. The body starts at
        the guide's title; before it come the title page, Contents and List of figures."""
        layout, out = doc.documentLayout(), []
        heading_k = figure_k = 0
        in_body = False
        self.front_pages = {}
        block = doc.begin()
        while block.isValid():
            rect = layout.blockBoundingRect(block)
            level = block.blockFormat().headingLevel()
            text = block.text().strip()
            kind, index = 'text', None
            if level == 1 and not in_body:
                if text == 'QuantumScope User Guide':
                    in_body = True
                else:
                    self.front_pages[text] = int(rect.top() // self.H)   # Contents, List of figures
            elif in_body and level in (2, 3):
                kind, index = 'heading', heading_k
                heading_k += 1
            elif in_body and any(f.fragment().charFormat().isImageFormat() for f in _fragments(block)):
                kind, index = 'figure', figure_k
                figure_k += 1
            lines = block.layout()
            if lines.lineCount():                                   # pages by line: Qt moves lines, not blocks
                first, last_line = lines.lineAt(0), lines.lineAt(lines.lineCount() - 1)
                top = rect.top() + first.y()
                bottom = rect.top() + last_line.y() + last_line.height()
            else:
                top, bottom = rect.top(), rect.bottom()
            page = int(top // self.H)
            out.append((page, top, bottom, kind, index, level))
            block = block.next()
        return out

    def layout(self, pages=None, repair=True):
        """Lay out, repairing blank spots, until the page numbers are stable."""
        pages = pages or {}
        for _ in range(60):
            doc, headings = self._document(pages)
            scan = self._scan(doc)
            changed = False
            if repair:
                for i, (page, top, bottom, kind, index, level) in enumerate(scan):
                    nxt = scan[i + 1] if i + 1 < len(scan) else None
                    if kind == 'heading' and nxt is not None and nxt[0] > page and index not in self.breaks:
                        if nxt[3] == 'figure' and _can_float(self.markdown, self.floats, nxt[4]):
                            self.floats[nxt[4]] = self.floats.get(nxt[4], 0) + 1   # text first, figure after
                            self._rebuild()
                        else:
                            self.breaks.add(index)                 # a heading alone at the bottom: move it
                        changed = True
                        break
                    if kind == 'figure' and i > 0 and top - page * self.H < 60 and scan[i - 1][0] < page:
                        end = max(b for (pg, t, b, *_r) in scan[:i] if b <= page * self.H)
                        gap = page * self.H - end
                        if gap > GAP_LIMIT * self.H and bottom > top:
                            current = self.shrink.get(index, 1.0)
                            scale = current * max(0.0, gap - 40) / (bottom - top)
                            if scale >= MIN_SCALE:
                                if abs(scale - current) > 0.01:
                                    self.shrink[index] = min(current, scale)
                                    changed = True
                                    break
                            elif _can_float(self.markdown, self.floats, index):
                                self.floats[index] = self.floats.get(index, 0) + 1
                                self._rebuild()
                                changed = True
                                break
            found = {}
            for page, top, bottom, kind, index, level in scan:
                if kind in ('heading', 'figure'):
                    found[(kind[0], index)] = page + 1
            if not changed and found == pages:
                return doc, headings, scan, pages
            pages = found
        return doc, headings, scan, pages

    def blank_spots(self, scan):
        """Pages (1-based) whose content ends early, other than the front matter and the last page."""
        last = {}
        for page, top, bottom, kind, index, level in scan:
            last[page] = max(last.get(page, 0), min(bottom, (page + 1) * self.H) - page * self.H)
        first_body = min(p for p, *_r in [s for s in scan if s[3] in ('heading', 'figure')])
        pages = sorted(last)
        return [(p + 1, 1 - last[p] / self.H) for p in pages
                if first_body <= p < pages[-1] and 1 - last[p] / self.H > GAP_LIMIT]

    def paint(self, doc, path):
        printer = self.printer
        printer.setOutputFileName(path)
        printer.setDocName('QuantumScope User Guide')
        scale = printer.resolution() / 96.0
        total = int(doc.documentLayout().documentSize().height() // self.H) + 1
        painter = QPainter(printer)
        font = QFont(doc.defaultFont())
        font.setPixelSize(12)                                      # in document units: the painter is scaled
        for p in range(total):
            if p:
                printer.newPage()
            painter.save()
            painter.scale(scale, scale)
            painter.translate(0, -p * self.H)
            doc.drawContents(painter, QRectF(0, p * self.H, self.W, self.H))
            painter.restore()
            if p:                                                  # no number on the title page
                painter.save()
                painter.scale(scale, scale)
                painter.setFont(font)
                painter.setPen(Qt.GlobalColor.darkGray)
                painter.drawText(QRectF(0, self.H + 4, self.W, FOOTER - 4), Qt.AlignmentFlag.AlignCenter, str(p + 1))
                painter.restore()
        painter.end()
        return total


def _fragments(block):
    it = block.begin()
    while not it.atEnd():
        yield it
        it += 1


def bookmarks_and_links(path, guide, doc, headings, scan, pages):
    """PDF outline (chapters with their sections) and clickable Contents / List of figures entries."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import ArrayObject, DictionaryObject, Fit, FloatObject, NameObject, NumberObject
    writer = PdfWriter(clone_from=PdfReader(path))
    writer.add_outline_item('Contents', guide.front_pages['Contents'], fit=Fit.fit())
    writer.add_outline_item('List of figures', guide.front_pages['List of figures'], fit=Fit.fit())
    parent = None
    for k, (level, text) in enumerate(headings):
        target = pages[('h', k)] - 1
        if level == 2:
            parent = writer.add_outline_item(text, target, fit=Fit.fit())
        else:
            writer.add_outline_item(text, target, parent=parent, fit=Fit.fit())
    # Links: each Contents / List of figures row points at its page.
    margin_pt = 18 / 25.4 * 72
    page_h_pt = float(writer.pages[0].mediabox.height)
    rows = _table_rows(doc)
    targets = [pages[('h', k)] - 1 for k in range(len(headings))] + [pages[('f', k)] - 1 for k in range(len(guide.figures))]
    for (page, top, bottom), target in zip(rows, targets):
        y0 = page_h_pt - margin_pt - (bottom - page * guide.H) * 0.75
        y1 = page_h_pt - margin_pt - (top - page * guide.H) * 0.75
        link = DictionaryObject({
            NameObject('/Type'): NameObject('/Annot'), NameObject('/Subtype'): NameObject('/Link'),
            NameObject('/Rect'): ArrayObject([FloatObject(v) for v in (margin_pt, y0, margin_pt + guide.W * 0.75, y1)]),
            NameObject('/Border'): ArrayObject([NumberObject(0), NumberObject(0), NumberObject(0)]),   # no box
            NameObject('/Dest'): ArrayObject([writer.pages[target].indirect_reference, NameObject('/Fit')])})
        holder = writer.pages[page]
        if '/Annots' not in holder:
            holder[NameObject('/Annots')] = ArrayObject()
        holder['/Annots'].append(writer._add_object(link))
    writer.page_mode = '/UseOutlines'                              # open with the bookmarks showing
    writer.add_metadata({'/Title': 'QuantumScope User Guide', '/Author': AUTHOR})
    with open(path, 'wb') as handle:
        writer.write(handle)


def _table_rows(doc):
    """(page, top, bottom) of each row of the Contents and List of figures tables, in order."""
    layout, rows = doc.documentLayout(), []
    frame_iter = doc.rootFrame().begin()
    tables = 0
    while not frame_iter.atEnd() and tables < 2:
        frame = frame_iter.currentFrame()
        if frame is not None and hasattr(frame, 'cellAt'):
            table = frame
            tables += 1
            for r in range(table.rows()):
                cell = table.cellAt(r, 0)
                rect = layout.blockBoundingRect(cell.firstCursorPosition().block())
                H = doc.pageSize().height()
                rows.append((int(rect.top() // H), rect.top(), rect.bottom()))
        frame_iter += 1
    return rows


def build(path):
    guide = Guide()
    doc, headings, scan, pages = guide.layout()
    total = guide.paint(doc, path)
    bookmarks_and_links(path, guide, doc, headings, scan, pages)
    gaps = guide.blank_spots(scan)
    return dict(pages=total, headings=len(headings), figures=len(guide.figures), shrunk=dict(guide.shrink),
                moved=sorted(guide.breaks), floated=dict(guide.floats), gaps=gaps)
