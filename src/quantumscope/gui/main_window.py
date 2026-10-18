"""QuantumScope Hydrogen Explorer Qt desktop UI."""
from pathlib import Path
import traceback
import os
import subprocess
import sys

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, QSettings, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap, QPainter, QPen, QColor
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPushButton, QScrollArea, QSpinBox, QDoubleSpinBox,
    QSplitter, QVBoxLayout, QWidget, QFileDialog, QDialog, QDialogButtonBox, QFrame, QInputDialog,
)
from pyvistaqt import QtInteractor
from quantumscope import __version__
from quantumscope.physics import HydrogenAtom, density_grid
from quantumscope.physics.hydrogen import A_MU_METERS, captured_probability, RealHydrogenState
from quantumscope.visualization.orbitals import draw_orbital, set_camera_view, probability_radius


class AboutDialog(QDialog):
    """GlassBalance-inspired QuantumScope project and developer dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About QuantumScope")
        self.setModal(True)
        self.setMinimumSize(380, 545)
        self.resize(400, 575)
        self.settings = QSettings("QuantumScope", "QuantumScope")
        self.setStyleSheet("""
            QDialog { background: #15263b; color: #f0f6ff; }
            QLabel { color: #e6efff; }
            QLabel#secondary { color: #adc4df; }
            QPushButton { background: #223a55; color: #f2f7ff;
                border: 1px solid #34516d; border-radius: 7px;
                padding: 9px 12px; min-height: 19px; font-weight: 600; }
            QPushButton:hover { background: #2b4b6d; }
            QPushButton:disabled { color: #8796a8; }
            QFrame#divider { background: #344b65; max-height: 1px; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 16, 14, 15)
        layout.setSpacing(9)

        self.photo = QLabel()
        self.photo.setFixedSize(78, 78)
        self.photo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo.setStyleSheet("background:#233d58; border-radius:7px; color:#b6cce5;")
        layout.addWidget(self.photo, alignment=Qt.AlignmentFlag.AlignHCenter)
        self._load_profile()

        photo_button = QPushButton("Change profile picture (local)")
        photo_button.clicked.connect(self._choose_photo)
        layout.addWidget(photo_button)

        logo = QLabel()
        logo.setFixedSize(58, 58)
        logo.setPixmap(self._make_logo())
        layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignHCenter)

        title = QLabel(f"QuantumScope v{__version__}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: 700;")
        layout.addWidget(title)

        for value in (
            "Hydrogen Explorer · Open-source quantum visualization",
            "Created and maintained by Md. Saif Hassan Onim, PhD",
            "Scientific visualization of the nonrelativistic hydrogen atom",
        ):
            label = QLabel(value)
            label.setObjectName("secondary")
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)

        website = QLabel('<a href="https://people.smu.edu/monim" style="color:#76d6ce;">Developer website ↗</a>')
        website.setTextFormat(Qt.TextFormat.RichText)
        website.setOpenExternalLinks(True)
        website.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(website)

        self.repo_button = QPushButton("GitHub project ↗")
        self.repo_button.clicked.connect(self._open_repo)
        layout.addWidget(self.repo_button)
        set_repo = QPushButton("Set GitHub repository URL")
        set_repo.clicked.connect(self._set_repo)
        layout.addWidget(set_repo)
        self._update_repo_button()

        rule = QFrame()
        rule.setObjectName("divider")
        layout.addWidget(rule)

        details = QLabel("Built with Python · PySide6 · PyVista · VTK · NumPy · SciPy\n"
                         "License: MIT · Scientific model: reduced-mass hydrogen")
        details.setObjectName("secondary")
        details.setWordWrap(True)
        details.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(details)
        layout.addStretch(1)

        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        layout.addWidget(close)

    def _load_profile(self):
        path = self.settings.value("about/profile_picture", "", type=str)
        pixmap = QPixmap(path) if path else QPixmap()
        if pixmap.isNull():
            self.photo.setText("Your photo")
            self.photo.setPixmap(QPixmap())
        else:
            self.photo.setText("")
            self.photo.setPixmap(pixmap.scaled(78, 78,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))

    def _choose_photo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select profile picture", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if not path:
            return
        image = QPixmap(path)
        if image.isNull():
            QMessageBox.warning(self, "Invalid image", "Could not open the selected image.")
            return
        # Store a local copy so the profile remains available even if the source moves.
        from PySide6.QtCore import QStandardPaths
        directory = Path(QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppConfigLocation)) / "QuantumScope"
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / "profile.png"
        if not image.save(str(destination), "PNG"):
            QMessageBox.warning(self, "Save failed", "Could not save the profile picture.")
            return
        self.settings.setValue("about/profile_picture", str(destination))
        self._load_profile()

    def _make_logo(self):
        picture = QPixmap(58, 58)
        picture.fill(Qt.GlobalColor.transparent)
        painter = QPainter(picture)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#45c5cf"), 2.0))
        for angle in (-55, 5, 65):
            painter.save()
            painter.translate(29, 29)
            painter.rotate(angle)
            painter.drawEllipse(-23, -10, 46, 20)
            painter.restore()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#ffc86c"))
        painter.drawEllipse(24, 24, 10, 10)
        painter.end()
        return picture

    def _repo_url(self):
        return self.settings.value("about/repository_url", "", type=str).strip()

    def _update_repo_button(self):
        url = QUrl(self._repo_url())
        valid = url.isValid() and url.scheme() == "https" and url.host().lower() == "github.com" and bool(url.path().strip("/"))
        self.repo_button.setEnabled(valid)
        self.repo_button.setToolTip("Configure the repository URL first" if not valid else self._repo_url())

    def _set_repo(self):
        value, ok = QInputDialog.getText(self, "GitHub repository", "Repository URL:",
                                         text=self._repo_url())
        if not ok:
            return
        url = QUrl(value.strip())
        if value.strip() and not (url.isValid() and url.scheme() == "https" and
                                   url.host().lower() == "github.com" and
                                   len(url.path().strip("/").split("/")) >= 2):
            QMessageBox.warning(self, "Invalid URL", "Enter a GitHub repository URL such as https://github.com/user/QuantumScope")
            return
        self.settings.setValue("about/repository_url", value.strip())
        self._update_repo_button()

    def _open_repo(self):
        if self.repo_button.isEnabled():
            QDesktopServices.openUrl(QUrl(self._repo_url()))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"QuantumScope {__version__} — Hydrogen Explorer")
        self.resize(1420, 920)
        self.atom = HydrogenAtom()
        self.axis = self.density = self.psi = self.state = None
        self.compare_axis = self.compare_density = self.compare_psi = self.compare_state = None
        # Signals from dependent quantum-number controls may fire during UI construction.
        # Do not render until all widgets and plotters have been initialized.
        self._ui_ready = False
        self._build_ui()
        self._ui_ready = True
        self._build_menu()
        self.refresh()

    def _build_menu(self):
        help_menu = self.menuBar().addMenu("&Help")
        about_action = help_menu.addAction("&About QuantumScope")
        about_action.triggered.connect(self.show_about)

    def show_about(self):
        AboutDialog(self).exec()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter, stretch=4)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(265)
        scroll.setMaximumWidth(420)
        options = QWidget()
        controls = QVBoxLayout(options)
        controls.setAlignment(Qt.AlignmentFlag.AlignTop)
        controls.setSpacing(10)

        state_box = QGroupBox("Hydrogen quantum state")
        state_form = QFormLayout(state_box)
        self.n = QSpinBox()
        self.n.setRange(1, 4)
        self.l = QComboBox()
        self.m = QComboBox()
        self.n.valueChanged.connect(self._update_l)
        self.l.currentIndexChanged.connect(self._update_m)
        state_form.addRow("Principal n", self.n)
        state_form.addRow("Angular l", self.l)
        state_form.addRow("Magnetic m", self.m)
        self.basis = QComboBox()
        self.basis.addItems(["Complex Y(l,m)", "Real cosine", "Real sine"])
        state_form.addRow("Orbital basis", self.basis)
        controls.addWidget(state_box)

        compare_box = QGroupBox("Side-by-side comparison")
        compare_form = QFormLayout(compare_box)
        self.compare_enable = QCheckBox("Enable second 3D viewer")
        self.compare_n = QSpinBox()
        self.compare_n.setRange(1, 4)
        self.compare_n.setValue(2)
        self.compare_l = QComboBox()
        self.compare_m = QComboBox()
        self.compare_basis = QComboBox()
        self.compare_basis.addItems(["Complex Y(l,m)", "Real cosine", "Real sine"])
        self.compare_n.valueChanged.connect(lambda: self._update_compare_l())
        self.compare_l.currentIndexChanged.connect(lambda: self._update_compare_m())
        compare_form.addRow(self.compare_enable)
        compare_form.addRow("Compare n", self.compare_n)
        compare_form.addRow("Compare l", self.compare_l)
        compare_form.addRow("Compare m", self.compare_m)
        compare_form.addRow("Compare basis", self.compare_basis)
        controls.addWidget(compare_box)
        self._update_compare_l()

        view_box = QGroupBox("Visualization")
        vf = QFormLayout(view_box)
        self.mode = QComboBox()
        self.mode.addItems(["Density cloud", "Probability enclosure", "Real(psi)", "Imag(psi)"])
        self.resolution = QSpinBox()
        self.resolution.setRange(32, 160)
        self.resolution.setSingleStep(8)
        self.resolution.setValue(96)
        self.enclosed = QSpinBox()
        self.enclosed.setRange(50, 99)
        self.enclosed.setValue(90)
        self.enclosed.setSuffix("%")
        self.opacity = QDoubleSpinBox()
        self.opacity.setRange(0.2, 4.0)
        self.opacity.setSingleStep(0.2)
        self.opacity.setValue(1.4)
        vf.addRow("Representation", self.mode)
        vf.addRow("Grid points/axis", self.resolution)
        vf.addRow("Enclosed probability", self.enclosed)
        vf.addRow("Cloud visibility", self.opacity)
        controls.addWidget(view_box)

        graphics_box = QGroupBox("Graphics")
        gf = QFormLayout(graphics_box)
        self.renderer = QComboBox()
        self.renderer.addItems(["Auto (GPU preferred)", "GPU", "CPU"])
        gf.addRow("Volume rendering method", self.renderer)
        note = QLabel("This selects the VTK density-cloud mapper, NOT the physical GPU. "
                      "The active Intel/NVIDIA graphics device is selected at application startup. "
                      "Surface rendering is independent of this setting.")
        note.setWordWrap(True)
        gf.addRow(note)
        controls.addWidget(graphics_box)

        camera_box = QGroupBox("Camera & scientific display")
        cf = QFormLayout(camera_box)
        self.camera_view = QComboBox()
        self.camera_view.addItems(["Perspective", "+X", "+Y", "+Z"])
        self.zoom_factor = QDoubleSpinBox()
        self.zoom_factor.setRange(0.5, 5.0)
        self.zoom_factor.setSingleStep(0.25)
        self.zoom_factor.setValue(1.3)
        self.phase_color = QCheckBox("Color enclosure by wavefunction phase")
        self.show_grid = QCheckBox("Show axes and coordinates (a_mu)")
        cf.addRow("View", self.camera_view)
        cf.addRow("Magnification", self.zoom_factor)
        cf.addRow(self.phase_color)
        cf.addRow(self.show_grid)
        controls.addWidget(camera_box)
        self.camera_view.currentIndexChanged.connect(self._change_camera)
        self.zoom_factor.valueChanged.connect(self._change_camera)

        diagnostic_box = QGroupBox("Graphics diagnostics")
        df = QVBoxLayout(diagnostic_box)
        self.gpu_diagnostics = QLabel("OpenGL context information pending")
        self.gpu_diagnostics.setWordWrap(True)
        self.gpu_diagnostics.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        df.addWidget(self.gpu_diagnostics)
        inspect_button = QPushButton("Refresh renderer information")
        inspect_button.clicked.connect(self._update_gpu_diagnostics)
        df.addWidget(inspect_button)
        if sys.platform.startswith("linux"):
            restart_gpu = QPushButton("Restart using NVIDIA (Linux)")
            restart_gpu.setToolTip("Restart using XCB/GLX and NVIDIA PRIME offloading")
            restart_gpu.clicked.connect(self._restart_on_nvidia)
            df.addWidget(restart_gpu)
        controls.addWidget(diagnostic_box)

        self.export_scale = QSpinBox()
        self.export_scale.setRange(1, 4)
        self.export_scale.setValue(2)
        controls.addWidget(QLabel("PNG export scale (1–4×)"))
        controls.addWidget(self.export_scale)
        self.auto_render = QCheckBox("Update when changing state/mode")
        controls.addWidget(self.auto_render)
        render_btn = QPushButton("Render state")
        render_btn.clicked.connect(self.refresh)
        controls.addWidget(render_btn)
        reset_btn = QPushButton("Reset camera")
        reset_btn.clicked.connect(self._reset_camera)
        controls.addWidget(reset_btn)
        screenshot_btn = QPushButton("Export PNG")
        screenshot_btn.clicked.connect(self.export_png)
        controls.addWidget(screenshot_btn)
        data_btn = QPushButton("Export grid (.npz)")
        data_btn.clicked.connect(self.export_grid)
        controls.addWidget(data_btn)

        details_box = QGroupBox("Scientific information")
        detail_layout = QVBoxLayout(details_box)
        self.details = QLabel()
        self.details.setWordWrap(True)
        self.details.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        detail_layout.addWidget(self.details)
        controls.addWidget(details_box)
        controls.addStretch()
        scroll.setWidget(options)
        splitter.addWidget(scroll)

        self.viewer_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.plotter = QtInteractor(central)
        self.viewer_splitter.addWidget(self.plotter)
        self.compare_plotter = QtInteractor(central)
        self.viewer_splitter.addWidget(self.compare_plotter)
        self.compare_plotter.hide()
        # Make the left sidebar span the full content height.
        # The compact radial plot belongs below the 3D viewers on the RIGHT only.
        viewer_column = QWidget()
        viewer_layout = QVBoxLayout(viewer_column)
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.setSpacing(6)
        viewer_layout.addWidget(self.viewer_splitter, stretch=1)
        splitter.addWidget(viewer_column)
        splitter.setSizes([330, 1070])

        bottom = QGroupBox("Radial probability  P(r) = r² |Rₙₗ(r)|²")
        blayout = QVBoxLayout(bottom)
        self.radial_plot = pg.PlotWidget()
        self.radial_plot.setBackground("#101820")
        self.radial_plot.setLabel("bottom", "r", units="a_mu")
        self.radial_plot.setLabel("left", "P(r)", units="a_mu^-1")
        self.radial_plot.showGrid(x=True, y=True, alpha=0.2)
        self.radial_plot.setMinimumHeight(95)
        blayout.addWidget(self.radial_plot)
        bottom.setMinimumHeight(125)
        bottom.setMaximumHeight(178)
        viewer_layout.addWidget(bottom, stretch=0)
        self.statusBar().showMessage("Nonrelativistic isolated hydrogen • reduced-mass Coulomb model")
        self._update_l()
        for ctrl in (self.basis, self.compare_enable, self.compare_n, self.compare_l,
                     self.compare_m, self.compare_basis):
            signal = (ctrl.stateChanged if isinstance(ctrl, QCheckBox) else
                      ctrl.valueChanged if isinstance(ctrl, QSpinBox) else ctrl.currentIndexChanged)
            signal.connect(self._auto_refresh)
        for ctrl, signal in ((self.n, self.n.valueChanged),
                             (self.l, self.l.currentIndexChanged),
                             (self.m, self.m.currentIndexChanged),
                             (self.mode, self.mode.currentIndexChanged),
                             (self.resolution, self.resolution.valueChanged),
                             (self.enclosed, self.enclosed.valueChanged),
                             (self.opacity, self.opacity.valueChanged),
                             (self.renderer, self.renderer.currentIndexChanged),
                             (self.phase_color, self.phase_color.stateChanged),
                             (self.show_grid, self.show_grid.stateChanged)):
            signal.connect(self._auto_refresh)

    def _update_compare_l(self):
        old = self.compare_l.currentData()
        self.compare_l.blockSignals(True)
        self.compare_l.clear()
        for l in range(self.compare_n.value()):
            self.compare_l.addItem(str(l), l)
        self.compare_l.setCurrentIndex(min(old if old is not None else 0,
                                           self.compare_n.value()-1))
        self.compare_l.blockSignals(False)
        self._update_compare_m()

    def _update_compare_m(self):
        l = self.compare_l.currentData()
        if l is None:
            return
        old = self.compare_m.currentData()
        self.compare_m.blockSignals(True)
        self.compare_m.clear()
        for m in range(-l, l + 1):
            self.compare_m.addItem(str(m), m)
        self.compare_m.setCurrentIndex((old if old is not None and abs(old) <= l else 0)+l)
        self.compare_m.blockSignals(False)
        self._auto_refresh()

    def _make_state(self, n, l, m, basis):
        if basis == "Complex Y(l,m)":
            return self.atom.state(n, l, m)
        order = abs(m)
        kind = "sin" if basis == "Real sine" and order else "cos"
        return RealHydrogenState(n, l, order, kind)

    def _auto_refresh(self, *_):
        if not self._ui_ready:
            return
        if self.auto_render.isChecked():
            self.refresh()

    def _update_l(self):
        prev = self.l.currentData()
        self.l.blockSignals(True)
        self.l.clear()
        for l in range(self.n.value()):
            self.l.addItem(str(l), l)
        self.l.setCurrentIndex(min(prev if prev is not None else 0, self.n.value() - 1))
        self.l.blockSignals(False)
        self._update_m()

    def _update_m(self):
        l = self.l.currentData()
        if l is None:
            return
        old = self.m.currentData()
        self.m.blockSignals(True)
        self.m.clear()
        for m in range(-l, l + 1):
            self.m.addItem(str(m), m)
        self.m.setCurrentIndex((old if old is not None and abs(old) <= l else 0) + l)
        self.m.blockSignals(False)
        self._auto_refresh()

    def _change_camera(self, *_):
        if self.density is None:
            return
        set_camera_view(self.plotter, probability_radius(self.axis, self.density),
                        self.camera_view.currentText(), self.zoom_factor.value())
        self.plotter.render()
        if self.compare_enable.isChecked() and self.compare_density is not None:
            set_camera_view(self.compare_plotter,
                            probability_radius(self.compare_axis, self.compare_density),
                            self.camera_view.currentText(), self.zoom_factor.value())
            self.compare_plotter.render()

    def _restart_on_nvidia(self):
        """GPU selection is process-wide: a new Qt/OpenGL context is required."""
        if not sys.platform.startswith("linux"):
            return
        choice = QMessageBox.question(
            self, "Restart on NVIDIA",
            "This closes QuantumScope and restarts it with NVIDIA PRIME offloading.\n"
            "Unsaved visualization settings will be reset. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if choice != QMessageBox.StandardButton.Yes:
            return
        env = os.environ.copy()
        env.update({"QT_QPA_PLATFORM": "xcb", "QT_XCB_GL_INTEGRATION": "xcb_glx",
                    "__NV_PRIME_RENDER_OFFLOAD": "1", "__GLX_VENDOR_LIBRARY_NAME": "nvidia"})
        # Use the current interpreter (source installation) or executable (packaged build).
        command = [sys.executable] if getattr(sys, "frozen", False) else [sys.executable, "-m", "quantumscope"]
        try:
            subprocess.Popen(command, env=env, start_new_session=True,
                             cwd=str(Path.home()), close_fds=True)
        except OSError as exc:
            QMessageBox.warning(self, "NVIDIA launch failed", str(exc))
            return
        self.close()

    def _update_gpu_diagnostics(self):
        """Query the *current VTK GL context*; environment hints aren't proof."""
        try:
            window = self.plotter.render_window
            window.MakeCurrent()
            info = window.ReportCapabilities()
            if not info:
                info = "VTK did not report OpenGL capabilities for this context."
            lines = [line.strip() for line in str(info).splitlines()
                     if any(term in line.lower() for term in
                            ("renderer", "vendor", "version", "opengl"))]
            if not lines:
                lines = [str(info)[:600]]
            self.gpu_diagnostics.setText("\n".join(lines[:12]))
        except Exception as exc:
            self.gpu_diagnostics.setText(f"Renderer query unavailable: {exc}")

    def _reset_camera(self):
        if self.density is not None:
            self.camera_view.setCurrentText("Perspective")
            self.zoom_factor.setValue(1.3)
            self._change_camera()

    def refresh(self):
        try:
            self.statusBar().showMessage("Rendering…")
            self.state = self._make_state(self.n.value(), self.l.currentData(),
                                          self.m.currentData(), self.basis.currentText())
            self.axis, self.density, self.psi = density_grid(
                self.state, resolution=self.resolution.value())
            backend, radius = draw_orbital(
                self.plotter, self.axis, self.density, self.psi,
                self.mode.currentText(), self.enclosed.value(),
                self.renderer.currentText(), self.opacity.value(),
                self.phase_color.isChecked(), self.show_grid.isChecked(),
                self.camera_view.currentText(), self.zoom_factor.value())
            self.compare_plotter.setVisible(self.compare_enable.isChecked())
            if self.compare_enable.isChecked():
                self.compare_state = self._make_state(
                    self.compare_n.value(), self.compare_l.currentData(),
                    self.compare_m.currentData(), self.compare_basis.currentText())
                self.compare_axis, self.compare_density, self.compare_psi = density_grid(
                    self.compare_state, resolution=self.resolution.value())
                draw_orbital(self.compare_plotter, self.compare_axis,
                             self.compare_density, self.compare_psi,
                             self.mode.currentText(), self.enclosed.value(),
                             self.renderer.currentText(), self.opacity.value(),
                             self.phase_color.isChecked(), self.show_grid.isChecked(),
                             self.camera_view.currentText(), self.zoom_factor.value())
            else:
                self.compare_axis = self.compare_density = self.compare_psi = self.compare_state = None
            r = np.linspace(0, max(30, 10*self.state.n*self.state.n), 1000)
            probability = self.state.radial_probability(r)
            self.radial_plot.clear()
            self.radial_plot.plot(r, probability, pen=pg.mkPen("#64c9f2", width=2.5))
            integral = np.cumsum(probability) * float(r[1] - r[0])
            cutoff = int(np.searchsorted(integral, 0.999 * integral[-1]))
            self.radial_plot.setXRange(0, float(r[min(len(r)-1, cutoff)]) * 1.05,
                                       padding=0)
            self.radial_plot.setYRange(0, float(max(probability)) * 1.12, padding=0)
            captured = captured_probability(self.axis, self.density)
            orbital = "spdf"[self.state.l]
            state_name = getattr(self.state, "label", f"{self.state.n}{orbital} (m={self.state.m})")
            self.details.setText(
                f"<b>Orbital:</b> {state_name}<br>"
                f"<b>Energy:</b> {self.state.energy_ev:.6f} eV<br>"
                f"<b>Basis:</b> {self.basis.currentText()}<br>"
                f"<b>Comparison:</b> {getattr(self.compare_state, 'label', 'active' if self.compare_state else 'off')}<br>"
                f"<b>Bohr radius (reduced mass):</b> {A_MU_METERS * 1e12:.4f} pm<br>"
                f"<b>Grid:</b> ±{self.axis[-1]:g} a_mu per axis<br>"
                f"<b>Grid probability:</b> {captured:.6f} (numerical estimate)<br>"
                f"<b>Camera framing:</b> {radius:.1f} a_mu radius (99.5% of grid mass)<br>"
                f"<b>Volume backend:</b> {backend}<br><br>"
                "Cloud displays a transformed intensity of |ψ|² to reveal dim regions, "
                "not electron trajectories. Grid data export contains unmodified |ψ|². "
                "Nucleus marker is symbolic (not to scale). "
                "Enclosures refer to probability captured on the finite grid.")
            self.statusBar().showMessage(f"Render complete • {backend}")
            self._update_gpu_diagnostics()
        except Exception as exc:
            self.statusBar().showMessage("Render failed")
            QMessageBox.critical(self, "Rendering error", f"{exc}\n\n{traceback.format_exc()}")

    def export_png(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export 3D image", "orbital.png", "PNG (*.png)")
        if path:
            try:
                self.plotter.screenshot(str(Path(path).with_suffix(".png")),
                                        scale=self.export_scale.value())
            except Exception as exc:
                QMessageBox.critical(self, "Export error", str(exc))

    def export_grid(self):
        if self.axis is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export scientific data", "orbital.npz", "NumPy (*.npz)")
        if path:
            try:
                np.savez_compressed(str(Path(path).with_suffix(".npz")),
                                    axis_a_mu=self.axis, density_a_mu_minus3=self.density,
                                    psi_a_mu_minus3_over2=self.psi,
                                    n=self.state.n, l=self.state.l, m=self.state.m,
                                    energy_ev=self.state.energy_ev,
                                    orbital_basis=self.basis.currentText(),
                                    reduced_bohr_radius_m=A_MU_METERS)
            except Exception as exc:
                QMessageBox.critical(self, "Export error", str(exc))

    def closeEvent(self, event):
        self.plotter.close()
        self.compare_plotter.close()
        super().closeEvent(event)
