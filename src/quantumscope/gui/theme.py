"""Unified QuantumScope desktop appearance (Qt Fusion-compatible)."""

STYLESHEET = """
QMainWindow, QWidget#workspaceShell { background: #0b101b; color: #e9f2ff; }
QWidget { color: #dce7f7; font-family: "Inter", "Segoe UI", "Noto Sans", sans-serif; font-size: 12px; }
QMenu { background: #141e2d; color: #e5effc; border: 1px solid #304058; padding: 6px; }
QMenu::item { padding: 8px 20px; border-radius: 4px; }
QMenu::item:selected { background: #214666; }
QWidget#workspaceHeader { background: #111d2e; border: 1px solid #263a52; border-radius: 13px; }
QLabel#brandMark { background: transparent; padding-right: 5px; }
QLabel#brandTitle { color: #ffffff; font-size: 21px; font-weight: 750; }
QLabel#brandCaption { color: #819eb8; font-size: 10px; letter-spacing: 1px; }
QPushButton { background: #20344b; color: #ebf5ff; border: 1px solid #34506c;
  border-radius: 7px; padding: 7px 12px; min-height: 19px; }
QPushButton:hover { background: #2b4966; border-color: #4c9bc1; }
QPushButton:pressed { background: #16334c; }
QPushButton:disabled { background: #182332; color: #75869b; border-color: #263348; }
QToolButton#newExperiment { background: #18536b; color: #d6ffff; border: 1px solid #3885a0;
  border-radius: 8px; padding: 9px 16px; font-weight: 700; min-height: 24px; }
QToolButton#newExperiment:hover { background: #236b88; }
QToolButton#headerTool { background: #1b2f45; color: #bdebf8; border: 1px solid #314a62;
  border-radius: 8px; min-width: 35px; min-height: 35px; font-size: 19px; }
QToolButton#headerTool:hover, QToolButton#tabAddButton:hover { background: #2a4c67; }
QToolButton#tabAddButton { background: #172940; color: #94dcea; border: 1px solid #304760;
  border-radius: 6px; min-width: 27px; min-height: 27px; font-size: 20px; }
QTabWidget#experimentWorkspace::pane { border: 1px solid #27384d; background: #101824; border-radius: 9px; top: -1px; }
QTabWidget#experimentWorkspace QTabBar::tab { background: #162336; color: #96b0cb;
  border: 1px solid #273b55; border-bottom: 0; padding: 11px 19px;
  margin-right: 3px; border-top-left-radius: 8px; border-top-right-radius: 8px; }
QTabWidget#experimentWorkspace QTabBar::tab:selected { background: #223c56;
  color: #ffffff; border-color: #428cad; }
QTabWidget#experimentWorkspace QTabBar::tab:hover:!selected { background: #20314a; }
QGroupBox { background: #131f2d; border: 1px solid #2b3e54; border-radius: 9px;
  margin-top: 14px; padding: 13px 9px 9px; font-weight: 600; color: #cadbee; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; color: #8bd9e9; }
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox { background: #17283b; color: #eef7ff;
  border: 1px solid #38516b; border-radius: 6px; padding: 5px 8px; min-height: 20px; }
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border-color: #52c6d1; }
QComboBox::drop-down { border: none; width: 23px; }
QScrollArea { background: #101824; border: none; }
QScrollArea > QWidget > QWidget { background: #101824; }
QSplitter::handle { background: #25394f; }
QSplitter::handle:hover { background: #3883a0; }
QCheckBox { spacing: 7px; }
QCheckBox::indicator { width: 15px; height: 15px; }
QStatusBar { background: #101c2a; color: #829db7; border-top: 1px solid #273c50; }
QToolTip { background: #23364a; color: #ffffff; border: 1px solid #4d738f; }
QScrollBar:vertical { background: #111d2c; width: 10px; }
QScrollBar::handle:vertical { background: #38536c; border-radius: 5px; min-height: 25px; }
QScrollBar:horizontal { background: #111d2c; height: 10px; }
QScrollBar::handle:horizontal { background: #38536c; border-radius: 5px; min-width: 25px; }

/* Circuit palette, circuit grid, simulation readout and verification are theme-aware. */
QListWidget { background:#112035; color:#dfeeff; border:1px solid #3b5975; border-radius:7px; }
QListWidget::item { background:#213c56; color:#f2f7ff; border:1px solid #3b5975; border-radius:4px; padding:5px; }
QListWidget::item:selected { background:#145c82; color:#ffffff; }
QTableWidget { background:#101c2c; color:#deefff; gridline-color:#34516d; border:1px solid #304962; }
QTableWidget::item { background:#101c2c; color:#deefff; }
QTableWidget::item:selected { background:#245574; color:#ffffff; }
QHeaderView::section { background:#1b3047; color:#e3f2ff; border:1px solid #34516d; padding:4px; }
QHeaderView { background:#101c2c; }
QTableCornerButton::section { background:#1b3047; border:1px solid #34516d; }
QTextEdit { background:#101c2c; color:#deefff; border:1px solid #304962; }
"""

# Light appearance is an optional preference; the default remains QuantumScope dark.
LIGHT_STYLESHEET = STYLESHEET + """
QMainWindow, QWidget#workspaceShell { background: #edf3f9; color: #23394e; }
QWidget { color: #24394e; }
QWidget#workspaceHeader { background: #ffffff; border-color: #c7d9e6; }
QLabel#brandTitle { color: #142d42; }
QLabel#brandCaption { color: #4c7188; }
QTabWidget#experimentWorkspace::pane { background: #f8fbff; border-color: #c8d8e6; }
QTabWidget#experimentWorkspace QTabBar::tab { background: #e4edf6; color: #35546e; border-color: #b6cede; }
QTabWidget#experimentWorkspace QTabBar::tab:selected { background: #ffffff; color: #15384e; border-color: #1d879d; }
QGroupBox { background: #ffffff; color: #25475b; border-color: #b7ccdc; }
QGroupBox::title { color: #136c83; }
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox { background: #ffffff; color: #193a52; border-color: #a7bfd2; }
QScrollArea, QScrollArea > QWidget > QWidget { background: #f8fbff; }
QPushButton { background: #e4eef7; color: #23435c; border-color: #b0c7db; }
QPushButton:hover { background: #d1e6f4; }
QStatusBar { background: #e9f0f7; color: #38546a; border-color: #bed0df; }
QMenu { background: #ffffff; color: #243c50; border-color: #b8cfdf; }
QMenu::item:selected { background: #ceeafa; }
QToolButton#headerTool { background: #e4eef7; color: #226276; border-color: #b2cede; }
QToolButton#tabAddButton { background: #e7f1fa; color: #17657d; border-color: #b2cede; }

QListWidget { background:#f4f8fc; color:#19334b; border:1px solid #aac4d8; }
QListWidget::item { background:#e4eff8; color:#1b4058; border:1px solid #c2d5e4; }
QListWidget::item:selected { background:#1b6d91; color:#ffffff; }
QTableWidget { background:#f5f9fe; color:#1b364e; gridline-color:#c3d5e5; border:1px solid #aac4d8; }
QTableWidget::item { background:#f5f9fe; color:#1b364e; }
QTableWidget::item:selected { background:#c8e6f5; color:#14344d; }
QHeaderView::section { background:#dceaf5; color:#1b364e; border:1px solid #b4cada; padding:4px; }
QHeaderView { background:#f5f9fe; }
QTableCornerButton::section { background:#dceaf5; border:1px solid #b4cada; }
QTextEdit { background:#ffffff; color:#1b364e; border:1px solid #aac4d8; }
QToolTip { background:#f7fbff; color:#183a54; border-color:#9ebbcf; }
QCheckBox { color:#183a54; }
"""

# Explicit rules for nested tabs and dialogs: Qt styles do not automatically
# translate the dark widget-specific selectors into a readable light palette.
LIGHT_STYLESHEET += """
QDialog, QDialog QWidget, QTabWidget, QTabWidget::pane { background:#f8fbff; color:#20374d; }
QTabBar::tab { background:#e0ebf5; color:#26465d; border:1px solid #a9c3d5; padding:7px 12px; }
QTabBar::tab:selected { background:#ffffff; color:#103850; border-bottom:2px solid #177eaa; }
QTabBar::tab:hover { background:#d5e7f5; color:#143a54; }
QLabel, QGroupBox, QGroupBox::title { color:#203c54; }
QTableView, QTableWidget, QAbstractItemView { background:#f6faff; color:#203c54; alternate-background-color:#e9f1f8; selection-background-color:#c4e1f2; selection-color:#14334a; }
QTableWidget::item, QTableView::item { background:#f6faff; color:#203c54; }
QHeaderView::section { background:#dce9f3; color:#1d374e; }
QScrollBar:vertical, QScrollBar:horizontal { background:#e5eef6; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background:#a4bbc9; }
QTextBrowser, QPlainTextEdit { background:#ffffff; color:#20384c; }
QToolButton { color:#1e4057; }
"""


# ---------------------------------------------------------------------------
# Canvas colors for custom-painted widgets (circuit grid, Bloch glyphs, charts).
#
# Widgets painted with QPainter do not follow the stylesheet, so each theme
# defines semantic roles here. Each role is checked against the surface it is
# drawn on: text roles target WCAG 2.1 AA (4.5:1) and graphical roles target
# WCAG 1.4.11 (3:1). tests/test_theme_contrast.py enforces these ratios.
#
# Self-contained visualization panels (Bloch scene, entanglement stage,
# double-slit apparatus, dynamics plots) deliberately paint their own dark
# background in both themes and are not covered by these roles.
# ---------------------------------------------------------------------------

CANVAS = {
    'dark': {
        'surface':        '#101c2c',  # circuit table / panel background
        'wire':           '#6b8fb0',
        'connector':      '#b3d0e7',
        'control':        '#d5f5ff',
        'gate_fill':      '#174865',
        'gate_border':    '#60bddb',
        'gate_text':      '#effaff',
        'target_fill':    '#11283c',
        'target_stroke':  '#60bddb',
        'preview_line':   '#ffe19a',
        'preview_fill':   '#226783',
        'preview_stroke': '#ffcf73',
        'preview_text':   '#ffe7af',
        'measure_fill':   '#273747',
        'measure_border': '#ffd58e',
        'measure_text':   '#ffe9bc',
        'bloch_outline':  '#6687a6',
        'bloch_axis':     '#4f6c89',
        'bloch_vector':   '#52d4df',
        'bloch_text':     '#ddefff',
        'chart_text':     '#dceeff',
        'chart_axis':     '#6b8aa6',
        'chart_theory':   '#52c8e5',
        'chart_sampled':  '#f6b05e',
        'pass':           '#77e6a1',
        'fail':           '#ff8d87',
        'header_text':    '#e3f2ff',  # matches QHeaderView::section in STYLESHEET
        'header_current': '#1c6987',
        'header_past':    '#223648',
        'header_future':  '#29313c',
    },
    'light': {
        'surface':        '#f5f9fe',
        'wire':           '#5f7f99',
        'connector':      '#1f4a66',
        'control':        '#12344c',
        'gate_fill':      '#1d5f80',
        'gate_border':    '#0f4561',
        'gate_text':      '#ffffff',
        'target_fill':    '#ffffff',
        'target_stroke':  '#12344c',
        'preview_line':   '#a86200',
        'preview_fill':   '#fff1d6',
        'preview_stroke': '#a86200',
        'preview_text':   '#7a4700',
        'measure_fill':   '#fff1d6',
        'measure_border': '#9a5a00',
        'measure_text':   '#5e3600',
        'bloch_outline':  '#5f7f99',
        'bloch_axis':     '#7f98ac',
        'bloch_vector':   '#08778b',
        'bloch_text':     '#1b364e',
        'chart_text':     '#233e54',
        'chart_axis':     '#5f7f99',
        'chart_theory':   '#1683a8',
        'chart_sampled':  '#b5600a',
        'pass':           '#17703a',
        'fail':           '#b3261e',
        'header_text':    '#1b364e',  # matches QHeaderView::section in LIGHT_STYLESHEET
        'header_current': '#b9dff0',
        'header_past':    '#dceaf5',
        'header_future':  '#eef3f8',
    },
}

# (foreground role, background role, minimum ratio) checked by the tests.
CONTRAST_REQUIREMENTS = (
    ('wire', 'surface', 3.0), ('connector', 'surface', 3.0), ('control', 'surface', 3.0),
    ('gate_border', 'surface', 3.0), ('gate_text', 'gate_fill', 4.5),
    ('target_stroke', 'target_fill', 3.0), ('target_stroke', 'surface', 3.0),
    ('preview_line', 'surface', 3.0), ('preview_stroke', 'preview_fill', 3.0),
    ('preview_text', 'surface', 4.5),
    ('measure_border', 'surface', 3.0), ('measure_text', 'measure_fill', 4.5),
    ('bloch_outline', 'surface', 3.0), ('bloch_vector', 'surface', 3.0), ('bloch_text', 'surface', 4.5),
    ('chart_text', 'surface', 4.5), ('chart_axis', 'surface', 3.0),
    ('chart_theory', 'surface', 3.0), ('chart_sampled', 'surface', 3.0),
    ('pass', 'surface', 4.5), ('fail', 'surface', 4.5),
    ('header_text', 'header_current', 4.5), ('header_text', 'header_past', 4.5),
    ('header_text', 'header_future', 4.5),
)


def current_theme():
    """'light' or 'dark', following the application's appearance setting."""
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        return 'light' if app is not None and app.property('quantumscope_light') else 'dark'
    except ImportError:
        return 'dark'


def canvas_hex(role, theme=None):
    return CANVAS[theme or current_theme()][role]


def canvas_color(role, theme=None):
    """QColor for a canvas role in the current (or given) theme."""
    from PySide6.QtGui import QColor
    return QColor(canvas_hex(role, theme))


def contrast_ratio(foreground, background):
    """WCAG 2.1 contrast ratio between two '#rrggbb' colors."""
    def luminance(hex_color):
        channels = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
    hi, lo = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)
