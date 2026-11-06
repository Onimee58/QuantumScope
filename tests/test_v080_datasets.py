"""v0.8.0 (16a): built-in datasets, import, the checker and preprocessing (quantumscope.ml.datasets)."""
import math

import numpy as np
import pytest

from quantumscope.ml import datasets as D

UCI = {'iris': (150, 4, [50, 50, 50]), 'wine': (178, 13, [59, 71, 48]), 'breast_cancer': (569, 30, [212, 357]),
       'digits': (1797, 64, [178, 182, 177, 183, 181, 182, 181, 179, 174, 180]), 'mnist': (2000, 784, [200] * 10)}


@pytest.mark.parametrize('name', list(UCI))
def test_builtin_datasets_match_their_sources(name):
    ds = D.load(name)
    rows, features, counts = UCI[name]
    assert ds.X.shape == (rows, features) and ds.counts.tolist() == counts
    assert len(ds.features) == features and ds.license and 'https://' in ds.citation or name == 'mnist'
    assert ds.license == ('CC BY-SA 3.0' if name == 'mnist' else 'CC BY 4.0')
    if name in ('digits', 'mnist'):
        assert ds.image_shape == ((8, 8) if name == 'digits' else (28, 28))
        assert 0 <= ds.X.min() and ds.X.max() <= (16 if name == 'digits' else 255)


@pytest.mark.parametrize('kind', D.SYNTHETIC)
def test_synthetic_datasets_are_balanced_and_reproducible(kind):
    a, b = D.load(kind, samples=120, noise=0.05, seed=3), D.load(kind, samples=120, noise=0.05, seed=3)
    assert a.X.shape == (120, 2) and a.counts.tolist() == [60, 60] and np.array_equal(a.X, b.X)
    assert not np.array_equal(a.X, D.load(kind, samples=120, noise=0.05, seed=4).X)


def test_csv_import_header_label_column_text_and_missing(tmp_path):
    path = tmp_path / 'plants.csv'
    path.write_text('height;colour;label;width\n1.5;red;A;2\n2.0;blue;B;?\n1.7;red;A;2.5\n2.2;;B;3\n')
    ds = D.import_file(str(path))
    assert ds.features == ['height', 'colour', 'width'] and ds.classes == ['A', 'B']   # 'label' found by name
    assert ds.y.tolist() == [0, 1, 0, 1] and ds.text_columns == {1: ['blue', 'red']}
    assert int(np.isnan(ds.X).sum()) == 2                                               # '?' and the empty cell
    plain = tmp_path / 'plain.csv'
    plain.write_text('0.1,0.2,0\n0.3,0.4,1\n0.5,0.6,1\n')
    ds = D.import_file(str(plain))                                                     # no header: last column
    assert ds.features == ['column 1', 'column 2'] and ds.y.tolist() == [0, 1, 1]


def test_npz_import_flattens_images_and_rejects_bad_files(tmp_path):
    path = tmp_path / 'tiny.npz'
    np.savez(path, images=np.zeros((6, 4, 4)), labels=np.array(['cat', 'dog'] * 3))
    ds = D.import_file(str(path))
    assert ds.X.shape == (6, 16) and ds.image_shape == (4, 4) and ds.classes == ['cat', 'dog']
    bad = tmp_path / 'bad.npz'
    np.savez(bad, something=np.zeros(3))
    with pytest.raises(ValueError, match='X and y'):
        D.import_file(str(bad))
    with pytest.raises(ValueError):
        D.import_file(str(tmp_path / 'data.xlsx'))


def test_checker_findings_and_verdicts():
    verdict, findings, recipe = D.check(D.load('mnist'), qubits=4)
    messages = ' '.join(f.message for f in findings)
    assert verdict == 'preprocess' and '10 classes' in messages and 'PCA' in ' '.join(f.suggestion for f in findings)
    assert recipe.components == 4 and recipe.per_class == 100 and recipe.classes == (0, 1)
    one = D.Dataset('one', np.zeros((20, 2)), np.zeros(20, int), ['a', 'b'], ['only'])
    assert D.check(one)[0] == 'stop'
    tiny = D.Dataset('tiny', np.random.default_rng(0).normal(size=(12, 2)), np.array([0] * 6 + [1] * 6), ['a', 'b'],
                     ['x', 'y'])
    assert D.check(tiny)[0] == 'stop'                                                   # under 10 per class
    ready = D.Dataset('ready', np.random.default_rng(1).uniform(0.5, 2.5, (40, 2)), np.array([0, 1] * 20), ['a', 'b'],
                      ['x', 'y'])
    assert D.check(ready, qubits=2)[0] == 'ready'


def test_prepare_fits_on_training_data_only_and_gives_plus_minus_labels():
    ds = D.load('wine')
    verdict, _, recipe = D.check(ds, qubits=3)
    p = D.prepare(ds, recipe)
    assert p.X_train.shape[1] == 3 and set(np.unique(p.y_train)) == {1, -1}
    assert p.X_train.min() == pytest.approx(0) and p.X_train.max() == pytest.approx(math.pi)   # train fills [0, π]
    assert len(p.y_test) == pytest.approx(0.25 * (len(p.y_train) + len(p.y_test)), abs=2)
    assert 'PCA' in ' '.join(p.steps)
    # The test data never influences the fitted steps: changing it leaves the training data unchanged.
    changed = D.Dataset(ds.name, ds.X.copy(), ds.y, ds.features, ds.classes)
    q = D.prepare(changed, recipe)
    assert np.allclose(p.X_train, q.X_train)


def test_prepare_handles_missing_values_and_text(tmp_path):
    rng = np.random.default_rng(2)
    rows = ['size,shape,kind'] + [f'{rng.uniform(1, 3):.3f},{"round" if k % 2 else "square"},{k % 2}' for k in range(60)]
    rows[5] = 'nan,round,0'
    path = tmp_path / 'shapes.csv'
    path.write_text('\n'.join(rows) + '\n')
    ds = D.import_file(str(path))
    verdict, findings, recipe = D.check(ds, qubits=2)
    assert verdict == 'preprocess' and recipe.missing == 'drop'
    p = D.prepare(ds, recipe)
    assert not np.isnan(p.X_train).any() and not np.isnan(p.X_test).any()
    recipe.missing, recipe.text = 'mean', 'drop'
    p = D.prepare(ds, recipe)
    assert p.features == ['size'] and not np.isnan(p.X_test).any()
