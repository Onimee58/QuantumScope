"""Optional whole-window checks for the Quantum ML area (QUANTUMSCOPE_GUI_TESTS=1; own process)."""
import os

import numpy as np
import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')
pv = pytest.importorskip('pyvista')
pv.OFF_SCREEN = True


class OffscreenInteractor(QtWidgets.QWidget):
    def __init__(self, parent=None, *a, **k):
        super().__init__(parent)
        self.__dict__['_p'] = pv.Plotter(off_screen=True, window_size=(300, 300))

    def __getattr__(self, name):
        return getattr(self.__dict__['_p'], name)

    def render(self, *a, **k):
        return self.__dict__['_p'].render()


@pytest.fixture(scope='module')
def window():
    QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    import quantumscope.gui.main_window as module
    original = module.QtInteractor
    module.QtInteractor = OffscreenInteractor
    w = module.MainWindow()
    w.show()
    yield w
    module.QtInteractor = original


def test_quantum_ml_area_and_trained_circuit_in_the_simulator(window):
    w = window
    titles = [w.categories.tabText(i).strip() for i in range(w.categories.count())]
    assert titles[-1].endswith('Quantum ML') and 'qml' in w.workspaces
    start = w.workspaces['qml']
    assert start.count() == 1 and start.tabText(0) == 'Start'                    # opens on its Start page
    w._launch_qml_variational()
    v = w._open_experiments['qml_variational']
    assert w.workspaces['qml'].indexOf(v) >= 0
    v.data.source.setCurrentIndex(v.data.source.findData('moons'))
    v.steps.setValue(20)
    v.train()
    x = v.open_in_circuit()
    circuit = w.circuit_widget
    assert w.categories.currentWidget() is w.workspaces['circuits'] and circuit.n == 2
    assert float(circuit.model.expectation()) == pytest.approx(float(v.model.expectation(x[None])[0]), abs=1e-10)
    for view in ('qml_datasets', 'qml_kernel', 'qml_variational'):
        w.launch_view(view)                                                       # Try it link names
        assert w.categories.currentWidget() is w.workspaces['qml']
