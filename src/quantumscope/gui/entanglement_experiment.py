"""Entanglement, redesigned (v0.7.5): pairs fly to Alice and Bob, each qubit's own Bloch sphere,
live correlations, and a Bell-test (CHSH) meter. The physics is quantumscope.physics.bell."""
import math

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QSlider,
                               QSpinBox, QVBoxLayout, QWidget)

from quantumscope.gui.principles_visuals import BlochView, _dark, angles
from quantumscope.physics import bell as B

PLUS, MINUS = QColor(90, 230, 150), QColor(255, 150, 90)


class PairFlight(QWidget):
    """The source emits a pair; the particles fly to the two detectors, which light up ±1."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(70)
        self.flights = []                       # [progress 0..1, alice ±1, bob ±1]
        self.lights = [0, 0]                    # last results shown at the detectors
        self.glow = [0.0, 0.0]
        self.on_arrival = None
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)

    def launch(self, alice, bob, speed=0.06):
        self.flights.append([0.0, alice, bob, speed])
        self._timer.start()

    def busy(self):
        return bool(self.flights)

    def _tick(self):
        arrived = []
        for flight in self.flights:
            flight[0] += flight[3]
            if flight[0] >= 1:
                arrived.append(flight)
        for flight in arrived:
            self.flights.remove(flight)
            self.lights, self.glow = [flight[1], flight[2]], [1.0, 1.0]
            if self.on_arrival is not None:
                self.on_arrival(flight[1], flight[2])
        self.glow = [max(0.0, g - 0.03) for g in self.glow]
        if not self.flights and max(self.glow) <= 0:
            self._timer.stop()
        self.update()

    def paintEvent(self, event):
        dark = _dark()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cy = h / 2
        line = QColor(120, 170, 210) if dark else QColor(80, 110, 140)
        p.setPen(QPen(line, 1, Qt.PenStyle.DashLine))
        p.drawLine(QPointF(40, cy), QPointF(w - 40, cy))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 210, 110))
        p.drawEllipse(QPointF(w / 2, cy), 9, 9)                               # the source
        text = QColor(220, 235, 250) if dark else QColor(25, 50, 75)
        p.setPen(text)
        p.setFont(QFont('Sans', 8))
        p.drawText(QRectF(w / 2 - 60, cy + 10, 120, 16), Qt.AlignmentFlag.AlignCenter, 'pair source')
        for side, x in ((0, 22), (1, w - 22)):                               # detectors
            result = self.lights[side]
            colour = PLUS if result == 1 else MINUS if result == -1 else line
            glow = QColor(colour)
            glow.setAlpha(int(40 + 160 * self.glow[side]))
            p.setPen(QPen(colour, 2))
            p.setBrush(glow)
            p.drawRoundedRect(QRectF(x - 16, cy - 18, 32, 36), 6, 6)
            p.setPen(text)
            p.setFont(QFont('Sans', 10, QFont.Weight.Bold))
            p.drawText(QRectF(x - 16, cy - 18, 32, 36), Qt.AlignmentFlag.AlignCenter,
                       '+1' if result == 1 else '−1' if result == -1 else '·')
        p.setPen(Qt.PenStyle.NoPen)
        for progress, _, _, _ in self.flights:
            reach = progress * (w / 2 - 40)
            p.setBrush(QColor(90, 230, 255))
            p.drawEllipse(QPointF(w / 2 - reach, cy), 5, 5)
            p.drawEllipse(QPointF(w / 2 + reach, cy), 5, 5)
        p.end()


class CorrelationGrid(QWidget):
    """Joint results (Alice row, Bob column), shaded by frequency, with the predicted share."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 150)
        self.counts = np.zeros((2, 2), int)
        self.expected = np.full((2, 2), 0.25)

    def paintEvent(self, event):
        dark = _dark()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        text = QColor(220, 235, 250) if dark else QColor(25, 50, 75)
        total = int(self.counts.sum())
        left, top = 64, 26
        cell = min((self.width() - left - 8) / 2, (self.height() - top - 8) / 2)
        p.setPen(text)
        p.setFont(QFont('Sans', 9))
        p.drawText(QRectF(left, 2, 2 * cell, 20), Qt.AlignmentFlag.AlignCenter, 'Bob')
        p.save()
        p.translate(12, top + cell)
        p.rotate(-90)
        p.drawText(QRectF(-cell, -10, 2 * cell, 20), Qt.AlignmentFlag.AlignCenter, 'Alice')
        p.restore()
        for j, label in enumerate(('+1', '−1')):
            p.drawText(QRectF(left + j * cell, top - 14, cell, 14), Qt.AlignmentFlag.AlignCenter, label)
            p.drawText(QRectF(28, top + j * cell, 32, cell), Qt.AlignmentFlag.AlignCenter, label)
        for i in range(2):
            for j in range(2):
                share = self.counts[i, j] / total if total else 0.0
                same = (i == j)
                base = PLUS if same else MINUS
                fill = QColor(base)
                fill.setAlpha(int(25 + 200 * share * 2 if share < 0.5 else 225))
                rect = QRectF(left + j * cell + 2, top + i * cell + 2, cell - 4, cell - 4)
                p.setPen(QPen(base, 1.2))
                p.setBrush(fill)
                p.drawRoundedRect(rect, 6, 6)
                p.setPen(text)
                p.setFont(QFont('Sans', 11, QFont.Weight.Bold))
                p.drawText(rect.adjusted(0, 0, 0, -cell * 0.3), Qt.AlignmentFlag.AlignCenter,
                           f'{self.counts[i, j]}' + (f'\n{share:.0%}' if total else ''))
                p.setFont(QFont('Sans', 8))
                p.drawText(rect.adjusted(0, cell * 0.55, 0, 0), Qt.AlignmentFlag.AlignCenter,
                           f'predicted {self.expected[i, j]:.0%}')
        p.end()


class ChshMeter(QWidget):
    """|S| on a gauge from 0 to 2√2, with the classical limit 2 marked."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(260, 150)
        self.value = None
        self.error = 0.0
        self.progress = ''

    def set_value(self, value, error=0.0, progress=''):
        self.value, self.error, self.progress = value, error, progress
        self.update()

    def paintEvent(self, event):
        dark = _dark()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        text = QColor(220, 235, 250) if dark else QColor(25, 50, 75)
        w, h = self.width(), self.height()
        cx, cy, r = w / 2, h - 40, max(30.0, min(w / 2 - 46, h - 70))      # room for the end labels
        top = B.QUANTUM_LIMIT
        rect = QRectF(cx - r, cy - r, 2 * r, 2 * r)

        def at(value, radius):
            a = math.pi * (1 - value / top)
            return QPointF(cx + radius * math.cos(a), cy - radius * math.sin(a))
        p.setPen(QPen(QColor(120, 160, 200, 120), 14, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
        p.drawArc(rect, 0, 180 * 16)                                         # the scale
        classical = B.CLASSICAL_LIMIT / top
        p.setPen(QPen(QColor(255, 120, 90, 170), 14, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
        p.drawArc(rect, 0, int(180 * 16 * (1 - classical)))                  # beyond classical
        p.setPen(QPen(QColor(255, 186, 80), 3))
        p.drawLine(at(B.CLASSICAL_LIMIT, r - 14), at(B.CLASSICAL_LIMIT, r + 12))
        p.setPen(text)
        p.setFont(QFont('Sans', 8, QFont.Weight.Bold))
        for value, label, radius in ((0, '0', r + 18), (B.CLASSICAL_LIMIT, '2 = classical limit', r + 24),
                                     (top, '2√2', r + 22)):
            point = at(value, radius)
            p.drawText(QRectF(point.x() - 55, point.y() - 9, 110, 18), Qt.AlignmentFlag.AlignCenter, label)
        if self.value is not None:
            needle = max(0.0, min(top, abs(self.value)))
            p.setPen(QPen(QColor(90, 230, 255), 3.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(cx, cy), at(needle, r - 6))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(90, 230, 255))
            p.drawEllipse(QPointF(cx, cy), 6, 6)
        p.setPen(text)
        p.setFont(QFont('Sans', 12, QFont.Weight.Bold))
        label = 'Bell test: not run yet' if self.value is None else f'|S| = {abs(self.value):.3f} ± {self.error:.3f}'
        p.drawText(QRectF(0, h - 26, w, 22), Qt.AlignmentFlag.AlignCenter, label)
        if self.progress:
            p.setFont(QFont('Sans', 8))
            p.drawText(QRectF(0, 0, w, 16), Qt.AlignmentFlag.AlignCenter, self.progress)
        p.end()


class EntanglementDialog(QWidget):
    """Send entangled pairs to Alice and Bob, see each qubit's own state, and test Bell's inequality."""

    SPEEDS = (('Slow', 1, 700), ('Fast', 20, 40), ('Instant', 0, 0))

    def __init__(self, parent=None):
        super().__init__(parent)
        import pyqtgraph as pg
        root = QHBoxLayout(self)
        left = QWidget()
        left.setMaximumWidth(370)
        form = QVBoxLayout(left)
        title = QLabel('QUANTUM ENTANGLEMENT')
        title.setStyleSheet('font-weight:700; letter-spacing:1px;')
        form.addWidget(title)
        hint = QLabel('A source sends pairs to Alice and Bob. Drag the amber axis on each sphere to aim a '
                      'detector (right-drag turns a sphere), then send pairs or run the Bell test.')
        hint.setWordWrap(True)
        hint.setObjectName('muted')
        form.addWidget(hint)
        pair = QGroupBox('The pair')
        pv = QFormLayout(pair)
        self.state = QComboBox()
        for key, (label, _) in B.STATES.items():
            self.state.addItem(label, key)
        pv.addRow('State', self.state)
        self.visibility = QSlider(Qt.Orientation.Horizontal)
        self.visibility.setRange(0, 100)
        self.visibility.setValue(100)
        self.visibility_label = QLabel('100%')
        row = QHBoxLayout()
        row.addWidget(self.visibility, 1)
        row.addWidget(self.visibility_label)
        pv.addRow('Clean pairs', row)
        form.addWidget(pair)
        aim = QGroupBox('Detectors')
        av = QFormLayout(aim)
        self.alice_axis, self.bob_axis = self._axis_slider(0), self._axis_slider(45)
        av.addRow('Alice axis', self.alice_axis[0])
        av.addRow('Bob axis', self.bob_axis[0])
        form.addWidget(aim)
        send = QGroupBox('Measure')
        sv = QFormLayout(send)
        self.one = QPushButton('Send one pair')
        self.one.setToolTip('One pair, step by step: Alice measures, then Bob')
        sv.addRow(self.one)
        many = QHBoxLayout()
        self.count = QSpinBox()
        self.count.setRange(10, 20000)
        self.count.setValue(500)
        many.addWidget(self.count)
        self.speed = QComboBox()
        for label, _, _ in self.SPEEDS:
            self.speed.addItem(label)
        self.speed.setCurrentIndex(1)
        many.addWidget(self.speed)
        sv.addRow('Many', many)
        buttons = QHBoxLayout()
        self.many = QPushButton('Send many')
        self.stop = QPushButton('Stop')
        self.stop.setEnabled(False)
        buttons.addWidget(self.many)
        buttons.addWidget(self.stop)
        sv.addRow(buttons)
        self.bell = QPushButton('Run Bell test')
        self.bell.setToolTip('Measure many pairs at the four standard axis settings and compute S')
        sv.addRow(self.bell)
        self.clear_button = QPushButton('Clear results')
        sv.addRow(self.clear_button)
        form.addWidget(send)
        self.explain = QLabel('')
        self.explain.setWordWrap(True)
        form.addWidget(self.explain)
        form.addStretch()
        root.addWidget(left)
        right = QVBoxLayout()
        spheres = QHBoxLayout()
        self.alice, self.bob = BlochView(), BlochView()
        for view, name in ((self.alice, 'Alice'), (self.bob, 'Bob')):
            view.drag_mode, view.caption = 'axis', name
            view.setMinimumSize(260, 260)
        spheres.addWidget(self.alice, 1)
        spheres.addWidget(self.bob, 1)
        right.addLayout(spheres, 3)
        self.flight = PairFlight()
        self.flight.on_arrival = self._arrived
        right.addWidget(self.flight)
        bottom = QHBoxLayout()
        self.grid = CorrelationGrid()
        bottom.addWidget(self.grid, 1)
        self.curve = pg.PlotWidget()
        self.curve.setMinimumHeight(170)
        self.curve.setLabel('bottom', "Bob's axis (°), Alice's fixed")
        self.curve.setLabel('left', 'Correlation E')
        self.curve.setYRange(-1.05, 1.05)
        self.curve.setXRange(-180, 180)
        self.curve.showGrid(x=True, y=True, alpha=0.2)
        self.curve.addLegend(offset=(8, 4))
        self.quantum_line = self.curve.plot(pen=pg.mkPen('#5ae6ff', width=2.5), name='quantum')
        self.classical_line = self.curve.plot(pen=pg.mkPen('#ffba50', width=2, style=Qt.PenStyle.DashLine),
                                              name='simple classical model')
        self.measured = self.curve.plot(pen=None, symbol='o', symbolSize=8, symbolBrush='#ffffff', name='measured')
        self.marker = pg.InfiniteLine(angle=90, pen=pg.mkPen('#9fb4cb', width=1))
        self.curve.addItem(self.marker)
        bottom.addWidget(self.curve, 2)
        self.meter = ChshMeter()
        bottom.addWidget(self.meter, 1)
        right.addLayout(bottom, 2)
        root.addLayout(right, 1)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._stream)
        self._bob_timer = QTimer(self)
        self._bob_timer.setSingleShot(True)
        self._bob_timer.timeout.connect(lambda: self._bob_measures(*self._bob_next))
        self._pending, self._bell = 0, None
        self.points = {}                    # (alice axis, bob axis) -> [sum of A·B, pairs]
        self.state.currentIndexChanged.connect(self._new_pair)
        self.visibility.valueChanged.connect(self._new_pair)
        self.alice.axisChanged.connect(lambda a: self._set_axis(self.alice_axis, a))
        self.bob.axisChanged.connect(lambda a: self._set_axis(self.bob_axis, a))
        self.one.clicked.connect(self.send_one)
        self.many.clicked.connect(self.send_many)
        self.stop.clicked.connect(self._stop)
        self.bell.clicked.connect(self.run_bell_test)
        self.clear_button.clicked.connect(self.clear_results)
        self._new_pair()

    # ---- controls ---------------------------------------------------------------------------------
    def _axis_slider(self, value):
        box = QWidget()
        h = QHBoxLayout(box)
        h.setContentsMargins(0, 0, 0, 0)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(-180, 180)
        slider.setValue(value)
        label = QLabel(f'{value}°')
        label.setMinimumWidth(44)
        h.addWidget(slider, 1)
        h.addWidget(label)
        slider.valueChanged.connect(lambda v, l=label: (l.setText(f'{v}°'), self._axes_changed()))
        return box, slider

    def _set_axis(self, control, angle):
        control[1].setValue(int(round(angle)))

    @property
    def a(self):
        return float(self.alice_axis[1].value())

    @property
    def b(self):
        return float(self.bob_axis[1].value())

    def rho(self):
        return B.density(self.state.currentData(), self.visibility.value() / 100)

    # ---- display -----------------------------------------------------------------------------------
    def _show_own_states(self):
        """Each sphere shows its qubit's own (reduced) state: for an entangled pair, completely random."""
        for view, qubit in ((self.alice, 0), (self.bob, 1)):
            vector = B.bloch(self.rho(), qubit)
            length = float(np.linalg.norm(vector))
            theta, phi = angles(vector) if length > 1e-9 else (0.0, 0.0)
            view.set_state(theta, phi, length=length)

    def _axes_changed(self):
        self.alice.axis, self.bob.axis = self.a, self.b
        self.alice.update()
        self.bob.update()
        self._stop()
        self.grid.counts[:] = 0
        self.grid.expected = B.joint(self.rho(), self.a, self.b)
        self.grid.update()
        self._show_own_states()
        self._draw_curve()

    def _new_pair(self, *_):
        self.visibility_label.setText(f'{self.visibility.value()}%')
        self.points.clear()
        self.meter.set_value(None)
        self._axes_changed()
        name = self.state.currentData()
        self.explain.setText('Classically correlated: each pair is |00⟩ or |11⟩. The results agree along z, '
                             'but this pair can never beat the classical limit.' if name == 'classical' else
                             'Entangled: each qubit on its own is completely random (the empty spheres), '
                             'yet the two results are correlated.')

    def _draw_curve(self):
        bs = np.arange(-180, 181, 3)
        rho, name = self.rho(), self.state.currentData()
        self.quantum_line.setData(bs, [B.correlation(rho, self.a, b) for b in bs])
        model = [B.classical_model(name, self.a, b) for b in bs]
        visibility = self.visibility.value() / 100
        self.classical_line.setData(bs, [m * visibility for m in model] if model[0] is not None else [])
        xs = [b for (a, b), (_, n) in self.points.items() if a == self.a and n]
        self.measured.setData(xs, [self.points[(self.a, b)][0] / self.points[(self.a, b)][1] for b in xs])
        self.marker.setValue(self.b)

    def _record(self, alice, bob, a=None, b=None):
        a, b = self.a if a is None else a, self.b if b is None else b
        alice, bob = np.atleast_1d(alice), np.atleast_1d(bob)
        if a == self.a and b == self.b:
            for i, s in enumerate((1, -1)):
                for j, t in enumerate((1, -1)):
                    self.grid.counts[i, j] += int(np.count_nonzero((alice == s) & (bob == t)))
            self.grid.update()
        entry = self.points.setdefault((a, b), [0.0, 0])
        entry[0] += float(np.sum(alice * bob))
        entry[1] += alice.size
        self._draw_curve()

    # ---- one pair, step by step ---------------------------------------------------------------------
    def send_one(self):
        """One pair: it flies out; Alice measures (both spheres jump), then Bob measures."""
        self._stop()
        self._show_own_states()
        alice, bob = B.sample(self.rho(), self.a, self.b, 1)
        self._one = (int(alice[0]), int(bob[0]))
        self.flight.launch(*self._one)
        self.explain.setText('A pair is on its way…')

    def _arrived(self, alice, bob):
        if getattr(self, '_one', None) != (alice, bob) or self._timer.isActive():
            return
        self._one = None
        a_theta = self.a if alice == 1 else self.a + 180
        self.alice.set_state(*_axis_state(a_theta), animate=True, flash=True)
        _, bob_vector = B.after_alice(self.rho(), self.a, alice)
        length = float(np.linalg.norm(bob_vector))
        theta, phi = angles(bob_vector) if length > 1e-9 else (0.0, 0.0)
        self.bob.set_state(theta, phi, animate=True, flash=True, length=length)
        self.explain.setText(f'Alice measured {alice:+d}. Bob\'s qubit is now definite as well (his sphere), '
                             'but Bob cannot tell: on his own his results stay 50/50 until they compare notes. '
                             'No signal travels.')
        self._bob_next = (alice, bob)
        self._bob_timer.start(900)        # owned by the dialog: never fires into a deleted dialog

    def _bob_measures(self, alice, bob):
        self.bob.set_state(*_axis_state(self.b if bob == 1 else self.b + 180), animate=True, flash=True)
        self._record(alice, bob)
        same = 'the same' if alice == bob else 'opposite'
        self.explain.setText(f'Alice {alice:+d}, Bob {bob:+d}: {same} results. One pair proves nothing; '
                             'send many to see the correlation.')

    # ---- many pairs ------------------------------------------------------------------------------------
    def send_many(self):
        self._stop()
        self._show_own_states()
        self._bell = None
        self._pending = self.count.value()
        self._run()

    def run_bell_test(self):
        """The four CHSH settings, each with `count` pairs; the meter fills as they come in."""
        self._stop()
        angles4 = B.chsh_angles(self.state.currentData() if self.state.currentData() != 'classical' else 'phi+')
        a, a2, b, b2 = angles4
        self._bell = {'settings': [(a, b), (a, b2), (a2, b), (a2, b2)], 'index': 0, 'sums': [0.0] * 4,
                      'n': [0] * 4}
        self._start_setting()

    def _start_setting(self):
        a, b = self._bell['settings'][self._bell['index']]
        for control, value in ((self.alice_axis, a), (self.bob_axis, b)):
            control[1].blockSignals(True)
            control[1].setValue(int(value))
            control[1].blockSignals(False)
            control[0].findChild(QLabel).setText(f'{int(value)}°')
        self.alice.axis, self.bob.axis = a, b
        self.alice.update()
        self.bob.update()
        self.grid.counts[:] = 0
        self.grid.expected = B.joint(self.rho(), a, b)
        self.grid.update()
        self._pending = self.count.value()
        self._run()

    def _run(self):
        _, per_tick, interval = self.SPEEDS[self.speed.currentIndex()]
        if per_tick == 0:
            while self._pending > 0:
                self._stream(everything=True)
            return
        self.stop.setEnabled(True)
        self._timer.start(interval)

    def _stream(self, everything=False):
        _, per_tick, _ = self.SPEEDS[self.speed.currentIndex()]
        n = self._pending if everything or per_tick == 0 else min(per_tick, self._pending)
        if n <= 0:
            self._stop()
            return
        alice, bob = B.sample(self.rho(), self.a, self.b, n)
        if not everything:
            self.flight.launch(int(alice[-1]), int(bob[-1]), speed=0.12)
        self._record(alice, bob)
        self._pending -= n
        if self._bell is not None:
            k = self._bell['index']
            self._bell['sums'][k] += float(np.sum(alice * bob))
            self._bell['n'][k] += n
            self._update_meter()
        if self._pending <= 0:
            if self._bell is not None and self._bell['index'] < 3:
                self._bell['index'] += 1
                self._timer.stop()
                self._start_setting()
                return
            self._stop()
            self._finish()

    def _update_meter(self):
        bell = self._bell
        es = [s / n if n else 0.0 for s, n in zip(bell['sums'], bell['n'])]
        s = es[0] + es[1] + es[2] - es[3]
        error = math.sqrt(sum((1 - e * e) / n for e, n in zip(es, bell['n']) if n)) if any(bell['n']) else 0.0
        done = sum(1 for n in bell['n'] if n >= self.count.value())
        self.meter.set_value(s, error, f'setting {min(done + 1, 4)} of 4' if done < 4 else 'all four settings measured')

    def _finish(self):
        if self._bell is None:
            n = int(self.grid.counts.sum())
            e = (self.grid.counts[0, 0] + self.grid.counts[1, 1] - self.grid.counts[0, 1] - self.grid.counts[1, 0]) / n
            self.explain.setText(f'{n} pairs at these axes: correlation E = {e:+.3f} '
                                 f'(quantum prediction {B.correlation(self.rho(), self.a, self.b):+.3f}).')
            return
        value, error = abs(self.meter.value), self.meter.error
        if value - 2 * error > B.CLASSICAL_LIMIT:
            verdict = 'beats the classical limit of 2: no local hidden-variable model can explain these results.'
        elif value + 2 * error < B.CLASSICAL_LIMIT:
            verdict = 'stays below the classical limit of 2: these correlations have a classical explanation.'
        else:
            verdict = 'is too close to 2 to decide: send more pairs per setting.'
        self.explain.setText(f'Bell test: |S| = {value:.3f} ± {error:.3f}, which {verdict} '
                             f'(The quantum maximum is 2√2 ≈ 2.828.)')
        self._bell = None

    def _stop(self):
        if self._timer.isActive():
            self._timer.stop()
        self.stop.setEnabled(False)

    def clear_results(self):
        self._stop()
        self.points.clear()
        self.meter.set_value(None)
        self._axes_changed()


def _axis_state(angle):
    """(θ, φ) of the direction at `angle` degrees in the x–z plane."""
    a = math.radians(angle)
    return angles(np.array([math.sin(a), 0.0, math.cos(a)]))
