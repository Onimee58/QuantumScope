"""Theme colors never fall back to the operating system (Windows dark-mode report)."""
import glob
import re

import pytest

from quantumscope.gui import theme

PAIRS = {  # (text, background) for each theme: category tabs and drop-down lists
    'dark': [('#b7cbe0', '#162336'), ('#ffffff', '#234766'), ('#eef7ff', '#17283b'), ('#ffffff', '#1c6987')],
    'light': [('#26465d', '#e4edf6'), ('#103850', '#ffffff'), ('#193a52', '#ffffff'), ('#10324a', '#b9dff0')],
}


@pytest.mark.parametrize('name', ['dark', 'light'])
def test_tab_and_dropdown_colors_meet_wcag_aa(name):
    for text, background in PAIRS[name]:
        assert theme.contrast_ratio(text, background) >= 4.5, (name, text, background)


def test_stylesheets_style_category_tabs_and_dropdown_lists():
    for sheet in (theme.STYLESHEET, theme.LIGHT_STYLESHEET):
        assert 'QTabWidget#categoryWorkspace QTabBar::tab' in sheet and 'QComboBox QAbstractItemView' in sheet


def test_palette_text_contrast():
    for index, name in enumerate(('dark', 'light')):
        p = theme.PALETTES
        for text, base in (('WindowText', 'Window'), ('Text', 'Base'), ('ButtonText', 'Button'),
                           ('HighlightedText', 'Highlight'), ('ToolTipText', 'ToolTipBase')):
            assert theme.contrast_ratio(p[text][index], p[base][index]) >= 4.5, (name, text)


def test_theme_overrides_a_light_system_palette():
    # Ubuntu CI runners have no graphics libraries: Qt GUI modules exist but fail to load
    # (libEGL), which pytest.importorskip does not treat as a skip. Skip explicitly.
    try:
        from PySide6 import QtWidgets
        from PySide6.QtGui import QColor, QPalette
    except ImportError as exc:
        pytest.skip(f'Qt GUI libraries unavailable: {exc}')
    import os
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')     # no display needed
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    system = QPalette()
    system.setColor(QPalette.ColorRole.Window, QColor('#f0f0f0'))
    system.setColor(QPalette.ColorRole.Base, QColor('#ffffff'))
    app.setPalette(system)                                   # like Windows in light mode
    theme.apply_theme('dark')
    assert app.palette().color(QPalette.ColorRole.Window).name() == '#101824'
    assert app.palette().color(QPalette.ColorRole.Base).name() == '#17283b'
    theme.apply_theme('light')
    assert app.palette().color(QPalette.ColorRole.Window).name() == '#f5f8fc'


def test_no_bare_ampersands_in_widget_titles():
    # Qt reads a single & as a keyboard-shortcut marker ("Camera & display" shows as "Camera _display").
    pattern = re.compile(r'Q(GroupBox|PushButton|CheckBox|RadioButton|ToolButton)\((["\'])([^"\']*)\2')
    for path in glob.glob('src/quantumscope/gui/*.py'):
        for match in pattern.finditer(open(path, encoding='utf-8').read()):
            text = match.group(3).replace('&&', '')
            assert '&' not in text, (path, match.group(3))
