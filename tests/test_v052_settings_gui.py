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
    assert w.recent_button.menu().actions()[0].text() == 'saved.qscope'

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
