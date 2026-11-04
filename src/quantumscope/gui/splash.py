"""The start-up splash: only the Q, on a transparent background, while QuantumScope loads."""
from importlib.resources import files

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QGuiApplication, QPainter
from PySide6.QtWidgets import QWidget

SIZE = 220


class Splash(QWidget):
    """A frameless, see-through window with the QuantumScope mark (no box behind it). Desktops
    without a compositor (rare) show the transparent part as a plain colour instead."""

    def __init__(self):
        super().__init__(None, Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint
                         | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(SIZE, SIZE)
        self.renderer = None
        try:
            from PySide6.QtSvg import QSvgRenderer
            self.renderer = QSvgRenderer(str(files('quantumscope').joinpath('assets/quantumscope-mark.svg')))
        except ImportError:                                   # no SVG module: the PNG icon instead
            pass
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            area = screen.availableGeometry()
            self.move(area.center().x() - SIZE // 2, area.center().y() - SIZE // 2)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        if self.renderer is not None and self.renderer.isValid():
            self.renderer.render(painter, QRectF(8, 8, SIZE - 16, SIZE - 16))
        else:
            from PySide6.QtGui import QPixmap
            painter.drawPixmap(self.rect().adjusted(8, 8, -8, -8),
                               QPixmap(str(files('quantumscope').joinpath('assets/quantumscope-256.png'))))
        painter.end()


def show_splash(app):
    """Show the splash at once (before the slow imports) and return it, or None if it cannot show."""
    try:
        splash = Splash()
        splash.show()
        for _ in range(3):                                    # paint it before anything slow starts
            app.processEvents()
        return splash
    except Exception:                                         # noqa: BLE001 - a splash must never stop start-up
        return None
