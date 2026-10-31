"""Optional GUI checks for the Learn window (QUANTUMSCOPE_GUI_TESTS=1)."""
import os
import re

import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')
from PySide6.QtCore import QUrl  # noqa: E402

from quantumscope.gui import preferences as prefs  # noqa: E402
from quantumscope.learn import actions  # noqa: E402
from quantumscope.learn.lessons import builtin_lessons  # noqa: E402


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def setup(app, tmp_path, monkeypatch):
    monkeypatch.setenv('QUANTUMSCOPE_SETTINGS_FILE', str(tmp_path / 'settings.ini'))
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    from quantumscope.gui.learn_window import LearnWindow
    monkeypatch.setattr(QtWidgets.QDialog, 'exec', lambda self: 0)      # Gate Explorer opens modally
    workspace = CircuitWorkspace()
    window = LearnWindow(workspace=workspace)
    window.show()
    return window, workspace


def test_every_builtin_try_it_link_runs(setup):
    window, workspace = setup
    for lesson in builtin_lessons():
        window.open_lesson(lesson.key)
        for link in re.findall(r'\]\((qs:[^)\s]+)\)', lesson.body):
            window._link(QUrl(link))
            assert not window.status.text().startswith('Could not'), (lesson.key, link, window.status.text())


def test_try_it_sets_up_the_circuit(setup):
    window, workspace = setup
    window._link(QUrl('qs:circuit?n=1&gates=T:0&states=%2B&inspector=1'))
    assert workspace.model.n == 1 and workspace.model.initial_states[0].label == '|+⟩'
    assert workspace._inspector is not None and workspace._inspector.isVisible()


def test_contents_quiz_and_navigation(setup):
    window, _ = setup
    window.show_area('circuits')
    assert window.lesson.key == 'circuits/01-qubits' and 'Show answer' in window.reader.toHtml()
    window._link(QUrl('qsquiz:0'))
    assert 0 in window.revealed['circuits/01-qubits']
    window.open_lesson('circuits/02-single-qubit-gates')
    window._go(-1)
    assert window.lesson.key == 'circuits/01-qubits' and window.forward.isEnabled()


def test_lab_progress_updates_as_the_circuit_changes(setup):
    window, workspace = setup
    window.open_lesson('circuits/90-lab-bell-pair')
    window._link(QUrl('qs:circuit?n=2'))
    assert window.lab_status.text() == 'Lab progress: 0/3 steps'
    workspace.place('H', 0, 0)
    workspace.place('CX', 1, 1)
    workspace.cell_click(0, 1)
    assert window.lab_status.text().startswith('Lab progress: 3/3 steps')


def test_search_course_folder_and_pdf(setup, tmp_path):
    window, _ = setup
    window.search_box.setText('hadamard')
    assert window.tree.topLevelItem(0).childCount() >= 1
    window.search_box.setText('')
    (tmp_path / 'week1.md').write_text('# Week 1\nHello $x$.', encoding='utf-8')
    prefs.set('learn/course_folder', str(tmp_path))
    window.refresh_contents()
    assert window.open_lesson('course/week1.md')
    window.open_lesson('circuits/02-single-qubit-gates')
    path = window.export_pdf(str(tmp_path / 'lesson.pdf'))
    assert path and os.path.getsize(path) > 10000


def test_try_it_links_set_and_clear_noise(setup):
    from quantumscope.physics.noise import PRESETS
    window, workspace = setup
    window._link(QUrl('qs:circuit?n=2&gates=H:0;CX:0,1&noise=Moderate&elements=depolarizing:1:2:0.2'))
    assert workspace.model.noise_model == PRESETS['Moderate'] and len(workspace.model.noise) == 1
    window._link(QUrl('qs:circuit?n=1&gates=H:0'))
    assert not workspace.model.noisy                          # a link without noise= starts ideal


def test_lab_steps_update_live_in_the_real_app_wiring(app, tmp_path, monkeypatch):
    """Regression: the main window creates Learn with host=self (no workspace argument);
    lab steps must still tick off as the circuit changes, without any other click."""
    monkeypatch.setenv('QUANTUMSCOPE_SETTINGS_FILE', str(tmp_path / 's.ini'))
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    from quantumscope.gui.learn_window import LearnWindow

    class Host:
        circuit_widget = CircuitWorkspace()
        launch_view = staticmethod(lambda view: None)
    window = LearnWindow(host=Host())
    window.show()
    window.open_lesson('circuits/90-lab-bell-pair')
    window._link(QUrl('qs:circuit?n=2'))
    assert window.lab_status.text() == 'Lab progress: 0/3 steps'
    Host.circuit_widget.place('H', 0, 0)                          # no other action in the Learn window
    assert window.lab_status.text() == 'Lab progress: 1/3 steps' and '✓ Done' in window.reader.toPlainText()


def test_quiz_answers_are_checked_immediately(setup):
    window, _ = setup
    window.open_lesson('circuits/01-qubits')            # quiz 1: the correct answer is option C (index 2)
    window._link(QUrl('qsquiz:0:0'))
    text = window.reader.toPlainText()
    assert '✗ Not quite' in text and '✓ Correct!' not in text
    window._link(QUrl('qsquiz:0:2'))
    text = window.reader.toPlainText()
    assert '✓ Correct!' in text and 'squared magnitude' in text
