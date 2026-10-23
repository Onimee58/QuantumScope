"""Interactive hydrogen superposition volume animation; density is computed from eigenstates."""
from __future__ import annotations
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QScrollArea, QLabel, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QSlider,
    QFileDialog, QMessageBox, QApplication, QSplitter)
from quantumscope.physics.hydrogen import HydrogenAtom
from quantumscope.physics.dynamics import HydrogenSuperposition, suggested_half_width
from quantumscope.gui.controls import Debouncer, with_action, with_quick_values
from quantumscope.gui.dynamics_3d_scene import HydrogenScene3D

STATES = [(1,0,0),(2,0,0),(2,1,0),(2,1,1),(3,0,0),(3,1,0),(3,2,0),(4,0,0),(4,1,0)]


class HydrogenDynamics3DDialog(QDialog):
    """Nonrelativistic two-state dynamics; a visualization, not electron trajectories."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('QuantumScope — Hydrogen Dynamics 3D')
        self.resize(1310, 820)
        self.atom = HydrogenAtom()
        self.model = None
        self._building = True
        self._rebuild_later = Debouncer(self, self._rebuild_now)
        self.timer = QTimer(self)
        self.timer.setInterval(75)
        self.timer.timeout.connect(self._tick)
        outer = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        outer.addWidget(splitter)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(540)
        scroll.setMaximumWidth(650)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        options = QWidget()
        options.setMinimumWidth(520)
        form = QFormLayout(options)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        self.a = QComboBox(); self.b = QComboBox()
        for n,l,m in STATES:
            label=f"{n}{'spdf'[l]} (m={m})"
            self.a.addItem(label,(n,l,m)); self.b.addItem(label,(n,l,m))
        self.b.setCurrentIndex(2)
        form.addRow('State A', self.a); form.addRow('State B', self.b)
        self.prob = QDoubleSpinBox(); self.prob.setRange(0,100); self.prob.setValue(50)
        self.prob.setSuffix(' %'); self.prob.setSingleStep(5)
        form.addRow('State A probability',with_quick_values(self.prob,[('0',0),('25',25),('50',50),('75',75),('100',100)]))
        self.phase = QDoubleSpinBox(); self.phase.setRange(-180,180)
        self.phase.setSuffix(' degrees'); self.phase.setSingleStep(15)
        form.addRow('Initial phase',with_quick_values(self.phase,[('−90°',-90),('0°',0),('90°',90),('180°',180)]))
        self.npoints = QSpinBox(); self.npoints.setRange(48,160); self.npoints.setValue(96)
        self.npoints.setToolTip('Higher values are smoother but slower; Max (160³ ≈ 4 million points) can take seconds to build.')
        form.addRow('3D grid points / axis',with_quick_values(self.npoints,[('Low',64),('Default',96),('High',128),('Max',160)]))
        self.halfwidth = QDoubleSpinBox(); self.halfwidth.setRange(5,100)
        self.halfwidth.setValue(22); self.halfwidth.setSuffix(' a_mu'); self.halfwidth.setSingleStep(1)
        form.addRow('Spatial half-width',with_action(self.halfwidth,'Fit to states',self._fit_extent,
            'Set the half-width so the view holds 99.5% of each state’s probability'))
        self.render_mode = QComboBox()
        self.render_mode.addItems(['GPU volume cloud','Density isosurface'])
        form.addRow('Representation',self.render_mode)
        self.opacity = QDoubleSpinBox(); self.opacity.setRange(.2,4); self.opacity.setValue(1.4)
        self.opacity.setSingleStep(.2)
        form.addRow('Cloud visibility',with_quick_values(self.opacity,[('Faint',.6),('Default',1.4),('Max',4)]))
        self.play = QPushButton('Play'); form.addRow(self.play)
        self.slider = QSlider(Qt.Orientation.Horizontal); self.slider.setRange(0,1000)
        form.addRow('Time / beat period',self.slider)
        self.timelabel = QLabel('t = 0 fs'); form.addRow(self.timelabel)
        self.info = QLabel(''); self.info.setWordWrap(True)
        form.addRow(self.info)
        self.reset_camera = QPushButton('Reset camera')
        self.reset_camera.setToolTip('Return to the standard isometric view, centered and zoomed to fit')
        views = QWidget(); view_row = QHBoxLayout(views); view_row.setContentsMargins(0,0,0,0)
        self.view_buttons = {}
        for label, view, tip in (('Top (xy)','xy','Look down the z axis'),('Front (xz)','xz','Look along the y axis'),
                                 ('Side (yz)','yz','Look along the x axis')):
            button = QPushButton(label); button.setToolTip(tip + '; matches the 2D cross-section of the same name')
            button.clicked.connect(lambda _=False, v=view: self.scene.reset_view(v))
            view_row.addWidget(button); self.view_buttons[view] = button
        form.addRow(self.reset_camera); form.addRow('Views', views)
        self.export_png = QPushButton('Export 3D frame (PNG)'); form.addRow(self.export_png)
        self.gif_frames = QSpinBox(); self.gif_frames.setRange(12,120); self.gif_frames.setValue(48)
        form.addRow('Frames / GIF period',with_quick_values(self.gif_frames,[('Min',12),('Max',120)]))
        self.gif_fps = QSpinBox(); self.gif_fps.setRange(2,30); self.gif_fps.setValue(12)
        form.addRow('GIF frames / second',with_quick_values(self.gif_fps,[('Min',2),('Max',30)]))
        self.export_gif = QPushButton('Export 3D GIF (fixed camera)'); form.addRow(self.export_gif)
        self.note = QLabel('3D density comes from an exact coherent superposition of isolated hydrogen eigenstates. '
            'The rendering transform changes appearance, not probability. Export uses one beat period; '
            'GIF projection is 2D and retains the current 3D camera angle.')
        self.note.setWordWrap(True); form.addRow(self.note)
        scroll.setWidget(options)
        splitter.addWidget(scroll)
        self.plotter = QtInteractor(self)
        self.plotter.set_background('#101820')
        self.scene = HydrogenScene3D(self.plotter)
        splitter.addWidget(self.plotter)
        splitter.setStretchFactor(0,0); splitter.setStretchFactor(1,1)
        splitter.setSizes([560,750])
        self.play.clicked.connect(self._toggle)
        self.slider.valueChanged.connect(self._draw)
        # clicked() passes a 'checked' flag; calling reset_camera with it skipped the redraw.
        self.reset_camera.clicked.connect(lambda _=False: self.scene.reset_view('isometric'))
        self.export_png.clicked.connect(self._export_png)
        self.export_gif.clicked.connect(self._export_gif)
        for w,signal in ((self.a,self.a.currentIndexChanged),(self.b,self.b.currentIndexChanged),
             (self.prob,self.prob.valueChanged),(self.phase,self.phase.valueChanged),
             (self.npoints,self.npoints.valueChanged),(self.halfwidth,self.halfwidth.valueChanged)):
            signal.connect(self._rebuild)
        # Appearance only: redraw the same densities without re-sampling the grid.
        self.render_mode.currentIndexChanged.connect(self._draw)
        self.opacity.valueChanged.connect(self._draw)
        self._building = False
        self._rebuild_now()

    def _rebuild(self,*_):
        """Coalesce rapid changes (arrow keys, quick buttons) into one rebuild."""
        if self._building: return
        self._rebuild_later()

    def _rebuild_now(self):
        if self._building: return
        self.timer.stop(); self.play.setText('Play')
        a,b = self.a.currentData(),self.b.currentData()
        if a==b:
            self.model=None; self.info.setText('Select two different eigenstates.')
            self.scene.clear(); return
        self.model = HydrogenSuperposition(self.atom.state(*a),self.atom.state(*b),
                       self.prob.value()/100, np.deg2rad(self.phase.value()))
        n=self.npoints.value()
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self.scene.set_model(self.model, n, self.halfwidth.value())
        finally:
            QApplication.restoreOverrideCursor()
        self._draw()
        period=self.model.beat_period_fs
        fit=suggested_half_width([self.model.first,self.model.second])
        clipped=' The view clips part of the states: try Fit to states.' if self.halfwidth.value()<fit-1e-9 else ''
        self.info.setText((f'Beat period: {period:.6f} fs' if np.isfinite(period)
            else 'Degenerate levels: stationary density (no finite beat period)')
            + f'\n3D grid: {n}³; active renderer: OpenGL / VTK' + clipped)

    def _fit_extent(self):
        a,b = self.a.currentData(),self.b.currentData()
        self.halfwidth.setValue(suggested_half_width([self.atom.state(*a),self.atom.state(*b)]))

    def _draw(self,*_):
        if self.model is None: return
        fraction=self.slider.value()/1000
        self.scene.draw(fraction,'volume' if self.render_mode.currentIndex()==0 else 'surface',self.opacity.value())
        period=self.model.beat_period_fs
        t=period*fraction if np.isfinite(period) else 0.0
        self.timelabel.setText(f't = {t:.5f} fs ({fraction:.1%} of beat period)')

    def _tick(self):
        self.slider.setValue((self.slider.value()+10)%1001)

    def _toggle(self):
        if self.model is None: return
        if self.timer.isActive(): self.timer.stop(); self.play.setText('Play')
        else: self.timer.start(); self.play.setText('Pause')

    def _export_png(self):
        path,_=QFileDialog.getSaveFileName(self,'Export 3D view','hydrogen_3d.png','PNG (*.png)')
        if path:
            try: self.plotter.screenshot(path)
            except Exception as exc: QMessageBox.warning(self,'PNG export error',str(exc))

    def _export_gif(self):
        if self.model is None or not np.isfinite(self.model.beat_period_fs):
            QMessageBox.information(self,'No beat period','Select states with different energies.')
            return
        path,_=QFileDialog.getSaveFileName(self,'Export 3D GIF','hydrogen_3d.gif','GIF (*.gif)')
        if not path: return
        if not path.lower().endswith('.gif'): path+='.gif'
        self.timer.stop(); self.play.setText('Play')
        self.export_gif.setEnabled(False)
        old=self.slider.value()
        try:
            from PIL import Image
            frames=[]
            n=self.gif_frames.value()
            for k in range(n):
                self.slider.setValue(round(1000*k/n))
                QApplication.processEvents()
                rgb=self.plotter.screenshot(return_img=True)
                frames.append(Image.fromarray(np.asarray(rgb,dtype=np.uint8)[:,:,:3]).convert('RGB'))
            frames[0].save(path,save_all=True,append_images=frames[1:],loop=0,
                           duration=round(1000/self.gif_fps.value()))
        except Exception as exc:
            QMessageBox.warning(self,'GIF export error',str(exc))
        finally:
            self.slider.setValue(old)
            self.export_gif.setEnabled(True)

    def closeEvent(self,event):
        self.timer.stop()
        self.plotter.close()
        super().closeEvent(event)
