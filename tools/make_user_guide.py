"""Build QuantumScope's user guide: screenshots of the real app, then the PDF (authors only).

Usage:  python tools/make_user_guide.py            # screenshots + PDF
        python tools/make_user_guide.py --pdf-only # rebuild the PDF from the existing screenshots

Writes docs/images/*.png and src/quantumscope/assets/QuantumScope-User-Guide.pdf from
docs/user-guide.md. On a normal desktop the Hydrogen screenshot includes the live 3-D view; with
QT_QPA_PLATFORM=offscreen (no display) it shows the Explorer's controls and chart instead, since
software 3-D rendering is unreliable there.
"""
import os
import re
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'src'))
DOCS = os.path.join(ROOT, 'docs')
IMAGES = os.path.join(DOCS, 'images')
PDF = os.path.join(ROOT, 'src', 'quantumscope', 'assets', 'QuantumScope-User-Guide.pdf')
OFFSCREEN = os.environ.get('QT_QPA_PLATFORM') == 'offscreen'


def settle(app, seconds=0.0):
    end = time.time() + seconds
    while True:
        app.processEvents()
        if time.time() >= end:
            break
        time.sleep(0.01)


def save(widget, name, crop=None, scale=1.0):
    from PySide6.QtCore import Qt
    image = widget.grab().toImage()
    if crop is not None:
        image = image.copy(*crop)
    if scale != 1.0:
        image = image.scaledToWidth(int(image.width() * scale), Qt.TransformationMode.SmoothTransformation)
    os.makedirs(IMAGES, exist_ok=True)
    image.save(os.path.join(IMAGES, name))
    print('  ', name, image.width(), 'x', image.height())


def screenshots():
    import pyvista as pv
    from PySide6.QtWidgets import QApplication, QWidget
    os.environ.setdefault('QUANTUMSCOPE_SETTINGS_FILE', os.path.join(DOCS, '.guide-settings.ini'))
    os.environ.setdefault('QUANTUMSCOPE_DATA_DIR', os.path.join(DOCS, '.guide-data'))
    app = QApplication.instance() or QApplication([])
    app.setStyle('Fusion')
    import quantumscope.gui.main_window as M
    if OFFSCREEN:                                    # no display: a stand-in for the 3-D widget
        pv.OFF_SCREEN = True

        class Interactor(QWidget):
            def __init__(self, parent=None, *a, **k):
                super().__init__(parent)
                self.__dict__['_p'] = pv.Plotter(off_screen=True, window_size=(300, 300))

            def __getattr__(self, name):
                return getattr(self.__dict__['_p'], name)

            def render(self, *a, **k):
                return self.__dict__['_p'].render()
        M.QtInteractor = Interactor
    from quantumscope.gui.theme import apply_theme
    apply_theme('dark')
    w = M.MainWindow()
    w.resize(1480, 920)
    w.show()
    settle(app, 0.5)

    # Main window and Hydrogen
    w.n.setValue(3)
    w.l.setCurrentIndex(w.l.findText('2'))
    settle(app, 0.5)
    w.refresh()
    settle(app, 1.0)
    if OFFSCREEN:
        panel = w.n.parentWidget().parentWidget()
        while panel.parentWidget() is not None and panel.width() < 300:
            panel = panel.parentWidget()
        x = panel.mapTo(w, panel.rect().topLeft()).x()
        save(w, 'hydrogen-controls.png', crop=(0, 0, x + panel.width() + 6, w.height()), scale=0.8)
    else:
        save(w, 'hydrogen-controls.png', scale=0.75)

    # The window tour: the Quantum Principles area with Double-Slit (it renders everywhere)
    w._launch_double_slit()
    double = w._open_experiments['double_slit']
    double.wavelength.setValue(650)
    double.speed.setCurrentIndex(2)
    double.batch.setValue(6000)
    double.add.click()
    settle(app, 0.6)
    save(w, 'main-window.png', scale=0.75)

    # Quantum Principles
    from quantumscope.gui.quantum_principles import SuperpositionDialog
    from quantumscope.gui.double_slit_dialog import DoubleSlitDialog
    from quantumscope.gui.entanglement_experiment import EntanglementDialog
    from quantumscope.gui.teleportation_experiment import TeleportationDialog
    d = SuperpositionDialog()
    d.resize(1300, 760)
    d.show()
    d._preset(60, 30)
    d.axis.setValue(30)
    d.speed.setCurrentIndex(2)
    d.sample.click()
    settle(app, 0.8)
    save(d, 'superposition.png', scale=0.75)
    d = DoubleSlitDialog()
    d.resize(1300, 800)
    d.show()
    d.wavelength.setValue(532)
    d.speed.setCurrentIndex(2)
    d.batch.setValue(8000)
    d.add.click()
    settle(app, 0.5)
    save(d, 'double-slit.png', scale=0.75)
    d = EntanglementDialog()
    d.resize(1400, 860)
    d.show()
    d.speed.setCurrentIndex(2)
    d.count.setValue(2000)
    d.run_bell_test()
    d.bob_axis[1].setValue(30)
    d.send_many()
    settle(app, 0.5)
    save(d, 'entanglement.png', scale=0.7)
    d = TeleportationDialog()
    d.resize(1400, 880)
    d.show()
    d.result.setCurrentIndex(d.result.findData('11'))
    for step in range(1, 5):
        d.go(step, animate=False)
    settle(app, 0.5)
    save(d, 'teleportation.png', scale=0.7)

    # Quantum Circuits
    c = w.circuit_widget
    w._launch_circuits()
    c.load_library('teleportation', {'input': '+'})
    c.verify_circuit()
    settle(app, 0.5)
    save(c, 'circuit-tab.png', scale=0.72)
    c.load_library('qaoa', {'graph': 'ring6', 'layers': 2})
    settle(app, 0.5)
    save(c.param_panel, 'parameters.png', scale=0.8)              # the panel itself (the page may be scrolled)
    c.example()                                         # the Bell pair (as Examples… → Bell pair)
    from quantumscope.gui.state_inspector import StateInspector
    try:
        inspector = StateInspector(c)
        inspector.resize(1000, 640)
        inspector.show()
        inspector.refresh()
        settle(app, 0.5)
        save(inspector, 'state-inspector.png', scale=0.8)
    except Exception as exc:                                     # noqa: BLE001
        print('   (state inspector skipped:', exc, ')')

    # Learn, Settings, About
    from PySide6.QtCore import QUrl
    from quantumscope.gui.learn_window import LearnWindow
    learn = LearnWindow()
    learn.resize(1250, 820)
    learn.move(0, 0)
    learn.show()
    learn.open_lesson('principles/08-observables')
    settle(app, 0.4)
    learn._link(QUrl('glossary:Hermitian'))
    settle(app, 0.3)
    from PySide6.QtGui import QPainter
    image = learn.grab().toImage()
    painter = QPainter(image)
    popup = learn._term_popup
    painter.drawImage(learn.mapFromGlobal(popup.pos()) if not OFFSCREEN else learn.reader.mapTo(learn, learn.reader.rect().center()),
                      popup.grab().toImage())
    painter.end()
    from PySide6.QtCore import Qt
    image.scaledToWidth(int(image.width() * 0.75), Qt.TransformationMode.SmoothTransformation).save(
        os.path.join(IMAGES, 'learn.png'))
    print('   learn.png')
    popup.hide()
    from quantumscope.gui.settings_dialog import SettingsDialog
    settings = SettingsDialog(w)
    settings.resize(820, 560)
    settings.show()
    settle(app, 0.3)
    save(settings, 'settings.png', scale=0.85)


def build_pdf():
    """docs/user-guide.md → PDF, laid out by Qt (no other dependencies)."""
    from PySide6.QtCore import QMarginsF, QSizeF, QUrl
    from PySide6.QtGui import QPageLayout, QPageSize, QTextDocument
    from PySide6.QtWidgets import QApplication
    from PySide6.QtPrintSupport import QPrinter
    QApplication.instance() or QApplication([])
    with open(os.path.join(DOCS, 'user-guide.md'), encoding='utf-8') as handle:
        markdown = handle.read()
    document = QTextDocument()
    font = document.defaultFont()
    font.setPointSizeF(10.5)
    document.setDefaultFont(font)
    document.setBaseUrl(QUrl.fromLocalFile(DOCS + os.sep))
    document.setMarkdown(markdown)
    html = document.toHtml()
    from PySide6.QtGui import QImage

    def fit(match):
        """Keep an image's own size, shrunk only to fit the page (at most 640 wide, 430 tall)."""
        src = match.group(1)
        image = QImage(os.path.join(DOCS, src))
        if image.isNull():
            return match.group(0)
        scale = min(1.0, 640 / image.width(), 430 / image.height())
        return f'<img src="{src}" width="{int(image.width() * scale)}" height="{int(image.height() * scale)}" />'
    html = re.sub(r'<img src="([^"]+)"[^>]*/?>', fit, html)
    document.setHtml(html)
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(PDF)
    printer.setPageLayout(QPageLayout(QPageSize(QPageSize.PageSizeId.Letter), QPageLayout.Orientation.Portrait,
                                      QMarginsF(18, 18, 18, 18), QPageLayout.Unit.Millimeter))
    printer.setDocName('QuantumScope User Guide')
    # Lay the text out across the whole printable width: in the document's own units (screen
    # pixels, 96 per inch here), the page is the printable area in inches times 96.
    area = printer.pageLayout().paintRect(QPageLayout.Unit.Inch)
    dpi = 96.0
    document.setPageSize(QSizeF(area.width() * dpi, area.height() * dpi))
    document.print_(printer)
    print('PDF:', PDF, os.path.getsize(PDF) // 1024, 'KB')


if __name__ == '__main__':
    if '--pdf-only' not in sys.argv:
        screenshots()
    build_pdf()
    os._exit(0)                                       # skip Qt/VTK teardown (see tests/conftest.py)
