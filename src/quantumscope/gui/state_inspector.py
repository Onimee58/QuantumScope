"""State Inspector: a separate window showing the circuit's state in detail.

It follows the circuit workspace's step slider (or holds a frozen snapshot)
and shows amplitudes, the statevector in Dirac notation with text/LaTeX/CSV
export, reduced density matrices of up to three qubits, and circuit
statistics. All calculations come from physics.state_analysis.
"""
import math

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFileDialog, QGridLayout, QHBoxLayout,
                               QHeaderView, QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
                               QTabWidget, QTextBrowser, QVBoxLayout, QWidget)

from quantumscope.gui.theme import canvas_color
from quantumscope.physics.gate_education import format_amplitude
from quantumscope.physics.state_analysis import (MAX_REDUCED_QUBITS, amplitude_rows, dirac_latex, dirac_text,
                                                 reduced_summary, state_csv)


def phase_color(phase):
    """Hue encodes phase: red at 0, then around the color wheel to 2π."""
    hue = ((phase % (2 * math.pi)) / (2 * math.pi)) % 1.0
    return QColor.fromHsvF(hue, 0.75, 0.92)


def _item(text, align=Qt.AlignmentFlag.AlignCenter, tooltip=None):
    item = QTableWidgetItem(text)
    item.setTextAlignment(align)
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    if tooltip:
        item.setToolTip(tooltip)
    return item


class MatrixHeatmap(QWidget):
    """|ρ_ij| as shaded cells, so coherences (off-diagonal terms) stand out."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.matrix = None
        self.labels = []
        self.setMinimumSize(220, 220)

    def set_matrix(self, matrix, labels):
        self.matrix, self.labels = matrix, labels
        self.update()

    def paintEvent(self, event):
        if self.matrix is None:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        dim = self.matrix.shape[0]
        margin = 46
        size = max(10, min(self.width(), self.height()) - margin - 8)
        cell = size / dim
        base = canvas_color('chart_theory')
        ink = canvas_color('chart_text')
        grid = canvas_color('chart_axis')
        p.setFont(QFont('Sans', 8))
        top = max(abs(v) for v in self.matrix.flat) or 1.0
        for r in range(dim):
            for c in range(dim):
                value = abs(self.matrix[r, c])
                color = QColor(base)
                color.setAlphaF(min(1.0, value / top) * 0.9 + 0.05 if value > 1e-10 else 0.03)
                x, y = margin + c * cell, margin + r * cell
                p.fillRect(int(x), int(y), int(cell) + 1, int(cell) + 1, color)
        p.setPen(QPen(grid, 1))
        p.drawRect(int(margin), int(margin), int(cell * dim), int(cell * dim))
        p.setPen(ink)
        for i, label in enumerate(self.labels):
            p.drawText(int(margin + i * cell), 6, int(cell), margin - 10, Qt.AlignmentFlag.AlignCenter, label)
            p.drawText(0, int(margin + i * cell), margin - 4, int(cell),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label)
        p.end()


class StateInspector(QWidget):
    def __init__(self, workspace):
        super().__init__(workspace, Qt.WindowType.Window)
        self.workspace = workspace
        self.view = None
        self.setWindowTitle('QuantumScope — State Inspector')
        # A top-level window does not inherit the workspace background: use the
        # themed shell style so text and tables stay readable in both themes.
        self.setObjectName('workspaceShell')
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.resize(820, 640)
        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        layout.addLayout(top)
        self.where = QLabel()
        self.where.setWordWrap(True)
        top.addWidget(self.where, 1)
        self.relative = QCheckBox('Remove global phase')
        self.relative.setToolTip('Show amplitudes with the global phase rotated away (the first nonzero amplitude '
                                 'made real and positive). Global phase is not physically observable.')
        self.relative.toggled.connect(self._render)
        top.addWidget(self.relative)
        self.freeze = QCheckBox('Freeze')
        self.freeze.setToolTip('Hold the current state so you can step elsewhere and compare')
        self.freeze.toggled.connect(lambda on: None if on else self.refresh())
        top.addWidget(self.freeze)

        self.tabs = QTabWidget()
        self.tabs.setObjectName('experimentWorkspace')   # reuse the themed tab style
        layout.addWidget(self.tabs)
        self._build_amplitudes()
        self._build_statevector()
        self._build_reduced()
        self._build_circuit()
        workspace.state_changed.connect(self._on_state_changed)

    # ---- tabs -------------------------------------------------------------------------
    def _build_amplitudes(self):
        tab = QWidget()
        v = QVBoxLayout(tab)
        row = QHBoxLayout()
        v.addLayout(row)
        self.show_all = QCheckBox('Show all basis states')
        self.show_all.toggled.connect(self._render)
        row.addWidget(self.show_all)
        row.addWidget(QLabel('Sort by'))
        self.sort = QComboBox()
        self.sort.addItems(['Basis order', 'Largest probability'])
        self.sort.currentIndexChanged.connect(self._render)
        row.addWidget(self.sort)
        row.addStretch()
        self.amp_summary = QLabel()
        row.addWidget(self.amp_summary)
        self.amp_table = QTableWidget(0, 6)
        self.amp_table.setHorizontalHeaderLabels(['Basis', 'Amplitude', 'Magnitude', 'Probability', 'Phase', ''])
        self.amp_table.verticalHeader().setVisible(False)
        header = self.amp_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.amp_table.setColumnWidth(5, 34)
        v.addWidget(self.amp_table)
        v.addWidget(QLabel('Basis labels list q0 first (leftmost). Phase is shown as a multiple of π; '
                           'the color swatch encodes phase around the color wheel.'))
        self.tabs.addTab(tab, 'Amplitudes')

    def _build_statevector(self):
        tab = QWidget()
        v = QVBoxLayout(tab)
        self.dirac = QTextBrowser()
        v.addWidget(self.dirac)
        row = QHBoxLayout()
        v.addLayout(row)
        for text, handler in (('Copy as text', self._copy_text), ('Copy as LaTeX', self._copy_latex),
                              ('Copy as CSV', self._copy_csv), ('Save CSV…', self._save_csv)):
            button = QPushButton(text)
            button.clicked.connect(handler)
            row.addWidget(button)
        row.addStretch()
        self.copy_status = QLabel()
        row.addWidget(self.copy_status)
        self.tabs.addTab(tab, 'Statevector')

    def _build_reduced(self):
        tab = QWidget()
        v = QVBoxLayout(tab)
        v.addWidget(QLabel(f'Choose up to {MAX_REDUCED_QUBITS} qubits. The other qubits are traced out.'))
        self.keep_row = QHBoxLayout()
        v.addLayout(self.keep_row)
        self.keep_boxes = []
        body = QHBoxLayout()
        v.addLayout(body, 1)
        self.rho_table = QTableWidget(0, 0)
        self.rho_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        body.addWidget(self.rho_table, 3)
        self.heatmap = MatrixHeatmap()
        body.addWidget(self.heatmap, 2)
        self.reduced_info = QLabel()
        self.reduced_info.setWordWrap(True)
        self.reduced_info.setTextFormat(Qt.TextFormat.RichText)
        v.addWidget(self.reduced_info)
        self.tabs.addTab(tab, 'Reduced state')

    def _build_circuit(self):
        tab = QWidget()
        grid = QGridLayout(tab)
        self.stats = QTableWidget(0, 2)
        self.stats.setHorizontalHeaderLabels(['Statistic', 'Value'])
        self.stats.verticalHeader().setVisible(False)
        self.stats.horizontalHeader().setStretchLastSection(True)
        self.stats.setColumnWidth(0, 260)
        grid.addWidget(self.stats, 0, 0)
        self.counts = QTableWidget(0, 2)
        self.counts.setHorizontalHeaderLabels(['Gate', 'Count'])
        self.counts.verticalHeader().setVisible(False)
        self.counts.horizontalHeader().setStretchLastSection(True)
        grid.addWidget(self.counts, 0, 1)
        note = QLabel('Drawn depth counts the occupied columns as laid out. Minimum depth is the fewest layers '
                      'if every gate ran as early as possible (gates on different qubits in parallel). '
                      'T-count counts T and T† gates. Clifford gates map Pauli operators to Pauli operators; '
                      'rotations count as Clifford only at multiples of π/2.')
        note.setWordWrap(True)
        grid.addWidget(note, 1, 0, 1, 2)
        self.tabs.addTab(tab, 'Circuit')

    # ---- updates ---------------------------------------------------------------------
    def _on_state_changed(self):
        if self.isVisible() and not self.freeze.isChecked():
            self.refresh()

    def refresh(self):
        view = self.workspace.inspected_view()
        model = view['model']
        self.view = {'state': np.array(view['state'], complex), 'n': view['n'], 'step': view['step'],
                     'steps': view['steps'], 'layers_done': view['layers_done'],
                     'analysis': model.analysis(), 'measured': sorted(model.measurements),
                     'initial': [s.label for s in model.initial_states]}
        self._sync_keep_boxes()
        self._render()

    def _sync_keep_boxes(self):
        n = self.view['n']
        if len(self.keep_boxes) == n:
            return
        previous = [i for i, b in enumerate(self.keep_boxes) if b.isChecked() and i < n] or [0]
        for box in self.keep_boxes:
            self.keep_row.removeWidget(box)
            box.deleteLater()
        self.keep_boxes = []
        for q in range(n):
            box = QCheckBox(f'q{q}')
            box.setChecked(q in previous)
            box.toggled.connect(self._keep_changed)
            self.keep_row.addWidget(box)
            self.keep_boxes.append(box)
        self._limit_keep()

    def _keep_changed(self):
        self._limit_keep()
        self._render_reduced()

    def _limit_keep(self):
        chosen = sum(b.isChecked() for b in self.keep_boxes)
        for b in self.keep_boxes:
            b.setEnabled(b.isChecked() or chosen < MAX_REDUCED_QUBITS)

    def _render(self):
        if self.view is None:
            return
        v = self.view
        frozen = ' (frozen)' if self.freeze.isChecked() else ''
        measured = (' Terminal measurements on ' + ', '.join(f'q{q}' for q in v['measured'])
                    + ' are not applied: this is the state before measurement.') if v['measured'] else ''
        starts = ', '.join(f'q{q} {label}' for q, label in enumerate(v['initial']) if label != '|0⟩')
        self.where.setText(f'<b>State after column {v["step"]} of {v["steps"]}</b>{frozen} · '
                           f'{v["layers_done"]} occupied column(s) applied · {v["n"]} qubit(s)'
                           + (f' · initial states: {starts}' if starts else '') + '.' + measured)
        self._render_amplitudes()
        self._render_statevector()
        self._render_reduced()
        self._render_circuit()

    def _render_amplitudes(self):
        v = self.view
        rows = amplitude_rows(v['state'], v['n'], self.show_all.isChecked(), self.relative.isChecked(),
                              'probability' if self.sort.currentIndex() == 1 else 'basis')
        self.amp_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.amp_table.setItem(r, 0, _item(row['label']))
            self.amp_table.setItem(r, 1, _item(row['text'], tooltip=f'{row["amplitude"]:.12g}'))
            self.amp_table.setItem(r, 2, _item(f'{row["magnitude"]:.4f}'))
            self.amp_table.setItem(r, 3, _item(f'{row["probability"] * 100:.2f}%'))
            degrees = '' if row['phase'] is None else f'{math.degrees(row["phase"]):.2f}°'
            self.amp_table.setItem(r, 4, _item(row['phase_text'], tooltip=degrees))
            # A cell widget, because the stylesheet overrides item backgrounds.
            swatch = QLabel()
            if row['phase'] is not None:
                swatch.setStyleSheet(f'background:{phase_color(row["phase"]).name()}; margin:5px; border-radius:3px;')
                swatch.setToolTip(row['phase_text'])
            self.amp_table.setCellWidget(r, 5, swatch)
        nonzero = int(np.sum(np.abs(v['state']) > 1e-10))
        self.amp_summary.setText(f'{nonzero} of {1 << v["n"]} amplitudes nonzero')

    def _render_statevector(self):
        v = self.view
        text = dirac_text(v['state'], v['n'], self.relative.isChecked())
        self.dirac.setHtml(f'<p style="font-size:17px">|ψ⟩ = {text}</p>'
                           '<p style="color:gray">q0 is the leftmost bit of each basis label.</p>')

    def _render_reduced(self):
        if self.view is None:
            return
        v = self.view
        keep = [q for q, b in enumerate(self.keep_boxes) if b.isChecked()]
        if not keep:
            self.rho_table.setRowCount(0)
            self.rho_table.setColumnCount(0)
            self.heatmap.set_matrix(None, [])
            self.reduced_info.setText('Select at least one qubit.')
            return
        info = reduced_summary(v['state'], v['n'], keep)
        rho = info['rho']
        dim = rho.shape[0]
        labels = [f'|{i:0{len(keep)}b}⟩' for i in range(dim)]
        self.rho_table.setRowCount(dim)
        self.rho_table.setColumnCount(dim)
        self.rho_table.setHorizontalHeaderLabels(labels)
        self.rho_table.setVerticalHeaderLabels(labels)
        for r in range(dim):
            for c in range(dim):
                self.rho_table.setItem(r, c, _item(format_amplitude(rho[r, c]), tooltip=f'{rho[r, c]:.12g}'))
        self.rho_table.resizeColumnsToContents()
        for c in range(dim):
            self.rho_table.setColumnWidth(c, max(84, self.rho_table.columnWidth(c)))
        self.heatmap.set_matrix(rho, labels)
        names = ', '.join(f'q{q}' for q in info['keep'])
        text = (f'<b>ρ of {names}</b> · purity Tr(ρ²) = {info["purity"]:.4f} (1 = pure, '
                f'{1 / dim:.4g} = maximally mixed) · entanglement entropy S = {info["entropy"]:.4f} bits '
                f'(max {info["max_entropy"]:g}) · <b>{info["verdict"]}</b>')
        if info['bloch'] is not None:
            x, y, z = (round(c, 10) + 0.0 for c in info['bloch'])   # avoid printing -0.0000
            length = math.sqrt(x * x + y * y + z * z)
            text += f'<br>Bloch vector ({x:.4f}, {y:.4f}, {z:.4f}), length {length:.4f}'
        self.reduced_info.setText(text)

    def _render_circuit(self):
        a = self.view['analysis']
        stats = [
            ('Qubits (used)', f'{a["qubits"]} ({len(a["qubits_used"])} used)'),
            ('Unitary gates', a['total']),
            ('Single-qubit gates', a['single_qubit']),
            ('Two-qubit gates', a['two_qubit']),
            ('Three-qubit gates', a['three_qubit']),
            ('T-count', a['t_count']),
            ('Clifford gates', a['clifford']),
            ('Non-Clifford gates', a['non_clifford']),
            ('Parameterized gates', a['parameterized']),
            ('Drawn depth (occupied columns)', a['drawn_depth']),
            ('Minimum depth', a['minimum_depth']),
            ('Terminal measurements', a['measurements']),
        ]
        self.stats.setRowCount(len(stats))
        for r, (name, value) in enumerate(stats):
            self.stats.setItem(r, 0, _item(name, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter))
            self.stats.setItem(r, 1, _item(str(value)))
        counts = a['counts']
        self.counts.setRowCount(len(counts))
        for r, (name, count) in enumerate(counts.items()):
            self.counts.setItem(r, 0, _item(name))
            self.counts.setItem(r, 1, _item(str(count)))

    def apply_theme(self):
        self.heatmap.update()

    # ---- export ------------------------------------------------------------------------
    def _copy(self, text, what):
        QApplication.clipboard().setText(text)
        self.copy_status.setText(f'Copied {what}')

    def _copy_text(self):
        self._copy('|ψ⟩ = ' + dirac_text(self.view['state'], self.view['n'], self.relative.isChecked()), 'text')

    def _copy_latex(self):
        self._copy(r'\lvert\psi\rangle = ' + dirac_latex(self.view['state'], self.view['n'],
                                                         self.relative.isChecked()), 'LaTeX')

    def _copy_csv(self):
        self._copy(state_csv(self.view['state'], self.view['n']), 'CSV')

    def _save_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Save statevector', 'statevector.csv', 'CSV files (*.csv)')
        if not path:
            return
        if not path.lower().endswith('.csv'):
            path += '.csv'
        try:
            with open(path, 'w', encoding='utf-8', newline='') as handle:
                handle.write(state_csv(self.view['state'], self.view['n']))
            self.copy_status.setText('Saved ' + path)
        except OSError as exc:
            QMessageBox.warning(self, 'Save failed', str(exc))
