"""The Settings window: sections on the left, options on the right.

Most changes apply immediately. The graphics device and the interface size
take effect after a restart; the window says so and offers to restart.
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout, QLabel,
                               QLineEdit, QListWidget, QMessageBox, QPushButton, QSpinBox, QStackedWidget,
                               QVBoxLayout, QWidget)

from quantumscope.gui import preferences as prefs

SECTIONS = ('Appearance', 'Circuits', 'Graphics', 'Files')


class SettingsDialog(QDialog):
    """host provides: apply_theme(choice), apply_preferences(), graphics_information() -> str,
    restart_application(). Any of them may be missing (e.g. in tests)."""

    def __init__(self, host=None, parent=None):
        super().__init__(parent if parent is not None else (host if isinstance(host, QWidget) else None))
        self.host = host
        self.setWindowTitle('Settings')
        # A settings window has only a Close button: no maximize or minimize.
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint
                            | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint)
        self.setFixedSize(780, 540)
        self._restart_needed = False
        outer = QVBoxLayout(self)
        body = QHBoxLayout()
        outer.addLayout(body, 1)
        self.nav = QListWidget()
        self.nav.setObjectName('settingsNav')
        self.nav.addItems(SECTIONS)
        self.nav.setFixedWidth(170)
        body.addWidget(self.nav)
        self.pages = QStackedWidget()
        body.addWidget(self.pages, 1)
        for build in (self._appearance, self._circuits, self._graphics, self._files):
            page = QWidget()
            build(page)
            self.pages.addWidget(page)
        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.nav.setCurrentRow(0)

        self.restart_bar = QWidget()
        bar = QHBoxLayout(self.restart_bar)
        bar.setContentsMargins(0, 0, 0, 0)
        self.restart_label = QLabel('Some changes apply after QuantumScope restarts.')
        bar.addWidget(self.restart_label, 1)
        restart = QPushButton('Restart now')
        restart.clicked.connect(self._restart)
        bar.addWidget(restart)
        self.restart_bar.setVisible(False)
        outer.addWidget(self.restart_bar)

        buttons = QHBoxLayout()
        reset = QPushButton('Restore defaults')
        reset.setToolTip('Reset every setting to its default (the recent-files list is kept)')
        reset.clicked.connect(self._restore_defaults)
        buttons.addWidget(reset)
        buttons.addStretch()
        close = QPushButton('Close')
        close.setDefault(True)
        close.clicked.connect(self.accept)
        buttons.addWidget(close)
        outer.addLayout(buttons)

    # ---- helpers -------------------------------------------------------------------------
    @staticmethod
    def _page(page, title, intro=''):
        v = QVBoxLayout(page)
        heading = QLabel(title)
        heading.setStyleSheet('font-weight: 700; font-size: 17px;')
        v.addWidget(heading)
        if intro:
            text = QLabel(intro)
            text.setWordWrap(True)
            v.addWidget(text)
        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        v.addLayout(form)
        return v, form

    @staticmethod
    def _note(text):
        label = QLabel(text)
        label.setWordWrap(True)
        label.setObjectName('settingsNote')
        label.setStyleSheet('font-size: 12px;')
        return label

    def _combo(self, key, labels):
        """A combo box bound to a choice preference; labels map value -> shown text."""
        box = QComboBox()
        for value, label in labels:
            box.addItem(label, value)
        box.setCurrentIndex(max(0, box.findData(prefs.get(key))))
        box.currentIndexChanged.connect(lambda _=0, k=key, b=box: self._changed(k, b.currentData()))
        return box

    def _changed(self, key, value):
        prefs.set(key, value)
        if prefs.PREFS[key].restart:
            self._restart_needed = True
            self.restart_bar.setVisible(True)
        if key == 'appearance/theme':
            self._call('apply_theme', value)
        else:
            self._call('apply_preferences')

    def _call(self, name, *args):
        method = getattr(self.host, name, None)
        return method(*args) if callable(method) else None

    # ---- pages -----------------------------------------------------------------------------
    def _appearance(self, page):
        v, form = self._page(page, 'Appearance')
        self.theme = self._combo('appearance/theme', (('dark', 'Dark'), ('light', 'Light'),
                                                      ('system', 'Follow system')))
        form.addRow('Theme', self.theme)
        form.addRow(self._note('Follow system matches your operating system’s light or dark mode, '
                               'including when it changes.'))
        self.scale = self._combo('appearance/scale', tuple((s, f'{s}%') for s in prefs.PREFS['appearance/scale'].choices))
        form.addRow('Interface size', self.scale)
        form.addRow(self._note('Enlarges text, buttons and circuits, e.g. for projecting in a classroom. '
                               'Applies after restarting.'))
        v.addStretch()

    def _circuits(self, page):
        v, form = self._page(page, 'Circuits', 'Defaults for new circuits in the Gate Circuit Simulator.')
        self.default_qubits = QSpinBox()
        self.default_qubits.setRange(1, 10)
        self.default_qubits.setValue(prefs.get('circuits/default_qubits'))
        self.default_qubits.valueChanged.connect(lambda v: self._changed('circuits/default_qubits', v))
        form.addRow('Qubits in a new circuit', self.default_qubits)
        self.default_shots = QSpinBox()
        self.default_shots.setRange(1, 100000)
        self.default_shots.setValue(prefs.get('circuits/default_shots'))
        self.default_shots.valueChanged.connect(lambda v: self._changed('circuits/default_shots', v))
        form.addRow('Measurement shots', self.default_shots)
        self.show_blochs = QCheckBox('Show Bloch spheres beside wires')
        self.show_blochs.setChecked(prefs.get('circuits/show_blochs'))
        self.show_blochs.toggled.connect(lambda on: self._changed('circuits/show_blochs', on))
        form.addRow(self.show_blochs)
        self.confirm_clear = QCheckBox('Ask before clearing a circuit')
        self.confirm_clear.setChecked(prefs.get('circuits/confirm_clear'))
        self.confirm_clear.toggled.connect(lambda on: self._changed('circuits/confirm_clear', on))
        form.addRow(self.confirm_clear)
        v.addStretch()

    def _graphics(self, page):
        v, form = self._page(page, 'Graphics')
        linux = sys.platform.startswith('linux')
        self.device = self._combo('graphics/device', (('auto', 'Automatic'), ('integrated', 'Integrated graphics'),
                                                      ('nvidia', 'NVIDIA (PRIME offloading)')))
        self.device.setEnabled(linux)
        form.addRow('Graphics device', self.device)
        form.addRow(self._note(
            'Applies after restarting. NVIDIA uses PRIME offloading on Linux laptops with two GPUs.' if linux else
            'Your operating system chooses the graphics device (Windows: Settings → System → Display → Graphics; '
            'macOS chooses automatically).'))
        self.volume = self._combo('graphics/volume_method', tuple((m, m) for m in prefs.PREFS['graphics/volume_method'].choices))
        form.addRow('3D volume rendering', self.volume)
        form.addRow(self._note('How 3D orbital clouds are drawn. CPU is slower but works on any computer; '
                               'surfaces are not affected.'))
        info_head = QLabel('Graphics information')
        info_head.setStyleSheet('font-weight: 600; margin-top: 8px;')
        v.addWidget(info_head)
        self.graphics_info = QLabel('Press Refresh to read the current OpenGL renderer.')
        self.graphics_info.setWordWrap(True)
        self.graphics_info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        v.addWidget(self.graphics_info)
        refresh = QPushButton('Refresh')
        refresh.setToolTip('Read the renderer, vendor and OpenGL version actually in use (useful for bug reports)')
        refresh.clicked.connect(self._refresh_graphics)
        v.addWidget(refresh, 0, Qt.AlignmentFlag.AlignLeft)
        v.addStretch()

    def _refresh_graphics(self):
        text = self._call('graphics_information')
        self.graphics_info.setText(text or 'Graphics information is available once a 3D view has been drawn.')

    def _files(self, page):
        v, form = self._page(page, 'Files')
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        self.folder = QLineEdit(prefs.get('files/folder') or '')
        self.folder.setPlaceholderText('Documents folder')
        self.folder.setReadOnly(True)
        h.addWidget(self.folder, 1)
        browse = QPushButton('Browse…')
        browse.clicked.connect(self._choose_folder)
        h.addWidget(browse)
        reset_folder = QPushButton('Use Documents')
        reset_folder.clicked.connect(lambda: (self.folder.clear(), self._changed('files/folder', '')))
        h.addWidget(reset_folder)
        form.addRow('Save and export to', row)
        self.autosave = QCheckBox('Autosave the circuit and offer to recover it after a crash')
        self.autosave.setChecked(prefs.get('files/autosave'))
        self.autosave.toggled.connect(lambda on: self._changed('files/autosave', on))
        form.addRow(self.autosave)
        self.pdf_report = self._combo('files/pdf_report', (('ask', 'Ask each time'), ('always', 'Always include'),
                                                          ('never', 'Never include')))
        form.addRow('Probability report in PDF exports', self.pdf_report)
        recent_head = QLabel('Recent circuits')
        recent_head.setStyleSheet('font-weight: 600; margin-top: 8px;')
        v.addWidget(recent_head)
        self.recent = QListWidget()
        self.recent.addItems(list(prefs.get('files/recent')))
        self.recent.setMaximumHeight(130)
        v.addWidget(self.recent)
        clear = QPushButton('Clear recent list')
        clear.clicked.connect(lambda: (prefs.set('files/recent', ()), self.recent.clear(), self._call('apply_preferences')))
        v.addWidget(clear, 0, Qt.AlignmentFlag.AlignLeft)
        v.addStretch()

    def _choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Save and export to', prefs.default_folder())
        if folder:
            self.folder.setText(folder)
            self._changed('files/folder', folder)

    # ---- actions -------------------------------------------------------------------------------
    def _restore_defaults(self):
        answer = QMessageBox.question(self, 'Restore defaults', 'Reset every setting to its default value?',
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                      QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        before = {k: prefs.get(k) for k, p in prefs.PREFS.items() if p.restart}
        prefs.restore_defaults()
        if any(prefs.get(k) != v for k, v in before.items()):
            self._restart_needed = True
            self.restart_bar.setVisible(True)
        self._reload()
        self._call('apply_theme', prefs.get('appearance/theme'))
        self._call('apply_preferences')

    def _reload(self):
        """Show the stored values again (after Restore defaults)."""
        for box, key in ((self.theme, 'appearance/theme'), (self.scale, 'appearance/scale'),
                         (self.device, 'graphics/device'), (self.volume, 'graphics/volume_method'),
                         (self.pdf_report, 'files/pdf_report')):
            box.blockSignals(True)
            box.setCurrentIndex(max(0, box.findData(prefs.get(key))))
            box.blockSignals(False)
        for widget, key in ((self.default_qubits, 'circuits/default_qubits'), (self.default_shots, 'circuits/default_shots')):
            widget.blockSignals(True)
            widget.setValue(prefs.get(key))
            widget.blockSignals(False)
        for widget, key in ((self.show_blochs, 'circuits/show_blochs'), (self.confirm_clear, 'circuits/confirm_clear'),
                            (self.autosave, 'files/autosave')):
            widget.blockSignals(True)
            widget.setChecked(prefs.get(key))
            widget.blockSignals(False)
        self.folder.setText(prefs.get('files/folder') or '')

    def _restart(self):
        self._call('restart_application')
