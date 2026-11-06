"""Show the solution: the VQLS circuit's state against the classical solution A⁻¹b, live."""
import numpy as np
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout

from quantumscope.physics import vqls


class VqlsSolutionDialog(QDialog):
    def __init__(self, workspace):
        import pyqtgraph as pg
        super().__init__(workspace)
        self.setWindowTitle('VQLS solution')
        self.workspace = workspace
        layout = QVBoxLayout(self)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.plot = pg.PlotWidget()
        self.plot.setLabel('left', 'amplitude')
        self.plot.setLabel('bottom', 'basis state')
        self.plot.showGrid(y=True, alpha=0.2)
        self.plot.addLegend(offset=(8, 4))
        for side in ('left', 'bottom'):
            self.plot.getAxis(side).enableAutoSIPrefix(False)
        layout.addWidget(self.plot, 1)
        note = QLabel('Amplitudes of the circuit\'s state |x(θ)⟩ (cyan) and of the classical solution A⁻¹b, '
                      'normalized (orange). The circuit\'s state is first turned by a global phase, which no '
                      'measurement can see. Optimize, or move the sliders, and watch the bars meet.')
        note.setWordWrap(True)
        layout.addWidget(note)
        workspace.state_changed.connect(self.refresh)
        self.resize(760, 460)
        self.refresh()

    def refresh(self):
        import pyqtgraph as pg
        entry = self.workspace.model.active_entry
        self.plot.clear()
        params = dict(entry[1]) if entry and entry[0] == 'vqls' else None
        try:
            n, A, b, text, about = vqls.system(params) if params else (None,) * 5
        except ValueError:
            n = None
        if params is None or n is None or self.workspace.model.n != n:
            self.summary.setText('This circuit is no longer a VQLS example: load one from Algorithms → '
                                 'Variational quantum linear solver.')
            self.values = None
            return
        state = np.asarray(self.workspace.model.simulate().column_states[-1])
        solution = vqls.classical_solution(A, b)
        overlap = np.vdot(solution, state)
        aligned = state * (np.conj(overlap) / abs(overlap) if abs(overlap) > 1e-12 else 1)
        x = np.arange(2 ** n)
        self.plot.addItem(pg.BarGraphItem(x=x - 0.18, height=np.real(solution), width=0.34, brush='#ff9a5a',
                                          name='solution A⁻¹b'))
        self.plot.addItem(pg.BarGraphItem(x=x + 0.18, height=np.real(aligned), width=0.34, brush='#5ae6ff',
                                          name='circuit |x(θ)⟩'))
        ticks = [(k, f'|{k:0{n}b}⟩') for k in x]
        self.plot.getAxis('bottom').setTicks([ticks])
        fid, cost = vqls.fidelity(A, b, state), vqls.normalized_cost(A, b, state)
        self.summary.setText(f'<b>A x = b</b> for {about}, condition number {vqls.condition_number(A):.1f}: '
                             f'fidelity <b>{fid:.4f}</b> with the solution, cost <b>{cost:.4f}</b> '
                             f'(0 at the solution).')
        self.values = (np.real(solution), np.real(aligned), fid)
