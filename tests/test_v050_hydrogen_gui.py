"""Optional checks of the Hydrogen Dynamics windows (QUANTUMSCOPE_GUI_TESTS=1).

The 3D checks render with an off-screen PyVista plotter in place of the
OpenGL Qt widget, so they need a VTK build that can render off-screen.
"""
import os
import warnings

import numpy as np
import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')
pv = pytest.importorskip('pyvista')
warnings.filterwarnings('ignore')
pv.OFF_SCREEN = True


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


class OffscreenInteractor(QtWidgets.QWidget):
    """Stand-in for pyvistaqt.QtInteractor backed by an off-screen Plotter."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.__dict__['_p'] = pv.Plotter(off_screen=True, window_size=(300, 300))

    def __getattr__(self, name):
        return getattr(self.__dict__['_p'], name)

    def render(self, *a, **k):
        return self.__dict__['_p'].render()

    def close(self):
        self.__dict__['_p'].close()
        return QtWidgets.QWidget.close(self)


@pytest.fixture
def dialog3d(app, monkeypatch):
    import quantumscope.gui.dynamics_3d_dialog as module
    monkeypatch.setattr(module, 'QtInteractor', OffscreenInteractor)
    dlg = module.HydrogenDynamics3DDialog()
    dlg.npoints.setValue(48)
    dlg._rebuild_later.flush()
    yield dlg
    dlg.close()


def direction(camera_position):
    d = np.subtract(camera_position[0], camera_position[1])
    return d / np.linalg.norm(d)


def test_reset_camera_restores_the_isometric_view(dialog3d):
    p = dialog3d.plotter
    iso = direction(p.camera_position)
    p.camera.azimuth = 75
    p.camera.elevation = 30
    p.render()
    assert not np.allclose(direction(p.camera_position), iso)
    dialog3d.reset_camera.click()
    assert np.allclose(direction(p.camera_position), iso)


@pytest.mark.parametrize('view,axis', [('xy', [0, 0, 1]), ('xz', [0, -1, 0]), ('yz', [1, 0, 0])])
def test_standard_views(dialog3d, view, axis):
    dialog3d.view_buttons[view].click()
    assert np.allclose(direction(dialog3d.plotter.camera_position), axis)


def test_playback_and_appearance_changes_reuse_the_scene(dialog3d):
    actor, data = dialog3d.scene._actor, dialog3d.scene._aa
    dialog3d.slider.setValue(500)
    assert dialog3d.scene._actor is actor
    dialog3d.opacity.setValue(3.0)
    assert dialog3d.scene._aa is data          # no re-sampling for appearance


def test_quick_values_and_fit(dialog3d):
    dialog3d.a.setCurrentIndex(0)
    dialog3d.b.setCurrentIndex(8)              # 1s + 4p
    dialog3d._rebuild_later.flush()
    assert 'clips' in dialog3d.info.text()
    dialog3d.halfwidth.parentWidget().action_button.click()
    dialog3d._rebuild_later.flush()
    assert dialog3d.halfwidth.value() == 44.0 and 'clips' not in dialog3d.info.text()
    dialog3d.prob.parentWidget().quick_buttons['25'].click()
    dialog3d._rebuild_later.flush()
    assert dialog3d.model.probability_first == pytest.approx(0.25)
    assert dialog3d.npoints.parentWidget().quick_buttons['Max'].toolTip().endswith('160')


def test_2d_dialog_controls(app):
    from quantumscope.gui.dynamics_dialog import HydrogenDynamicsDialog
    d = HydrogenDynamicsDialog()
    d.plane.setCurrentIndex(2)
    d._rebuild_later.flush()
    assert (d.plot.getAxis('bottom').labelText, d.plot.getAxis('left').labelText) == ('y', 'z')
    raw = d.current_density.copy()
    d.contrast.setCurrentText('Logarithmic')
    assert np.array_equal(d.current_density, raw)        # display only
    d.resolution.parentWidget().quick_buttons['Max'].click()
    d._rebuild_later.flush()
    assert d.current_density.shape == (400, 400)
    d.plot.getViewBox().scaleBy((0.2, 0.2))
    d.reset_view.click()
    span = d.plot.getViewBox().viewRange()[0]
    assert span[1] - span[0] > 1.9 * d.extent.value()
    d.close()
