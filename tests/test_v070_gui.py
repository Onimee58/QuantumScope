"""Optional GUI checks for v0.7.0 (QUANTUMSCOPE_GUI_TESTS=1)."""
import os

import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')
from test_v070_updater import RELEASES, github  # noqa: E402


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def answers(monkeypatch):
    seen = {'info': [], 'warn': []}
    monkeypatch.setattr(QtWidgets.QMessageBox, 'question',
                        staticmethod(lambda *a, **k: QtWidgets.QMessageBox.StandardButton.Yes))
    monkeypatch.setattr(QtWidgets.QMessageBox, 'information', staticmethod(lambda *a, **k: seen['info'].append(a[2])))
    monkeypatch.setattr(QtWidgets.QMessageBox, 'warning', staticmethod(lambda *a, **k: seen['warn'].append(a[2])))
    monkeypatch.setattr(QtWidgets.QDialog, 'exec', lambda self: QtWidgets.QDialog.DialogCode.Accepted)
    return seen


def test_declined_means_no_connection(app, monkeypatch):
    from quantumscope.gui.update_dialog import check_for_updates
    monkeypatch.setattr(QtWidgets.QMessageBox, 'question',
                        staticmethod(lambda *a, **k: QtWidgets.QMessageBox.StandardButton.No))
    assert check_for_updates(None, opener=lambda *a, **k: pytest.fail('connected without permission')) == 'declined'


def test_up_to_date(app, answers, monkeypatch):
    from quantumscope.gui import update_dialog
    monkeypatch.setattr(update_dialog, '__version__', '0.7.0')
    assert update_dialog.check_for_updates(None, opener=github(), platform='linux') == 'up to date'
    assert 'latest version' in answers['info'][-1]


def test_running_from_source_shows_git_pull(app, answers):
    from quantumscope.gui.update_dialog import check_for_updates
    outcome = check_for_updates(None, opener=github(), platform='linux', frozen=False)
    assert outcome == 'source' and 'git pull' in answers['info'][-1]


def test_full_update_flow(app, answers, tmp_path):
    from quantumscope.gui.update_dialog import check_for_updates
    ran = []
    outcome = check_for_updates(None, opener=github(), platform='linux', frozen=True, folder=str(tmp_path),
                                run=lambda command: ran.append(command))
    assert outcome == 'installing' and ran[0][:2] == ['pkexec', 'apt-get']
    assert os.path.exists(ran[0][-1])


def test_tampered_download_is_refused(app, answers, tmp_path):
    from quantumscope.gui.update_dialog import check_for_updates
    outcome = check_for_updates(None, opener=github(installer=b'bad'), platform='win32', frozen=True,
                                folder=str(tmp_path), run=lambda c: pytest.fail('ran a bad installer'))
    assert outcome == 'download failed' and 'does not match' in answers['warn'][-1] and os.listdir(tmp_path) == []


def test_settings_has_an_updates_section(app):
    from quantumscope.gui.settings_dialog import SECTIONS, SettingsDialog
    calls = []

    class Host:
        def check_for_updates(self):
            calls.append(True)
    d = SettingsDialog(Host())
    assert 'Updates' in SECTIONS
    d.nav.setCurrentRow(SECTIONS.index('Updates'))
    button = next(b for b in d.findChildren(QtWidgets.QPushButton) if b.text() == 'Check for updates…')
    button.click()
    assert calls == [True]


def test_about_page_has_check_for_updates(app, monkeypatch):
    from quantumscope.gui import update_dialog
    from quantumscope.gui.main_window import AboutDialog
    calls = []
    monkeypatch.setattr(update_dialog, 'check_for_updates', lambda parent: calls.append(parent))
    about = AboutDialog()
    assert about.update_button.text() == 'Check for updates…'
    about.update_button.click()
    assert calls == [about]


@pytest.fixture
def ansatz(app):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    w.set_circuit(2, [])
    w.place('RY', 0, 0)
    w.place('RY', 1, 0)
    w.place('CX', 1, 1)
    w.cell_click(0, 1)
    return w


def test_gate_editor_accepts_parameter_names(ansatz, monkeypatch):
    def type_into(text):
        def run(dialog):
            dialog.findChild(QtWidgets.QLineEdit).setText(text)
            dialog.findChild(QtWidgets.QDialogButtonBox).accepted.emit()
            return QtWidgets.QDialog.DialogCode.Accepted
        return run
    monkeypatch.setattr(QtWidgets.QDialog, 'exec', type_into('theta'))
    ansatz.edit_gate_at(0, 0)
    monkeypatch.setattr(QtWidgets.QDialog, 'exec', type_into('2*theta'))
    ansatz.edit_gate_at(1, 0)
    assert ansatz.model.bindings[(1, 0, 'angle')] == ('theta', 2.0) and 'theta' in ansatz._param_widgets
    monkeypatch.setattr(QtWidgets.QDialog, 'exec', type_into('pi/2'))     # a plain number unbinds
    ansatz.edit_gate_at(1, 0)
    assert (1, 0, 'angle') not in ansatz.model.bindings


def test_slider_drag_updates_gates_and_is_one_undo_step(ansatz):
    import math
    ansatz.model.bind(0, 0, 'angle', 'θ')
    ansatz.model.bind(1, 0, 'angle', 'θ', 2.0)
    ansatz._refresh_parameter_panel()
    slider, box = ansatz._param_widgets['θ']
    start = ansatz.model.parameters['θ']
    slider.sliderPressed.emit()
    for v in (300, 600, 900):
        slider.setValue(v)
    assert ansatz.model.parameters['θ'] == pytest.approx(math.pi / 2) and box.value() == pytest.approx(math.pi / 2, abs=1e-6)
    assert ansatz.model.gates[(1, 0)].angle == pytest.approx(math.pi)
    ansatz.undo()
    assert ansatz.model.parameters['θ'] == pytest.approx(start)


def test_observable_panel_and_exports(ansatz, tmp_path, monkeypatch):
    ansatz.observable_edit.setText('Z0 Z1 + 0.5 X0')
    ansatz._observable_edited()
    assert '⟨O⟩' in ansatz.expectation_label.text() and '-1.118034' in ansatz.expectation_label.text()
    ansatz.observable_edit.setText('Z7')
    ansatz._observable_edited()
    assert 'no qubit q7' in ansatz.expectation_label.text()
    ansatz.model.bind(0, 0, 'angle', 'θ')
    for name, action in (('v.qasm', ansatz.export_qasm), ('v.qscope', ansatz.save_native)):
        path = str(tmp_path / name)
        monkeypatch.setattr(QtWidgets.QFileDialog, 'getSaveFileName', staticmethod(lambda *a, p=path, **k: (p, '')))
        action()
    text = (tmp_path / 'v.qasm').read_text()
    assert '// parameter θ' in text and '// observable: Z0 Z1 + 0.5 X0' in text
    ansatz.clear()
    assert not ansatz._param_widgets
    monkeypatch.setattr(QtWidgets.QFileDialog, 'getOpenFileName', staticmethod(lambda *a, **k: (str(tmp_path / 'v.qscope'), '')))
    ansatz.load_native()
    assert 'θ' in ansatz._param_widgets and ansatz.observable_edit.text() == 'Z0 Z1 + 0.5 X0'


def test_parameter_panel_shows_when_in_use_and_explains_observables(app):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    w.show()
    w.set_circuit(1, [])
    assert not w.param_panel.isVisible()                          # nothing in use: out of the way
    w.param_toggle.setChecked(True)
    assert w.param_panel.isVisible()
    w.param_toggle.setChecked(False)
    w.place('RY', 0, 0)
    w.model.bind(0, 0, 'angle', 'θ')
    w._changed()
    assert w.param_panel.isVisible()                              # a parameter brings it up
    examples = [w.observable_examples.itemData(i) for i in range(w.observable_examples.count())]
    assert examples[0] is None and 'Z0' in examples and 'Z0 Z1' not in examples   # one qubit
    w.qubits.setValue(3)
    examples = [w.observable_examples.itemData(i) for i in range(w.observable_examples.count())]
    assert 'Z0 Z1' in examples and any(e and e.startswith('Z0 Z1 + Z1 Z2') for e in examples)
    w.observable_examples.activated.emit(examples.index('Z0 Z1'))
    assert w.model.observable == 'Z0 Z1' and 'observable is a quantity' in w.param_panel.findChildren(
        QtWidgets.QLabel)[-2].text() + ''.join(l.text() for l in w.param_panel.findChildren(QtWidgets.QLabel))
    w.clear()
    assert not w.param_panel.isVisible()


def test_optimize_and_landscape_from_the_panel(app):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    w.load_library('vqe', {'problem': 'h2', 'layers': 1})
    assert w.opt_button.isEnabled() and w.param_panel.isVisibleTo(w)
    before = dict(w.model.parameters)
    dialog = w.optimize_parameters()
    assert 'ground state is reached' in dialog.summary.text()
    assert w.model.expectation() == pytest.approx(-1.137306, abs=1e-6)
    w.undo()                                                     # the whole optimization is one undo step
    assert w.model.parameters == pytest.approx(before)
    landscape = w.show_landscape()
    assert landscape.view.data is not None and len(landscape.view.data) == 3
    landscape.second.setCurrentIndex(0)
    assert len(landscape.draw()) == 2                            # one parameter: a curve
    w.observable_edit.setText('')
    w._observable_edited()
    assert not w.opt_button.isEnabled()


def test_parameter_rows_are_never_squashed_and_the_page_grows(app):
    from PySide6.QtWidgets import QLabel
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    w.resize(1400, 950)
    w.show()
    w.set_circuit(2, [])
    app.processEvents()
    empty_page = w._center.minimumHeight()
    for name in ('a', 'b', 'c', 'd', 'e', 'f'):
        w.model.add_parameter(name)
    w.observable_edit.setText('Z0')
    w._observable_edited()
    app.processEvents()
    rows = [w.param_rows.itemAt(i).widget() for i in range(w.param_rows.count())]
    assert all(r.height() == w.PARAM_ROW for r in rows)
    assert [b.y() - a.y() for a, b in zip(rows, rows[1:])] == [w.PARAM_ROW + 4] * 5   # spaced, not overlapping
    assert w.param_scroll.height() < w.param_list.height()                            # extra rows scroll
    assert w._center.minimumHeight() > empty_page
    help_label = next(l for l in w.findChildren(QLabel) if l.text().startswith('Drag a multi-qubit'))
    bottom = w.param_panel.mapTo(w._center, w.param_panel.rect().bottomLeft()).y()
    assert bottom < help_label.mapTo(w._center, help_label.rect().topLeft()).y()     # nothing drawn over it
    w.clear()
    app.processEvents()
    assert not w.param_panel.isVisible() and w._center.minimumHeight() <= empty_page   # shrinks back


def test_convergence_summary_and_chart_range(app):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    from quantumscope.gui.variational_views import ConvergenceChart
    w = CircuitWorkspace()
    w.set_circuit(1, [])
    w.place('RY', 0, 0)
    w.model.bind(0, 0, 'angle', 'θ')
    w.model.set_parameter('θ', 3.141592653589793)
    w.observable_edit.setText('Z0')
    w._observable_edited()
    dialog = w.optimize_parameters()
    assert 'already at the exact minimum' in dialog.summary.text()
    w.model.set_parameter('θ', 0.3)
    dialog = w.optimize_parameters()
    import re
    text = dialog.summary.text()
    steps = int(re.search(r'after (\d+) step', text).group(1))
    assert 'went from' in text and (f'{steps} step ' if steps == 1 else f'{steps} steps ') in text
    assert 'circuit evaluations' in text
    chart = ConvergenceChart()
    chart.resize(600, 320)
    chart.set_data([-1.0000000001, -1.0], -1.0)
    chart.grab()                                                  # paints without collapsing to a zero range


def test_maxcut_graph_window_follows_the_circuit(app):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    w.load_library('qaoa', {'graph': 'ring4', 'layers': 1})
    w.verify_circuit()
    assert w.graph_button.isVisibleTo(w)
    graph = w.show_maxcut_graph()
    before = graph.summary.text()
    w.optimize_parameters().close()
    assert graph.summary.text() != before and 'ratio 0.750' in graph.summary.text()   # updated live
    graph.view.grab()
    w.clear()
    assert 'no longer a QAOA example' in graph.summary.text()
    w.load_library('teleportation', {'input': '+'})
    w.verify_circuit()
    assert not w.graph_button.isVisibleTo(w)


def test_optimizer_results_land_inside_the_slider_range(app):
    import math
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    w.load_library('qaoa', {'graph': 'ring4', 'layers': 1})
    w.model.set_parameter('γ0', 9.0)                              # far outside −π…π
    w.opt_method.setCurrentIndex(w.opt_method.findData('gradient'))
    w.optimize_parameters().close()
    assert all(-math.pi <= v < math.pi for v in w.model.parameters.values())
    slider, _ = w._param_widgets['γ0']
    assert slider.minimum() < slider.value() < slider.maximum()   # not pinned at an end
    assert w.observable_edit.width() > w.observable_examples.width()
