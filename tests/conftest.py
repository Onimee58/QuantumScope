"""Keep the test suite away from the real user's settings and data folders."""
import os
import tempfile

_folder = tempfile.mkdtemp(prefix='quantumscope-tests-')
os.environ.setdefault('QUANTUMSCOPE_SETTINGS_FILE', os.path.join(_folder, 'settings.ini'))
os.environ.setdefault('QUANTUMSCOPE_DATA_DIR', os.path.join(_folder, 'data'))


def pytest_sessionfinish(session, exitstatus):
    """Tear Qt down in an orderly way before the interpreter exits.

    GUI tests leave widgets (and their Python wrappers) alive until shutdown, when Python
    and Qt can destroy them in an unsafe order and crash *after* every test has passed.
    Closing and deleting top-level widgets while Qt is still running avoids that race.
    """
    import sys
    if 'PySide6.QtWidgets' not in sys.modules:
        return
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        return
    import gc
    for widget in QApplication.topLevelWidgets():
        widget.close()
        widget.deleteLater()
    from PySide6.QtCore import QCoreApplication, QEvent
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()
    gc.collect()
