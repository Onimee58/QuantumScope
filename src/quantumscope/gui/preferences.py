"""Application preferences: one place for every setting, its default and its valid values.

Values are stored with QSettings (per user, per platform). Settings that must
take effect before Qt or OpenGL start (graphics device, interface size) are
applied by `startup_environment()` in __main__, so they apply after a restart.
"""
import os
import sys
from dataclasses import dataclass

ORGANIZATION = 'QuantumScope'
APPLICATION = 'QuantumScope'


@dataclass(frozen=True)
class Pref:
    key: str
    default: object
    choices: tuple = ()          # allowed values for choice settings
    minimum: int = None
    maximum: int = None
    restart: bool = False        # takes effect after restarting QuantumScope


PREFS = {p.key: p for p in (
    # Appearance
    Pref('appearance/theme', 'dark', ('dark', 'light', 'system')),
    Pref('appearance/scale', 100, (100, 125, 150, 175), restart=True),
    # Circuits
    Pref('circuits/default_qubits', 3, minimum=1, maximum=10),
    Pref('circuits/default_shots', 1024, minimum=1, maximum=100000),
    Pref('circuits/show_blochs', True, (True, False)),
    Pref('circuits/confirm_clear', True, (True, False)),
    # Graphics
    Pref('graphics/device', 'auto', ('auto', 'integrated', 'nvidia'), restart=True),
    Pref('graphics/volume_method', 'Auto (GPU preferred)', ('Auto (GPU preferred)', 'GPU', 'CPU')),
    # Files
    Pref('files/folder', ''),                         # '' means the user's Documents folder
    Pref('files/recent', ()),                          # most recent first
    Pref('files/autosave', True, (True, False)),
    Pref('files/pdf_report', 'ask', ('ask', 'always', 'never')),
)}

MAX_RECENT = 8


def _settings():
    """The user's settings store. QUANTUMSCOPE_SETTINGS_FILE redirects it (used by the tests,
    so they never read or change a real user's settings)."""
    from PySide6.QtCore import QSettings
    path = os.environ.get('QUANTUMSCOPE_SETTINGS_FILE')
    if path:
        return QSettings(path, QSettings.Format.IniFormat)
    return QSettings(ORGANIZATION, APPLICATION)


def data_folder():
    """Per-user folder for autosave and session files (QUANTUMSCOPE_DATA_DIR overrides it)."""
    folder = os.environ.get('QUANTUMSCOPE_DATA_DIR')
    if not folder:
        from PySide6.QtCore import QStandardPaths
        folder = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        folder = folder or os.path.join(os.path.expanduser('~'), '.quantumscope')
    os.makedirs(folder, exist_ok=True)
    return folder


def _coerce(pref, value):
    """Turn a stored value back into the setting's type; invalid values give the default."""
    default = pref.default
    try:
        if isinstance(default, bool):
            value = value if isinstance(value, bool) else str(value).lower() in ('true', '1', 'yes')
        elif isinstance(default, int):
            value = int(value)
        elif isinstance(default, tuple):
            if value in (None, ''):
                value = ()
            value = tuple(value) if isinstance(value, (list, tuple)) else (str(value),)
        elif value is None:
            value = default
        else:
            value = str(value)
    except (TypeError, ValueError):
        return default
    if pref.choices and value not in pref.choices:
        return default
    if pref.minimum is not None and not pref.minimum <= value <= pref.maximum:
        return default
    return value


def get(key, store=None):
    pref = PREFS[key]
    store = store if store is not None else _settings()
    return _coerce(pref, store.value(key, pref.default))


def set(key, value, store=None):  # noqa: A001 - mirrors QSettings
    pref = PREFS[key]
    checked = _coerce(pref, value)
    if checked != value and not (isinstance(pref.default, tuple) and tuple(value) == checked):
        raise ValueError(f'Invalid value for {key}: {value!r}')
    store = store if store is not None else _settings()
    store.setValue(key, list(checked) if isinstance(checked, tuple) else checked)
    store.sync()


def restore_defaults(store=None):
    """Reset every setting except the recent-files list (that is history, not a preference)."""
    store = store if store is not None else _settings()
    for key in PREFS:
        if key != 'files/recent':
            store.remove(key)
    store.sync()


def add_recent(path, store=None):
    path = os.path.abspath(path)
    recent = [p for p in get('files/recent', store) if p != path]
    set('files/recent', tuple([path] + recent)[:MAX_RECENT], store)


def default_folder(store=None):
    folder = get('files/folder', store)
    if folder and os.path.isdir(folder):
        return folder
    from PySide6.QtCore import QStandardPaths
    documents = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
    return documents if documents and os.path.isdir(documents) else os.path.expanduser('~')


# ---- applied before Qt starts ------------------------------------------------------------

NVIDIA_ENV = {'__NV_PRIME_RENDER_OFFLOAD': '1', '__GLX_VENDOR_LIBRARY_NAME': 'nvidia',
              'QT_XCB_GL_INTEGRATION': 'xcb_glx'}


def startup_environment(device, scale, platform=None, environ=None):
    """Environment changes for the chosen graphics device and interface size.

    Returns (set, unset): variables to set and variables to remove. Pure, so it
    is unit-tested. NVIDIA PRIME offloading exists only on Linux; elsewhere the
    operating system chooses the graphics device. An explicit variable already
    set by the user or a launcher script is respected.
    """
    platform = platform or sys.platform
    environ = environ if environ is not None else os.environ
    to_set, to_unset = {}, []
    if platform.startswith('linux'):
        if device == 'nvidia':
            to_set.update({k: v for k, v in NVIDIA_ENV.items() if k not in environ})
            if 'QT_QPA_PLATFORM' not in environ:
                to_set['QT_QPA_PLATFORM'] = 'xcb'          # PRIME offloading uses GLX
        elif device == 'integrated':
            to_unset = [k for k in ('__NV_PRIME_RENDER_OFFLOAD', '__GLX_VENDOR_LIBRARY_NAME') if k in environ]
    if scale != 100 and 'QT_SCALE_FACTOR' not in environ:
        to_set['QT_SCALE_FACTOR'] = f'{scale / 100:g}'
    return to_set, to_unset


def apply_startup_environment():
    """Call before importing Qt GUI modules: applies device and size preferences."""
    try:
        store = _settings()
        to_set, to_unset = startup_environment(get('graphics/device', store), get('appearance/scale', store))
    except Exception:                       # never block start-up on a preference problem
        return
    os.environ.update(to_set)
    for key in to_unset:
        os.environ.pop(key, None)
    # Remember what QuantumScope set itself, so a restart can apply new choices cleanly.
    os.environ[APPLIED_MARKER] = ','.join(sorted(to_set))


APPLIED_MARKER = 'QUANTUMSCOPE_APPLIED_ENV'


def restart_environment(environ=None):
    """Environment for relaunching: drop the variables this session set from preferences."""
    env = dict(environ if environ is not None else os.environ)
    for key in filter(None, env.pop(APPLIED_MARKER, '').split(',')):
        env.pop(key, None)
    return env


def resolve_theme(choice, system_is_dark):
    """'dark' or 'light' for a theme choice ('dark', 'light' or 'system')."""
    if choice == 'system':
        return 'dark' if system_is_dark else 'light'
    return choice
