"""Optional GUI checks for v0.6.2 (QUANTUMSCOPE_GUI_TESTS=1)."""
import os

import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_several_bits_condition_from_the_menu(app, monkeypatch):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    w.set_circuit(3, [])
    w.place('M→c', 0, 0)
    w.place('M→c', 1, 0)
    w.place('X', 2, 1)
    pick = lambda self, menu, *a: next(s for act in menu.actions() if act.menu()
                                       for s in act.menu().actions() if s.text() == 'Several bits…')
    monkeypatch.setattr(type(w), '_exec_menu', pick)

    def choose(dialog):
        boxes = dialog.findChildren(QtWidgets.QComboBox)
        boxes[0].setCurrentText('1')
        boxes[1].setCurrentText('0')
        return QtWidgets.QDialog.DialogCode.Accepted
    monkeypatch.setattr(QtWidgets.QDialog, 'exec', choose)
    pos = w.grid.visualRect(w.grid.model().index(2, 1)).center()
    w.gate_context_menu(pos)
    assert w.model.conditions[(2, 1)] == ((0, 1), (1, 0))

    def only_one(dialog):
        boxes = dialog.findChildren(QtWidgets.QComboBox)
        boxes[0].setCurrentText('any')
        boxes[1].setCurrentText('1')
        return QtWidgets.QDialog.DialogCode.Accepted
    monkeypatch.setattr(QtWidgets.QDialog, 'exec', only_one)
    w.gate_context_menu(pos)
    assert w.model.conditions[(2, 1)] == (1, 1)                 # one bit chosen: a single-bit condition
