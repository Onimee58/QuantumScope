"""The update check, step by step, only when the user asks (Settings → Updates or the ⓘ menu)."""
import os
import subprocess
import tempfile

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (QApplication, QDialog, QDialogButtonBox, QLabel, QMessageBox, QProgressDialog,
                               QTextBrowser, QVBoxLayout)

from quantumscope import __version__, updater

PERMISSION = ('QuantumScope will contact github.com to look for a newer release.\n\n'
              'Nothing about you or your files is sent. Continue?')


def _busy(callable_, *args):
    QGuiApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
    try:
        return callable_(*args)
    finally:
        QGuiApplication.restoreOverrideCursor()


def _release_dialog(parent, release):
    dialog = QDialog(parent)
    dialog.setWindowTitle('Update available')
    layout = QVBoxLayout(dialog)
    layout.addWidget(QLabel(f'<b>QuantumScope {release.label}</b> is available (you have {__version__}).'))
    notes = QTextBrowser()
    notes.setOpenExternalLinks(True)
    notes.setMarkdown(release.notes or 'No release notes.')
    layout.addWidget(notes, 1)
    buttons = QDialogButtonBox()
    update = buttons.addButton('Update now', QDialogButtonBox.ButtonRole.AcceptRole)
    buttons.addButton('Not now', QDialogButtonBox.ButtonRole.RejectRole)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    dialog.resize(640, 480)
    dialog.update_button = update
    return dialog


def check_for_updates(parent, opener=None, platform=None, frozen=None, folder=None, run=None):
    """The whole flow. Returns a short outcome string (also used by tests)."""
    if QMessageBox.question(parent, 'Check for updates', PERMISSION,
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
        return 'declined'
    current = updater.parse_version(__version__)
    try:
        release = _busy(updater.check, current, platform, opener)
    except updater.UpdateError as exc:
        QMessageBox.warning(parent, 'Check for updates', str(exc))
        return 'error'
    if release is None:
        QMessageBox.information(parent, 'Check for updates', f'QuantumScope {__version__} is the latest version.')
        return 'up to date'
    if _release_dialog(parent, release).exec() != QDialog.DialogCode.Accepted:
        return 'not now'
    kind, _, message = updater.install_plan('', platform, frozen)
    if kind == 'source':                                   # running from a git checkout: nothing to download
        QMessageBox.information(parent, 'Update QuantumScope', message)
        return 'source'
    if not release.installer:
        QMessageBox.information(parent, 'Update QuantumScope', 'This release has no installer for your system. '
                                f'Download it from the release page:\n{release.page}')
        return 'no installer'
    progress = QProgressDialog(f'Downloading {release.installer["name"]}…', 'Cancel', 0, 100, parent)
    progress.setWindowTitle('Update QuantumScope')
    progress.setMinimumDuration(0)

    def report(done, total):
        progress.setValue(int(100 * done / total) if total else 0)
        QApplication.processEvents()
        return not progress.wasCanceled()
    try:
        path = updater.download(release, folder or tempfile.mkdtemp(prefix='quantumscope-update-'), report, opener)
    except updater.UpdateError as exc:
        progress.close()
        QMessageBox.warning(parent, 'Update QuantumScope', str(exc))
        return 'download failed'
    progress.close()
    kind, command, message = updater.install_plan(path, platform, frozen)
    if QMessageBox.question(parent, 'Install the update',
                            f'The download was verified against the release checksum.\n\n{message}\n\nInstall now?',
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.Yes) != QMessageBox.StandardButton.Yes:
        return 'downloaded'
    try:
        (run or subprocess.Popen)(command)
    except OSError as exc:
        QMessageBox.warning(parent, 'Update QuantumScope', f'The installer could not be started ({exc}). '
                            f'It is saved at:\n{path}\n\nOn a managed computer you may need an administrator.')
        return 'install failed'
    if kind == 'run' and updater.platform_key(platform) == 'windows':
        QApplication.instance().quit()                     # the installer replaces the running app
    return 'installing'
