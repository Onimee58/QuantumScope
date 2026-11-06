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
        # Lessons and their equation images must be inside the installed package.
        import os
        from quantumscope.learn.lessons import builtin_lessons, content_folder
        from quantumscope.learn.equations import equations_in, image_name
        lessons = builtin_lessons()
        missing = [name for lesson in lessons for tex, kind in equations_in(lesson.body)
                   for name in [image_name(tex, kind, "dark")]
                   if not os.path.exists(os.path.join(content_folder(), "eq", name))]
        if not lessons or missing:
            raise RuntimeError(f"Learn content incomplete: {len(lessons)} lessons, {len(missing)} missing equations")
        lines.append(f"Learn: {len(lessons)} lessons, all equation images present")
        # The glossary and the splash's logo must ship too (a missing glossary only hides links).
        from quantumscope.learn import glossary
        from importlib.resources import files
        terms = glossary.builtin().terms
        if len(terms) < 50 or not files("quantumscope").joinpath("assets/quantumscope-mark.svg").is_file():
            raise RuntimeError(f"Glossary or splash logo missing ({len(terms)} terms)")
        lines.append(f"Glossary: {len(terms)} terms; splash logo present")
        guide = files("quantumscope").joinpath("assets/QuantumScope-User-Guide.pdf")
        if not guide.is_file() or guide.read_bytes()[:5] != b"%PDF-":
            raise RuntimeError("User guide (assets/QuantumScope-User-Guide.pdf) missing")
        lines.append("User guide: present")
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
    # Graphics device and interface size must be set before Qt or OpenGL start.
    from quantumscope.gui.preferences import apply_startup_environment
    apply_startup_environment()
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    # The splash appears before the slow imports below (the 3-D libraries), so it covers the wait.
    from quantumscope.gui.splash import show_splash
    splash = show_splash(app)
    from quantumscope.gui.main_window import MainWindow
    from PySide6.QtGui import QIcon
    from importlib.resources import files
    app.setApplicationName("QuantumScope")
    app.setOrganizationName("QuantumScope")
    app.setWindowIcon(QIcon(str(files("quantumscope").joinpath("assets/quantumscope.png"))))
    app.setStyle("Fusion")
    from quantumscope.gui import preferences as prefs
    from quantumscope.gui.theme import apply_theme
    apply_theme(prefs.get("appearance/theme"))
    window = MainWindow()
    try:   # follow the operating system's light/dark switch when "Follow system" is chosen
        app.styleHints().colorSchemeChanged.connect(window._follow_system_theme)
    except AttributeError:
        pass
    window.show()
    if splash is not None:
        splash.close()
    window.offer_recovery()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
