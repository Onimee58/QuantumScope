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
"""
