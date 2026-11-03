"""Keep the test suite away from the real user's settings and data folders."""
import os
import tempfile

_folder = tempfile.mkdtemp(prefix='quantumscope-tests-')
os.environ.setdefault('QUANTUMSCOPE_SETTINGS_FILE', os.path.join(_folder, 'settings.ini'))
os.environ.setdefault('QUANTUMSCOPE_DATA_DIR', os.path.join(_folder, 'data'))


_EXIT_STATUS = {}


def pytest_sessionfinish(session, exitstatus):
    """Tear Qt down in an orderly way before the interpreter exits.

    GUI tests leave widgets (and their Python wrappers) alive until shutdown, when Python
    and Qt can destroy them in an unsafe order and crash *after* every test has passed.
    Closing and deleting top-level widgets while Qt is still running avoids that race.
    """
    import sys
    _EXIT_STATUS['status'] = int(exitstatus)                  # used by pytest_unconfigure below
    if 'PySide6.QtWidgets' not in sys.modules:
        return
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        return
    import gc
    if 'pyvista' in sys.modules:                 # VTK in this process: see pytest_unconfigure
        return
    for widget in QApplication.topLevelWidgets():
        widget.close()
        widget.deleteLater()
    from PySide6.QtCore import QCoreApplication, QEvent
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()
    gc.collect()



def pytest_unconfigure(config):
    """VTK (the 3-D view) and Qt can crash while destroying each other at interpreter exit — after
    every test has passed (measured: about half the runs of the Hydrogen GUI tests, also in v0.7.0).
    When this process used VTK, leave right after pytest has reported, with its exit status, so a
    teardown crash can never hide or fake a result."""
    import os
    import sys
    if 'pyvista' in sys.modules and 'status' in _EXIT_STATUS:
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(_EXIT_STATUS['status'])
