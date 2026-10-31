"""Optional GUI checks for Settings, autosave and recovery (QUANTUMSCOPE_GUI_TESTS=1)."""
import os

import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')
from PySide6.QtCore import Qt  # noqa: E402

from quantumscope.gui import preferences as prefs  # noqa: E402


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture(autouse=True)
def clean(tmp_path, monkeypatch):
    monkeypatch.setenv('QUANTUMSCOPE_SETTINGS_FILE', str(tmp_path / 'settings.ini'))
    monkeypatch.setenv('QUANTUMSCOPE_DATA_DIR', str(tmp_path / 'data'))
    monkeypatch.setattr(QtWidgets.QMessageBox, 'question',
                        staticmethod(lambda *a, **k: QtWidgets.QMessageBox.StandardButton.Yes))


class Host:
    def __init__(self):
        self.calls = []

    def apply_theme(self, choice):
        self.calls.append(('theme', choice))

    def apply_preferences(self):
        self.calls.append(('prefs',))

    def graphics_information(self):
        return 'Renderer: test GPU'

    def restart_application(self):
        self.calls.append(('restart',))


def test_settings_window_title_buttons_and_size(app):
    from quantumscope.gui.settings_dialog import SECTIONS, SettingsDialog
    d = SettingsDialog(Host())
    flags = d.windowFlags()
    assert d.windowTitle() == 'Settings'
    assert not flags & Qt.WindowType.WindowMaximizeButtonHint and not flags & Qt.WindowType.WindowMinimizeButtonHint
    assert d.minimumSize() == d.maximumSize()
    assert [d.nav.item(i).text() for i in range(d.nav.count())] == list(SECTIONS)


def test_changes_are_saved_and_applied(app):
    from quantumscope.gui.settings_dialog import SettingsDialog
    host = Host()
    d = SettingsDialog(host)
    d.theme.setCurrentIndex(d.theme.findData('light'))
    assert prefs.get('appearance/theme') == 'light' and ('theme', 'light') in host.calls
    d.default_shots.setValue(2048)
    assert prefs.get('circuits/default_shots') == 2048 and ('prefs',) in host.calls
    assert not d.restart_bar.isVisibleTo(d)
    d.scale.setCurrentIndex(d.scale.findData(150))
    assert d.restart_bar.isVisibleTo(d)
    d._restart()
    assert ('restart',) in host.calls
    d._refresh_graphics()
    assert 'test GPU' in d.graphics_info.text()


def test_restore_defaults(app):
    from quantumscope.gui.settings_dialog import SettingsDialog
    prefs.set('circuits/default_qubits', 7)
    d = SettingsDialog(Host())
    assert d.default_qubits.value() == 7
    d._restore_defaults()
    assert prefs.get('circuits/default_qubits') == 3 and d.default_qubits.value() == 3


def test_workspace_uses_defaults_and_confirms_clear(app, monkeypatch):
    prefs.set('circuits/default_shots', 333)
    prefs.set('circuits/show_blochs', False)
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    assert w.shots.value() == 333 and not w.show_blochs.isChecked()
    assert w.model.gates == {} and w.model.blocks == {}       # v0.5.2 starts with an empty circuit
    monkeypatch.setattr(QtWidgets.QMessageBox, 'question',
                        staticmethod(lambda *a, **k: pytest.fail('an empty circuit clears without asking')))
    w._clear_clicked()
    w.place('H', 0, 0)
    monkeypatch.setattr(QtWidgets.QMessageBox, 'question',
                        staticmethod(lambda *a, **k: QtWidgets.QMessageBox.StandardButton.No))
    w._clear_clicked()
    assert w.model.gates                              # "No" keeps the circuit
    prefs.set('circuits/confirm_clear', False)
    w._clear_clicked()
    assert not w.model.gates


def test_autosave_recent_and_recovery(app, tmp_path, monkeypatch):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    from quantumscope.gui.main_window import MainWindow
    w = CircuitWorkspace()
    w.load_library('bernstein_vazirani', {'n': 3, 's': '101'})
    w.enable_autosave(True)
    w._autosave.flush()
    assert os.path.exists(w.autosave_path())
    path = str(tmp_path / 'saved.qscope')
    monkeypatch.setattr(QtWidgets.QFileDialog, 'getSaveFileName', staticmethod(lambda *a, **k: (path, '')))
    w.save_native()
    assert prefs.get('files/recent')[0] == os.path.abspath(path)
    assert w.recent_menu.actions()[0].text() == 'saved.qscope'

    class FakeWindow:                                 # MainWindow needs OpenGL; reuse its recovery logic
        circuit_widget = CircuitWorkspace()
        _session_marker = MainWindow._session_marker
        _launch_circuits = staticmethod(lambda: None)
    fake = FakeWindow()
    open(MainWindow._session_marker(fake), 'w').close()       # a previous session crashed
    MainWindow.offer_recovery(fake)
    assert len(fake.circuit_widget.model.blocks) == 1 and 'Recovered' in fake.circuit_widget.status.text()


def test_pdf_report_preference(app, tmp_path, monkeypatch):
    from quantumscope.gui import circuit_pdf
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    seen = []
    monkeypatch.setattr(circuit_pdf, 'write_circuit_pdf', lambda *a, **k: seen.append(k['include_report']))
    monkeypatch.setattr(QtWidgets.QFileDialog, 'getSaveFileName', staticmethod(lambda *a, **k: (str(tmp_path / 'c.pdf'), '')))
    monkeypatch.setattr(QtWidgets.QMessageBox, 'question', staticmethod(lambda *a, **k: pytest.fail('should not ask')))
    w = CircuitWorkspace()
    for choice, expected in (('always', True), ('never', False)):
        prefs.set('files/pdf_report', choice)
        w.export_pdf()
        assert seen[-1] is expected


def test_toolbar_cleanup_and_file_menu(app):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    texts = [b.text() for b in w.findChildren(QtWidgets.QPushButton)] + [l.text() for l in w.findChildren(QtWidgets.QLabel)]
    assert 'Bell example' not in texts and 'Gate' not in texts            # leftovers removed
    actions = [a.text() for a in w.file_button.menu().actions() if a.text()]
    assert actions[:3] == ['Open .qscope…', 'Open recent', 'Save .qscope…'] and 'Export PDF…' in actions


def test_angle_units_setting(app):
    import math
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    w.angle.setValue(45)
    w.place('RY', 0, 0)
    assert w.model.gates[(0, 0)].angle == pytest.approx(math.pi / 4)
    prefs.set('circuits/angle_units', 'radians')
    w.apply_preferences()
    assert w.angle.value() == pytest.approx(math.pi / 4, abs=1e-4) and w.angle.suffix() == ' rad'
    w.angle.setValue(1.0)
    w.place('RX', 1, 0)
    assert w.model.gates[(1, 0)].angle == pytest.approx(1.0)
    assert w._parse_user_angle('pi/2') == pytest.approx(math.pi / 2)
    prefs.set('circuits/angle_units', 'degrees')
    w.apply_preferences()
    assert w._parse_user_angle('90') == pytest.approx(math.pi / 2) and w._parse_user_angle('pi') == pytest.approx(math.pi)


def test_bit_order_and_number_format_settings(app):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    from quantumscope.physics.circuits import Gate
    w = CircuitWorkspace()
    w.set_circuit(2, [Gate('X', (0,)), Gate('H', (1,))])
    w.open_state_inspector()
    assert '|10⟩' in w._inspector.dirac.toPlainText()
    prefs.set('circuits/bit_order', 'q0_right')
    prefs.set('circuits/number_format', 'decimal')
    prefs.set('circuits/decimals', 3)
    w.apply_preferences()
    text = w._inspector.dirac.toPlainText()
    assert '|01⟩' in text and '0.707' in text
    prefs.restore_defaults()
    w.apply_preferences()
    assert '|10⟩' in w._inspector.dirac.toPlainText()


def test_tools_simplify_and_equivalence(app, tmp_path, monkeypatch):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    w.place('H', 0, 0)
    w.place('H', 0, 1)
    w.place('X', 1, 0)
    path = str(tmp_path / 'original.qscope')
    monkeypatch.setattr(QtWidgets.QFileDialog, 'getSaveFileName', staticmethod(lambda *a, **k: (path, '')))
    w.save_native()
    monkeypatch.setattr(QtWidgets.QDialog, 'exec', lambda self: QtWidgets.QDialog.DialogCode.Accepted)
    w.simplify_dialog()
    assert list(w.model.gates.values()) == [w.model.gates[(1, 0)]]
    messages = []
    monkeypatch.setattr(QtWidgets.QMessageBox, 'information', staticmethod(lambda *a, **k: messages.append(a[2])))
    assert w.check_equivalence(path) is True and messages[-1].startswith('Equivalent')
    w.place('Z', 0, 0)
    assert w.check_equivalence(path) is False and messages[-1].startswith('Not equivalent')
