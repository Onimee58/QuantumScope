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
            'Fraunhofer far-field approximation • coherent, equal slits • idealized independent detections. '
            'Not a real-time particle trajectory simulation.')
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
        self.batch = QSpinBox(); self.batch.setRange(1, 5000); self.batch.setValue(250)
        form.addRow('Detections / batch', self.batch)
        self.which_path = QCheckBox('Which-path detectors at the slits')
        self.which_path.setToolTip('Ideal path information destroys two-slit interference; does not trace trajectories.')
        self.which_path.toggled.connect(self._update)
        form.addRow('Observation', self.which_path)
        self.path_note = QLabel('OFF: path information unavailable; interference fringes.')
        self.path_note.setWordWrap(True)
        form.addRow(self.path_note)
        self.add = QPushButton('Detect particles (+batch)')
        self.add.clicked.connect(self._add_detections); form.addRow(self.add)
        self.reset = QPushButton('Clear detections')
        self.reset.clicked.connect(self._clear); form.addRow(self.reset)
        self.export = QPushButton('Export probability and detections (CSV)')
        self.export.clicked.connect(self._export); form.addRow(self.export)
        self.info = QLabel(''); self.info.setWordWrap(True); form.addRow(self.info)
        self.note = QLabel('Curves represent probability density per mm, normalized over the '
            'selected screen width. The histogram is estimated from simulated detections, '
            'not a second theoretical distribution. All angles use the paraxial approximation.')
        self.note.setWordWrap(True); form.addRow(self.note)
        split.addWidget(left)
        right = QWidget(); rlayout = QVBoxLayout(right)
        self.apparatus = DoubleSlitApparatus()
        rlayout.addWidget(self.apparatus, 2)
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
        split.setChildrenCollapsible(False); split.setSizes([440, 760])
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
        self.samples = np.empty(0)
        self._render_hist()

    def _add_detections(self):
        if self.model is None: return
        new = self.model.sample_detections(self.batch.value(), which_path=self.which_path.isChecked())
        self.samples = np.concatenate([self.samples, new])
        self._render_hist()

    def _clear(self):
        self.samples = np.empty(0)
        self._render_hist()

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
