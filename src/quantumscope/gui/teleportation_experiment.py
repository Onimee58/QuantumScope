"""Quantum teleportation, redesigned (v0.7.6): the protocol step by step on three Bloch spheres, with
the circuit, the two classical bits travelling to Bob, a noisy pair, skipping the correction, and a
fidelity meter. The physics is quantumscope.physics.teleport_story (the circuit engine itself)."""
import math

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton,
                               QSlider, QSpinBox, QVBoxLayout, QWidget)

from quantumscope.gui.principles_visuals import BlochView, _dark, angles
from quantumscope.physics import teleport_story as story
from quantumscope.physics.initial_states import InitialState

PRESET_KEYS = ('0', '1', '+', '-', '+i', '-i')
# The circuit, step by step: (step, label, wires it touches, kind)
CIRCUIT = ((1, 'H', (1,), 'gate'), (1, '', (1, 2), 'cx'), (2, '', (0, 1), 'cx'), (2, 'H', (0,), 'gate'),
           (3, 'M', (0,), 'measure'), (3, 'M', (1,), 'measure'), (4, 'X', (2,), 'fix'), (4, 'Z', (2,), 'fix'))


class CircuitStrip(QWidget):
    """The teleportation circuit, with the current step's gates highlighted."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(118)
        self.step, self.correct = 0, True

    def paintEvent(self, event):
        dark = _dark()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        text = QColor(220, 235, 250) if dark else QColor(25, 50, 75)
        wire = QColor(110, 150, 190) if dark else QColor(90, 120, 150)
        w, h = self.width(), self.height()
        left, right = 150, w - 16
        ys = [22 + i * (h - 34) / 2 for i in range(3)]
        p.setFont(QFont('Sans', 9))
        for i, (y, name) in enumerate(zip(ys, ('q0 · Alice (to send)', 'q1 · Alice', 'q2 · Bob'))):
            p.setPen(text)
            p.drawText(QRectF(4, y - 9, left - 10, 18), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, name)
            p.setPen(QPen(wire, 1.4))
            p.drawLine(QPointF(left, y), QPointF(right, y))
        xs = [left + (right - left) * (k + 0.7) / (len(CIRCUIT) + 0.4) for k in range(len(CIRCUIT))]
        for x, (step, label, wires, kind) in zip(xs, CIRCUIT):
            skipped = kind == 'fix' and not self.correct
            done, now = step < self.step or (step == self.step), step == self.step
            colour = QColor(255, 200, 90) if now else (QColor(90, 230, 255) if done else wire)
            if skipped:
                colour = QColor(150, 150, 150)
            pen = QPen(colour, 2, Qt.PenStyle.DashLine if skipped else Qt.PenStyle.SolidLine)
            if kind == 'cx':
                control, target = wires
                p.setPen(pen)
                p.drawLine(QPointF(x, ys[control]), QPointF(x, ys[target]))
                p.setBrush(colour)
                p.drawEllipse(QPointF(x, ys[control]), 4, 4)
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(QPointF(x, ys[target]), 9, 9)
                p.drawLine(QPointF(x - 9, ys[target]), QPointF(x + 9, ys[target]))
                p.drawLine(QPointF(x, ys[target] - 9), QPointF(x, ys[target] + 9))
                continue
            y = ys[wires[0]]
            fill = QColor(colour)
            fill.setAlpha(60 if done else 25)
            p.setPen(pen)
            p.setBrush(fill)
            p.drawRoundedRect(QRectF(x - 14, y - 12, 28, 24), 5, 5)
            p.setPen(text)
            p.setFont(QFont('Sans', 9, QFont.Weight.Bold))
            p.drawText(QRectF(x - 14, y - 12, 28, 24), Qt.AlignmentFlag.AlignCenter, label)
            if kind == 'fix':                                   # classically controlled by c1 (X) / c0 (Z)
                p.setFont(QFont('Sans', 7))
                p.drawText(QRectF(x - 22, y - 26, 44, 12), Qt.AlignmentFlag.AlignCenter,
                           'skipped' if skipped else ('if c1' if label == 'X' else 'if c0'))
        p.end()


class BitChannel(QWidget):
    """Alice's two classical bits travelling to Bob over an ordinary channel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(46)
        self.bits = None
        self.progress = 0.0
        self.on_arrival = None
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)

    def send(self, bits):
        self.bits, self.progress = bits, 0.0
        self._timer.start()

    def show_at(self, bits, progress):
        self._timer.stop()
        self.bits, self.progress = bits, progress
        self.update()

    def _tick(self):
        self.progress = min(1.0, self.progress + 0.025)
        if self.progress >= 1.0:
            self._timer.stop()
            if self.on_arrival is not None:
                self.on_arrival()
        self.update()

    def paintEvent(self, event):
        dark = _dark()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        text = QColor(220, 235, 250) if dark else QColor(25, 50, 75)
        w, h = self.width(), self.height()
        y = h / 2
        x0, x1 = w * 0.17, w * 0.83
        p.setPen(QPen(QColor(120, 170, 210) if dark else QColor(80, 110, 140), 2, Qt.PenStyle.DotLine))
        p.drawLine(QPointF(x0, y), QPointF(x1, y))
        p.setPen(text)
        p.setFont(QFont('Sans', 8))
        p.drawText(QRectF(x0, y + 6, x1 - x0, 14), Qt.AlignmentFlag.AlignCenter,
                   'classical channel (no faster than light)')
        if self.bits:
            x = x0 + (x1 - x0) * self.progress
            for k, bit in enumerate(self.bits):
                cx = min(x1, max(x0, x)) - 24 + 48 * k
                token = QRectF(cx - 22, y - 23, 44, 20)
                p.setPen(QPen(QColor(255, 200, 90), 2))
                p.setBrush(QColor(255, 200, 90, 70))
                p.drawRoundedRect(token, 5, 5)
                p.setPen(text)
                p.setFont(QFont('Sans', 9, QFont.Weight.Bold))
                p.drawText(token, Qt.AlignmentFlag.AlignCenter, f'c{k}={bit}')
        p.end()


class FidelityMeter(QWidget):
    """The average fidelity of many teleports, against ½ (random), ⅔ (classical limit) and 1."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(64)
        self.values = []
        self.expected = 1.0

    def paintEvent(self, event):
        dark = _dark()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        text = QColor(220, 235, 250) if dark else QColor(25, 50, 75)
        w, h = self.width(), self.height()
        left, right, y = 36, w - 46, 30

        def x(f):
            return left + (right - left) * f
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(120, 160, 200, 60))
        p.drawRoundedRect(QRectF(left, y - 8, right - left, 16), 8, 8)
        mean = float(np.mean(self.values)) if self.values else None
        if mean is not None:
            p.setBrush(QColor(90, 230, 255))
            p.drawRoundedRect(QRectF(left, y - 8, x(mean) - left, 16), 8, 8)
        p.setFont(QFont('Sans', 8, QFont.Weight.Bold))
        for value, label, colour in ((0.5, '½ random', QColor(255, 150, 90)),
                                     (story.CLASSICAL_LIMIT, '⅔ classical limit', QColor(255, 186, 80)),
                                     (1.0, '1 perfect', QColor(90, 230, 150))):
            p.setPen(QPen(colour, 2))
            p.drawLine(QPointF(x(value), y - 13), QPointF(x(value), y + 13))
            p.setPen(text)
            box = QRectF(min(w - 122, max(2, x(value) - 60)), 2, 120, 12)        # kept inside the widget
            p.drawText(box, Qt.AlignmentFlag.AlignCenter, label)
        p.setPen(QPen(text, 1.5, Qt.PenStyle.DashLine))
        p.drawLine(QPointF(x(self.expected), y - 11), QPointF(x(self.expected), y + 11))
        p.setFont(QFont('Sans', 9))
        p.drawText(QRectF(0, h - 18, w, 16), Qt.AlignmentFlag.AlignCenter,
                   f'Average fidelity of {len(self.values)} teleports: {mean:.3f}   (expected {self.expected:.3f})'
                   if self.values else f'Teleport many to measure the average fidelity (expected {self.expected:.3f}).')
        p.end()


class _SceneState:
    """Keeps the last computed view (the older interface: scene.view)."""
    view = {}


class TeleportationDialog(QWidget):
    """Teleport a qubit from Alice to Bob, step by step."""

    SPEEDS = (('Fast', 25, 30), ('Instant', 0, 0))

    def __init__(self, parent=None):
        super().__init__(parent)
        from quantumscope.gui.quantum_principles import SuperpositionDialog
        root = QHBoxLayout(self)
        side = QWidget()
        side.setMaximumWidth(370)
        form = QVBoxLayout(side)
        title = QLabel('QUANTUM TELEPORTATION')
        title.setStyleSheet('font-weight:700; letter-spacing:1px;')
        form.addWidget(title)
        hint = QLabel('Alice sends Bob a qubit state using a shared Bell pair and two classical bits. '
                      'Step through it, or let it play.')
        hint.setWordWrap(True)
        hint.setObjectName('muted')
        form.addWidget(hint)
        send = QGroupBox('The state to send')
        sv = QFormLayout(send)
        self.preset = QComboBox()
        for key in PRESET_KEYS:
            self.preset.addItem(InitialState.preset(key).label, key)
        self.preset.addItem('Custom (θ, φ, or drag q0)', 'custom')
        self.preset.setCurrentIndex(self.preset.findData('+i'))
        sv.addRow('State', self.preset)
        self.theta = SuperpositionDialog._angle(60, 0, 180)
        self.phi = SuperpositionDialog._angle(40, 0, 360)
        sv.addRow('θ (custom)', SuperpositionDialog._slider_control(self.theta))
        sv.addRow('φ (custom)', SuperpositionDialog._slider_control(self.phi))
        form.addWidget(send)
        setup = QGroupBox('The experiment')
        ev = QFormLayout(setup)
        self.visibility = QSlider(Qt.Orientation.Horizontal)
        self.visibility.setRange(0, 100)
        self.visibility.setValue(100)
        self.visibility_label = QLabel('100%')
        row = QHBoxLayout()
        row.addWidget(self.visibility, 1)
        row.addWidget(self.visibility_label)
        ev.addRow('Clean pairs', row)
        self.correct = QCheckBox('Bob applies the correction')
        self.correct.setChecked(True)
        ev.addRow(self.correct)
        form.addWidget(setup)
        steps = QGroupBox('Step by step')
        st = QVBoxLayout(steps)
        self.step_label = QLabel()
        self.step_label.setStyleSheet('font-weight:600;')
        self.step_label.setWordWrap(True)
        st.addWidget(self.step_label)
        nav = QHBoxLayout()
        self.back, self.next, self.play = QPushButton('◀ Back'), QPushButton('Next ▶'), QPushButton('▶ Play')
        for button in (self.back, self.next, self.play):
            nav.addWidget(button)
        st.addLayout(nav)
        self.result = QComboBox()
        self.result.addItem('Unknown to Bob (average of all four)', None)
        for bits in ('00', '01', '10', '11'):
            self.result.addItem(f'Alice got c0c1 = {bits}', bits)
        st.addWidget(self.result)
        self.run_once = QPushButton('Run once (random result)')
        self.run_once.setToolTip('Pick one actual measurement result, as a single real run would')
        st.addWidget(self.run_once)
        form.addWidget(steps)
        many = QGroupBox('Many teleports')
        mv = QHBoxLayout(many)
        self.count = QSpinBox()
        self.count.setRange(10, 5000)
        self.count.setValue(200)
        mv.addWidget(self.count)
        self.speed = QComboBox()
        for label, _, _ in self.SPEEDS:
            self.speed.addItem(label)
        mv.addWidget(self.speed)
        self.many = QPushButton('Teleport many')
        mv.addWidget(self.many)
        form.addWidget(many)
        self.explain = QLabel()
        self.explain.setWordWrap(True)
        form.addWidget(self.explain)
        self.open_circuit = QPushButton('Open in the circuit simulator')
        self.open_circuit.setToolTip('Load the same protocol as a circuit, with mid-circuit measurements and '
                                     'classically controlled corrections')
        form.addWidget(self.open_circuit)
        form.addStretch()
        root.addWidget(side)
        right = QVBoxLayout()
        self.circuit = CircuitStrip()
        right.addWidget(self.circuit)
        spheres = QHBoxLayout()
        self.q0, self.q1, self.q2 = BlochView(), BlochView(), BlochView()
        for view, caption in ((self.q0, 'q0 · Alice, to send'), (self.q1, 'q1 · Alice\'s half'), (self.q2, 'q2 · Bob')):
            view.caption, view.show_axis = caption, False
            view.setMinimumSize(220, 240)
            spheres.addWidget(view, 1)
        self.q1.draggable = self.q2.draggable = False
        right.addLayout(spheres, 3)
        self.channel = BitChannel()
        self.channel.on_arrival = self._bits_arrived
        right.addWidget(self.channel)
        self.fidelity = FidelityMeter()
        right.addWidget(self.fidelity)
        root.addLayout(right, 1)
        self.scene = _SceneState()
        self.step = 0
        self._playing = QTimer(self)
        self._playing.setInterval(1500)
        self._playing.timeout.connect(self._play_step)
        self._stream_timer = QTimer(self)
        self._stream_timer.timeout.connect(self._stream)
        self._pending = 0
        self.back.clicked.connect(lambda: self.go(self.step - 1))
        self.next.clicked.connect(lambda: self.go(self.step + 1))
        self.play.clicked.connect(self._toggle_play)
        self.preset.currentIndexChanged.connect(self._state_changed)
        for spin in (self.theta, self.phi):
            spin.valueChanged.connect(self._state_changed)
        self.q0.stateChanged.connect(self._dragged)
        self.visibility.valueChanged.connect(self._setup_changed)
        self.correct.toggled.connect(self._setup_changed)
        self.result.currentIndexChanged.connect(lambda *_: self.refresh())
        self.run_once.clicked.connect(self._run_once)
        self.many.clicked.connect(self.teleport_many)
        self.open_circuit.clicked.connect(self._open_in_circuit)
        self._setup_changed()

    # ---- the state to send ---------------------------------------------------------------------------
    def input_state(self):
        key = self.preset.currentData()
        if key == 'custom':
            return InitialState(math.radians(self.theta.value()), math.radians(self.phi.value()))
        return InitialState.preset(key)

    def _dragged(self, theta, phi):
        """Dragging q0 (in step 1) chooses a custom state to send."""
        for spin, value in ((self.theta, theta), (self.phi, phi % 360)):
            spin.blockSignals(True)
            spin.setValue(value)
            spin.blockSignals(False)
        self.preset.blockSignals(True)
        self.preset.setCurrentIndex(self.preset.findData('custom'))
        self.preset.blockSignals(False)
        self.refresh(animate=False)

    def _state_changed(self, *_):
        self.fidelity.values = []
        self.refresh()

    def _setup_changed(self, *_):
        self.visibility_label.setText(f'{self.visibility.value()}%')
        self.circuit.correct = self.correct.isChecked()
        self.circuit.update()
        self.fidelity.values = []
        self.fidelity.expected = story.expected_fidelity(self.visibility.value() / 100, self.correct.isChecked())
        self.fidelity.update()
        self.refresh()

    # ---- steps -------------------------------------------------------------------------------------------
    def go(self, step, animate=True):
        self.step = max(0, min(len(story.STEPS) - 1, step))
        if self.step == 4 and self.result.currentData() is not None and animate:
            self.refresh(animate=True, hold_bob=True)            # the bits travel first, then Bob corrects
            self.channel.send(self.result.currentData())
            return
        self.refresh(animate=animate)

    def _bits_arrived(self):
        if self.step == 4:
            self.refresh(animate=True)

    def _toggle_play(self):
        if self._playing.isActive():
            self._playing.stop()
            self.play.setText('▶ Play')
            return
        if self.step >= len(story.STEPS) - 1:
            self.go(0)
        if self.result.currentData() is None:                   # a real run has one result
            self.result.blockSignals(True)
            self.result.setCurrentIndex(self.result.findData(story.random_record()))
            self.result.blockSignals(False)
        self.play.setText('❚❚ Pause')
        self._playing.start()

    def _play_step(self):
        if self.step >= len(story.STEPS) - 1:
            self._playing.stop()
            self.play.setText('▶ Play')
            return
        self.go(self.step + 1)

    def _run_once(self):
        if self.step < 3:
            self.step = 3
        self.result.setCurrentIndex(self.result.findData(story.random_record()))
        self.refresh()

    def refresh(self, *_, animate=True, hold_bob=False):
        custom = self.preset.currentData() == 'custom'
        self.theta.setEnabled(custom)
        self.phi.setEnabled(custom)
        state = self.input_state()
        record = self.result.currentData() if self.step >= 3 else None
        v, correct = self.visibility.value() / 100, self.correct.isChecked()
        view = story.state_at(state.vector(), self.step, record, v, correct)
        if hold_bob:                                             # Bob has not received the bits yet
            before = story.state_at(state.vector(), 3, record, v, correct)
            view = dict(view, blochs=[view['blochs'][0], view['blochs'][1], before['blochs'][2]],
                        bob_fidelity=before['bob_fidelity'], bob_purity=before['bob_purity'])
        self.scene.view = view
        title, text = story.STEPS[self.step]
        if self.step == 4 and not correct:
            title, text = 'Bob skips the correction', ('The bits reach Bob, but he ignores them. Only for c0c1 = 00 is '
                                                       'his qubit right; on average it is completely random '
                                                       '(fidelity ½).')
        self.step_label.setText(f'Step {self.step + 1} of {len(story.STEPS)}: {title}')
        extra = ''
        if self.step >= 3 and record is not None and correct:
            extra = (f'\n\nWith result {record}, Bob ' + ('needs no correction.' if record == '00' else
                     'must apply ' + ' and '.join(g for g, bit in (('X', record[1]), ('Z', record[0])) if bit == '1')
                     + '.'))
        if self.step == 4 and v < 1:
            extra += (f'\n\nThe pair was only {v:.0%} clean, so Bob\'s qubit matches with fidelity '
                      f'{view["bob_fidelity"]:.3f}, not 1.')
        self.explain.setText(text + extra)
        self.back.setEnabled(self.step > 0)
        self.next.setEnabled(self.step < len(story.STEPS) - 1)
        self.result.setEnabled(self.step >= 3)
        self.q0.draggable = self.step == 0
        self.circuit.step = self.step
        self.circuit.update()
        flash = animate and self.step == 3 and record is not None
        for qubit, sphere in enumerate((self.q0, self.q1, self.q2)):
            vector = np.asarray(view['blochs'][qubit], float)
            length = float(np.linalg.norm(vector))
            theta, phi = angles(vector) if length > 1e-9 else (0.0, 0.0)
            sphere.set_state(theta, phi, animate=animate and length > 1e-9, length=min(1.0, length),
                             flash=flash and qubit < 2 or (animate and qubit == 2 and self.step == 4 and not hold_bob))
        if self.step == 3 and record is not None:
            self.channel.show_at(record, 0.0)
        elif self.step == 4 and record is not None and not hold_bob:
            self.channel.show_at(record, 1.0)
        elif self.step < 3:
            self.channel.show_at(None, 0.0)

    # ---- many teleports --------------------------------------------------------------------------------------
    def teleport_many(self):
        self.fidelity.values = []
        self._pending = self.count.value()
        _, per_tick, interval = self.SPEEDS[self.speed.currentIndex()]
        if per_tick == 0:
            while self._pending > 0:
                self._stream(everything=True)
            return
        self._stream_timer.start(interval)

    def _stream(self, everything=False):
        _, per_tick, _ = self.SPEEDS[self.speed.currentIndex()]
        n = self._pending if everything or per_tick == 0 else min(per_tick, self._pending)
        vector, v, correct = self.input_state().vector(), self.visibility.value() / 100, self.correct.isChecked()
        fidelities = {record: story.state_at(vector, 4, record, v, correct)['bob_fidelity'] for record in ('00', '01', '10', '11')}
        probabilities = story.state_at(vector, 3, visibility=v)['probabilities']
        keys = sorted(probabilities)
        weights = np.array([probabilities[k] for k in keys])
        picks = np.random.default_rng().choice(len(keys), size=n, p=weights / weights.sum())
        self.fidelity.values.extend(fidelities[keys[i]] for i in picks)
        self.fidelity.update()
        self._pending -= n
        if self._pending <= 0:
            self._stream_timer.stop()
            mean = float(np.mean(self.fidelity.values))
            verdict = ('better than any classical method (⅔)' if mean > story.CLASSICAL_LIMIT + 0.02 else
                       'no better than a classical method (⅔): the pair is too noisy' if correct else
                       'random: without the correction, the bits are wasted')
            self.explain.setText(f'{len(self.fidelity.values)} teleports: average fidelity {mean:.3f}, {verdict}.')

    def _open_in_circuit(self):
        window = self.window()
        workspace = getattr(window, 'circuit_widget', None)
        if workspace is None:
            return
        state = self.input_state()
        key = self.preset.currentData()
        workspace.load_library('teleportation', {'input': key if key != 'custom' else '+i'})
        if key == 'custom':
            workspace.model.set_initial_state(0, state)
            workspace._changed()
        launch = getattr(window, '_launch_circuits', None)
        if callable(launch):
            launch()
