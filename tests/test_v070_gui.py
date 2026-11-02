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
