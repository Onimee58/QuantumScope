"""The MaxCut graph for QAOA: the likeliest cut drawn on the graph, and the spread of cut sizes."""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QWidget

from quantumscope.gui.theme import canvas_color
from quantumscope.physics.algorithms import marginal
from quantumscope.physics.maxcut import GRAPHS, best_cuts, cut_value, expected_cut

SIDE = (QColor('#4fc3f7'), QColor('#ffb74d'))            # node colours for 0 and 1


class MaxCutView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 340)
        self.graph, self.probabilities = None, {}

    def set_state(self, graph, probabilities):
        self.graph, self.probabilities = graph, probabilities
        self.update()

    def paintEvent(self, event):
        if self.graph is None:
            return
        label, n, edges, positions = GRAPHS[self.graph]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        text = canvas_color('chart_text')
        likeliest = max(self.probabilities, key=self.probabilities.get) if self.probabilities else '0' * n
        size = min(self.height() - 50, self.width() * 0.5 - 30)
        ox, oy = 20, 30
        at = lambda k: QPointF(ox + positions[k][0] * size, oy + positions[k][1] * size)
        p.setPen(text)
        p.setFont(QFont('Sans', 10, QFont.Weight.DemiBold))
        p.drawText(QRectF(ox, 4, size, 20), Qt.AlignmentFlag.AlignCenter, f'Likeliest result {likeliest}')
        for i, j in edges:                                   # cut edges bright and solid, others faint and dashed
            cut = likeliest[i] != likeliest[j]
            p.setPen(QPen(canvas_color('bloch_vector') if cut else canvas_color('bloch_axis'), 4 if cut else 1.6,
                          Qt.PenStyle.SolidLine if cut else Qt.PenStyle.DashLine))
            p.drawLine(at(i), at(j))
        for k in range(n):
            p.setPen(QPen(QColor('#0d1117'), 2))
            p.setBrush(SIDE[int(likeliest[k])])
            p.drawEllipse(at(k), 17, 17)
            p.setPen(QColor('#0d1117'))
            p.drawText(QRectF(at(k).x() - 17, at(k).y() - 17, 34, 34), Qt.AlignmentFlag.AlignCenter, f'q{k}')
        # the distribution of cut sizes
        best, _ = best_cuts(n, edges)
        by_size = [0.0] * (len(edges) + 1)
        for bits, prob in self.probabilities.items():
            by_size[cut_value(bits, edges)] += prob
        left, right = self.width() * 0.55, self.width() - 16
        top, bottom = 40, self.height() - 40
        width = (right - left) / len(by_size)
        p.setFont(QFont('Sans', 9))
        p.setPen(text)
        p.drawText(QRectF(left, 8, right - left, 20), Qt.AlignmentFlag.AlignCenter, 'probability of each cut size')
        for c, prob in enumerate(by_size):
            h = (bottom - top) * prob
            colour = QColor(canvas_color('bloch_vector'))
            if c != best:
                colour.setAlpha(130)
            p.fillRect(QRectF(left + c * width + 4, bottom - h, width - 8, h), colour)
            p.setPen(text)
            p.drawText(QRectF(left + c * width, bottom + 2, width, 16), Qt.AlignmentFlag.AlignCenter,
                       f'{c}' + (' ★' if c == best else ''))
            if prob > 0.005:
                p.drawText(QRectF(left + c * width, bottom - h - 16, width, 14), Qt.AlignmentFlag.AlignCenter, f'{prob:.2f}')
        p.drawText(QRectF(left, bottom + 18, right - left, 16), Qt.AlignmentFlag.AlignCenter,
                   f'edges cut (★ = maximum cut, {best})')
        p.end()


class MaxCutDialog(QDialog):
    """Follows the circuit live while the sliders move or the optimizer runs."""

    def __init__(self, workspace):
        super().__init__(workspace)
        self.setWindowTitle('MaxCut graph')
        self.workspace = workspace
        layout = QVBoxLayout(self)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.view = MaxCutView()
        layout.addWidget(self.view, 1)
        note = QLabel('Node colours show the likeliest measured result: blue = 0, orange = 1. Bright edges are cut. '
                      'Optimize (or move γ and β) and watch the likeliest cut and the spread change.')
        note.setWordWrap(True)
        layout.addWidget(note)
        workspace.state_changed.connect(self.refresh)
        self.resize(780, 480)
        self.refresh()

    def refresh(self):
        entry = self.workspace.model.active_entry
        params = dict(entry[1]) if entry and entry[0] == 'qaoa' else None
        if params is None or self.workspace.model.n != GRAPHS[params['graph']][1]:
            self.summary.setText('This circuit is no longer a QAOA example: load one from Algorithms → QAOA for MaxCut.')
            self.view.set_state(None, {})
            return
        label, n, edges, _ = GRAPHS[params['graph']]
        model = self.workspace.model
        probabilities = marginal(model.simulate().column_states[-1], n, list(range(n)))
        best, cuts = best_cuts(n, edges)
        average = expected_cut(probabilities, edges)
        p_best = sum(probabilities.get(c, 0.0) for c in cuts)
        self.summary.setText(f'<b>{label}</b>: expected cut <b>{average:.3f}</b> of a maximum {best} '
                             f'(ratio {average / best:.3f}); a best cut is measured with probability <b>{p_best:.3f}</b>.')
        self.view.set_state(params['graph'], probabilities)
