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
from quantumscope.physics.dynamics import HydrogenSuperposition

STATES = [(1,0,0),(2,0,0),(2,1,0),(2,1,1),(3,0,0),(3,1,0),(3,2,0),(4,0,0),(4,1,0)]


class HydrogenDynamics3DDialog(QDialog):
    """Nonrelativistic two-state dynamics; a visualization, not electron trajectories."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('QuantumScope — Hydrogen Dynamics 3D (v0.2.0)')
        self.resize(1310, 820)
        self.atom = HydrogenAtom()
        self.model = None
        self._building = True
        self._grid = None
        self.timer = QTimer(self)
        self.timer.setInterval(75)
        self.timer.timeout.connect(self._tick)
        outer = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        outer.addWidget(splitter)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(420)
        scroll.setMaximumWidth(650)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        options = QWidget()
        options.setMinimumWidth(410)
        form = QFormLayout(options)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.a = QComboBox(); self.b = QComboBox()
        for n,l,m in STATES:
            label=f"{n}{'spdf'[l]} (m={m})"
            self.a.addItem(label,(n,l,m)); self.b.addItem(label,(n,l,m))
        self.b.setCurrentIndex(2)
        form.addRow('State A', self.a); form.addRow('State B', self.b)
        self.prob = QDoubleSpinBox(); self.prob.setRange(0,100); self.prob.setValue(50)
        self.prob.setSuffix(' %'); form.addRow('State A probability',self.prob)
        self.phase = QDoubleSpinBox(); self.phase.setRange(-180,180)
        self.phase.setSuffix(' degrees'); form.addRow('Initial phase',self.phase)
        self.npoints = QSpinBox(); self.npoints.setRange(48,160); self.npoints.setValue(96)
        form.addRow('3D grid points / axis',self.npoints)
        self.halfwidth = QDoubleSpinBox(); self.halfwidth.setRange(5,100)
        self.halfwidth.setValue(22); self.halfwidth.setSuffix(' a_mu')
        form.addRow('Spatial half-width',self.halfwidth)
        self.render_mode = QComboBox()
        self.render_mode.addItems(['GPU volume cloud','Density isosurface'])
        form.addRow('Representation',self.render_mode)
        self.opacity = QDoubleSpinBox(); self.opacity.setRange(.2,4); self.opacity.setValue(1.4)
        self.opacity.setSingleStep(.2); form.addRow('Cloud visibility',self.opacity)
        self.play = QPushButton('Play'); form.addRow(self.play)
        self.slider = QSlider(Qt.Orientation.Horizontal); self.slider.setRange(0,1000)
        form.addRow('Time / beat period',self.slider)
        self.timelabel = QLabel('t = 0 fs'); form.addRow(self.timelabel)
        self.info = QLabel(''); self.info.setWordWrap(True)
        form.addRow(self.info)
        self.reset_camera = QPushButton('Reset camera'); form.addRow(self.reset_camera)
        self.export_png = QPushButton('Export 3D frame (PNG)'); form.addRow(self.export_png)
        self.gif_frames = QSpinBox(); self.gif_frames.setRange(12,120); self.gif_frames.setValue(48)
        form.addRow('Frames / GIF period',self.gif_frames)
        self.gif_fps = QSpinBox(); self.gif_fps.setRange(2,30); self.gif_fps.setValue(12)
        form.addRow('GIF frames / second',self.gif_fps)
        self.export_gif = QPushButton('Export 3D GIF (fixed camera)'); form.addRow(self.export_gif)
        self.note = QLabel('3D density comes from an exact coherent superposition of isolated hydrogen eigenstates. '
            'The rendering transform changes appearance, not probability. Export uses one beat period; '
            'GIF projection is 2D and retains the current 3D camera angle.')
        self.note.setWordWrap(True); form.addRow(self.note)
        scroll.setWidget(options)
        splitter.addWidget(scroll)
        self.plotter = QtInteractor(self)
        self.plotter.set_background('#101820')
        splitter.addWidget(self.plotter)
        splitter.setStretchFactor(0,0); splitter.setStretchFactor(1,1)
        splitter.setSizes([460,850])
        self.play.clicked.connect(self._toggle)
        self.slider.valueChanged.connect(self._draw)
        self.reset_camera.clicked.connect(self.plotter.reset_camera)
        self.export_png.clicked.connect(self._export_png)
        self.export_gif.clicked.connect(self._export_gif)
        for w,signal in ((self.a,self.a.currentIndexChanged),(self.b,self.b.currentIndexChanged),
             (self.prob,self.prob.valueChanged),(self.phase,self.phase.valueChanged),
             (self.npoints,self.npoints.valueChanged),(self.halfwidth,self.halfwidth.valueChanged),
             (self.render_mode,self.render_mode.currentIndexChanged),(self.opacity,self.opacity.valueChanged)):
            signal.connect(self._rebuild)
        self._building = False
        self._rebuild()

    def _rebuild(self,*_):
        if self._building: return
        self.timer.stop(); self.play.setText('Play')
        a,b = self.a.currentData(),self.b.currentData()
        if a==b:
            self.model=None; self.info.setText('Select two different eigenstates.')
            self.plotter.clear(); return
        self.model = HydrogenSuperposition(self.atom.state(*a),self.atom.state(*b),
                       self.prob.value()/100, np.deg2rad(self.phase.value()))
        n=self.npoints.value(); extent=self.halfwidth.value()
        axis=np.linspace(-extent,extent,n)
        x,y,z=np.meshgrid(axis,axis,axis,indexing='ij',sparse=True)
        # Cache eigenstates once; only the interference term changes during playback.
        psi_a=np.asarray(self.model.first.wavefunction(x,y,z),dtype=np.complex64)
        psi_b=np.asarray(self.model.second.wavefunction(x,y,z),dtype=np.complex64)
        shape=(n,n,n)
        self._aa=np.broadcast_to(np.abs(psi_a)**2,shape).astype(np.float32).copy()
        self._bb=np.broadcast_to(np.abs(psi_b)**2,shape).astype(np.float32).copy()
        self._cross=np.broadcast_to(np.conjugate(psi_a)*psi_b,shape).astype(np.complex64).copy()
        self._peak=float(max(np.max(self._aa),np.max(self._bb))*2.5)
        self._peak=max(self._peak,1e-12)
        self._grid=pv.ImageData(dimensions=(n,n,n),spacing=(axis[1]-axis[0],)*3,
                                origin=(axis[0],)*3)
        self._grid.point_data['density']=np.zeros(n**3,dtype=np.float32)
        self._draw(preserve_camera=False)
        period=self.model.beat_period_fs
        self.info.setText((f'Beat period: {period:.6f} fs' if np.isfinite(period)
            else 'Degenerate levels: stationary density (no finite beat period)')
            + f'\n3D grid: {n}³; active renderer: OpenGL / VTK')

    def _frame_density(self, fraction):
        p=self.model.probability_first
        theta=self.model.relative_phase-2*np.pi*fraction if np.isfinite(self.model.beat_period_fs) else self.model.relative_phase
        return (p*self._aa+(1-p)*self._bb+2*np.sqrt(p*(1-p))*np.real(np.exp(1j*theta)*self._cross)).clip(0).astype(np.float32)

    def _draw(self,*_,preserve_camera=True):
        if self.model is None or self._grid is None: return
        fraction=self.slider.value()/1000
        density=self._frame_density(fraction)
        self._grid.point_data['density']=density.ravel(order='F')
        camera=self.plotter.camera_position if preserve_camera and self.plotter.renderer.actors else None
        self.plotter.clear()
        if self.render_mode.currentIndex()==0:
            # Scalar values are true density; nonlinear visual transfer is display-only.
            display=(density/max(self._peak,1e-12))**(0.60 / self.opacity.value())
            self._grid.point_data['intensity']=display.astype(np.float32).ravel(order='F')
            self.plotter.add_volume(self._grid,scalars='intensity',cmap='viridis',
                clim=(0,1),opacity='sigmoid',mapper='smart',show_scalar_bar=False)
        else:
            cutoff=float(np.quantile(density[density>0],.75)) if np.any(density>0) else 1e-12
            mesh=self._grid.contour([cutoff],scalars='density')
            if mesh.n_points:
                self.plotter.add_mesh(mesh, color='#4eb5d6',smooth_shading=True,
                    opacity=min(.95,.50+.12*self.opacity.value()))
        self.plotter.add_axes()
        if camera is not None: self.plotter.camera_position=camera
        else: self.plotter.reset_camera()
        period=self.model.beat_period_fs
        t=period*fraction if np.isfinite(period) else 0.0
        self.timelabel.setText(f't = {t:.5f} fs ({fraction:.1%} of beat period)')
        self.plotter.render()

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
