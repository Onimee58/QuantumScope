"""Optional GUI checks for v0.7.1 (QUANTUMSCOPE_GUI_TESTS=1)."""
import os

import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_the_circuit_canvas_never_selects_cells(app):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    w.show()
    w.set_circuit(3, [])
    w.grid.setFocus()
    QTest.keyClick(w.grid, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    w.grid.setCurrentCell(1, 1)
    QTest.keyClick(w.grid, Qt.Key.Key_Right, Qt.KeyboardModifier.ShiftModifier)
    QTest.keyClick(w.grid, Qt.Key.Key_Down, Qt.KeyboardModifier.ShiftModifier)
    assert w.grid.selectedIndexes() == []                         # no highlighted "background rows"
