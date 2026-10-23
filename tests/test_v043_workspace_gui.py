"""Optional GUI check that the circuit workspace delegates to CircuitModel.

Skipped unless QUANTUMSCOPE_GUI_TESTS=1, because CI runners have no display.
Run locally with:  QUANTUMSCOPE_GUI_TESTS=1 QT_QPA_PLATFORM=offscreen pytest tests/test_v043_workspace_gui.py
"""
import os

import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def workspace(app):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    return CircuitWorkspace()


def test_widget_state_is_the_model_state(workspace):
    w = workspace
    w.clear()
    w.place('H', 0, 0)
    w.place('CX', 1, 0)        # anchored on q1, needs a control
    assert w._pending_gate == w.model.pending == ('CX', 0, (1,))
    w.cell_click(0, 0)         # occupied by H -> rejected, still pending
    assert 'occupied' in w.status.text() and w.model.pending
    w.cancel_pending()
    w.place('CX', 1, 1)
    w.cell_click(0, 1)
    assert w.gates is w.model.gates and set(w.gates) == {(0, 0), (1, 1)}
    assert w.grid.columnCount() == w.model.columns == 3
    assert w.grid.rowCount() == w.model.n == 3


def test_rejections_show_in_status_without_changing_the_circuit(workspace):
    w = workspace
    w.clear()
    w.place('H', 0, 0)
    before = dict(w.gates)
    w.place('X', 0, 0)
    assert w.status.text().startswith('Cell occupied') and w.gates == before


def test_remove_from_control_wire(workspace):
    w = workspace
    w.clear()
    w.place('CX', 2, 0)
    w.cell_click(0, 0)
    rect = w.grid.visualRect(w.grid.model().index(0, 0))
    w.remove_at(rect.center())
    assert w.gates == {}


def test_example_verification_renders_from_model(workspace):
    w = workspace
    index = [w.examples.itemText(i) for i in range(w.examples.count())].index('Half adder (a=1,b=1)')
    w.load_example(index)
    verdicts = [w.verify_table.item(r, 3).text() for r in range(w.verify_table.rowCount())]
    assert verdicts and all('PASS' in v for v in verdicts)
    w.undo()
    assert w.active_example == w.model.active_example
