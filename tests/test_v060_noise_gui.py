"""Optional GUI checks for noise in the circuit tab (QUANTUMSCOPE_GUI_TESTS=1)."""
import os

import numpy as np
import pytest

if os.environ.get('QUANTUMSCOPE_GUI_TESTS') != '1':
    pytest.skip('GUI tests are opt-in: set QUANTUMSCOPE_GUI_TESTS=1', allow_module_level=True)

QtWidgets = pytest.importorskip('PySide6.QtWidgets')

from quantumscope.physics import noise as N  # noqa: E402


@pytest.fixture(scope='module')
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def bell(app):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    w = CircuitWorkspace()
    w.set_circuit(2, [])
    w.place('H', 0, 0)
    w.place('CX', 1, 1)
    w.cell_click(0, 1)
    return w


def test_palette_has_a_noise_section(bell):
    texts = [bell.palette.item(i).text() for i in range(bell.palette.count())]
    assert '— Noise —' in texts and 'Depolarize' in texts
    assert bell.noise_button.text() == 'Noise: off'


def test_noise_from_the_palette_changes_the_view(bell):
    ideal = bell.result.toPlainText()
    bell.new_noise_p = 0.5
    bell.place('Dephase', 0, 2)
    assert bell.model.noise[(0, 2)].kind == 'phase_damping' and bell.model.noise[(0, 2)].p == 0.5
    assert bell.noise_button.text() == 'Noise: 1 element'
    assert 'purity' in bell.result.toPlainText() and bell.result.toPlainText() != ideal
    assert 'noisy density-matrix simulation' in bell.status.text()
    bell.undo()
    assert not bell.model.noise and 'exact ideal simulation' in bell.status.text()


def test_rejections_and_editing(bell, monkeypatch):
    bell.place('Bit flip', 0, 0)                               # H is there
    assert 'occupied' in bell.status.text() and not bell.model.noise
    bell.place('Bit flip', 1, 2)

    def accept(dialog):
        dialog.findChild(QtWidgets.QDoubleSpinBox).setValue(0.25)
        return QtWidgets.QDialog.DialogCode.Accepted
    monkeypatch.setattr(QtWidgets.QDialog, 'exec', accept)
    bell.edit_gate_at(1, 2)                                    # double-click opens the noise editor
    assert bell.model.noise[(1, 2)].p == 0.25


def test_noise_dialog_applies_a_preset(bell, monkeypatch):
    def choose(dialog):
        dialog.findChild(QtWidgets.QComboBox).setCurrentText('Moderate')
        return QtWidgets.QDialog.DialogCode.Accepted
    monkeypatch.setattr(QtWidgets.QDialog, 'exec', choose)
    bell.noise_dialog()
    assert bell.model.noise_model == N.PRESETS['Moderate'] and bell.noise_button.text() == 'Noise: Moderate'


def test_bloch_vectors_shrink_and_shots_use_noisy_probabilities(bell):
    bell.model.set_noise_model(N.NoiseModel(True, readout=0.2))
    bell._changed()
    vectors = bell.blochs.vecs if hasattr(bell.blochs, 'vecs') else None
    probs = bell._final_distribution()
    assert probs[1] == pytest.approx(0.5 * 0.2 * 0.8 * 2, abs=1e-9)       # readout flips one of the two bits
    bell.measure()
    assert '(noisy)' in bell.bars.title
    bell.model.set_noise_model(N.NoiseModel(True, single=0.2, two=0.2))
    bell._changed()
    lengths = [np.linalg.norm(v) for v in bell.inline_blochs.vecs]
    assert all(length < 0.5 for length in lengths)              # Bell qubits are mixed


def test_save_reopen_qasm_and_pdf_with_noise(bell, tmp_path, monkeypatch):
    bell.place('Amp. damp', 1, 2)
    bell.model.set_noise_model(N.PRESETS['Gentle'])
    bell._changed()
    final = bell.noisy_view[1][-1]
    monkeypatch.setattr(QtWidgets.QMessageBox, 'question',
                        staticmethod(lambda *a, **k: QtWidgets.QMessageBox.StandardButton.Yes))
    for name, action in (('c.qscope', bell.save_native), ('c.qasm', bell.export_qasm), ('c.pdf', bell.export_pdf)):
        path = str(tmp_path / name)
        monkeypatch.setattr(QtWidgets.QFileDialog, 'getSaveFileName', staticmethod(lambda *a, p=path, **k: (p, '')))
        action()
        assert os.path.getsize(path) > 100
    assert 'not exported' in (tmp_path / 'c.qasm').read_text()
    monkeypatch.setattr(QtWidgets.QFileDialog, 'getOpenFileName',
                        staticmethod(lambda *a, **k: (str(tmp_path / 'c.qscope'), '')))
    bell.clear()
    bell.load_native()
    assert bell.model.noise and bell.model.noise_model == N.PRESETS['Gentle']
    assert np.allclose(bell.noisy_view[1][-1], final)


def test_large_registers_show_noise_only_at_the_end(app):
    from quantumscope.gui.circuit_workspace import CircuitWorkspace
    from quantumscope.physics.circuits import Gate
    w = CircuitWorkspace()
    n = N.MAX_STORED_QUBITS + 1
    w.set_circuit(n, [Gate('H', (0,)), Gate('X', (0,))])     # two columns: a middle step exists
    w.model.set_noise_model(N.PRESETS['Gentle'])
    w._changed()
    assert 'purity' in w.result.toPlainText()                 # final column: noisy
    w.step.setValue(1)
    assert 'final column' in w.result.toPlainText()
