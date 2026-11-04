"""Interactive far-field double-slit experiment with sampled detection events."""
import csv
import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QComboBox, QDoubleSpinBox, QSpinBox, QLabel, QPushButton, QWidget,
    QSplitter, QFileDialog, QMessageBox, QCheckBox)
from quantumscope.physics.double_slit import DoubleSlit
from quantumscope.gui.double_slit_apparatus import DoubleSlitApparatus


class DoubleSlitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('QuantumScope 0.2.0 — Double-Slit Experiment')
        self.resize(1200, 760)
        self.samples = np.empty(0)
        self.model = None
        root = QVBoxLayout(self)
        self.description = QLabel(
            'DOUBLE-SLIT  ·  Fire particles one at a time and watch the interference pattern build up. '
            'Drag the slits to change their separation.')
        self.description.setWordWrap(True)
        root.addWidget(self.description)
        split = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(split, 1)
        left = QWidget()
        left.setMinimumWidth(390)
        form = QFormLayout(left)
        self.wavelength = self._double(200, 1200, 500, ' nm', 10)
        self.width = self._double(1, 200, 20, ' µm', 1)
        self.separation = self._double(1, 500, 100, ' µm', 5)
        self.distance = self._double(.1, 10, 1, ' m', .1)
        self.halfwidth = self._double(5, 100, 40, ' mm', 5)
        for name, ctrl in [('Wavelength',self.wavelength), ('Slit width',self.width),
                           ('Slit separation',self.separation), ('Screen distance',self.distance),
                           ('Screen half-width',self.halfwidth)]:
            form.addRow(name, ctrl)
            ctrl.valueChanged.connect(self._update)
        self.batch = QSpinBox(); self.batch.setRange(1, 20000); self.batch.setValue(3000)
        form.addRow('Particles', self.batch)
        self.speed = QComboBox()
        for label in ('Slow', 'Fast', 'Instant'):
            self.speed.addItem(label)
        self.speed.setCurrentIndex(1)
        form.addRow('Speed', self.speed)
        self.colour_note = QLabel(''); self.colour_note.setObjectName('muted')
        form.addRow(self.colour_note)
        self.which_path = QCheckBox('Which-path detectors at the slits')
        self.which_path.setToolTip('Ideal path information destroys two-slit interference; does not trace trajectories.')
        self.which_path.toggled.connect(self._update)
        form.addRow('Observation', self.which_path)
        self.path_note = QLabel('OFF: path information unavailable; interference fringes.')
        self.path_note.setWordWrap(True)
        form.addRow(self.path_note)
        fire = QHBoxLayout()
        self.add = QPushButton('Fire particles')
        self.add.setToolTip('Send particles through the slits one after another')
        self.add.clicked.connect(self._fire); fire.addWidget(self.add)
        self.stop = QPushButton('Stop'); self.stop.setEnabled(False)
        self.stop.clicked.connect(self._stop_firing); fire.addWidget(self.stop)
        form.addRow(fire)
        self.reset = QPushButton('Clear screen')
        self.reset.clicked.connect(self._clear); form.addRow(self.reset)
        self.export = QPushButton('Export probability and detections (CSV)')
        self.export.clicked.connect(self._export); form.addRow(self.export)
        self.info = QLabel(''); self.info.setWordWrap(True); form.addRow(self.info)
        self.note = QLabel('Each particle lands at one random spot; only many together show the fringes. '
            'Model: Fraunhofer far field, coherent equal slits, paraxial angles; not particle trajectories.')
        self.note.setWordWrap(True); self.note.setObjectName('muted'); form.addRow(self.note)
        split.addWidget(left)
        right = QWidget(); rlayout = QVBoxLayout(right)
        self.apparatus = DoubleSlitApparatus()
        self.apparatus.separationDragged.connect(self.separation.setValue)
        rlayout.addWidget(self.apparatus, 2)
        from quantumscope.gui.principles_visuals import DetectorScreen
        self.screen = DetectorScreen()
        rlayout.addWidget(self.screen, 1)
        self.animation = QCheckBox('Animate illustrative wavefronts')
        self.animation.setChecked(True)
        self.animation.toggled.connect(self.apparatus.set_animated)
        rlayout.addWidget(self.animation)
        self.curve = pg.PlotWidget(title='Double-slit screen probability density')
        self.curve.setLabel('bottom', 'Position on screen', units='mm')
        self.curve.setLabel('left', 'Probability density', units='1/mm')
        self.curve.showGrid(x=True, y=True, alpha=.2)
        self.curve.addLegend()
        self.theory = self.curve.plot(pen=pg.mkPen('#4aa8db', width=3), name='Fraunhofer model')
        self.hist = self.curve.plot(pen=pg.mkPen('#e2a84f', width=2), name='Sampled detections')
        rlayout.addWidget(self.curve, 1)
        self.status = QLabel('0 simulated detections')
        rlayout.addWidget(self.status)
        split.addWidget(right)
        split.setChildrenCollapsible(False); split.setSizes([380, 820])
        from PySide6.QtCore import QTimer
        self._pending = 0
        self._timer = QTimer(self); self._timer.timeout.connect(self._stream)
        self.wavelength.valueChanged.connect(self._colour)
        self._colour()
        self._update()

    @staticmethod
    def _double(lo, hi, initial, suffix, step):
        w = QDoubleSpinBox(); w.setRange(lo, hi); w.setValue(initial)
        w.setSuffix(suffix); w.setSingleStep(step); w.setDecimals(2)
        return w

    def _update(self, *_):
        try:
            model = DoubleSlit(self.wavelength.value(), self.width.value(),
                self.separation.value(), self.distance.value(), self.halfwidth.value())
            x, y = model.distribution(which_path=self.which_path.isChecked())
        except ValueError as exc:
            self.model = None
            self.info.setText('Invalid setup: ' + str(exc))
            self.add.setEnabled(False)
            return
        self.model = model; self.x = x; self.y = y
        observing = self.which_path.isChecked()
        self.path_note.setText('ON: ideal which-path information; incoherent single-slit envelope (not always exactly two bands).' if observing else 'OFF: coherent two-slit interference fringes.')
        self.apparatus.set_which_path(observing)
        self.add.setEnabled(True)
        self.info.setText(f'Central fringe spacing (small angle): '
            f'{model.wavelength_nm*1e-9*model.screen_distance_m/(model.slit_separation_um*1e-6)*1e3:.3g} mm')
        self.theory.setData(x, y)
        self._stop_firing()
        self.samples = np.empty(0)
        self.screen.set_halfwidth(model.screen_halfwidth_mm)
        self.screen.clear()
        self._render_hist()

    def _add_detections(self):
        if self.model is None: return
        new = self.model.sample_detections(self.batch.value(), which_path=self.which_path.isChecked())
        self.samples = np.concatenate([self.samples, new])
        self._render_hist()

    def _clear(self):
        self._stop_firing()
        self.samples = np.empty(0)
        self.screen.clear()
        self._render_hist()

    SPEEDS = ((3, 40), (40, 30), (0, 0))                  # particles per tick, milliseconds per tick

    def _colour(self, *_):
        from quantumscope.gui.principles_visuals import wavelength_colour
        colour, visible = wavelength_colour(self.wavelength.value())
        self.screen.set_colour(colour)
        self.apparatus.set_colour(colour)
        nm = self.wavelength.value()
        self.colour_note.setText('' if visible else
                                 f'{nm:g} nm is {"ultraviolet" if nm < 380 else "infrared"}: invisible, shown in false colour.')

    def _fire(self):
        """Stream particles onto the screen at the chosen speed (Instant: all at once)."""
        if self.model is None:
            return
        self._stop_firing()
        per_tick, interval = self.SPEEDS[self.speed.currentIndex()]
        self._pending = self.batch.value()
        if per_tick == 0:
            self._stream(everything=True)
            return
        self.stop.setEnabled(True)
        self._timer.start(interval)

    def _stream(self, everything=False):
        per_tick, _ = self.SPEEDS[self.speed.currentIndex()]
        n = self._pending if everything or per_tick == 0 else min(per_tick, self._pending)
        if n <= 0 or self.model is None:
            self._stop_firing()
            return
        new = self.model.sample_detections(n, which_path=self.which_path.isChecked())
        self.samples = np.concatenate([self.samples, new])
        self.screen.add_hits(new)
        self._pending -= n
        self._render_hist()
        if self._pending <= 0:
            self._stop_firing()

    def _stop_firing(self):
        if hasattr(self, '_timer') and self._timer.isActive():
            self._timer.stop()
        if hasattr(self, 'stop'):
            self.stop.setEnabled(False)

    def _render_hist(self):
        if self.model is None: return
        if len(self.samples):
            counts, edges = np.histogram(self.samples, bins=100,
                range=(-self.model.screen_halfwidth_mm, self.model.screen_halfwidth_mm), density=True)
            self.hist.setData((edges[:-1]+edges[1:])/2, counts)
        else:
            self.hist.setData([], [])
        self.status.setText(f'{len(self.samples):,} simulated detections')
        self.apparatus.set_experiment(self.model, self.samples)

    def _export(self):
        if self.model is None: return
        path, _ = QFileDialog.getSaveFileName(self, 'Export double-slit data',
            'quantumscope-double-slit.csv', 'CSV Files (*.csv)')
        if not path: return
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([f'# Which-path detectors: {self.which_path.isChecked()}'])
                writer.writerow(['screen_x_mm', 'probability_density_per_mm',
                                 'simulated_detection_x_mm'])
                length = max(len(self.x), len(self.samples))
                for i in range(length):
                    writer.writerow([self.x[i] if i < len(self.x) else '',
                                     self.y[i] if i < len(self.y) else '',
                                     self.samples[i] if i < len(self.samples) else ''])
        except OSError as exc:
            QMessageBox.warning(self, 'Export failed', str(exc))
