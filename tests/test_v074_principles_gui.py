"""Optional GUI checks for the v0.7.4 Quantum Principles redesign (QUANTUMSCOPE_GUI_TESTS=1)."""
import os

import numpy as np
import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

def test_superposition_presets_collapse_and_statistics(app):
    from quantumscope.gui.quantum_principles import SuperpositionDialog
    from quantumscope.physics.qubits import qubit_state, spin_probabilities
    d = SuperpositionDialog()
    d._preset(60, 30)
    d.axis.setValue(30)
    expected = spin_probabilities(qubit_state(60, 30), 30)
    assert d.theta.value() == 60 and np.allclose(d.tally.expected, expected)
    d.measure.click()
    state = d.prepared
    plus, minus = qubit_state(30), qubit_state(210)
    overlap = max(abs(np.vdot(plus, state)), abs(np.vdot(minus, state)))
    assert overlap == pytest.approx(1) and sum(d.tally.counts) == 1           # collapsed onto the axis
    d.speed.setCurrentIndex(2)
    d.hits.setValue(2000)
    d.sample.click()
    assert sum(d.tally.counts) == 2000
    assert d.tally.fractions()[0] == pytest.approx(expected[0], abs=0.05)     # Born rule
    d.speed.setCurrentIndex(0)
    d.sample.click()
    assert d._timer.isActive() and d.stop_button.isEnabled()
    d.stop_button.click()
    assert not d._timer.isActive()
    d.view._side = 1
    d.view._drag(d.view.project(np.array([0.0, -1.0, 0.0]))[0])             # drag to −y (in front)
    assert d.theta.value() == pytest.approx(90, abs=1) and d.phi.value() == pytest.approx(270, abs=1)

def test_double_slit_firing_dragging_and_colour(app):
    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    from quantumscope.gui.double_slit_dialog import DoubleSlitDialog
    d = DoubleSlitDialog()
    d.resize(1200, 760)
    d.show()
    d.speed.setCurrentIndex(2)
    d.batch.setValue(5000)
    d.add.click()
    assert d.screen.count == 5000 == len(d.samples)
    d.which_path.setChecked(True)                                              # a new pattern: cleared
    assert d.screen.count == 0 and len(d.samples) == 0
    d.speed.setCurrentIndex(0)
    d.add.click()
    assert d._timer.isActive()
    d._stream()
    assert 0 < d.screen.count < 5000
    d.stop.click()
    assert not d._timer.isActive()
    a = d.apparatus
    x, y = 315 * a.width() / 700, (152 - 35) * a.height() / 300
    a.mousePressEvent(QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(x, y), QPointF(x, y), Qt.MouseButton.LeftButton,
                                  Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))
    assert d.separation.value() == pytest.approx(160)
    d.wavelength.setValue(1000)
    assert 'infrared' in d.colour_note.text()
    d.wavelength.setValue(532)
    assert d.colour_note.text() == ''
