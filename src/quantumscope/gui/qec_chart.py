"""Logical error rate charts and the Error-correction explorer (one sweep, two entry points)."""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QFont, QPainter, QPen
from PySide6.QtWidgets import (QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QPushButton, QSlider,
                               QVBoxLayout, QWidget)

from quantumscope.editor import qec_analysis as qa
from quantumscope.gui.theme import canvas_color
from quantumscope.physics.qec import repetition_theory, unprotected_failure

PS = [i / 40 for i in range(21)]                    # p from 0 to 0.5
CHANNELS = (('Bit flips', 'bit_flip'), ('Phase flips', 'phase_flip'), ('Depolarizing', 'depolarizing'))
CODES = (('No code (one qubit)', 'none'), ('Bit-flip code', 'bit_flip'), ('Phase-flip code', 'phase_flip'))


def crossing(ps, encoded, unprotected):
    """The first p > 0 where the code stops helping, or None if it always helps or never does."""
    helps = [e < u - 1e-12 for e, u in zip(encoded, unprotected)]
    for i in range(1, len(ps)):
        if helps[i - 1] and not helps[i]:
            return ps[i]
    return None


def verdict(p, encoded, unprotected):
    if abs(encoded - unprotected) < 1e-9:
        return 'the code makes no difference'
    if encoded < unprotected:
        return f'the code helps: {unprotected / max(encoded, 1e-12):.1f}× fewer failures'
    return f'the code HURTS: {encoded / max(unprotected, 1e-12):.1f}× more failures'


class LogicalErrorChart(QWidget):
    """Logical failure rate against physical error rate p, with the unprotected line y = p."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(520, 330)
        self.ps, self.encoded, self.unprotected, self.theory, self.marker = [], [], [], None, None

    def set_data(self, ps, encoded, unprotected, theory=None, marker=None):
        self.ps, self.encoded, self.unprotected, self.theory, self.marker = ps, encoded, unprotected, theory, marker
        self.update()

    def paintEvent(self, event):
        if not self.ps:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        left, top, right, bottom = 62, 18, self.width() - 18, self.height() - 52
        top_value = max(0.5, max(self.encoded + self.unprotected))
        x = lambda v: left + (right - left) * v / 0.5
        y = lambda v: bottom - (bottom - top) * v / top_value
        text = canvas_color('chart_text')
        p.setPen(QPen(canvas_color('bloch_axis'), 1))
        for i in range(6):
            p.drawLine(QPointF(x(i * 0.1), top), QPointF(x(i * 0.1), bottom))
            p.drawLine(QPointF(left, y(i * top_value / 5)), QPointF(right, y(i * top_value / 5)))
        p.setPen(text)
        p.setFont(QFont('Sans', 8))
        for i in range(6):
            p.drawText(QRectF(x(i * 0.1) - 20, bottom + 4, 40, 14), Qt.AlignmentFlag.AlignCenter, f'{i * 0.1:.1f}')
            p.drawText(QRectF(left - 50, y(i * top_value / 5) - 7, 44, 14), Qt.AlignmentFlag.AlignRight,
                       f'{i * top_value / 5:.2f}')
        p.setFont(QFont('Sans', 9))
        p.drawText(QRectF(left, bottom + 20, right - left, 16), Qt.AlignmentFlag.AlignCenter,
                   'physical error rate p (per qubit)')
        p.save()
        p.translate(14, (top + bottom) / 2)
        p.rotate(-90)
        p.drawText(QRectF(-80, -8, 160, 16), Qt.AlignmentFlag.AlignCenter, 'logical failure rate')
        p.restore()
        # unprotected (dashed) and encoded (solid) curves
        def line(values, pen):
            p.setPen(pen)
            points = [QPointF(x(a), y(b)) for a, b in zip(self.ps, values)]
            for a, b in zip(points, points[1:]):
                p.drawLine(a, b)
        line(self.unprotected, QPen(canvas_color('chart_sampled'), 2, Qt.PenStyle.DashLine))
        line(self.encoded, QPen(canvas_color('bloch_vector'), 2.6))
        if self.theory:
            p.setBrush(canvas_color('bloch_vector'))
            p.setPen(Qt.PenStyle.NoPen)
            for a, b in zip(self.ps, self.encoded):
                p.drawEllipse(QPointF(x(a), y(b)), 2.6, 2.6)
        if self.marker is not None:
            mp, me = self.marker
            p.setPen(QPen(text, 1, Qt.PenStyle.DotLine))
            p.drawLine(QPointF(x(mp), top), QPointF(x(mp), bottom))
            p.setBrush(canvas_color('bloch_vector'))
            p.drawEllipse(QPointF(x(mp), y(me)), 5, 5)
        cross = crossing(self.ps, self.encoded, self.unprotected)
        legend = [(canvas_color('bloch_vector'), Qt.PenStyle.SolidLine, 'with the code'),
                  (canvas_color('chart_sampled'), Qt.PenStyle.DashLine, 'unprotected qubit')]
        for i, (color, style, label) in enumerate(legend):
            yy = top + 8 + 16 * i
            p.setPen(QPen(color, 2.4, style))
            p.drawLine(QPointF(left + 12, yy), QPointF(left + 36, yy))
            p.setPen(text)
            p.drawText(QPointF(left + 42, yy + 4), label)
        if cross is not None:
            p.setPen(text)
            p.drawText(QPointF(left + 12, top + 52), f'the code stops helping at p ≈ {cross:.2f}')
        p.end()


def _summary(code, channel, p, encoded, unprotected):
    theory = repetition_theory(code, channel, p) if code != 'none' else None
    extra = f' (theory {theory:.4f})' if theory is not None else ''
    return (f'At p = {p:.3f}: unprotected qubit fails with probability {unprotected:.4f}; '
            f'with the code {encoded:.4f}{extra} — {verdict(p, encoded, unprotected)}.')


def plot_circuit(workspace):
    """The verification panel's "Plot logical error rate": sweep the noise boxes of the current circuit."""
    model = workspace.model
    kind = qa.noise_kind(model)
    dialog = QDialog(workspace)
    dialog.setWindowTitle('Logical error rate of this circuit')
    v = QVBoxLayout(dialog)
    if kind is None:
        v.addWidget(QLabel('This plot varies the strength of the circuit\'s noise boxes. Choose "Random errors on '
                           'every data qubit" in the example, or place noise boxes of one kind on q0–q2.'))
    else:
        encoded = qa.curve(model, PS)
        unprotected = [unprotected_failure(kind, x) for x in PS]
        chart = LogicalErrorChart()
        chart.set_data(PS, encoded, unprotected, theory=True)
        v.addWidget(chart)
        note = QLabel('Every noise box in this circuit is set to strength p; the failure rate is the worst case '
                      'over the six standard starting states of q0. Edit the circuit and plot again to compare.')
        note.setWordWrap(True)
        v.addWidget(note)
        dialog.chart = chart
    close = QPushButton('Close')
    close.clicked.connect(dialog.accept)
    v.addWidget(close)
    dialog.resize(720, 520)
    return dialog


class ErrorCorrectionExplorer(QWidget):
    """Quantum Circuits experiment: which code helps against which noise, and when."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        side = QWidget()
        form = QFormLayout(side)
        heading = QLabel('ERROR-CORRECTION EXPLORER  ·  how often does the encoded qubit still fail?')
        heading.setWordWrap(True)
        form.addRow(heading)
        self.code = QComboBox()
        for label, key in CODES:
            self.code.addItem(label, key)
        self.code.setCurrentIndex(1)
        form.addRow('Code', self.code)
        self.channel = QComboBox()
        for label, key in CHANNELS:
            self.channel.addItem(label, key)
        form.addRow('Noise on each qubit', self.channel)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 500)
        self.slider.setValue(100)
        self.p_label = QLabel()
        form.addRow('Error rate p', self.slider)
        form.addRow(self.p_label)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        form.addRow(self.summary)
        self.open_button = QPushButton('Open this circuit in the simulator')
        self.open_button.clicked.connect(self._open)
        form.addRow(self.open_button)
        layout.addWidget(side, 1)
        self.chart = LogicalErrorChart()
        layout.addWidget(self.chart, 2)
        self.code.currentIndexChanged.connect(self.recompute)
        self.channel.currentIndexChanged.connect(self.recompute)
        self.slider.valueChanged.connect(self.update_marker)
        self.recompute()

    @property
    def p(self):
        return self.slider.value() / 1000

    def recompute(self, *_):
        code, channel = self.code.currentData(), self.channel.currentData()
        self.model, self.data = qa.example_model(code, channel)
        self.encoded = qa.curve(self.model, PS, self.data)
        self.unprotected = [unprotected_failure(channel, x) for x in PS]
        self.update_marker()

    def update_marker(self, *_):
        code, channel = self.code.currentData(), self.channel.currentData()
        p = self.p
        encoded = qa.logical_failure(self.model, p, self.data)
        unprotected = unprotected_failure(channel, p)
        self.p_label.setText(f'p = {p:.3f}')
        self.summary.setText(_summary(code, channel, p, encoded, unprotected))
        self.chart.set_data(PS, self.encoded, self.unprotected, theory=True, marker=(p, encoded))

    def _open(self):
        window = self.window()
        workspace = getattr(window, 'circuit_widget', None)
        if workspace is None:
            return
        model, _ = qa.example_model(self.code.currentData(), self.channel.currentData(), self.p)
        layout_gates, columns, _, _ = model.layout()
        classical, conditions = model.classical_layout()
        workspace.set_circuit(model.n, layout_gates, columns, initial_states=model.initial_states,
                              noise=model.noise_layout(), classical=classical, conditions=conditions)
        launch = getattr(window, '_launch_circuits', None)
        if callable(launch):
            launch()
