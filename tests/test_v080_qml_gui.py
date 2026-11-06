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
