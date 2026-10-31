"""Optional GUI checks for blocks, algorithms and Gate Explorer additions (QUANTUMSCOPE_GUI_TESTS=1)."""
import os

import numpy as np
import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')
from PySide6.QtCore import QPointF, Qt  # noqa: E402
from PySide6.QtGui import QMouseEvent  # noqa: E402


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def workspace(app):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    w.resize(1300, 900)
    w.show()
    w.load_library('grover', {'n': 3, 'marked': '101', 'iterations': -1})
    app.processEvents()
    return w


def first_block(w):
    return w.model.block_summary()[0][0]


def test_algorithm_loads_with_blocks_and_passes(workspace):
    assert len(workspace.model.blocks) == 4
    assert 'PASS' in workspace.verify_status.text()
    assert workspace.status.text().startswith('Loaded Grover search')
    workspace.refresh()
    assert '43 gates' in workspace.status.text() and '4 blocks' in workspace.status.text()


def test_double_click_expands_and_chip_collapses(workspace, app):
    w = workspace
    bid = first_block(w)
    pl = w.model.blocks[bid]
    w.edit_gate_at(pl.block.low, pl.col)                    # what a double-click calls
    assert w.model.blocks[bid].expanded
    w.grid.viewport().repaint()
    app.processEvents()
    chip = w.grid._chips[bid].center()
    press = QMouseEvent(QMouseEvent.Type.MouseButtonPress, QPointF(chip), QPointF(chip),
                        Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    w.grid.mousePressEvent(press)
    assert not w.model.blocks[bid].expanded


def test_locked_cells_explain_themselves(workspace):
    w = workspace
    bid = first_block(w)
    w.expand_block(bid)
    pl = w.model.blocks[bid]
    w.edit_gate_at(1, pl.col + 1)
    assert 'Part of block Oracle' in w.status.text()
    w.place('X', 1, pl.col + 1)
    assert 'Part of block Oracle' in w.status.text()


def test_block_actions_through_the_widget(workspace):
    w = workspace
    final = w.model.simulate().column_states[-1]
    bid = first_block(w)
    w.ungroup_block(bid)
    assert bid not in w.model.blocks and np.allclose(w.model.simulate().column_states[-1], final)
    w.undo()
    w.remove_block(bid)
    assert bid not in w.model.blocks
    w.insert_column(0)                                       # never raises out of the widget


def test_edit_block_dialog(workspace, monkeypatch):
    from quantumscope.gui import parameter_dialog
    w = workspace
    bid = first_block(w)

    class Accepting(parameter_dialog.ParameterDialog):
        def exec(self):
            self.fields['marked'].setText('011')
            return QtWidgets.QDialog.DialogCode.Accepted
    monkeypatch.setattr(parameter_dialog, 'ParameterDialog', Accepting)
    w.edit_block_dialog(bid)
    assert w.model.blocks[bid].block.param('marked') == '011'


def test_parameter_dialog_resizes_bits_and_validates(app):
    from quantumscope.gui.parameter_dialog import ParameterDialog
    from quantumscope.physics.algorithms import entry
    e = entry('grover')
    d = ParameterDialog(e.title, e.params, {})
    d.fields['n'].setValue(5)
    assert len(d.fields['marked'].text()) == 5 and d.fields['iterations'].text() == 'Optimal'
    d.fields['marked'].setText('1')
    d._accept()
    assert 'bits' in d.error.text() and d.result() != QtWidgets.QDialog.DialogCode.Accepted


def test_examples_menu_loads_new_reversible_examples(workspace):
    w = workspace
    index = [w.examples.itemText(i) for i in range(w.examples.count())].index('Full adder')
    w.load_example(index)
    assert w.model.active_entry[0] == 'full_adder' and '8/8 PASS' in w.verify_status.text()


def test_try_it_and_worked_identity(workspace):
    from quantumscope.gui.gate_explorer import GateExplorer
    w = workspace
    g = GateExplorer('CX', w)
    assert [g.tabs.tabText(i) for i in range(g.tabs.count())][-1] == 'Worked identity'
    g._try_it()
    assert [s.label for s in w.model.initial_states] == ['|+⟩', '|0⟩'] and w.model.blocks == {}


def test_block_contents_viewer(workspace):
    from quantumscope.gui.gate_explorer import BlockExplorer
    b = BlockExplorer(workspace.model.blocks[first_block(workspace)].block, workspace)
    tables = b.findChildren(QtWidgets.QTableWidget)
    assert tables and tables[0].rowCount() == 5


def test_save_reopen_qasm_and_pdf_with_blocks(workspace, tmp_path, monkeypatch):
    w = workspace
    w.expand_block(first_block(w))
    final = w.model.simulate().column_states[-1]
    expected = [(pl.block, pl.col, pl.expanded) for pl in w.model.blocks.values()]
    monkeypatch.setattr(QtWidgets.QMessageBox, 'warning', staticmethod(lambda *a, **k: pytest.fail(str(a[2]))))
    monkeypatch.setattr(QtWidgets.QMessageBox, 'question',
                        staticmethod(lambda *a, **k: QtWidgets.QMessageBox.StandardButton.Yes))
    for name, action in (('c.qscope', w.save_native), ('c.qasm', w.export_qasm), ('c.pdf', w.export_pdf)):
        path = str(tmp_path / name)
        monkeypatch.setattr(QtWidgets.QFileDialog, 'getSaveFileName', staticmethod(lambda *a, p=path, **k: (p, '')))
        action()
        assert os.path.getsize(path) > 100
    monkeypatch.setattr(QtWidgets.QFileDialog, 'getOpenFileName',
                        staticmethod(lambda *a, **k: (str(tmp_path / 'c.qscope'), '')))
    w.clear()
    w.load_native()
    assert [(pl.block, pl.col, pl.expanded) for pl in w.model.blocks.values()] == expected
    assert np.allclose(w.model.simulate().column_states[-1], final)


def test_dark_dialogs_are_readable(app):
    from quantumscope.gui.theme import STYLESHEET
    from quantumscope.gui.gate_explorer import GateExplorer
    app.setStyleSheet(STYLESHEET)
    try:
        g = GateExplorer('H')
        g.resize(500, 300)
        g.show()
        app.processEvents()
        image = g.grab().toImage()
        color = image.pixelColor(3, image.height() - 3)
        assert color.lightness() < 80                       # dark background, not light grey
    finally:
        app.setStyleSheet('')
