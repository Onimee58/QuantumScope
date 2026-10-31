"""Console entry point: python -m quantumscope or quantumscope."""
import sys


def _self_test():
    """Start the packaged application's core without showing a window.

    Used by CI after packaging: it checks that Qt (including its platform
    plugin), the 3D visualization libraries and the circuit workspace load
    and simulate inside the frozen bundle. The OpenGL main window itself is
    not created, because CI machines have no GPU. Returns 0 on success.
    A report is written to $QUANTUMSCOPE_SELF_TEST_REPORT when set, since
    windowed builds on Windows have no console output.
    """
    import os
    import traceback
    lines = []
    try:
        from quantumscope import __version__
        lines.append(f"QuantumScope {__version__} self-test")
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv[:1])
        lines.append(f"Qt platform: {app.platformName()}")
        import pyvista, pyvistaqt, pyqtgraph, vtkmodules  # noqa: F401  (bundling check)
        import quantumscope.gui.main_window  # noqa: F401  (imports every workspace module)
        from quantumscope.gui.circuit_workspace import CircuitWorkspace
        from quantumscope.physics.circuit_examples import EXAMPLE_NAMES
        workspace = CircuitWorkspace()
        workspace.load_example(1 + EXAMPLE_NAMES.index("Half adder (a=1,b=1)"))
        verdicts = [workspace.verify_table.item(r, 3).text() for r in range(workspace.verify_table.rowCount())]
        if not verdicts or not all("PASS" in v for v in verdicts):
            raise RuntimeError(f"Example verification failed: {verdicts}")
        lines.append(f"Circuit workspace: half adder {len(verdicts)}/{len(verdicts)} PASS")
        from quantumscope.gui.state_inspector import StateInspector
        inspector = StateInspector(workspace)
        inspector.refresh()
        if "column" not in inspector.where.text() or inspector.amp_table.rowCount() == 0:
            raise RuntimeError("State Inspector did not render the state")
        lines.append(f"State Inspector: {inspector.amp_table.rowCount()} amplitude row(s) rendered")
        workspace.load_library("grover", {"n": 3, "marked": "101", "iterations": -1})
        rows, _ = workspace.model.verification()
        if not rows or rows[0].passed is not True or len(workspace.model.blocks) != 4:
            raise RuntimeError("Algorithm library did not build Grover correctly")
        lines.append(f"Algorithm library: Grover {rows[0].output_label} (PASS)")
        lines.append("RESULT: PASS")
        status = 0
    except Exception:
        lines.append(traceback.format_exc())
        lines.append("RESULT: FAIL")
        status = 1
    report = "\n".join(lines)
    print(report)
    path = os.environ.get("QUANTUMSCOPE_SELF_TEST_REPORT")
    if path:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(report + "\n")
    return status


def main():
    if "--version" in sys.argv:
        from quantumscope import __version__
        print(f"QuantumScope {__version__}")
        return 0
    if "--self-test" in sys.argv:
        return _self_test()
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
