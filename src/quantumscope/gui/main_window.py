"""QuantumScope Hydrogen Explorer Qt desktop UI."""
from pathlib import Path
from importlib.resources import files
import traceback
import os
import subprocess
import sys

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, QSettings, QUrl, QStandardPaths, QTimer
from PySide6.QtGui import QDesktopServices, QPixmap, QPainter, QPen, QColor, QIcon
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPushButton, QScrollArea, QSpinBox, QDoubleSpinBox,
    QSplitter, QVBoxLayout, QWidget, QFileDialog, QDialog, QDialogButtonBox, QFrame, QInputDialog, QTabWidget, QSizePolicy, QToolButton, QMenu, QApplication,
)
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from pyvistaqt import QtInteractor
from quantumscope import __version__
from quantumscope.physics import HydrogenAtom, density_grid
from quantumscope.physics.hydrogen import A_MU_METERS, captured_probability, RealHydrogenState
from quantumscope.visualization.orbitals import draw_orbital, set_camera_view, probability_radius


class AboutDialog(QDialog):
    """Branded, accessible project credits; GitHub avatar is cached offline."""
    AVATAR_URL = 'https://avatars.githubusercontent.com/u/50075168?s=256&v=4'

    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle('About QuantumScope')
        self.resize(510,580)
        self.setMinimumWidth(440)
        self.setStyleSheet("""QDialog {background:#0d1828;color:#eaf4ff;}
            QLabel {color:#eaf4ff;} QLabel#muted {color:#aac2d7;}
            QPushButton {background:#203a56;color:#eaf5ff;border:1px solid #355a78;
            border-radius:8px;padding:9px 13px;font-weight:600;}
            QPushButton:hover {background:#285474;border-color:#59cce6;}
            QFrame#divider {background:#2f4d69;max-height:1px;}""")
        layout=QVBoxLayout(self);layout.setContentsMargins(28,20,28,20);layout.setSpacing(10)
        logo=QLabel();logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setPixmap(QPixmap(str(files('quantumscope').joinpath('assets/quantumscope-128.png'))).scaled(76,76,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(logo)
        title=QLabel('QuantumScope');title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet('font-size:25px;font-weight:800;');layout.addWidget(title)
        subtitle=QLabel(f'Quantum Visualization Studio  •  v{__version__}')
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter);subtitle.setObjectName('muted');layout.addWidget(subtitle)
        tagline=QLabel('Explore  •  Visualize  •  Simulate');tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setStyleSheet('color:#5ad1e9;font-size:12px;');layout.addWidget(tagline)
        divider=QFrame();divider.setObjectName('divider');layout.addWidget(divider)
        dev=QHBoxLayout();dev.setSpacing(17);layout.addLayout(dev)
        self.photo=QLabel('GitHub avatar');self.photo.setFixedSize(90,90)
        self.photo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo.setStyleSheet('background:#1d3852;border-radius:12px;color:#aac3d8;')
        dev.addWidget(self.photo)
        identity=QVBoxLayout();identity.setSpacing(4);dev.addLayout(identity,1)
        name=QLabel('Md. Saif Hassan Onim, PhD');name.setStyleSheet('font-size:15px;font-weight:700;');identity.addWidget(name)
        for line in ('Developer & maintainer','Postdoctoral Fellow','Southern Methodist University, Dallas'):
            label=QLabel(line);label.setObjectName('muted');label.setWordWrap(True);identity.addWidget(label)
        self._load_avatar()
        desc=QLabel('Open-source scientific software for hydrogen orbitals, quantum principles, and interactive quantum circuits.')
        desc.setWordWrap(True);desc.setAlignment(Qt.AlignmentFlag.AlignCenter);layout.addWidget(desc)
        features=QLabel('Hydrogen Explorer & Dynamics  •  Double Slit  •  Superposition & Entanglement  •  Circuit Simulator  •  QASM Converter')
        features.setObjectName('muted');features.setWordWrap(True)
        features.setAlignment(Qt.AlignmentFlag.AlignCenter);layout.addWidget(features)
        links=QHBoxLayout();layout.addLayout(links)
        for text,url in (('GitHub repository','https://github.com/Onimee58/QuantumScope'),('Developer profile','https://github.com/Onimee58'),('SMU page','https://people.smu.edu/monim')):
            btn=QPushButton(text+' ↗');btn.clicked.connect(lambda checked=False,u=url:QDesktopServices.openUrl(QUrl(u)))
            links.addWidget(btn)
        footer=QLabel('MIT licensed  •  Python / PySide6 / NumPy / VTK  •  Idealized educational simulations')
        footer.setObjectName('muted');footer.setWordWrap(True);footer.setAlignment(Qt.AlignmentFlag.AlignCenter);layout.addWidget(footer)
        layout.addStretch()
        close=QPushButton('Close');close.clicked.connect(self.accept);layout.addWidget(close)

    def _load_avatar(self):
        directory=Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.CacheLocation)) / 'QuantumScope'
        directory.mkdir(parents=True,exist_ok=True)
        self._avatar_path=directory/'github-avatar.png'
        if self._avatar_path.exists():
            self._display_avatar(self._avatar_path.read_bytes())
        self._network=QNetworkAccessManager(self)
        request=QNetworkRequest(QUrl(self.AVATAR_URL))
        self._reply=self._network.get(request)
        self._reply.finished.connect(self._avatar_received)

    def _display_avatar(self,data):
        pix=QPixmap()
        if pix.loadFromData(data):
            self.photo.setText('')
            self.photo.setPixmap(pix.scaled(90,90,Qt.AspectRatioMode.KeepAspectRatioByExpanding,Qt.TransformationMode.SmoothTransformation))
            return True
        return False

    def _avatar_received(self):
        if self._reply.error()==self._reply.NetworkError.NoError:
            data=bytes(self._reply.readAll())
            if self._display_avatar(data):
                try:self._avatar_path.write_bytes(data)
                except OSError:pass
        self._reply.deleteLater()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"QuantumScope {__version__} — Quantum Visualization Studio")
        self.setWindowIcon(QIcon(str(files("quantumscope").joinpath("assets/quantumscope.png"))))
        self.resize(1420, 920)
        self.atom = HydrogenAtom()
        self.axis = self.density = self.psi = self.state = None
        self.compare_axis = self.compare_density = self.compare_psi = self.compare_state = None
        # Signals from dependent quantum-number controls may fire during UI construction.
        # Do not render until all widgets and plotters have been initialized.
        self._ui_ready = False
        self._syncing_camera = False
        self._rendering = False
        self._build_ui()
        self._ui_ready = True
        self._build_workspace()
        self.refresh()

    def _experiment_menu(self, parent, category=None):
        """Single extensible experiment catalog shared by header and tab bar."""
        menu = QMenu(parent)
        menu.setObjectName("experimentMenu")
        if category in (None,"hydrogen"):
            menu.addSection("ATOMIC PHYSICS")
            menu.addAction("Hydrogen Explorer", self._show_hydrogen)
            menu.addAction("Hydrogen Dynamics 2D", self.show_dynamics)
            menu.addAction("Hydrogen Dynamics 3D", self.show_dynamics_3d)
        if category in (None,"principles"):
            menu.addSection("QUANTUM PRINCIPLES")
            menu.addAction("Double-Slit Experiment", self._launch_double_slit)
            menu.addAction("Quantum Superposition (spin-½)", self._launch_superposition)
            menu.addAction("Quantum Entanglement (electron spins)", self._launch_entanglement)
        if category in (None,"circuits"):
            menu.addSection("QUANTUM CIRCUITS")
            menu.addAction("Gate Circuit Simulator", self._launch_circuits)
            menu.addAction("QASM Converter", self._launch_converter)
        return menu

    def _show_settings(self):
        """Small, honest preferences panel; more settings can be added later."""
        dialog = QDialog(self)
        dialog.setWindowTitle("QuantumScope Settings")
        dialog.setMinimumWidth(370)
        dialog.setWindowIcon(self.windowIcon())
        layout = QVBoxLayout(dialog)
        heading = QLabel("Appearance")
        heading.setStyleSheet("font-weight: 700; font-size: 16px;")
        layout.addWidget(heading)
        layout.addWidget(QLabel("Interface theme"))
        themes = QComboBox(dialog)
        themes.addItems(["Dark", "Light"])
        settings = QSettings("QuantumScope", "QuantumScope")
        themes.setCurrentIndex(1 if settings.value("appearance/theme", "dark") == "light" else 0)
        layout.addWidget(themes)
        note = QLabel("Theme changes apply immediately and are saved for your next launch.")
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.accept)
        layout.addWidget(buttons)
        def set_theme(index):
            from quantumscope.gui.theme import STYLESHEET, LIGHT_STYLESHEET
            choice = "light" if index == 1 else "dark"
            settings.setValue("appearance/theme", choice)
            QApplication.instance().setStyleSheet(LIGHT_STYLESHEET if choice == "light" else STYLESHEET)
        themes.currentIndexChanged.connect(set_theme)
        dialog.exec()

    def _header_button(self, label, tooltip, action):
        button = QToolButton(self)
        button.setObjectName("headerTool")
        button.setText(label)
        button.setToolTip(tooltip)
        button.setAccessibleName(tooltip)
        button.clicked.connect(action)
        return button

    def _build_workspace(self):
        """Host every experiment in the same extensible, closable tab workspace."""
        explorer = self.takeCentralWidget()
        shell = QWidget(self)
        shell.setObjectName("workspaceShell")
        outer = QVBoxLayout(shell)
        outer.setContentsMargins(15, 12, 15, 12)
        outer.setSpacing(10)
        self.menuBar().hide()  # Native menu retained internally but not shown.
        header = QWidget()
        header.setObjectName("workspaceHeader")
        row = QHBoxLayout(header)
        row.setContentsMargins(15, 10, 15, 10)
        mark = QLabel()
        mark.setObjectName("brandMark")
        mark.setPixmap(QPixmap(str(files("quantumscope").joinpath("assets/quantumscope.png"))).scaled(
            44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        mark.setFixedSize(50, 50)
        row.addWidget(mark)
        titles = QVBoxLayout()
        titles.setSpacing(1)
        name = QLabel("QuantumScope")
        name.setObjectName("brandTitle")
        titles.addWidget(name)
        caption = QLabel("QUANTUM VISUALIZATION STUDIO  /  v0.3.0")
        caption.setObjectName("brandCaption")
        titles.addWidget(caption)
        row.addLayout(titles)
        row.addStretch()
        new_button = QToolButton(self)
        new_button.setObjectName("newExperiment")
        new_button.setText("+ New Experiment  ▾")
        new_button.setToolTip("Open or switch to an experiment")
        new_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        new_button.setMenu(self._experiment_menu(new_button))
        row.addWidget(new_button)
        row.addWidget(self._header_button("⚙", "Settings", self._show_settings))
        row.addWidget(self._header_button("ⓘ", "About QuantumScope", self.show_about))
        outer.addWidget(header)
        self.categories = QTabWidget()
        self.categories.setObjectName("categoryWorkspace")
        self.categories.setDocumentMode(True)
        self.workspaces = {}
        for category, title in (("hydrogen", "⚛  Hydrogen"),
                                ("principles", "◈  Quantum Principles"),
                                ("circuits", "▦  Quantum Circuits")):
            tabs = QTabWidget()
            tabs.setObjectName("experimentWorkspace")
            tabs.setTabsClosable(True)
            tabs.setDocumentMode(True)
            tabs.tabCloseRequested.connect(lambda idx, cat=category: self._close_workspace_tab(cat, idx))
            plus = QToolButton(tabs)
            plus.setObjectName("tabAddButton")
            plus.setText("+")
            plus.setToolTip("New experiment")
            plus.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            plus.setMenu(self._experiment_menu(plus,category))
            tabs.setCornerWidget(plus, Qt.Corner.TopRightCorner)
            self.categories.addTab(tabs, title)
            self.workspaces[category] = tabs
        self.workspace = self.workspaces["hydrogen"]
        self.workspace.addTab(explorer, QIcon(str(files("quantumscope").joinpath("assets/quantumscope-24.png"))), "Hydrogen Explorer")
        self.workspace.tabBar().setTabButton(0, self.workspace.tabBar().ButtonPosition.RightSide, None)
        from quantumscope.gui.circuit_workspace import CircuitWorkspace
        self.circuit_widget = CircuitWorkspace(self.workspaces["circuits"])
        self.workspaces["circuits"].addTab(self.circuit_widget, "Gate Circuit Simulator")
        self.workspaces["circuits"].tabBar().setTabButton(0, self.workspaces["circuits"].tabBar().ButtonPosition.RightSide, None)
        from quantumscope.gui.qasm_converter import QasmConverter
        self.converter_widget = QasmConverter(self._load_converted_circuit, self.workspaces["circuits"])
        self.workspaces["circuits"].addTab(self.converter_widget,"QASM Converter")
        outer.addWidget(self.categories, 1)
        self.setCentralWidget(shell)
        self._open_experiments = {}
        self._launch_double_slit()
        self._select_category("hydrogen")
        self.statusBar().showMessage("Ready  ·  Choose an experiment or explore hydrogen orbitals")

    def _select_category(self, category):
        tabs=self.workspaces[category]
        self.categories.setCurrentWidget(tabs)
        return tabs

    def _open_experiment(self, key, label, constructor):
        """One persistent experiment tab in the appropriate category."""
        category = "hydrogen" if key.startswith("dynamics_") else "principles"
        tabs=self._select_category(category)
        if key in self._open_experiments:
            widget=self._open_experiments[key]
            index=tabs.indexOf(widget)
            if index>=0:
                tabs.setCurrentIndex(index)
                return
            del self._open_experiments[key]
        widget=constructor(tabs)
        widget.setWindowFlags(Qt.WindowType.Widget)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
        icon_name={"double_slit":"◫","dynamics_2d":"∿","dynamics_3d":"⬡"}.get(key,"◈")
        index=tabs.addTab(widget,f"{icon_name}  {label.strip()}")
        self._open_experiments[key]=widget
        tabs.setCurrentIndex(index)
        self.statusBar().showMessage(f"Opened {label.strip()}",3500)

    def _close_workspace_tab(self,category,index):
        tabs=self.workspaces[category]
        if index<=0 or category=="circuits":return
        widget=tabs.widget(index)
        tabs.removeTab(index)
        for key,active in list(self._open_experiments.items()):
            if active is widget:del self._open_experiments[key]
        widget.close()
        widget.deleteLater()

    def _launch_circuits(self):
        tabs=self._select_category("circuits")
        tabs.setCurrentWidget(self.circuit_widget)

    def _launch_converter(self):
        tabs=self._select_category("circuits")
        tabs.setCurrentWidget(self.converter_widget)

    def _load_converted_circuit(self,n,gates,measured=()):
        self.circuit_widget.set_circuit(n,gates)
        col=max((c for _,c in self.circuit_widget.gates),default=-1)+1
        self.circuit_widget.measurements={q:col for q in measured}
        self.circuit_widget._expand_columns(col)
        self.circuit_widget.refresh()
        self._launch_circuits()

    def _show_hydrogen(self):
        tabs=self._select_category("hydrogen")
        tabs.setCurrentIndex(0)

    def _launch_double_slit(self):
        from quantumscope.gui.double_slit_dialog import DoubleSlitDialog
        self._open_experiment("double_slit", "  Double-Slit Experiment  ", DoubleSlitDialog)

    def _launch_superposition(self):
        from quantumscope.gui.quantum_principles import SuperpositionDialog
        self._open_experiment("superposition", "Quantum Superposition", SuperpositionDialog)

    def _launch_entanglement(self):
        from quantumscope.gui.quantum_principles import EntanglementDialog
        self._open_experiment("entanglement", "Quantum Entanglement", EntanglementDialog)

    def show_dynamics(self):
        from quantumscope.gui.dynamics_dialog import HydrogenDynamicsDialog
        self._open_experiment("dynamics_2d", "  Hydrogen Dynamics 2D  ", HydrogenDynamicsDialog)

    def show_dynamics_3d(self):
        from quantumscope.gui.dynamics_3d_dialog import HydrogenDynamics3DDialog
        self._open_experiment("dynamics_3d", "  Hydrogen Dynamics 3D  ", HydrogenDynamics3DDialog)

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
        scroll.setMinimumWidth(410)
        scroll.setMaximumWidth(820)
        options = QWidget()
        controls = QVBoxLayout(options)
        controls.setAlignment(Qt.AlignmentFlag.AlignTop)
        controls.setSpacing(10)

        state_box = QGroupBox("Hydrogen quantum state")
        state_form = QFormLayout(state_box)
        state_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
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
        compare_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
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
        vf.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
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
        gf.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
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
        cf.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.camera_view = QComboBox()
        self.camera_view.addItems(["Perspective", "+X", "+Y", "+Z"])
        self.zoom_factor = QDoubleSpinBox()
        self.zoom_factor.setRange(0.5, 5.0)
        self.zoom_factor.setSingleStep(0.25)
        self.zoom_factor.setValue(1.3)
        self.phase_color = QCheckBox("Color enclosure by wavefunction phase")
        self.show_grid = QCheckBox("Show axes and coordinates (a_mu)")
        self.sync_cameras = QCheckBox("Synchronize comparison cameras")
        self.sync_cameras.setChecked(True)
        cf.addRow("View", self.camera_view)
        cf.addRow("Magnification", self.zoom_factor)
        cf.addRow(self.phase_color)
        cf.addRow(self.show_grid)
        cf.addRow(self.sync_cameras)
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
        details_box.setCheckable(True)
        details_box.setChecked(True)
        detail_layout = QVBoxLayout(details_box)
        self.details = QLabel()
        self.details.setWordWrap(True)
        self.details.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        detail_layout.addWidget(self.details)
        controls.addWidget(details_box)
        controls.addStretch()
        # Allow long setting labels to wrap instead of creating horizontal scrolling.
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        options.setMinimumWidth(398)
        scroll.setWidget(options)
        splitter.addWidget(scroll)

        self.viewer_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.plotter = QtInteractor(central)
        self.compare_plotter = QtInteractor(central)
        self.primary_panel = QWidget()
        primary_layout = QVBoxLayout(self.primary_panel)
        primary_layout.setContentsMargins(0, 0, 0, 0)
        primary_layout.setSpacing(2)
        self.primary_label = QLabel("Primary orbital")
        primary_layout.addWidget(self.primary_label)
        primary_layout.addWidget(self.plotter, stretch=1)
        self.viewer_splitter.addWidget(self.primary_panel)
        self.compare_panel = QWidget()
        compare_layout = QVBoxLayout(self.compare_panel)
        compare_layout.setContentsMargins(0, 0, 0, 0)
        compare_layout.setSpacing(2)
        self.compare_label = QLabel("Comparison orbital")
        compare_layout.addWidget(self.compare_label)
        compare_layout.addWidget(self.compare_plotter, stretch=1)
        self.viewer_splitter.addWidget(self.compare_panel)
        self.compare_panel.hide()
        self.plotter.camera.AddObserver("ModifiedEvent", lambda *_: self._mirror_camera(self.plotter, self.compare_plotter))
        self.compare_plotter.camera.AddObserver("ModifiedEvent", lambda *_: self._mirror_camera(self.compare_plotter, self.plotter))
        # Make the left sidebar span the full content height.
        # The compact radial plot belongs below the 3D viewers on the RIGHT only.
        viewer_column = QWidget()
        viewer_layout = QVBoxLayout(viewer_column)
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.setSpacing(6)
        viewer_layout.addWidget(self.viewer_splitter, stretch=1)
        splitter.addWidget(viewer_column)
        splitter.setSizes([455, 965])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        bottom = QGroupBox("Radial probability  P(r) = r² |Rₙₗ(r)|²")
        bottom.setCheckable(True)
        bottom.setChecked(True)
        self.radial_group = bottom
        blayout = QVBoxLayout(bottom)
        self.radial_plot = pg.PlotWidget()
        self.radial_plot.setBackground("#101820")
        self.radial_plot.setLabel("bottom", "r", units="a_mu")
        self.radial_plot.setLabel("left", "P(r)", units="a_mu^-1")
        self.radial_plot.showGrid(x=True, y=True, alpha=0.2)
        self.radial_plot.setMinimumHeight(95)
        blayout.addWidget(self.radial_plot)
        bottom.setMinimumHeight(125)
        bottom.setMaximumHeight(170)
        bottom.toggled.connect(self._toggle_radial_plot)
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

    def _toggle_radial_plot(self, shown):
        self.radial_plot.setVisible(shown)
        self.radial_group.setMaximumHeight(170 if shown else 35)

    def _mirror_camera(self, source, destination):
        """Keep both cameras in matching world coordinates without recursive updates."""
        if (not self._ui_ready or self._syncing_camera or self._rendering or
                not self.compare_enable.isChecked() or not self.sync_cameras.isChecked()):
            return
        self._syncing_camera = True
        try:
            src, dst = source.camera, destination.camera
            dst.SetPosition(*src.GetPosition())
            dst.SetFocalPoint(*src.GetFocalPoint())
            dst.SetViewUp(*src.GetViewUp())
            dst.SetParallelProjection(src.GetParallelProjection())
            dst.SetParallelScale(src.GetParallelScale())
            dst.SetViewAngle(src.GetViewAngle())
            destination.reset_camera_clipping_range()
            destination.render()
        finally:
            self._syncing_camera = False

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
        self._rendering = True
        try:
            self.statusBar().showMessage("Rendering…")
            self.state = self._make_state(self.n.value(), self.l.currentData(),
                                          self.m.currentData(), self.basis.currentText())
            self.axis, self.density, self.psi = density_grid(
                self.state, resolution=self.resolution.value())
            self.primary_label.setText("Primary: " + getattr(self.state, "label", f"n={self.state.n}, l={self.state.l}, m={self.state.m}"))
            backend, radius = draw_orbital(
                self.plotter, self.axis, self.density, self.psi,
                self.mode.currentText(), self.enclosed.value(),
                self.renderer.currentText(), self.opacity.value(),
                self.phase_color.isChecked(), self.show_grid.isChecked(),
                self.camera_view.currentText(), self.zoom_factor.value())
            self.compare_panel.setVisible(self.compare_enable.isChecked())
            if self.compare_enable.isChecked():
                self.compare_state = self._make_state(
                    self.compare_n.value(), self.compare_l.currentData(),
                    self.compare_m.currentData(), self.compare_basis.currentText())
                self.compare_label.setText("Comparison: " + getattr(self.compare_state, "label", f"n={self.compare_state.n}, l={self.compare_state.l}, m={self.compare_state.m}"))
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
            self._rendering = False
            if self.compare_enable.isChecked() and self.sync_cameras.isChecked():
                # Ensure both begin with the same orientation after a refresh.
                self._mirror_camera(self.plotter, self.compare_plotter)
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
            self._rendering = False
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
