"""Optional GUI checks for the Quantum ML experiments (QUANTUMSCOPE_GUI_TESTS=1)."""
import os

import numpy as np
import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_datasets_check_prepare_import_and_share(app, tmp_path, monkeypatch):
    from quantumscope.gui import qml_experiments as Q
    d = Q.DatasetsExperiment()
    d.source.setCurrentIndex(d.source.findData('mnist'))
    assert 'preprocessing' in d.verdict.text() and 'PCA' in d.findings.text()
    assert Q.STORE.prepared is not None and Q.STORE.prepared.X_train.shape[1] == 4
    assert d.images.isVisibleTo(d) and len(d.images.rows) == 2                    # example images per class
    d.components.setValue(2)
    d.prepare()
    assert Q.STORE.prepared.X_train.shape[1] == 2
    path = tmp_path / 'mine.csv'
    rng = np.random.default_rng(0)
    path.write_text('a,b,colour,label\n' + '\n'.join(f'{rng.uniform():.3f},{rng.uniform():.3f},{"red" if k % 2 else "blue"},{k % 2}'
                                                       for k in range(40)) + '\n')
    imported = d.import_file(str(path))
    assert imported.text_columns and 'Text columns' in d.findings.text()
    bad = tmp_path / 'bad.npz'
    np.savez(bad, nothing=np.zeros(2))
    warnings = []
    monkeypatch.setattr(QtWidgets.QMessageBox, 'warning', staticmethod(lambda *a, **k: warnings.append(a)))
    assert d.import_file(str(bad)) is None and warnings


def test_kernel_classifier_trains_with_and_without_shot_noise(app):
    from quantumscope.gui import qml_experiments as Q
    k = Q.KernelExperiment()
    k.data.source.setCurrentIndex(k.data.source.findData('circles'))
    k.feature_map.setCurrentIndex(k.feature_map.findData('angle'))
    exact = k.train()
    assert exact['test'] >= 0.9 and 'support vectors' in k.result.text()
    k.shots.setValue(200)
    noisy = k.train()
    assert 'shots' in k.result.text() and noisy['test'] >= 0.7
    k.method.setCurrentIndex(k.method.findData('ridge'))
    assert k.train()['test'] >= 0.7


def test_variational_classifier_trains_and_stops(app):
    from quantumscope.gui import qml_experiments as Q
    v = Q.VariationalExperiment()
    v.data.source.setCurrentIndex(v.data.source.findData('circles'))
    v.steps.setValue(40)
    result = v.train()
    assert result['test'] >= 0.8 and v.open_circuit.isEnabled()
    assert len(v.loss_line.getData()[0]) == len(result['history'])
    v.method.setCurrentIndex(v.method.findData('Adam'))
    v._stop = False
    original = v.model.__class__.train

    def stop_early(model, *args, callback=None, **kwargs):              # press Stop after three steps
        def wrapped(index, *rest):
            if index == 3:
                v._stop = True
            return callback(index, *rest)
        return original(model, *args, callback=wrapped, **kwargs)
    v.model.__class__.train = stop_early
    try:
        v.train()
    finally:
        v.model.__class__.train = original
    assert 'Stopped after 3 steps' in v.result.text()


def test_decision_regions_for_any_number_of_features_and_concentration_hint(app):
    import pyqtgraph as pg
    from quantumscope.gui import qml_experiments as Q
    k = Q.KernelExperiment()
    k.resize(1200, 800)
    for name, qubits in (('circles', 2), ('mnist', 4), ('wine', 6), ('iris', 1)):
        k.data.source.setCurrentIndex(k.data.source.findData(name))
        k.data.qubits.setValue(qubits)
        k.train()
        items = k.regions.getPlotItem().items
        assert any(isinstance(i, pg.ImageItem) for i in items), name                  # regions always drawn
        assert any(isinstance(c, pg.IsocurveItem) for i in items for c in i.childItems()), name   # and the boundary
        title = k.regions.getPlotItem().titleLabel.text
        assert ('principal components' in title) == (qubits > 2), name
    k.data.source.setCurrentIndex(k.data.source.findData('wine'))
    k.data.qubits.setValue(6)
    k.reps.setValue(1)
    k.feature_map.setCurrentIndex(k.feature_map.findData('zz'))
    k.train()
    assert 'kernel concentration' in k.result.text()
    k.bandwidth.setValue(0.1)
    k.train()
    assert 'kernel concentration' not in k.result.text()                              # a smaller bandwidth helps


def test_classifier_qubits_follow_the_datasets_tab(app):
    from quantumscope.gui import qml_experiments as Q
    d = Q.DatasetsExperiment()
    d.source.setCurrentIndex(d.source.findData('wine'))
    d.qubits.setValue(3)
    for experiment in (Q.KernelExperiment(), Q.VariationalExperiment()):
        picker = experiment.data
        picker.source.setCurrentIndex(picker.source.findData('store'))
        assert not picker.qubits.isEnabled() and picker.qubits.value() == 3 and 'Datasets tab' in picker.summary.text()
        d.qubits.setValue(2)                                                      # follows a new preparation
        assert picker.qubits.value() == 2
        d.qubits.setValue(3)
        picker.source.setCurrentIndex(picker.source.findData('moons'))
        assert picker.qubits.isEnabled()


def test_vqls_example_check_and_live_solution_view(app):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    w.show()
    w.load_library('vqls', {'problem': 'single', 'layers': 1})
    w.verify_circuit()
    assert w.solution_button.isVisibleTo(w) and 'Optimize' in w.verify_status.text()
    dialog = w.show_vqls_solution()
    before = dialog.values[2]
    w.optimize_parameters()
    w.verify_circuit()
    assert dialog.values[2] > 0.999 > before and 'prepares the solution' in w.verify_status.text()
    assert np.allclose(dialog.values[0], dialog.values[1], atol=1e-3)            # the bars meet
    w.clear()
    assert not w.solution_button.isVisibleTo(w) and 'no longer a VQLS example' in dialog.summary.text()


def test_quantum_ml_lab_steps_tick_as_the_experiments_run(app):
    from quantumscope.gui import qml_experiments as Q
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    from quantumscope.gui.learn_window import LearnWindow
    from quantumscope.ml import progress
    progress.reset()
    learn = LearnWindow(workspace=CircuitWorkspace())
    learn.open_lesson('qml/90-lab-classify-the-circles')
    assert not any(learn._lab_steps().values())
    k = Q.KernelExperiment()
    k.data.source.setCurrentIndex(k.data.source.findData('circles'))
    k.feature_map.setCurrentIndex(k.feature_map.findData('angle'))
    k.train()
    assert learn._lab_steps() == {0: True, 1: False}                             # step 1 done, live
    k.feature_map.setCurrentIndex(k.feature_map.findData('zz'))
    k.train()
    assert all(learn._lab_steps().values())
    learn.open_lesson('qml/91-lab-mnist-pixels-to-qubits')
    d = Q.DatasetsExperiment()
    d.source.setCurrentIndex(d.source.findData('mnist'))
    assert learn._lab_steps()[0]                                                   # prepared with 4 features
    progress.reset()


def test_classifiers_choose_the_classes_of_a_many_class_dataset(app):
    from quantumscope.gui import qml_experiments as Q
    k = Q.KernelExperiment()
    k.show()
    picker = k.data
    picker.source.setCurrentIndex(picker.source.findData('mnist'))
    picker.qubits.setValue(4)
    assert picker.class_row.isVisibleTo(k) and picker.class_a.count() == 10
    assert (picker.class_a.currentText(), picker.class_b.currentText()) == ('0', '1')     # the suggestion
    picker.class_a.setCurrentIndex(picker.class_a.findText('3'))
    picker.class_b.setCurrentIndex(picker.class_b.findText('8'))
    p = picker.prepared()
    assert p.classes == ('3', '8') and '3 (+1) vs 8 (−1)' in picker.summary.text()
    picker.class_b.setCurrentIndex(picker.class_b.findText('3'))
    assert picker.prepared() is None and 'two different classes' in picker.summary.text()
    picker.source.setCurrentIndex(picker.source.findData('iris'))
    assert picker.class_row.isVisibleTo(k) and picker.class_a.count() == 3
    for key in ('circles', 'breast_cancer', 'store'):                                       # two classes, or prepared
        picker.source.setCurrentIndex(picker.source.findData(key))
        assert not picker.class_row.isVisibleTo(k), key
