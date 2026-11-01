"""Quantum Principles experiment: teleportation told as a story (Alice, Bob and a classical channel).

The physics comes from physics.teleport_story, which runs the same branch engine as the
circuit simulator; "Open in the circuit simulator" loads the matching circuit.
"""
import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (QComboBox, QFormLayout, QHBoxLayout, QLabel, QPushButton, QSplitter, QVBoxLayout,
                               QWidget)

from quantumscope.gui.theme import canvas_color
from quantumscope.physics import teleport_story as story
from quantumscope.physics.initial_states import InitialState

PRESET_KEYS = ('0', '1', '+', '-', '+i', '-i')


class TeleportScene(QWidget):
    """Alice's two qubits on the left, Bob's on the right, a classical channel between them."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 360)
        self.view, self.step, self.input_bloch = None, 0, (0, 0, 1)

    def show_state(self, view, step, input_bloch):
        self.view, self.step, self.input_bloch = view, step, input_bloch
        self.update()

    def _sphere(self, p, cx, cy, r, vector, title, subtitle, ghost=None):
        p.setPen(QPen(canvas_color('bloch_outline'), 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r, r)
        p.drawEllipse(QRectF(cx - r, cy - r * .29, 2 * r, r * .58))
        p.setPen(QPen(canvas_color('bloch_axis'), 1))
        p.drawLine(QPointF(cx - r, cy), QPointF(cx + r, cy))
        p.drawLine(QPointF(cx, cy - r), QPointF(cx, cy + r))

        def tip(v):
            x, y, z = v
            return QPointF(cx + r * (.87 * x + .34 * y), cy - r * (z + .28 * y))
        if ghost is not None:                       # the state Alice sent, for comparison
            p.setPen(QPen(canvas_color('chart_sampled'), 1.5, Qt.PenStyle.DashLine))
            p.drawLine(QPointF(cx, cy), tip(ghost))
        p.setPen(QPen(canvas_color('bloch_vector'), 3.2))
        end = tip(vector)
        p.drawLine(QPointF(cx, cy), end)
        p.setBrush(canvas_color('bloch_vector'))
        p.drawEllipse(end, 4.5, 4.5)
        p.setPen(canvas_color('bloch_text'))
        p.setFont(QFont('Sans', 10, QFont.Weight.Bold))
        p.drawText(QRectF(cx - r - 30, cy + r + 6, 2 * r + 60, 18), Qt.AlignmentFlag.AlignCenter, title)
        p.setFont(QFont('Sans', 9))
        p.drawText(QRectF(cx - r - 40, cy + r + 24, 2 * r + 80, 18), Qt.AlignmentFlag.AlignCenter, subtitle)

    def paintEvent(self, event):
        if self.view is None:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        r = max(30.0, min(70.0, w / 11, h / 5))
        cy = h * 0.42
        mid = w * 0.62
        # Alice's lab and Bob's lab, far apart
        p.setPen(QPen(canvas_color('bloch_axis'), 1, Qt.PenStyle.DashLine))
        p.drawLine(QPointF(mid, 10), QPointF(mid, h - 10))
        p.setPen(canvas_color('bloch_text'))
        p.setFont(QFont('Sans', 11, QFont.Weight.Bold))
        p.drawText(QRectF(0, 8, mid, 22), Qt.AlignmentFlag.AlignCenter, 'Alice')
        p.drawText(QRectF(mid, 8, w - mid, 22), Qt.AlignmentFlag.AlignCenter, 'Bob (far away)')
        v = self.view
        length = lambda b: math.sqrt(sum(c * c for c in b))
        q0, q1, q2 = v['blochs']
        self._sphere(p, mid * 0.28, cy, r, q0, 'q0 · to send', f'arrow length {length(q0):.2f}')
        self._sphere(p, mid * 0.72, cy, r, q1, 'q1 · her half of the pair', f'arrow length {length(q1):.2f}')
        self._sphere(p, mid + (w - mid) / 2, cy, r, q2, 'q2 · Bob\'s qubit',
                     f'matches the input: {v["bob_fidelity"] * 100:.1f}%', ghost=self.input_bloch)
        # The Bell pair link and the classical channel
        y_link = cy + r + 52
        if self.step >= 1:
            used = self.step >= 3                  # Alice's measurement consumes the entanglement
            p.setPen(QPen(canvas_color('bloch_axis' if used else 'bloch_vector'), 1.5, Qt.PenStyle.DotLine))
            p.drawLine(QPointF(mid * 0.72, cy + r * 0.2), QPointF(mid + (w - mid) / 2, cy + r * 0.2))
            p.setFont(QFont('Sans', 8))
            p.drawText(QRectF(mid * 0.72, cy + r * 0.2 - 16, mid + (w - mid) / 2 - mid * 0.72, 14),
                       Qt.AlignmentFlag.AlignCenter,
                       'Bell pair used up by the measurement' if used else 'entangled (Bell pair)')
        if self.step >= 3:
            bits = v['record']
            text = (f'classical bits c0c1 = {bits}' if bits else 'classical bits c0c1 = ?? (one of 00, 01, 10, 11)')
            color = QColor(canvas_color('measure_border'))
            p.setPen(QPen(color, 2.4))
            end_x = mid + (w - mid) / 2 if self.step >= 4 else mid - 12
            p.drawLine(QPointF(mid * 0.28, y_link), QPointF(end_x, y_link))
            p.drawLine(QPointF(end_x, y_link), QPointF(end_x - 9, y_link - 6))
            p.drawLine(QPointF(end_x, y_link), QPointF(end_x - 9, y_link + 6))
            p.setPen(canvas_color('bloch_text'))
            p.setFont(QFont('Sans', 10, QFont.Weight.DemiBold))
            label = text + ('  →  sent to Bob at light speed' if self.step >= 4 else '  (not yet sent)')
            p.drawText(QRectF(10, y_link + 6, w - 20, 20), Qt.AlignmentFlag.AlignCenter, label)
        p.end()


class TeleportationDialog(QWidget):
    """Step through teleportation: choose a state, share a Bell pair, measure, send two bits, correct."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        heading = QLabel('QUANTUM TELEPORTATION  ·  a qubit\'s state moves from Alice to Bob using one Bell pair '
                         'and two classical bits')
        heading.setWordWrap(True)
        layout.addWidget(heading)
        split = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(split, 1)
        side = QWidget()
        form = QFormLayout(side)
        self.preset = QComboBox()
        for key in PRESET_KEYS:
            self.preset.addItem(InitialState.preset(key).label, key)
        self.preset.addItem('Custom (θ, φ)', 'custom')
        self.preset.setCurrentIndex(self.preset.findData('+i'))
        form.addRow('State to send', self.preset)
        from quantumscope.gui.quantum_principles import SuperpositionDialog
        self.theta = SuperpositionDialog._angle(60, 0, 180)
        self.phi = SuperpositionDialog._angle(40, 0, 360)
        form.addRow('θ (custom)', SuperpositionDialog._slider_control(self.theta))
        form.addRow('φ (custom)', SuperpositionDialog._slider_control(self.phi))
        steps = QHBoxLayout()
        self.back = QPushButton('◀ Back')
        self.next = QPushButton('Next step ▶')
        steps.addWidget(self.back)
        steps.addWidget(self.next)
        form.addRow(steps)
        self.step_label = QLabel()
        self.step_label.setStyleSheet('font-weight: 700;')
        form.addRow(self.step_label)
        self.result = QComboBox()
        self.result.addItem('Unknown to Bob (average of all four)', None)
        for bits in ('00', '01', '10', '11'):
            self.result.addItem(f'Alice got c0c1 = {bits}', bits)
        form.addRow('Measurement result', self.result)
        self.run_once = QPushButton('Run once (random result)')
        self.run_once.setToolTip('Pick one actual measurement result, as a single real run would')
        form.addRow(self.run_once)
        self.explain = QLabel()
        self.explain.setWordWrap(True)
        form.addRow(self.explain)
        self.open_circuit = QPushButton('Open in the circuit simulator')
        self.open_circuit.setToolTip('Load the same protocol as a circuit, with mid-circuit measurements and '
                                     'classically controlled corrections')
        form.addRow(self.open_circuit)
        split.addWidget(side)
        self.scene = TeleportScene()
        split.addWidget(self.scene)
        split.setSizes([330, 800])
        self.step = 0
        self.back.clicked.connect(lambda: self.go(self.step - 1))
        self.next.clicked.connect(lambda: self.go(self.step + 1))
        self.run_once.clicked.connect(self._run_once)
        self.open_circuit.clicked.connect(self._open_in_circuit)
        for widget in (self.preset, self.result):
            widget.currentIndexChanged.connect(self.refresh)
        for slider in (self.theta, self.phi):
            slider.valueChanged.connect(self.refresh)
        self.refresh()

    def input_state(self):
        key = self.preset.currentData()
        if key == 'custom':
            return InitialState(math.radians(self.theta.value()), math.radians(self.phi.value()))
        return InitialState.preset(key)

    def go(self, step):
        self.step = max(0, min(len(story.STEPS) - 1, step))
        self.refresh()

    def _run_once(self):
        if self.step < 3:
            self.step = 3
        self.result.setCurrentIndex(self.result.findData(story.random_record()))
        self.refresh()

    def refresh(self, *_):
        custom = self.preset.currentData() == 'custom'
        self.theta.setEnabled(custom)
        self.phi.setEnabled(custom)
        state = self.input_state()
        record = self.result.currentData() if self.step >= 3 else None
        view = story.state_at(state.vector(), self.step, record)
        title, text = story.STEPS[self.step]
        self.step_label.setText(f'Step {self.step + 1} of {len(story.STEPS)}: {title}')
        extra = ''
        if self.step >= 3 and record is not None:
            extra = (f'\n\nWith result {record}, Bob ' + ('needs no correction.' if record == '00' else
                     'must apply ' + ' and '.join(g for g, bit in (('X', record[1]), ('Z', record[0])) if bit == '1') + '.'))
        self.explain.setText(text + extra)
        self.back.setEnabled(self.step > 0)
        self.next.setEnabled(self.step < len(story.STEPS) - 1)
        self.result.setEnabled(self.step >= 3)
        self.scene.show_state(view, self.step, state.bloch())

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
