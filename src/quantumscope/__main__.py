"""Console entry point: python -m quantumscope or quantumscope."""
import sys


def main():
    if "--version" in sys.argv:
        from quantumscope import __version__
        print(f"QuantumScope {__version__}")
        return 0
    from PySide6.QtWidgets import QApplication
    from quantumscope.gui.main_window import MainWindow

    app = QApplication.instance() or QApplication(sys.argv)
    from PySide6.QtGui import QIcon
    from importlib.resources import files
    app.setApplicationName("QuantumScope")
    app.setOrganizationName("QuantumScope")
    app.setWindowIcon(QIcon(str(files("quantumscope").joinpath("assets/quantumscope.png"))))
    app.setStyle("Fusion")
    from quantumscope.gui.theme import STYLESHEET
    from PySide6.QtCore import QSettings
    from quantumscope.gui.theme import LIGHT_STYLESHEET
    selected_theme = QSettings("QuantumScope", "QuantumScope").value("appearance/theme", "dark")
    app.setProperty("quantumscope_light", selected_theme == "light")
    app.setStyleSheet(LIGHT_STYLESHEET if selected_theme == "light" else STYLESHEET)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
