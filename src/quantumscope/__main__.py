"""Console entry point: python -m quantumscope or quantumscope."""
import sys


def main():
    from PySide6.QtWidgets import QApplication
    from quantumscope.gui.main_window import MainWindow

    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
