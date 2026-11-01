"""Optional GUI checks for mid-circuit measurement, conditions and branches (QUANTUMSCOPE_GUI_TESTS=1)."""
import os

import numpy as np
import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def teleport(app):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    from quantumscope.physics.initial_states import InitialState
    w = CircuitWorkspace()
    w.set_circuit(3, [], initial_states=[InitialState.preset('+i')] + [InitialState.preset('0')] * 2)
    w.place('H', 1, 0)
    w.place('CX', 2, 1)
    w.cell_click(1, 1)
    w.place('CX', 1, 2)
    w.cell_click(0, 2)
    w.place('H', 0, 3)
    w.place('M→c', 0, 4)
    w.place('M→c', 1, 4)
    w.place('X', 2, 5)
    w.model.set_condition(2, 5, 1)
    w.place('Z', 2, 6)
    w.model.set_condition(2, 6, 0)
    w._changed()
    return w


def test_classical_palette_and_placement(teleport):
    names = [teleport.classical_palette.item(i).text() for i in range(teleport.classical_palette.count())]
    assert names == ['M→c', 'Reset']
    assert teleport.model.operation_at(0, 4)[0] == 'measure' and teleport.model.wires[(1, 4)].cbit == 1
    teleport.place('Reset', 0, 5)
    assert teleport.model.operation_at(0, 5)[0] == 'reset'
    teleport.place('M→c', 2, 0)                                # occupied by nothing? column 0 has H on q1 only
    assert teleport.model.operation_at(2, 0)[0] == 'measure'


def test_dynamic_status_and_result(teleport):
    assert 'dynamic circuit' in teleport.status.text()
    text = teleport.result.toPlainText()
    assert '4 branches' in text and 'fidelity with ideal' not in text


def test_branches_tab_shows_the_teleported_state(teleport):
    teleport.open_state_inspector()
    inspector = teleport._inspector
    assert inspector.tabs.tabText(4) == 'Branches'
    teleport.step.setValue(teleport.step.maximum())
    text = inspector.branch_view.toPlainText()
    assert text.count('(0.00, 1.00, 0.00)') >= 4                # q2 = |+i⟩ in every branch
    assert 'Dynamic circuit' in inspector.where.text()


def test_shots_record_the_classical_bits(teleport):
    teleport.measure()
    assert 'Classical bits c0c1' in teleport.bars.title
    total = sum(int(part.split()[-1]) for part in teleport.result.toPlainText().split(':', 1)[1].split('   ') if part.strip())
    assert total == teleport.shots.value()


def test_condition_menu_and_measure_bit(teleport, monkeypatch):
    def pick(label):
        def exec_(self, menu, *a):
            for action in menu.actions():
                if action.menu():
                    for sub in action.menu().actions():
                        if sub.text() == label:
                            return sub
                if action.text() == label:
                    return action
            return None
        return exec_
    pos = teleport.grid.visualRect(teleport.grid.model().index(2, 5)).center()
    monkeypatch.setattr(type(teleport), '_exec_menu', pick('c0 = 0'))
    teleport.gate_context_menu(pos)
    assert teleport.model.conditions[(2, 5)] == (0, 0)
    monkeypatch.setattr(type(teleport), '_exec_menu', pick('Always (no condition)'))
    teleport.gate_context_menu(pos)
    assert (2, 5) not in teleport.model.conditions
    pos = teleport.grid.visualRect(teleport.grid.model().index(0, 4)).center()
    monkeypatch.setattr(type(teleport), '_exec_menu', pick('c3'))
    teleport.gate_context_menu(pos)
    assert teleport.model.wires[(0, 4)].cbit == 3


def test_tools_explain_why_dynamic_circuits_are_excluded(teleport, monkeypatch):
    messages = []
    monkeypatch.setattr(QtWidgets.QMessageBox, 'information', staticmethod(lambda *a, **k: messages.append(a[2])))
    teleport.simplify_dialog()
    assert 'mid-circuit' in messages[-1]


def test_save_and_reopen_keeps_everything(teleport, tmp_path, monkeypatch):
    path = str(tmp_path / 'teleport.qscope')
    monkeypatch.setattr(QtWidgets.QFileDialog, 'getSaveFileName', staticmethod(lambda *a, **k: (path, '')))
    teleport.save_native()
    wires, conditions = dict(teleport.model.wires), dict(teleport.model.conditions)
    final = teleport.noisy_view[1][-1]
    teleport.clear()
    monkeypatch.setattr(QtWidgets.QFileDialog, 'getOpenFileName', staticmethod(lambda *a, **k: (path, '')))
    teleport.load_native()
    assert teleport.model.wires == wires and teleport.model.conditions == conditions
    assert np.allclose(teleport.noisy_view[1][-1], final)
