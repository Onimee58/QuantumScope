"""Self-contained hydrogen quantum dynamics experiment for desktop QuantumScope."""
import numpy as np
import pyqtgraph as pg
from pyqtgraph.exporters import ImageExporter
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QComboBox, QSpinBox, QDoubleSpinBox, QSlider, QLabel, QPushButton,
    QWidget, QSplitter, QFileDialog, QMessageBox, QCheckBox)
from quantumscope.physics.hydrogen import HydrogenAtom
from quantumscope.physics.dynamics import HydrogenSuperposition


def density_lut(grayscale=False):
    """Perceptual display mapping only; physical density is never altered."""
    x = np.linspace(0., 1., 256)
    if grayscale:
        return np.repeat(np.rint(255*x)[:, None].astype(np.uint8), 3, axis=1)
    # Approximate viridis anchor colors with linear interpolation.
    knots = np.array([0., .25, .5, .75, 1.])
    colors = np.array([[68,1,84], [59,82,139], [33,145,140], [94,201,98], [253,231,37]])
    return np.stack([np.interp(x, knots, colors[:, i]) for i in range(3)], axis=1).astype(np.uint8)


class HydrogenDynamicsDialog(QDialog):
    """Animates a physical 2D cross-section; never implies a classical trajectory."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("QuantumScope — Hydrogen Dynamics")
        self.resize(1120, 730)
        self.atom = HydrogenAtom()
        self.model = None
        self.time_fraction = 0.0
        self._grid = None
        self._playing = False
        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self._tick)
        root = QVBoxLayout(self)
        split = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(split, 1)
        controls = QWidget()
        controls.setMinimumWidth(365)
        form = QFormLayout(controls)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.a = QComboBox(); self.b = QComboBox()
        states = [(1,0,0), (2,0,0), (2,1,0), (2,1,1), (3,0,0), (3,1,0), (3,2,0)]
        for n,l,m in states:
            title = f"{n}{'spdf'[l]} (m={m})"
            self.a.addItem(title,(n,l,m)); self.b.addItem(title,(n,l,m))
        self.b.setCurrentIndex(2)
        form.addRow("State A", self.a); form.addRow("State B", self.b)
        self.prob = QDoubleSpinBox(); self.prob.setRange(0,100); self.prob.setValue(50)
        self.prob.setSuffix(" %"); self.prob.setSingleStep(5)
        form.addRow("State A probability",self.prob)
        self.phase = QDoubleSpinBox(); self.phase.setRange(-180,180); self.phase.setSuffix(" degrees")
        self.phase.setSingleStep(15)
        form.addRow("Initial relative phase",self.phase)
        self.plane = QComboBox(); self.plane.addItems(["xz","xy","yz"])
        form.addRow("Cross-section plane",self.plane)
        self.extent = QDoubleSpinBox(); self.extent.setRange(5,100); self.extent.setValue(24)
        self.extent.setSuffix(" a_mu"); form.addRow("Half-width",self.extent)
        self.resolution = QSpinBox(); self.resolution.setRange(64,400); self.resolution.setValue(170)
        form.addRow("Grid resolution",self.resolution)
        self.palette = QComboBox()
        self.palette.addItems(["Viridis (density)", "Grayscale (density)"])
        self.palette.currentIndexChanged.connect(self._palette_changed)
        form.addRow("Density colors", self.palette)
        self.info = QLabel("Select two distinct hydrogen states")
        self.info.setWordWrap(True); form.addRow(self.info)
        self.play = QPushButton("Play")
        self.play.clicked.connect(self._toggle)
        form.addRow(self.play)
        self.slider = QSlider(Qt.Orientation.Horizontal); self.slider.setRange(0,1000)
        self.slider.valueChanged.connect(self._seek)
        form.addRow("Time / beat period",self.slider)
        self.time_label = QLabel("t = 0 fs")
        form.addRow(self.time_label)
        self.export = QPushButton("Export frame as PNG")
        self.export.clicked.connect(self._export)
        form.addRow(self.export)
        self.gif_frames = QSpinBox()
        self.gif_frames.setRange(12, 240)
        self.gif_frames.setValue(72)
        form.addRow("GIF frames / period", self.gif_frames)
        self.gif_fps = QSpinBox()
        self.gif_fps.setRange(2, 30)
        self.gif_fps.setValue(12)
        form.addRow("GIF frames per second", self.gif_fps)
        self.export_gif = QPushButton("Export full-period GIF")
        self.export_gif.clicked.connect(self._export_gif)
        form.addRow(self.export_gif)
        self.export_data = QPushButton("Export slice as NPZ")
        self.export_data.clicked.connect(self._export_npz)
        form.addRow(self.export_data)
        self.norm_note = QLabel("2D color is density on a slice, not a 2D probability distribution. "
                                "Normalization refers to the full 3D state.")
        self.norm_note.setWordWrap(True); form.addRow(self.norm_note)
        split.addWidget(controls)
        viewer = QWidget(); vlayout = QVBoxLayout(viewer)
        self.plot = pg.PlotWidget()
        self.plot.setAspectLocked(True)
        self.plot.setBackground('#101820')
        self.plot.setLabel('bottom','First plane coordinate', units='a_mu')
        self.plot.setLabel('left','Second plane coordinate',units='a_mu')
        self.image = pg.ImageItem(axisOrder='row-major')
        self.plot.addItem(self.image)
        vlayout.addWidget(self.plot)
        self.legend = QLabel("Color: |psi|² (a_mu⁻³), common scale throughout animation")
        vlayout.addWidget(self.legend)
        split.addWidget(viewer); split.setChildrenCollapsible(False)
        split.setSizes([415, 705])
        for widget, signal in [(self.a,self.a.currentIndexChanged),
                (self.b,self.b.currentIndexChanged), (self.prob,self.prob.valueChanged),
                (self.phase,self.phase.valueChanged), (self.plane,self.plane.currentIndexChanged),
                (self.extent,self.extent.valueChanged), (self.resolution,self.resolution.valueChanged)]:
            signal.connect(self._rebuild)
        self._palette_changed()
        self._rebuild()

    def _palette_changed(self, *_):
        self._lut = density_lut(self.palette.currentIndex() == 1)
        self.image.setLookupTable(self._lut)
        self._draw()

    def _toggle(self):
        if self.model is None: return
        if self.timer.isActive(): self.timer.stop(); self.play.setText('Play')
        else: self.timer.start(); self.play.setText('Pause')

    def _tick(self):
        self.slider.setValue((self.slider.value() + 8) % 1001)

    def _seek(self, value):
        self.time_fraction = value / 1000
        self._draw()

    def _rebuild(self, *_):
        self.timer.stop(); self.play.setText('Play')
        a = self.a.currentData(); b = self.b.currentData()
        if a == b:
            self.model = None
            self.info.setText('Select TWO DIFFERENT eigenstates.')
            self.image.clear()
            return
        self.model = HydrogenSuperposition(self.atom.state(*a),self.atom.state(*b),
                         self.prob.value()/100,np.deg2rad(self.phase.value()))
        self.axis = np.linspace(-self.extent.value(),self.extent.value(),self.resolution.value())
        x,z = np.meshgrid(self.axis,self.axis,indexing='ij'); zero = np.zeros_like(x)
        plane = self.plane.currentText()
        coords = {'xz':(x,zero,z),'xy':(x,z,zero),'yz':(zero,x,z)}[plane]
        # Cache wavefunctions: animation updates only the exact relative phase.
        self.psi_a = self.model.first.wavefunction(*coords)
        self.psi_b = self.model.second.wavefunction(*coords)
        self._peak = max(float(np.max(np.abs(self.psi_a)**2)),
                         float(np.max(np.abs(self.psi_b)**2))) * 2.5
        self._peak = max(self._peak, 1e-12)
        period = self.model.beat_period_fs
        self.info.setText(f'E(A) = {self.model.first.energy_ev:.5f} eV\n'
                          f'E(B) = {self.model.second.energy_ev:.5f} eV\n'
                          + (f'Beat period: {period:.5f} fs' if np.isfinite(period)
                             else 'Degenerate levels: time-independent density'))
        self._draw()

    def _draw(self):
        if self.model is None: return
        period = self.model.beat_period_fs
        time_fs = self.time_fraction * period if np.isfinite(period) else 0.
        delta = self.model.second.energy_ev - self.model.first.energy_ev
        from scipy import constants
        angle = (-(delta*constants.e*1e-15/constants.hbar)*time_fs
                 + self.model.relative_phase)
        amplitude = (np.sqrt(self.model.probability_first)*self.psi_a
                     + np.sqrt(1-self.model.probability_first)*np.exp(1j*angle)*self.psi_b)
        density = np.abs(amplitude)**2
        # Colors are calibrated against a stable state-independent maximum.
        self.image.setImage(density.T, autoLevels=False, levels=(0,self._peak))
        from PySide6.QtCore import QRectF
        self.image.setRect(QRectF(float(self.axis[0]),float(self.axis[0]),
                                float(self.axis[-1]-self.axis[0]),float(self.axis[-1]-self.axis[0])))
        self.time_label.setText(f't = {time_fs:.5f} fs  ({self.time_fraction:.1%} of period)')
        self.current_density = density

    def _export_gif(self):
        if self.model is None:
            QMessageBox.warning(self, "No state", "Select two different states first.")
            return
        if not np.isfinite(self.model.beat_period_fs):
            QMessageBox.information(self, "No beat period", "These states are degenerate: the density is stationary. Select states with different energies to export one full beat period.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export one complete beat period", "hydrogen_dynamics.gif", "Animated GIF (*.gif)")
        if not path:
            return
        if not path.lower().endswith(".gif"):
            path += ".gif"
        try:
            from PIL import Image, ImageDraw
            from quantumscope.physics.dynamics_export import density_frames
            was_playing = self.timer.isActive()
            self.timer.stop()
            self.play.setText("Play")
            self.export_gif.setEnabled(False)
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            frames = []
            for density in density_frames(self.psi_a, self.psi_b, self.model.probability_first,
                                          self.model.relative_phase, self.gif_frames.value()):
                pixels = np.clip(density.T / self._peak, 0., 1.)
                rgb = self._lut[np.rint(pixels * 255).astype(np.uint8)]
                frame = Image.fromarray(np.flipud(rgb), mode="RGB")
                # Preserve display aspect without needing a live OpenGL framebuffer.
                frame = frame.resize((640, 640), resample=Image.Resampling.BILINEAR)
                frames.append(frame)
            frames[0].save(path, save_all=True, append_images=frames[1:],
                           duration=round(1000 / self.gif_fps.value()), loop=0,
                           optimize=False, disposal=2)
            self.info.setText(self.info.text() + "\nExported GIF: one full beat period")
            if was_playing:
                self.timer.start()
                self.play.setText("Pause")
        except Exception as exc:
            QMessageBox.warning(self, "GIF export error", str(exc))
        finally:
            self.export_gif.setEnabled(True)

    def _export(self):
        path,_ = QFileDialog.getSaveFileName(self,'Export frame','hydrogen_dynamics.png','PNG (*.png)')
        if path:
            try:
                exporter=ImageExporter(self.plot.plotItem)
                exporter.export(path)
            except Exception as exc: QMessageBox.warning(self,'Export error',str(exc))

    def _export_npz(self):
        path,_ = QFileDialog.getSaveFileName(self,'Export slice','hydrogen_dynamics.npz','NumPy (*.npz)')
        if path and self.model is not None:
            try:
                np.savez_compressed(path,axis_a_mu=self.axis,density_a_mu_minus3=self.current_density,
                                   state_a=(self.model.first.n,self.model.first.l,self.model.first.m),
                                   state_b=(self.model.second.n,self.model.second.l,self.model.second.m),
                                   time_fs=(self.time_fraction*self.model.beat_period_fs if np.isfinite(self.model.beat_period_fs) else 0.0),
                                   probability_a=self.model.probability_first,
                                   phase_rad=self.model.relative_phase,plane=self.plane.currentText())
            except Exception as exc: QMessageBox.warning(self,'Export error',str(exc))

    def closeEvent(self,event):
        self.timer.stop()
        super().closeEvent(event)
