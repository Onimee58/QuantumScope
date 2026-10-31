"""v0.5.2 patch 1: preferences, start-up environment and restart environment."""
import os

import pytest

QtCore = pytest.importorskip('PySide6.QtCore')
from quantumscope.gui import preferences as prefs  # noqa: E402


@pytest.fixture
def store(tmp_path):
    return QtCore.QSettings(str(tmp_path / 'test.ini'), QtCore.QSettings.Format.IniFormat)


def test_tests_never_touch_the_real_settings():
    assert os.environ.get('QUANTUMSCOPE_SETTINGS_FILE') and os.environ.get('QUANTUMSCOPE_DATA_DIR')


def test_defaults(store):
    assert prefs.get('appearance/theme', store) == 'dark'
    assert prefs.get('circuits/default_qubits', store) == 3
    assert prefs.get('circuits/show_blochs', store) is True
    assert prefs.get('files/recent', store) == ()


@pytest.mark.parametrize('key,value', [('appearance/theme', 'system'), ('appearance/scale', 150),
                                       ('circuits/default_shots', 4096), ('circuits/confirm_clear', False),
                                       ('graphics/device', 'nvidia'), ('files/pdf_report', 'always')])
def test_round_trip(store, key, value):
    prefs.set(key, value, store)
    assert prefs.get(key, store) == value


@pytest.mark.parametrize('key,value', [('appearance/theme', 'neon'), ('appearance/scale', 130),
                                       ('circuits/default_qubits', 11), ('graphics/device', 'amd')])
def test_invalid_values_are_rejected(store, key, value):
    with pytest.raises(ValueError):
        prefs.set(key, value, store)


def test_corrupt_stored_values_fall_back_to_defaults(store):
    store.setValue('circuits/default_qubits', 'many')
    store.setValue('appearance/theme', 'plaid')
    assert prefs.get('circuits/default_qubits', store) == 3 and prefs.get('appearance/theme', store) == 'dark'


def test_recent_files_are_unique_newest_first_and_capped(store, tmp_path):
    paths = [str(tmp_path / f'c{i}.qscope') for i in range(10)]
    for p in paths:
        prefs.add_recent(p, store)
    prefs.add_recent(paths[3], store)
    recent = prefs.get('files/recent', store)
    assert recent[0] == paths[3] and len(recent) == prefs.MAX_RECENT and len(set(recent)) == len(recent)


def test_restore_defaults_keeps_recent_files(store, tmp_path):
    prefs.set('appearance/theme', 'light', store)
    prefs.add_recent(str(tmp_path / 'a.qscope'), store)
    prefs.restore_defaults(store)
    assert prefs.get('appearance/theme', store) == 'dark' and len(prefs.get('files/recent', store)) == 1


def test_default_folder_falls_back_when_missing(store, tmp_path):
    prefs.set('files/folder', str(tmp_path / 'gone'), store)
    assert os.path.isdir(prefs.default_folder(store))


def test_nvidia_environment_on_linux():
    to_set, to_unset = prefs.startup_environment('nvidia', 100, 'linux', {})
    assert to_set['__NV_PRIME_RENDER_OFFLOAD'] == '1' and to_set['__GLX_VENDOR_LIBRARY_NAME'] == 'nvidia'
    assert to_set['QT_QPA_PLATFORM'] == 'xcb' and to_unset == []


def test_explicit_environment_is_respected():
    to_set, _ = prefs.startup_environment('nvidia', 150, 'linux', {'QT_QPA_PLATFORM': 'wayland', 'QT_SCALE_FACTOR': '2'})
    assert 'QT_QPA_PLATFORM' not in to_set and 'QT_SCALE_FACTOR' not in to_set


def test_integrated_removes_offloading_and_other_platforms_are_untouched():
    _, unset = prefs.startup_environment('integrated', 100, 'linux', {'__NV_PRIME_RENDER_OFFLOAD': '1'})
    assert unset == ['__NV_PRIME_RENDER_OFFLOAD']
    assert prefs.startup_environment('nvidia', 100, 'win32', {}) == ({}, [])
    assert prefs.startup_environment('auto', 100, 'linux', {}) == ({}, [])


def test_interface_size():
    assert prefs.startup_environment('auto', 150, 'darwin', {})[0] == {'QT_SCALE_FACTOR': '1.5'}


def test_restart_drops_variables_this_session_set():
    env = {'QT_SCALE_FACTOR': '1.5', 'PATH': '/bin', prefs.APPLIED_MARKER: 'QT_SCALE_FACTOR'}
    assert prefs.restart_environment(env) == {'PATH': '/bin'}
    assert prefs.restart_environment({'QT_SCALE_FACTOR': '2', 'PATH': '/bin'})['QT_SCALE_FACTOR'] == '2'


@pytest.mark.parametrize('choice,dark,expected', [('dark', False, 'dark'), ('light', True, 'light'),
                                                  ('system', True, 'dark'), ('system', False, 'light')])
def test_theme_resolution(choice, dark, expected):
    assert prefs.resolve_theme(choice, dark) == expected
