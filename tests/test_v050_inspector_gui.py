"""Optional GUI checks for the State Inspector and initial states (QUANTUMSCOPE_GUI_TESTS=1)."""
import math
import os

import numpy as np
import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')

from quantumscope.physics.circuits import Gate  # noqa: E402
from quantumscope.physics.initial_states import InitialState  # noqa: E402


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def workspace(app):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    w.set_circuit(2, [Gate('H', (0,)), Gate('CX', (0, 1))])
    return w


def test_inspector_follows_steps_and_freezes(workspace, app):
    w = workspace
    w.open_state_inspector()
    insp = w._inspector
    assert 'column 2 of 2' in insp.where.text() and '|11⟩' in insp.dirac.toPlainText()
    w.step.setValue(1)
    app.processEvents()
    assert 'column 1 of 2' in insp.where.text() and '|11⟩' not in insp.dirac.toPlainText()
    insp.freeze.setChecked(True)
    w.step.setValue(2)
    assert 'column 1 of 2' in insp.where.text()
    insp.freeze.setChecked(False)
    assert 'column 2 of 2' in insp.where.text()
    w.open_state_inspector()
    assert w._inspector is insp           # one window, brought to the front


def test_inspector_tabs_show_bell_physics(workspace):
    workspace.open_state_inspector()
    insp = workspace._inspector
    assert insp.amp_table.rowCount() == 2
    assert 'Mixed' in insp.reduced_info.text() and '1.0000 bits' in insp.reduced_info.text()
    stats = {insp.stats.item(r, 0).text(): insp.stats.item(r, 1).text() for r in range(insp.stats.rowCount())}
    assert stats['Two-qubit gates'] == '1' and stats['Minimum depth'] == '2'


def test_reduced_qubit_limit(workspace):
    workspace.set_circuit(4, [Gate('H', (q,)) for q in range(4)])
    workspace.open_state_inspector()
    insp = workspace._inspector
    for box in insp.keep_boxes[:3]:
        box.setChecked(True)
    assert not insp.keep_boxes[3].isEnabled() and insp.rho_table.rowCount() == 8


def test_initial_state_labels_simulation_and_copy(workspace, app):
    w = workspace
    w.set_initial_state(1, InitialState.preset('1'))
    assert w.grid.verticalHeaderItem(1).text().startswith('q1 |1⟩')
    w.open_state_inspector()
    assert '|01⟩' in w._inspector.dirac.toPlainText() or '|10⟩' in w._inspector.dirac.toPlainText()
    w._inspector._copy_latex()
    assert app.clipboard().text().startswith(r'\lvert\psi\rangle')


def test_save_open_qasm_and_pdf_with_initial_states(workspace, tmp_path, monkeypatch):
    w = workspace
    w.set_initial_state(0, InitialState(math.pi / 3, 1.0))
    final = w.model.simulate().column_states[-1]
    path = tmp_path / 'c.qscope'
    monkeypatch.setattr(QtWidgets.QFileDialog, 'getSaveFileName', staticmethod(lambda *a, **k: (str(path), '')))
    monkeypatch.setattr(QtWidgets.QFileDialog, 'getOpenFileName', staticmethod(lambda *a, **k: (str(path), '')))
    w.save_native()
    w.clear()
    w.load_native()
    assert w.model.initial_states[0] == InitialState(math.pi / 3, 1.0)
    assert np.allclose(w.model.simulate().column_states[-1], final)
    qasm = tmp_path / 'c.qasm'
    monkeypatch.setattr(QtWidgets.QFileDialog, 'getSaveFileName', staticmethod(lambda *a, **k: (str(qasm), '')))
    w.export_qasm()
    assert 'u3(' in qasm.read_text()
    pdf = tmp_path / 'c.pdf'
    monkeypatch.setattr(QtWidgets.QFileDialog, 'getSaveFileName', staticmethod(lambda *a, **k: (str(pdf), '')))
    monkeypatch.setattr(QtWidgets.QMessageBox, 'question', staticmethod(lambda *a, **k: QtWidgets.QMessageBox.StandardButton.Yes))
    w.export_pdf()
    assert pdf.stat().st_size > 1000
