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


def test_error_correction_explorer(app):
    from quantumscope.gui.qec_chart import ErrorCorrectionExplorer, crossing
    e = ErrorCorrectionExplorer()
    assert 'helps' in e.summary.text() and '0.0280' in e.summary.text()
    e.channel.setCurrentIndex(e.channel.findData('phase_flip'))
    assert 'HURTS' in e.summary.text()
    e.code.setCurrentIndex(e.code.findData('none'))
    assert 'no difference' in e.summary.text()
    e.slider.setValue(250)
    assert 'p = 0.250' in e.p_label.text()
    assert crossing([0, .1, .2], [0, .05, .3], [0, .1, .2]) == 0.2


def test_plot_button_appears_for_codes_and_plots_the_current_circuit(app):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    w.load_library('bit_flip_code', {'logical': '0', 'error': 'random', 'p': 0.1})
    w.verify_circuit()
    assert w.qec_button.isVisibleTo(w)
    from quantumscope.gui.qec_chart import plot_circuit
    dialog = plot_circuit(w)
    assert dialog.chart.encoded[4] == pytest.approx(3 * 0.1 ** 2 - 2 * 0.1 ** 3)
    w.load_library('teleportation', {'input': '+'})
    w.verify_circuit()
    assert not w.qec_button.isVisibleTo(w)


def test_explorer_opens_its_circuit(app):
    from PySide6.QtWidgets import QVBoxLayout, QWidget
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    from quantumscope.gui.qec_chart import ErrorCorrectionExplorer

    class Window(QWidget):
        def __init__(self):
            super().__init__()
            self.circuit_widget = CircuitWorkspace()
            self.explorer = ErrorCorrectionExplorer()
            QVBoxLayout(self).addWidget(self.explorer)
            self.launched = False

        def _launch_circuits(self):
            self.launched = True
    window = Window()
    window.explorer.open_button.click()
    model = window.circuit_widget.model
    assert window.launched and model.dynamic and len(model.noise) == 3 and model.n == 5


def test_example_title_bar_and_role_labels(app, monkeypatch):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    assert not w.example_bar.isVisibleTo(w)
    w.load_library('bit_flip_code', {'logical': '1', 'error': 'q1', 'p': 0.1})
    assert w.example_bar.isVisibleTo(w) and 'Bit-flip code' in w.example_title.text()
    assert 'strength' not in w.example_title.text()              # only shown for random errors
    assert w.grid.verticalHeaderItem(3).text().startswith('q3 syndrome')
    w.place('Z', 2, 0)
    assert '(edited)' in w.example_title.text()
    w.undo()
    assert '(edited)' not in w.example_title.text()

    def accept(dialog):
        return QtWidgets.QDialog.DialogCode.Accepted
    monkeypatch.setattr(QtWidgets.QDialog, 'exec', accept)
    w.change_example_parameters()                                # same values: rebuilt, still the example
    assert w.model.active_entry[0] == 'bit_flip_code'
    w.clear()
    assert not w.example_bar.isVisibleTo(w)


def test_saved_example_reopens_labelled(app, tmp_path, monkeypatch):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    w.load_library('teleportation', {'input': '+i'})
    path = str(tmp_path / 't.qscope')
    monkeypatch.setattr(QtWidgets.QFileDialog, 'getSaveFileName', staticmethod(lambda *a, **k: (path, '')))
    w.save_native()
    w.clear()
    monkeypatch.setattr(QtWidgets.QFileDialog, 'getOpenFileName', staticmethod(lambda *a, **k: (path, '')))
    w.load_native()
    assert 'Quantum teleportation' in w.example_title.text() and '10/10 PASS' in w.verify_status.text()
    assert w.grid.verticalHeaderItem(2).text().startswith('q2 Bob')


def test_role_labels_follow_the_example(app):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    w.load_library('bit_flip_code', {'logical': '1', 'error': 'q1', 'p': 0.1})
    labels = lambda: [w.grid.verticalHeaderItem(i).text() for i in range(w.n)]
    assert 'syndrome' in labels()[3]
    w.clear()
    assert not any('data' in l or 'syndrome' in l for l in labels()) and not w.example_bar.isVisibleTo(w)
    w.undo()
    assert 'syndrome' in labels()[3] and w.example_bar.isVisibleTo(w)
    w.qubits.setValue(6)
    assert w.n == 6 and not w.example_bar.isVisibleTo(w)            # no longer the example …
    assert 'syndrome' in labels()[3] and labels()[5].startswith('q5 |0')   # … but the labels stay
    w.label_qubit(5, 'extra ancilla')
    assert labels()[5].startswith('q5 extra ancilla')



def test_label_from_the_qubit_menu_and_exports(app, tmp_path, monkeypatch):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    w.set_circuit(2, [])
    monkeypatch.setattr(QtWidgets.QInputDialog, 'getText', staticmethod(lambda *a, **k: ('control', True)))
    w.label_qubit(0)
    assert w.grid.verticalHeaderItem(0).text().startswith('q0 control')
    w.place('H', 0, 0)
    for name, action in (('l.qasm', w.export_qasm), ('l.pdf', w.export_pdf), ('l.qscope', w.save_native)):
        path = str(tmp_path / name)
        monkeypatch.setattr(QtWidgets.QFileDialog, 'getSaveFileName', staticmethod(lambda *a, p=path, **k: (p, '')))
        monkeypatch.setattr(QtWidgets.QMessageBox, 'question',
                            staticmethod(lambda *a, **k: QtWidgets.QMessageBox.StandardButton.No))
        action()
    assert '// q0: control' in (tmp_path / 'l.qasm').read_text()
    w.clear()
    monkeypatch.setattr(QtWidgets.QFileDialog, 'getOpenFileName', staticmethod(lambda *a, **k: (str(tmp_path / 'l.qscope'), '')))
    w.load_native()
    assert w.grid.verticalHeaderItem(0).text().startswith('q0 control')
