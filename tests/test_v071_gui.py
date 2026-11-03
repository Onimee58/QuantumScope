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


def test_parameter_columns_dice_randomize_and_best_of(app):
    import math
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    w.resize(1536, 900)
    w.show()
    w.load_library('qaoa', {'graph': 'ring6', 'layers': 3})
    for _ in range(3):
        app.processEvents()
    assert w._param_columns == 2 and w.param_scroll.height() >= w.param_list.height()   # 6 in 3 rows: no scrolling
    rows = w._param_rows_widgets
    assert w.param_rows.getItemPosition(w.param_rows.indexOf(rows[1]))[:2] == (0, 1)    # γ0 β0 side by side
    w.resize(1100, 900)
    for _ in range(3):
        app.processEvents()
    assert w._param_columns == 1
    before = dict(w.model.parameters)
    w.randomize_button.click()
    assert w.model.parameters != before and all(-math.pi <= v < math.pi for v in w.model.parameters.values())
    w.undo()
    assert w.model.parameters == before
    dice = next(b for b in rows[0].findChildren(QtWidgets.QToolButton) if b.text() == '🎲')
    dice.click()
    assert w.model.parameters['γ0'] != before['γ0'] and w.model.parameters['β0'] == before['β0']
    w.opt_multi.setChecked(True)
    w.opt_starts.setValue(3)
    dialog = w.optimize_parameters()
    assert dialog.summary.text().startswith('Best of 3 starts')


def test_no_sideways_scrolling_at_common_widths(app):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    w.show()
    w.load_library('qaoa', {'graph': 'ring6', 'layers': 3})              # long status note, 6 parameters
    for width in (1366, 1536):
        w.resize(width, 900)
        for _ in range(3):
            app.processEvents()
        assert w.page_scroll.horizontalScrollBar().maximum() == 0, width
    assert w.status.wordWrap()
