"""Optimizer views: live convergence and energy landscapes (both use editor/variational.py)."""
import math

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
                               QWidget)

from quantumscope.editor import variational as V
from quantumscope.gui.theme import canvas_color

METHODS = (('BFGS (parameter-shift gradients)', 'BFGS'), ('Gradient descent (parameter shift)', 'gradient'),
           ('COBYLA (no gradients)', 'COBYLA'), ('Nelder–Mead (no gradients)', 'Nelder-Mead'))


class ConvergenceChart(QWidget):
    """⟨H⟩ against iteration, with the exact minimum as a dashed line."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(560, 300)
        self.energies, self.exact = [], None

    def set_data(self, energies, exact=None):
        self.energies, self.exact = list(energies), exact
        self.update()

    def paintEvent(self, event):
        if not self.energies:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        left, top, right, bottom = 70, 16, self.width() - 16, self.height() - 40
        values = self.energies + ([self.exact] if self.exact is not None else [])
        lo, hi = min(values), max(values)
        # Never zoom into rounding noise: show at least 1% of the energy scale (or 0.01).
        least = max(0.01, 0.01 * max(abs(lo), abs(hi)))
        if hi - lo < least:
            middle = (hi + lo) / 2
            lo, hi = middle - least / 2, middle + least / 2
        pad = 0.06 * (hi - lo)
        lo, hi = lo - pad, hi + pad
        digits = min(8, max(3, 2 - int(math.floor(math.log10(hi - lo)))))   # enough decimals to tell ticks apart
        count = max(1, len(self.energies) - 1)
        x = lambda i: left + (right - left) * i / count
        y = lambda e: bottom - (bottom - top) * (e - lo) / (hi - lo)
        text = canvas_color('chart_text')
        p.setPen(QPen(canvas_color('bloch_axis'), 1))
        p.drawLine(QPointF(left, bottom), QPointF(right, bottom))
        p.drawLine(QPointF(left, top), QPointF(left, bottom))
        p.setPen(text)
        p.setFont(QFont('Sans', 8))
        for k in range(5):
            e = lo + (hi - lo) * k / 4
            p.drawText(QRectF(2, y(e) - 7, left - 8, 14), Qt.AlignmentFlag.AlignRight, f'{e:.{digits}f}')
        p.drawText(QRectF(left, bottom + 6, right - left, 14), Qt.AlignmentFlag.AlignCenter,
                   'no steps taken' if len(self.energies) == 1 else f'step (0 … {len(self.energies) - 1})')
        if self.exact is not None:
            p.setPen(QPen(canvas_color('chart_sampled'), 1.6, Qt.PenStyle.DashLine))
            p.drawLine(QPointF(left, y(self.exact)), QPointF(right, y(self.exact)))
            p.setPen(text)
            p.drawText(QPointF(right - 190, y(self.exact) - 5), f'exact minimum {self.exact:.6f}')
        p.setPen(QPen(canvas_color('bloch_vector'), 2.4))
        if len(self.energies) == 1:                              # no step: a level line, not a lone dot
            level = y(self.energies[0])
            p.drawLine(QPointF(left, level), QPointF(right, level))
            p.setBrush(canvas_color('bloch_vector'))
            p.drawEllipse(QPointF(left, level), 4, 4)
            p.setPen(text)
            p.drawText(QRectF(left + 10, level - 22, right - left - 20, 16), Qt.AlignmentFlag.AlignLeft,
                       f'no step lowered ⟨H⟩ below {self.energies[0]:.6f}')
            p.end()
            return
        points = [QPointF(x(i), y(e)) for i, e in enumerate(self.energies)]
        for a, b in zip(points, points[1:]):
            p.drawLine(a, b)
        p.setBrush(canvas_color('bloch_vector'))
        p.drawEllipse(points[-1], 4, 4)
        p.end()


class OptimizeDialog(QDialog):
    """Runs the optimizer on the workspace's circuit with live progress; one undo step in total."""

    def __init__(self, workspace, method='BFGS', steps=200):
        super().__init__(workspace)
        self.setWindowTitle('Optimize parameters')
        self.workspace, self.method, self.steps = workspace, method, steps
        self.history, self.stopped = [], False
        layout = QVBoxLayout(self)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.summary.setMinimumHeight(3 * self.summary.fontMetrics().lineSpacing() + 4)   # wrapped text never clipped
        self.summary.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.summary)
        self.chart = ConvergenceChart()
        layout.addWidget(self.chart, 1)
        buttons = QHBoxLayout()
        self.stop_button = QPushButton('Stop')
        self.stop_button.clicked.connect(self._stop)
        self.close_button = QPushButton('Close')
        self.close_button.clicked.connect(self.accept)
        buttons.addStretch()
        buttons.addWidget(self.stop_button)
        buttons.addWidget(self.close_button)
        layout.addLayout(buttons)
        self.resize(720, 460)

    def _stop(self):
        self.stopped = True

    def run(self):
        model = self.workspace.model
        exact = V.Evaluator(model).exact_minimum()
        energies = []

        def progress(iteration, values, energy):
            if energies and iteration == len(energies) - 1:        # a heartbeat, not a new step
                QApplication.processEvents()
                return not self.stopped
            energies.append(energy)
            if len(energies) % 2 == 1 or iteration < 5:
                self.chart.set_data(energies, exact)
                self.summary.setText(f'Iteration {iteration}: ⟨H⟩ = {energy:.6f}' +
                                     (f'   (exact minimum {exact:.6f})' if exact is not None else ''))
                QApplication.processEvents()
            return not self.stopped
        self.history = V.optimize(model, self.method, self.steps, callback=progress)
        values, energy = self.history[-1]
        model.snapshot()                                      # the whole optimization is one undo step
        values = V.wrap_safely(model, values)                 # back into −π…π where that changes nothing
        for name, value in zip(list(model.parameters), values):
            model.parameters[name] = float(value)
        model._apply_bindings()
        self.workspace._changed()
        self.workspace._sync_parameter_values()
        self.chart.set_data([e for _, e in self.history], exact)
        gap = energy - exact if exact is not None else None
        start = self.history[0][1]
        steps = len(self.history) - 1
        evaluations = getattr(self.history, 'evaluations', 0)
        if exact is not None and start - exact < 1e-6:
            self.summary.setText(f'⟨H⟩ = {start:.6f} was already at the exact minimum: nothing to improve.')
        elif steps == 0 and not self.stopped:
            self.summary.setText(
                f'No step lowered ⟨H⟩ = {start:.6f} ({evaluations} circuit evaluations): these parameters are '
                f'already at a minimum of what this circuit can do. The exact minimum over all states is '
                f'{exact:.6f}' + ('; this circuit may not be able to reach it (its layers or its structure, such '
                                  'as a symmetry, limit which states it makes), or this is a local minimum: try '
                                  'other starting values.' if exact is not None else '.'))
        else:
            verdict = ('' if gap is None else
                       ' — the ground state is reached.' if gap < 1e-6 else
                       f' — {gap:.4g} above the exact minimum over all states. This may be the best this circuit '
                       'can reach (its layers or its structure, such as a symmetry, limit which states it makes), '
                       'or a local minimum: try another method or other starting values.')
            evaluations = getattr(self.history, 'evaluations', 0)
            self.summary.setText(f'{"Stopped" if self.stopped else "Finished"} after {steps} '
                                 f'step{"" if steps == 1 else "s"} ({evaluations} circuit evaluations): '
                                 f'⟨H⟩ went from {start:.6f} to {energy:.6f}'
                                 + (f' (exact minimum {exact:.6f})' if exact is not None else '') + verdict)
        self.stop_button.setEnabled(False)
        return self.history


def _colour(t):
    """Blue (low) → yellow (high) for t in [0, 1]."""
    stops = [(0, (40, 60, 160)), (0.5, (60, 190, 200)), (1, (250, 230, 90))]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if t <= b:
            f = (t - a) / (b - a)
            return QColor(*[round(x + (y - x) * f) for x, y in zip(ca, cb)])
    return QColor(*stops[-1][1])


class LandscapeView(QWidget):
    """A curve (one parameter) or a colour map (two), with the current point and optional path."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(560, 420)
        self.data, self.current, self.path, self.names = None, None, None, ('', '')

    def set_data(self, data, names, current, path=None):
        self.data, self.names, self.current, self.path = data, names, current, path
        self.update()

    def paintEvent(self, event):
        if self.data is None:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        left, top, right, bottom = 64, 16, self.width() - 100, self.height() - 44
        text = canvas_color('chart_text')
        span = math.pi
        sx = lambda v: left + (right - left) * (v + span) / (2 * span)
        p.setFont(QFont('Sans', 8))
        if len(self.data) == 2:                                   # a curve
            xs, energies = self.data
            lo, hi = float(energies.min()), float(energies.max())
            hi = hi if hi - lo > 1e-12 else lo + 1
            sy = lambda e: bottom - (bottom - top) * (e - lo) / (hi - lo)
            p.setPen(QPen(canvas_color('bloch_vector'), 2.2))
            pts = [QPointF(sx(a), sy(b)) for a, b in zip(xs, energies)]
            for a, b in zip(pts, pts[1:]):
                p.drawLine(a, b)
            if self.current is not None:
                p.setBrush(canvas_color('chart_sampled'))
                p.setPen(Qt.PenStyle.NoPen)
                e = float(np.interp(self.current[0], xs, energies))
                p.drawEllipse(QPointF(sx(self.current[0]), sy(e)), 5, 5)
            p.setPen(text)
            for k in range(5):
                e = lo + (hi - lo) * k / 4
                p.drawText(QRectF(2, sy(e) - 7, left - 8, 14), Qt.AlignmentFlag.AlignRight, f'{e:.3f}')
        else:                                                     # a colour map
            xs, ys, grid = self.data
            lo, hi = float(grid.min()), float(grid.max())
            image = QImage(len(xs), len(ys), QImage.Format.Format_RGB32)
            for i in range(len(ys)):
                for j in range(len(xs)):
                    image.setPixelColor(j, len(ys) - 1 - i, _colour((grid[i, j] - lo) / (hi - lo + 1e-12)))
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)        # smooth, same values
            p.drawImage(QRectF(left, top, right - left, bottom - top), image)
            sy = lambda v: bottom - (bottom - top) * (v + span) / (2 * span)
            if self.path is not None and len(self.path) > 1:
                p.setPen(QPen(QColor('white'), 1.6))
                pts = [QPointF(sx(a), sy(b)) for a, b in self.path]
                for a, b in zip(pts, pts[1:]):
                    p.drawLine(a, b)
            if self.current is not None:
                p.setPen(QPen(QColor('white'), 2))
                p.setBrush(QColor('#ff5a5a'))
                p.drawEllipse(QPointF(sx(self.current[0]), sy(self.current[1])), 5, 5)
            for k in range(40):                                   # colour scale, low at the bottom
                h = (bottom - top) / 40
                p.fillRect(QRectF(right + 12, bottom - (k + 1) * h, 14, h + 0.5), _colour((k + 0.5) / 40))
            p.setPen(text)
            p.drawText(QRectF(right + 30, top - 2, 66, 14), Qt.AlignmentFlag.AlignLeft, f'{hi:.3f}')
            p.drawText(QRectF(right + 30, bottom - 12, 66, 14), Qt.AlignmentFlag.AlignLeft, f'{lo:.3f}')
            p.drawText(QRectF(right + 30, (top + bottom) / 2 - 7, 66, 14), Qt.AlignmentFlag.AlignLeft, '⟨H⟩')
            for k, v in enumerate((-span, 0, span)):
                label = ('−π', '0', 'π')[k]
                p.drawText(QRectF(2, sy(v) - 7, left - 8, 14), Qt.AlignmentFlag.AlignRight, label)
            p.save()
            p.translate(14, (top + bottom) / 2)
            p.rotate(-90)
            p.drawText(QRectF(-60, -8, 120, 16), Qt.AlignmentFlag.AlignCenter, self.names[1])
            p.restore()
        p.setPen(text)
        for k, v in enumerate((-span, 0, span)):
            p.drawText(QRectF(sx(v) - 20, bottom + 4, 40, 14), Qt.AlignmentFlag.AlignCenter, ('−π', '0', 'π')[k])
        p.drawText(QRectF(left, bottom + 20, right - left, 16), Qt.AlignmentFlag.AlignCenter,
                   self.names[0] + ('   (⟨H⟩ along this parameter, others fixed)' if len(self.data) == 2 else ''))
        p.end()


class LandscapeDialog(QDialog):
    """⟨H⟩ over one or two chosen parameters, the others held at their current values."""

    def __init__(self, workspace, path=None):
        super().__init__(workspace)
        self.setWindowTitle('Energy landscape')
        self.workspace, self.path_history = workspace, path
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        names = list(workspace.model.parameters)
        self.first, self.second = QComboBox(), QComboBox()
        self.first.addItems(names)
        self.second.addItem('— (one parameter: a curve)', None)
        for n in names:
            self.second.addItem(n, n)
        if len(names) > 1:
            self.second.setCurrentIndex(2)
        row.addWidget(QLabel('Horizontal'))
        row.addWidget(self.first)
        row.addWidget(QLabel('Vertical'))
        row.addWidget(self.second)
        draw = QPushButton('Draw')
        draw.clicked.connect(self.draw)
        row.addWidget(draw)
        row.addStretch()
        layout.addLayout(row)
        self.view = LandscapeView()
        layout.addWidget(self.view, 1)
        self.note = QLabel('Blue is low ⟨H⟩, yellow is high. The red dot is the current parameters; the white '
                           'line is the last optimization path. Other parameters are held at their current values, '
                           'so with more than two parameters the path is a projection.')
        self.note.setWordWrap(True)
        layout.addWidget(self.note)
        self.resize(720, 600)

    def draw(self):
        model = self.workspace.model
        a, b = self.first.currentText(), self.second.currentData()
        if b == a:
            b = None
        from PySide6.QtGui import QGuiApplication
        QGuiApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            data = V.landscape(model, a, b, points=41 if b else 121)
        finally:
            QGuiApplication.restoreOverrideCursor()
        names = list(model.parameters)
        current = (model.parameters[a], model.parameters[b] if b else 0.0)
        path = None
        if b and self.path_history:
            ia, ib = names.index(a), names.index(b)
            wrap = lambda v: (v + math.pi) % (2 * math.pi) - math.pi
            path = [(wrap(v[ia]), wrap(v[ib])) for v, _ in self.path_history]
        self.view.set_data(data, (a, b or ''), current, path)
        return data
