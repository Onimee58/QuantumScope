"""Animated, explicitly schematic view of the double-slit apparatus.

Geometry is drawn for explanation, not to scale. Curved wavefronts indicate
coherent phase fronts, not measured particle trajectories or a wave solver.
"""
import math

import numpy as np
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


class DoubleSlitApparatus(QWidget):
    """Responsive source -> slit barrier -> screen diagram with sample hits."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(390, 220)
        self.setToolTip('Illustrative wavefronts only; probability and detections come from the Fraunhofer model.')
        self._phase = 0.0
        self._samples = np.empty(0)
        self._screen_halfwidth_mm = 40.0
        self._separation_um = 100.0
        self._width_um = 20.0
        self._animated = True
        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def set_experiment(self, model, samples):
        self._screen_halfwidth_mm = model.screen_halfwidth_mm
        self._separation_um = model.slit_separation_um
        self._width_um = model.slit_width_um
        self._samples = np.asarray(samples, dtype=float).copy()
        self.update()

    def set_animated(self, enabled):
        self._animated = bool(enabled)
        if enabled and self.isVisible():
            self._timer.start()
        else:
            self._timer.stop()
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        if self._animated:
            self._timer.start()

    def hideEvent(self, event):
        self._timer.stop()
        super().hideEvent(event)

    def _tick(self):
        self._phase = (self._phase + 0.024) % 1.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor('#101923'))
        w, h = self.width(), self.height()
        # Scene coordinates in a consistent 700x300 rectangle.
        painter.translate(0, 0)
        painter.scale(w / 700.0, h / 300.0)
        painter.setPen(QPen(QColor('#34495e'), 1))
        painter.drawRoundedRect(QRectF(5, 5, 690, 290), 9, 9)
        sx, barrier, detector, cy = 70.0, 315.0, 640.0, 152.0
        painter.setPen(QPen(QColor('#638398'), 1, Qt.PenStyle.DashLine))
        painter.drawLine(QPointF(48, cy), QPointF(663, cy))
        # A stylized upstream plane wave, converging on the two apertures.
        for n in range(10):
            x = sx + ((n * 32 + self._phase * 32) % (barrier - sx - 15))
            painter.setPen(QPen(QColor(73, 170, 220, 60 + int(80 * (x - sx) / (barrier - sx))), 1.7))
            painter.drawLine(QPointF(x, 54), QPointF(x, 249))
        painter.setPen(QPen(QColor('#d7e8f0'), 2))
        painter.setBrush(QColor('#54b8e7'))
        painter.drawEllipse(QPointF(sx, cy), 10, 10)
        # Physical gap sizes are exaggerated to remain visible. They still track
        # the slit-width / separation ratio within safe visual bounds.
        gap = max(6., min(16., 12. * self._width_um / 20.))
        spacing = max(24., min(95., 44. * self._separation_um / 100.))
        slit_ys = (cy - spacing / 2., cy + spacing / 2.)
        boundaries = [30., slit_ys[0] - gap / 2., slit_ys[0] + gap / 2.,
                      slit_ys[1] - gap / 2., slit_ys[1] + gap / 2., 275.]
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor('#b8c9d3'))
        for a, b in ((0, 1), (2, 3), (4, 5)):
            painter.drawRoundedRect(QRectF(barrier - 5, boundaries[a], 10,
                                            boundaries[b] - boundaries[a]), 2, 2)
        # Two sets of expanding circular phase fronts from the apertures.
        # Clip the rings to the right side of the barrier and within the frame.
        painter.save()
        painter.setClipRect(QRectF(barrier + 7, 29, detector - barrier - 17, 246))
        for slit_y in slit_ys:
            for k in range(11):
                radius = 18 + (k + self._phase) * 35
                opacity = max(35, int(155 * (1 - radius / 550)))
                painter.setPen(QPen(QColor(74, 180, 238, opacity), 1.7))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(QPointF(barrier, slit_y), radius, radius)
        painter.restore()
        # Detector with actual sampled screen positions; no trajectories.
        painter.setPen(QPen(QColor('#f1c36a'), 6))
        painter.drawLine(QPointF(detector, 32), QPointF(detector, 272))
        if self._samples.size:
            # Bound visual complexity, retaining a representative range of hits.
            indices = np.linspace(0, self._samples.size - 1,
                                  min(350, self._samples.size), dtype=int)
            values = self._samples[indices]
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 201, 101, 185))
            for idx, value in enumerate(values):
                y = cy - (float(value) / self._screen_halfwidth_mm) * 113
                # Horizontal spread only distinguishes overlapping hits visually.
                x = detector - 3 - (idx % 5) * 3
                painter.drawEllipse(QPointF(x, y), 1.9, 1.9)
        painter.setPen(QColor('#e2edf3'))
        painter.setFont(QFont('Sans Serif', 10))
        painter.drawText(QRectF(27, 8, 105, 22), Qt.AlignmentFlag.AlignCenter, 'Source')
        painter.drawText(QRectF(252, 8, 130, 22), Qt.AlignmentFlag.AlignCenter, 'Double slit')
        painter.drawText(QRectF(585, 8, 105, 22), Qt.AlignmentFlag.AlignCenter, 'Detector')
        painter.setPen(QColor('#91a8b5'))
        painter.setFont(QFont('Sans Serif', 9))
        painter.drawText(QRectF(25, 274, 650, 20), Qt.AlignmentFlag.AlignCenter,
                         'Schematic, not to scale  |  Rings = illustrative phase fronts; dots = sampled detections')
        painter.end()
