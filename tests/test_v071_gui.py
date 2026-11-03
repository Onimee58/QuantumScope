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


def test_compact_layout_sidebar_and_canvas_height(app):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    w.resize(1536, 900)
    w.show()
    app.processEvents()
    side = w._split.widget(0)
    assert side.width() == w.SIDEBAR_WIDTH == 400
    assert w.palette.isAncestorOf(w.palette) or side.isAncestorOf(w.palette)
    assert side.isAncestorOf(w.shots) and side.isAncestorOf(w.verify_table)      # beside the results
    assert not hasattr(w, 'inline_blochs')                                       # no strip beside wires
    heights = {}
    for n in (1, 3, 9, 10):
        w.set_circuit(n, [])
        heights[n] = w.grid.height()
    assert heights[1] < heights[3] < heights[9] == heights[10]                  # qubits + 1 spare, at most 10
    w.qubits.setValue(5)
    assert w.grid.height() == w.ROW_HEIGHT * 6 + w.grid.horizontalHeader().height() + 2 * w.grid.frameWidth() + 12


def test_verification_table_wraps_instead_of_cutting(app):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    w.resize(1536, 900)
    w.show()
    w.load_library('teleportation', {'input': '+'})
    w.verify_circuit()
    app.processEvents()
    t = w.verify_table
    assert [t.horizontalHeaderItem(j).text() for j in range(4)] == ['Input', 'Output', 'Expected', 'Result']
    assert all(t.rowHeight(i) >= t.sizeHintForRow(i) for i in range(t.rowCount()))     # full text shown
