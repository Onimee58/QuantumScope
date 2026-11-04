"""v0.7.4: shared visuals for Quantum Principles (Qt-light parts and GUI checks)."""
import os

import numpy as np
import pytest

try:                                   # a missing system library (CI without graphics) raises a plain
    from PySide6 import QtWidgets      # ImportError, which importorskip does not treat as a skip
    from PySide6 import QtGui  # noqa: F401
except ImportError as exc:
    pytest.skip(f'Qt widgets are not available: {exc}', allow_module_level=True)


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_bloch_angles_and_drag_mapping(app):
    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    from quantumscope.gui.principles_visuals import BlochView, angles, direction
    for theta, phi in ((0, 0), (90, 0), (60, 30), (135, -100)):
        t, p = angles(direction(theta, phi))
        assert t == pytest.approx(theta, abs=1e-9) and (theta in (0, 180) or p == pytest.approx(phi, abs=1e-9))
    view = BlochView()
    view.resize(400, 400)
    for theta, phi in ((60, 30), (90, 90), (30, -60)):
        v = direction(theta, phi)
        point, depth = view.project(v)
        if depth > 0:                                              # front: the drag finds the same state
            assert np.allclose(view.unproject(point), v, atol=1e-6)
    seen = []
    view.stateChanged.connect(lambda t, p: seen.append((t, p)))
    press = lambda point: view.mousePressEvent(QMouseEvent(QEvent.Type.MouseButtonPress, point, point,
                                               Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
                                               Qt.KeyboardModifier.NoModifier))
    view.set_state(90, 90)                                          # +y sits slightly behind the sphere
    assert view.project(direction(90, 90))[1] < 0
    press(view.project(direction(90, 90))[0])                       # grabbing the arrow keeps the back side
    assert seen[-1][0] == pytest.approx(90, abs=1) and seen[-1][1] == pytest.approx(90, abs=1)
    view.set_state(90, 0)                                           # from the front, drag out past the rim...
    press(view.project(direction(90, 0))[0])
    cx, cy, r = view._frame()
    view._drag(QPointF(cx + 1.2 * r, cy))
    view._drag(QPointF(cx + 0.6 * r, cy))                           # ...and back in: now on the back
    assert np.dot(direction(*seen[-1]), view._F) < 0


def test_every_preset_is_clearly_visible_from_the_camera():
    from quantumscope.gui.principles_visuals import BlochView, direction
    for theta, phi in ((0, 0), (180, 0), (90, 0), (90, 180), (90, 90), (90, 270), (60, 30), (45, 45)):
        v = direction(theta, phi)
        assert np.sqrt(1 - np.dot(v, BlochView._F) ** 2) > 0.5, (theta, phi)    # never seen end-on


def test_wavelength_colours():
    from quantumscope.gui.principles_visuals import wavelength_colour
    def rgb(nm):
        c, visible = wavelength_colour(nm)
        return (c.red(), c.green(), c.blue()), visible
    (r, g, b), visible = rgb(532)
    assert visible and g > r and g > b
    assert rgb(650)[0][0] > rgb(650)[0][2] and rgb(450)[0][2] > rgb(450)[0][0]
    assert rgb(300)[1] is False and rgb(900)[1] is False


if os.environ.get('QUANTUMSCOPE_GUI_TESTS') == '1':
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
