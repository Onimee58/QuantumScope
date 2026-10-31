"""Noise Explorer: what a noise channel does, with equations and live numbers."""
import math
import os

import numpy as np
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import (QApplication, QDialog, QDoubleSpinBox, QHBoxLayout, QLabel, QPushButton, QSlider,
                               QTabWidget, QTextBrowser, QVBoxLayout)

from quantumscope.learn.lessons import content_folder, reference_page
from quantumscope.learn.render import to_html
from quantumscope.physics import noise as N
from quantumscope.physics.gate_education import format_amplitude

# Starting states shown in the live table: (label, Bloch vector)
PROBE_STATES = (('|0⟩', (0.0, 0.0, 1.0)), ('|1⟩', (0.0, 0.0, -1.0)), ('|+⟩', (1.0, 0.0, 0.0)), ('|+i⟩', (0.0, 1.0, 0.0)))
# A starting state that makes each channel's effect visible in "Try it"
TRY_START = {'bit_flip': '0', 'phase_flip': '+', 'depolarizing': '+', 'amplitude_damping': '1', 'phase_damping': '+'}


def _theme():
    app = QApplication.instance()
    return 'light' if app is not None and app.property('quantumscope_light') else 'dark'


class NoiseExplorer(QDialog):
    def __init__(self, kind, parent=None, p=0.2):
        super().__init__(parent)
        if kind not in N.CHANNELS:
            raise ValueError(f'Unknown channel: {kind}')
        self.kind = kind
        name, self.symbol, _ = N.CHANNELS[kind]
        self.setWindowTitle(f'{name} noise')
        self.resize(820, 720)
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self.about = QTextBrowser()
        self.tabs.addTab(self.about, 'About this channel')
        self.numbers = QTextBrowser()
        self.tabs.addTab(self.numbers, 'Effect at this strength')

        controls = QHBoxLayout()
        layout.addLayout(controls)
        controls.addWidget(QLabel(f'Strength {self.symbol}:'))
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 1000)
        controls.addWidget(self.slider, 1)
        self.strength = QDoubleSpinBox()
        self.strength.setRange(0, 1)
        self.strength.setDecimals(3)
        self.strength.setSingleStep(0.05)
        controls.addWidget(self.strength)
        self.slider.valueChanged.connect(lambda v: self.strength.setValue(v / 1000))
        self.strength.valueChanged.connect(self._strength_changed)
        if hasattr(parent, 'try_noise'):
            self.try_button = QPushButton('Try it in the circuit')
            self.try_button.setToolTip('Load a one-qubit circuit whose starting state shows this channel clearly')
            self.try_button.clicked.connect(self._try_it)
            controls.addWidget(self.try_button)
        close = QPushButton('Close')
        close.clicked.connect(self.accept)
        controls.addWidget(close)

        page = reference_page(kind)
        if page is not None:
            self.about.document().setBaseUrl(QUrl.fromLocalFile(page.folder + os.sep))
            self.about.setHtml(to_html(page, _theme(), os.path.join(content_folder(), 'eq')))
        self.strength.setValue(p)
        self._strength_changed(p)

    @property
    def p(self):
        return self.strength.value()

    def _strength_changed(self, value):
        self.slider.blockSignals(True)
        self.slider.setValue(round(value * 1000))
        self.slider.blockSignals(False)
        self.numbers.setHtml(self.effect_html(value))

    def effect_html(self, p):
        """The live part: where probe states go, their purity, and the Kraus matrices at strength p."""
        rows = []
        for label, start in PROBE_STATES:
            end = N.bloch_map(self.kind, p, start)
            length = math.sqrt(sum(c * c for c in end))
            purity = (1 + length ** 2) / 2
            rows.append(f'<tr><td><b>{label}</b></td><td>({start[0]:g}, {start[1]:g}, {start[2]:g})</td>'
                        f'<td>({end[0]:.3f}, {end[1]:.3f}, {end[2]:.3f})</td><td>{length:.3f}</td><td>{purity:.3f}</td></tr>')
        table = ('<table border="1" cellpadding="5" cellspacing="0"><tr><th>Start</th><th>Bloch vector</th>'
                 '<th>After the channel</th><th>Length</th><th>Purity</th></tr>' + ''.join(rows) + '</table>')
        matrices = []
        for i, k in enumerate(N.kraus(self.kind, p)):
            cells = ''.join('<tr>' + ''.join(f'<td align="center">{format_amplitude(complex(x))}</td>' for x in row)
                            + '</tr>' for row in k)
            matrices.append(f'<td><b>K{i}</b><table border="1" cellpadding="4" cellspacing="0">{cells}</table></td>')
        kraus = '<table cellpadding="6"><tr>' + ''.join(matrices) + '</tr></table>'
        check = sum(k.conj().T @ k for k in N.kraus(self.kind, p))
        ok = 'Σ K†K = I ✓' if np.allclose(check, np.eye(2)) else 'Σ K†K ≠ I'
        return (f'<h3>Strength {self.symbol} = {p:g}</h3>'
                '<p>Where four starting states end up (Bloch vectors; length 1 = pure, 0 = maximally mixed):</p>'
                + table + f'<h3>Kraus operators at {self.symbol} = {p:g}</h3>' + kraus
                + f'<p>{ok} — the channel preserves probability.</p>')

    def _try_it(self):
        self.parent().try_noise(self.kind, self.p, TRY_START[self.kind])
        self.accept()
