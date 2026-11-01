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


def test_qasm_and_pdf_export_of_a_dynamic_circuit(teleport, tmp_path, monkeypatch):
    monkeypatch.setattr(QtWidgets.QMessageBox, 'warning', staticmethod(lambda *a, **k: pytest.fail(str(a[2]))))
    for name, action in (('t.qasm', teleport.export_qasm), ('t.pdf', teleport.export_pdf)):
        path = str(tmp_path / name)
        monkeypatch.setattr(QtWidgets.QFileDialog, 'getSaveFileName', staticmethod(lambda *a, p=path, **k: (p, '')))
        monkeypatch.setattr(QtWidgets.QMessageBox, 'question',
                            staticmethod(lambda *a, **k: QtWidgets.QMessageBox.StandardButton.No))
        action()
        assert os.path.getsize(path) > 100
    text = (tmp_path / 't.qasm').read_text()
    assert 'if(m1==1) x q[2];' in text and 'noise' not in text
    monkeypatch.setattr(QtWidgets.QFileDialog, 'getOpenFileName', staticmethod(lambda *a, **k: (str(tmp_path / 't.qasm'), '')))
    monkeypatch.setattr(teleport, '_show_notes', lambda *a: None)
    teleport.clear()
    teleport.load_qasm()
    assert teleport.model.dynamic and len(teleport.model.conditions) == 2


def test_examples_menu_and_verification_panel(app):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    items = [w.examples.itemText(i) for i in range(w.examples.count())]
    assert 'Quantum teleportation' in items and 'Superdense coding' in items
    w.load_library('teleportation', {'input': '-i'})
    w.verify_circuit()
    assert '10/10 PASS' in w.verify_status.text() and w.model.dynamic
    w.load_library('superdense', {'b0': 1, 'b1': 1})
    w.verify_circuit()
    assert '1/1 PASS' in w.verify_status.text()


def test_teleportation_experiment(app):
    from quantumscope.gui.teleportation_experiment import TeleportationDialog
    d = TeleportationDialog()
    assert d.step_label.text().startswith('Step 1') and not d.back.isEnabled() and not d.result.isEnabled()
    for _ in range(4):
        d.next.click()
    assert d.step_label.text().startswith('Step 5') and not d.next.isEnabled()
    assert d.scene.view['bob_fidelity'] == pytest.approx(1)
    d.go(3)
    d.result.setCurrentIndex(d.result.findData('11'))
    assert 'X and Z' in d.explain.text() and d.scene.view['record'] == '11'
    d.run_once.click()
    assert d.scene.view['record'] in ('00', '01', '10', '11')
    d.preset.setCurrentIndex(d.preset.findData('custom'))
    d.theta.setValue(100)
    d.go(4)
    assert d.theta.isEnabled() and d.scene.view['bob_fidelity'] == pytest.approx(1)


def test_teleportation_experiment_opens_the_matching_circuit(app):
    from PySide6.QtWidgets import QWidget, QVBoxLayout
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    from quantumscope.gui.teleportation_experiment import TeleportationDialog

    class Window(QWidget):
        def __init__(self):
            super().__init__()
            self.circuit_widget = CircuitWorkspace()
            self.launched = False
            self.dialog = TeleportationDialog()
            QVBoxLayout(self).addWidget(self.dialog)

        def _launch_circuits(self):
            self.launched = True
    window = Window()
    window.dialog.preset.setCurrentIndex(window.dialog.preset.findData('-'))
    window.dialog.open_circuit.click()
    model = window.circuit_widget.model
    assert window.launched and model.dynamic and model.initial_states[0].label == '|−⟩'
    assert all(r.passed for r in model.verification()[0])
