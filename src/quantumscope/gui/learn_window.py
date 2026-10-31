"""The Learn window: lectures and labs for each area, plus a teacher's own course folder."""
import os

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
                               QSplitter, QTextBrowser, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from quantumscope.gui import preferences as prefs
from quantumscope.learn import actions, labs
from quantumscope.learn.lessons import AREAS, COURSE, builtin_lessons, content_folder, course_lessons, search
from quantumscope.learn.render import steps_of, to_html

KEY_ROLE = Qt.ItemDataRole.UserRole


def run_action(action, workspace, launch=None):
    """Carry out a lesson action on a circuit workspace. launch(view) opens other views
    (the main window supplies it). Returns a short status message."""
    launch = launch or (lambda view: None)
    if action.kind in ('circuit', 'algorithm', 'example', 'try', 'inspector', 'gate'):
        launch('circuits')
    if action.kind == 'circuit':
        p = action.params
        workspace.set_circuit(p['n'], p['gates'], initial_states=p['states'])
    elif action.kind == 'algorithm':
        workspace.load_library(action.target, action.params['values'])
    elif action.kind == 'example':
        titles = [workspace.examples.itemText(i) for i in range(workspace.examples.count())]
        workspace.load_example(titles.index(action.target))
    elif action.kind == 'try':
        workspace.try_gate(action.target)
    elif action.kind == 'gate':
        workspace.show_gate_explorer(action.target)
        return f'Opened {action.target} in the Gate Explorer'
    elif action.kind == 'open':
        launch(action.target)
        return f'Opened {action.target}'
    if action.kind == 'inspector' or action.params.get('inspector'):
        workspace.open_state_inspector()
    return 'Loaded in the Gate Circuit Simulator'


class LearnWindow(QWidget):
    """host (the main window) provides workspace() and launch(view); both optional in tests."""

    def __init__(self, host=None, workspace=None, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.host, self._workspace = host, workspace
        self.setWindowTitle('QuantumScope — Learn')
        self.setObjectName('workspaceShell')
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.resize(1100, 760)
        self.lesson = None
        self.history, self.position = [], -1
        self.revealed = {}                 # lesson key -> set of revealed quiz numbers
        self.font_size = 15
        layout = QVBoxLayout(self)
        split = QSplitter()
        layout.addWidget(split)

        side = QWidget()
        sv = QVBoxLayout(side)
        sv.setContentsMargins(0, 0, 0, 0)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText('Search lessons…')
        self.search_box.textChanged.connect(self._search)
        sv.addWidget(self.search_box)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemClicked.connect(self._tree_clicked)
        sv.addWidget(self.tree)
        course = QPushButton('My course folder…')
        course.setToolTip('Choose a folder of your own lessons (Markdown .md files); they appear under My course')
        course.clicked.connect(self._choose_course)
        sv.addWidget(course)
        split.addWidget(side)

        main = QWidget()
        mv = QVBoxLayout(main)
        mv.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        mv.addLayout(bar)
        self.back = QPushButton('◀ Back')
        self.back.clicked.connect(lambda: self._go(-1))
        self.forward = QPushButton('Forward ▶')
        self.forward.clicked.connect(lambda: self._go(1))
        smaller = QPushButton('A−')
        smaller.setToolTip('Smaller text')
        smaller.clicked.connect(lambda: self._zoom(-1))
        larger = QPushButton('A+')
        larger.setToolTip('Larger text')
        larger.clicked.connect(lambda: self._zoom(1))
        export = QPushButton('Export PDF…')
        export.setToolTip('Save this lesson as a PDF handout')
        export.clicked.connect(self.export_pdf)
        for widget in (self.back, self.forward, smaller, larger):
            bar.addWidget(widget)
        bar.addStretch()
        self.lab_status = QLabel('')
        bar.addWidget(self.lab_status)
        bar.addWidget(export)
        self.reader = QTextBrowser()
        self.reader.setOpenLinks(False)
        self.reader.anchorClicked.connect(self._link)
        mv.addWidget(self.reader)
        self.status = QLabel('')
        self.status.setWordWrap(True)
        mv.addWidget(self.status)
        split.addWidget(main)
        split.setSizes([280, 820])
        self.refresh_contents()
        if workspace is not None and hasattr(workspace, 'state_changed'):
            workspace.state_changed.connect(self._circuit_changed)

    # ---- contents -------------------------------------------------------------------------
    def lessons(self):
        return builtin_lessons() + course_lessons(prefs.get('learn/course_folder'))

    def refresh_contents(self):
        self.tree.clear()
        self._items = {}
        all_lessons = self.lessons()
        for area, title in list(AREAS.items()) + [(COURSE, 'My course')]:
            mine = [l for l in all_lessons if l.area == area]
            top = QTreeWidgetItem([title])
            self.tree.addTopLevelItem(top)
            if area == COURSE and not mine:
                hint = QTreeWidgetItem(['(choose a folder of .md lessons below)'])
                hint.setDisabled(True)
                top.addChild(hint)
            for kind, label in (('lecture', 'Lectures'), ('lab', 'Labs')):
                group = [l for l in mine if l.kind == kind]
                if not group:
                    continue
                parent = QTreeWidgetItem([label]) if area != COURSE else top
                if area != COURSE:
                    top.addChild(parent)
                for lesson in group:
                    item = QTreeWidgetItem([lesson.title])
                    item.setData(0, KEY_ROLE, lesson.key)
                    parent.addChild(item)
                    self._items[lesson.key] = item
            top.setExpanded(True)
            for i in range(top.childCount()):
                top.child(i).setExpanded(True)

    def show_area(self, area):
        """Open the first lesson of an area (used by each tab's Learn button)."""
        first = next((l for l in self.lessons() if l.area == area), None)
        if first is not None:
            self.open_lesson(first.key)
        else:
            self.reader.setHtml(f'<p>No lessons for {AREAS.get(area, area)} yet.</p>')

    def _tree_clicked(self, item):
        key = item.data(0, KEY_ROLE)
        if key:
            self.open_lesson(key)

    def _search(self, text):
        if not text.strip():
            self.refresh_contents()
            return
        self.tree.clear()
        results = search(self.lessons(), text)
        top = QTreeWidgetItem([f'{len(results)} result(s)'])
        self.tree.addTopLevelItem(top)
        for lesson in results:
            item = QTreeWidgetItem([f'{lesson.title}  ·  {AREAS.get(lesson.area, "My course")}'])
            item.setData(0, KEY_ROLE, lesson.key)
            top.addChild(item)
        top.setExpanded(True)

    def _choose_course(self):
        folder = QFileDialog.getExistingDirectory(self, 'Folder of your lessons', prefs.get('learn/course_folder')
                                                  or prefs.default_folder())
        if folder:
            prefs.set('learn/course_folder', folder)
            self.refresh_contents()
            self.status.setText(f'My course: {len(course_lessons(folder))} lesson(s) from {folder}')

    # ---- reading ------------------------------------------------------------------------------
    def open_lesson(self, key, record=True):
        lesson = next((l for l in self.lessons() if l.key == key), None)
        if lesson is None:
            self.status.setText(f'Lesson not found: {key}')
            return False
        self.lesson = lesson
        if record:
            self.history = self.history[:self.position + 1] + [key]
            self.position = len(self.history) - 1
        if key in getattr(self, '_items', {}):
            self.tree.setCurrentItem(self._items[key])
        self.setWindowTitle(f'QuantumScope — Learn — {lesson.title}')
        self.render(scroll_top=True)
        return True

    def _theme(self):
        app = QApplication.instance()
        return 'light' if app is not None and app.property('quantumscope_light') else 'dark'

    def _lab_steps(self):
        if self.lesson is None or self.lesson.kind != 'lab' or self.workspace() is None:
            return {}
        model = self.workspace().model
        return labs.progress(model, steps_of(self.lesson.body))

    def render(self, scroll_top=False):
        if self.lesson is None:
            return
        position = self.reader.verticalScrollBar().value()
        steps = self._lab_steps()
        html = to_html(self.lesson, self._theme(), os.path.join(content_folder(), 'eq'),
                       self.revealed.get(self.lesson.key, set()), steps, self.font_size)
        self.reader.document().setBaseUrl(QUrl.fromLocalFile(self.lesson.folder + os.sep))
        self.reader.setHtml(html)
        self.reader.verticalScrollBar().setValue(0 if scroll_top else position)
        if self.lesson.kind == 'lab' and steps:
            done = sum(steps.values())
            self.lab_status.setText(f'Lab progress: {done}/{len(steps)} steps' + ('  🎉 Complete!' if done == len(steps) else ''))
        else:
            self.lab_status.setText('')
        self.back.setEnabled(self.position > 0)
        self.forward.setEnabled(self.position < len(self.history) - 1)

    def _go(self, step):
        target = self.position + step
        if 0 <= target < len(self.history):
            self.position = target
            self.open_lesson(self.history[target], record=False)

    def _zoom(self, step):
        self.font_size = max(11, min(26, self.font_size + step))
        self.render()

    def apply_theme(self):
        self.render()

    def _circuit_changed(self):
        if self.isVisible() and self.lesson is not None and self.lesson.kind == 'lab':
            self.render()

    # ---- links -----------------------------------------------------------------------------------
    def workspace(self):
        if self._workspace is not None:
            return self._workspace
        return getattr(self.host, 'circuit_widget', None)

    def _link(self, url):
        text = url.toString()
        if text.startswith('qsquiz:'):
            self.revealed.setdefault(self.lesson.key, set()).add(int(text.split(':', 1)[1]))
            self.render()
            return
        if not text.startswith('qs:'):
            from PySide6.QtGui import QDesktopServices
            QDesktopServices.openUrl(url)             # ordinary web links open in the browser
            return
        try:
            action = actions.parse(text)
            if action.kind == 'lesson':
                self.open_lesson(action.target)
                return
            workspace = self.workspace()
            if workspace is None:
                raise ValueError('The circuit simulator is not available')
            launch = getattr(self.host, 'launch_view', None)
            self.status.setText(run_action(action, workspace, launch))
            self.render()
        except (ValueError, KeyError, IndexError) as exc:
            self.status.setText(f'Could not run this link: {exc}')

    # ---- export -----------------------------------------------------------------------------------
    def export_pdf(self, path=None):
        if self.lesson is None:
            return None
        if not path:
            suggestion = os.path.join(prefs.default_folder(), f'{self.lesson.title}.pdf'.replace('/', '-').replace(':', ''))
            path, _ = QFileDialog.getSaveFileName(self, 'Export lesson as PDF', suggestion, 'PDF files (*.pdf)')
        if not path:
            return None
        if not path.lower().endswith('.pdf'):
            path += '.pdf'
        from PySide6.QtPrintSupport import QPrinter
        from PySide6.QtGui import QTextDocument
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path)
        document = QTextDocument()
        document.setBaseUrl(QUrl.fromLocalFile(self.lesson.folder + os.sep))
        # Handouts print on white paper: always use the light theme's colors.
        document.setHtml(to_html(self.lesson, 'light', os.path.join(content_folder(), 'eq'),
                                 self.revealed.get(self.lesson.key, set()), self._lab_steps(), 12))
        try:
            document.print_(printer)
        except Exception as exc:                       # noqa: BLE001 - report any printing problem
            QMessageBox.warning(self, 'PDF export failed', str(exc))
            return None
        self.status.setText(f'Saved {path}')
        return path
