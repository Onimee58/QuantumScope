"""Optional GUI checks for v0.7.5: turning the spheres and the redesigned Entanglement experiment."""
import math
import os
import time

import numpy as np
import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')
from PySide6.QtCore import QEvent, QPointF, Qt  # noqa: E402
from PySide6.QtGui import QMouseEvent  # noqa: E402


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def mouse(kind, point, button, buttons, modifiers=Qt.KeyboardModifier.NoModifier):
    return QMouseEvent(kind, point, point, button, buttons, modifiers)


def test_right_drag_and_shift_drag_turn_the_sphere_left_drag_still_sets_the_state(app):
    from quantumscope.gui.principles_visuals import BlochView, direction
    view = BlochView()
    view.resize(400, 400)
    start = (view.azimuth, view.elevation)
    seen = []
    view.stateChanged.connect(lambda t, p: seen.append((t, p)))
    for button, modifiers in ((Qt.MouseButton.RightButton, Qt.KeyboardModifier.NoModifier),
                              (Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ShiftModifier)):
        view.reset_view()
        view.mousePressEvent(mouse(QEvent.Type.MouseButtonPress, QPointF(200, 200), button, button, modifiers))
        view.mouseMoveEvent(mouse(QEvent.Type.MouseMove, QPointF(260, 180), Qt.MouseButton.NoButton, button, modifiers))
        assert view.azimuth == pytest.approx((start[0] - 30) % 360) and view.elevation == pytest.approx(start[1] - 10)
        view.mouseReleaseEvent(mouse(QEvent.Type.MouseButtonRelease, QPointF(260, 180), button, Qt.MouseButton.NoButton))
    assert seen == []                                                        # turning never changes the state
    view.mouseDoubleClickEvent(None)
    assert (view.azimuth, view.elevation) == pytest.approx(start)
    view.set_view(150, 40)                                                   # turned: left-drag still exact
    target = direction(70, 160)
    point, depth = view.project(target)
    view._side = 1 if depth >= 0 else -1
    view._drag(point)
    assert np.allclose(direction(*seen[-1]), target, atol=1e-6)


def test_axis_mode_turns_the_detector(app):
    from quantumscope.gui.principles_visuals import BlochView
    view = BlochView()
    view.resize(400, 400)
    view.drag_mode = 'axis'
    got = []
    view.axisChanged.connect(got.append)
    a = math.radians(60)
    point, _ = view.project(np.array([math.sin(a), 0.0, math.cos(a)]))
    view._side = 1
    view._drag(point)
    assert got and got[-1] == pytest.approx(60, abs=1) and view.axis == got[-1]


def test_entanglement_one_pair_many_pairs_and_bell_test(app):
    from quantumscope.gui.entanglement_experiment import EntanglementDialog
    from quantumscope.physics import bell as B
    d = EntanglementDialog()
    d.resize(1300, 820)
    d.show()
    assert d.alice.length == pytest.approx(0) and d.bob.length == pytest.approx(0)   # each qubit alone: random
    d.bob.axisChanged.emit(30.0)                                                      # dragging Bob's axis
    assert d.b == 30 and d.bob.axis == 30
    d.speed.setCurrentIndex(2)
    d.count.setValue(4000)
    d.send_many()
    counts = d.grid.counts
    e = (counts[0, 0] + counts[1, 1] - counts[0, 1] - counts[1, 0]) / counts.sum()
    assert counts.sum() == 4000 and e == pytest.approx(B.correlation(d.rho(), 0, 30), abs=0.05)
    d.run_bell_test()
    assert abs(d.meter.value) == pytest.approx(B.QUANTUM_LIMIT, abs=0.15) and 'beats' in d.explain.text()
    d.state.setCurrentIndex(list(B.STATES).index('classical'))
    d.run_bell_test()
    assert abs(d.meter.value) < B.CLASSICAL_LIMIT + 0.15
    d.state.setCurrentIndex(0)
    d.visibility.setValue(50)
    d.run_bell_test()
    assert abs(d.meter.value) == pytest.approx(B.QUANTUM_LIMIT * 0.5, abs=0.15) and 'below' in d.explain.text()
    d.visibility.setValue(100)
    d.speed.setCurrentIndex(1)
    d.send_one()
    for _ in range(200):                                                      # flight, Alice, then Bob
        app.processEvents()
        time.sleep(0.01)
        if d.grid.counts.sum():
            break
    assert d.grid.counts.sum() == 1 and d.alice.length == pytest.approx(1) and d.bob.length == pytest.approx(1)
    d.clear_results()
    assert d.grid.counts.sum() == 0 and d.meter.value is None and not d.points
