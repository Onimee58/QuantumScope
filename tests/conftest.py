"""Keep the test suite away from the real user's settings and data folders."""
import os
import tempfile

_folder = tempfile.mkdtemp(prefix='quantumscope-tests-')
os.environ.setdefault('QUANTUMSCOPE_SETTINGS_FILE', os.path.join(_folder, 'settings.ini'))
os.environ.setdefault('QUANTUMSCOPE_DATA_DIR', os.path.join(_folder, 'data'))
