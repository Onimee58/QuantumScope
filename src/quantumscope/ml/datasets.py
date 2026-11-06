"""Datasets for quantum machine learning (NumPy only, no Qt): built-in and synthetic data, CSV and
.npz import, a checker that says whether a dataset fits a quantum model, and the preprocessing
that makes it fit. v0.8.0 classifies two classes at a time.

Everything a model learns from the data (column means, PCA, scaling) is fitted on the training
split only and then applied to the test split, so the test accuracy is honest.
"""
from dataclasses import dataclass, field
import csv
import math
import os

import numpy as np

DATA = os.path.join(os.path.dirname(__file__), 'data')
MAX_QUBITS = 10
LABEL_NAMES = ('label', 'labels', 'target', 'class', 'classes', 'y', 'species', 'diagnosis', 'category')
MISSING = ('', 'na', 'nan', 'n/a', 'null', 'none', '?', '-')

BUILTIN = {
    'iris': ('Iris', 'Measurements of 150 iris flowers of three species.', 'CC BY 4.0',
             'Fisher, R. (1936). Iris [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C56C76'),
    'wine': ('Wine', 'Chemical analysis of 178 wines from three cultivars.', 'CC BY 4.0',
             'Aeberhard, S. & Forina, M. (1992). Wine [Dataset]. UCI Machine Learning Repository. '
             'https://doi.org/10.24432/C5PC7J'),
    'breast_cancer': ('Breast Cancer Wisconsin (Diagnostic)', 'Features of cell nuclei in 569 breast masses, '
                      'malignant or benign.', 'CC BY 4.0',
                      'Wolberg, W., Mangasarian, O., Street, N., & Street, W. (1993). Breast Cancer Wisconsin '
                      '(Diagnostic) [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5DW2B'),
    'digits': ('Digits (8×8)', '1,797 handwritten digits as 8×8 images (the UCI test set).', 'CC BY 4.0',
               'Alpaydin, E. & Kaynak, C. (1998). Optical Recognition of Handwritten Digits [Dataset]. '
               'UCI Machine Learning Repository. https://doi.org/10.24432/C50P49'),
    'mnist': ('MNIST (2,000-image subset)', 'The first 200 images of each digit from the MNIST test set, 28×28.',
              'CC BY-SA 3.0',
              'LeCun, Y., Cortes, C., & Burges, C. J. C. The MNIST database of handwritten digits. '
              'Copyright Yann LeCun and Corinna Cortes.'),
}
SYNTHETIC = ('moons', 'circles', 'xor', 'blobs')


@dataclass
class Dataset:
    name: str
    X: np.ndarray                      # samples × features, float (NaN = missing)
    y: np.ndarray                      # class index per sample, 0 … k−1
    features: list
    classes: list
    description: str = ''
    license: str = ''
    citation: str = ''
    image_shape: tuple = None          # e.g. (8, 8) for images
    text_columns: dict = field(default_factory=dict)   # column → its categories (values are codes)

    @property
    def counts(self):
        return np.bincount(self.y, minlength=len(self.classes))


# ---- built-in and synthetic data -----------------------------------------------------------------
def load(name, **options):
    """A built-in dataset by key, or a synthetic one ('moons', 'circles', 'xor', 'blobs')."""
    if name in SYNTHETIC:
        return synthetic(name, **options)
    if name not in BUILTIN:
        raise ValueError(f'Unknown dataset {name!r}')
    title, description, license_, citation = BUILTIN[name]
    with np.load(os.path.join(DATA, f'{name}.npz'), allow_pickle=False) as z:
        shape = tuple(int(v) for v in z['shape']) if 'shape' in z.files else None
        return Dataset(title, z['X'].astype(float), z['y'].astype(int), [str(f) for f in z['features']],
                       [str(c) for c in z['classes']], description, license_, citation, shape)


def synthetic(kind, samples=200, noise=0.1, seed=0):
    """Two balanced classes in 2-D, for seeing decision boundaries."""
    rng = np.random.default_rng(seed)
    half = samples // 2
    if kind == 'moons':
        t = rng.uniform(0, math.pi, half)
        a = np.c_[np.cos(t), np.sin(t)]
        b = np.c_[1 - np.cos(t), 0.5 - np.sin(t)]
    elif kind == 'circles':
        t = rng.uniform(0, 2 * math.pi, half)
        a = np.c_[np.cos(t), np.sin(t)]
        b = 0.5 * np.c_[np.cos(t), np.sin(t)]
    elif kind == 'xor':
        points = rng.uniform(-1, 1, (2 * half, 2))
        same = points[:, 0] * points[:, 1] > 0
        a, b = points[same][:half], points[~same][:half]
        while len(a) < half or len(b) < half:                  # top up the smaller class
            extra = rng.uniform(-1, 1, (half, 2))
            s = extra[:, 0] * extra[:, 1] > 0
            a = np.r_[a, extra[s]][:half]
            b = np.r_[b, extra[~s]][:half]
    elif kind == 'blobs':
        a = rng.normal((-1, -1), 0.5, (half, 2))
        b = rng.normal((1, 1), 0.5, (half, 2))
    else:
        raise ValueError(f'Unknown synthetic dataset {kind!r}')
    X = np.r_[a, b] + rng.normal(0, noise, (2 * half, 2))
    y = np.r_[np.zeros(half, int), np.ones(half, int)]
    return Dataset(kind.capitalize(), X, y, ['x₁', 'x₂'], ['class A', 'class B'],
                   f'Synthetic: {kind}, {2 * half} points, noise {noise:g}, seed {seed}.')


# ---- your own data ----------------------------------------------------------------------------------
def import_file(path):
    """A dataset from a .csv or .npz file."""
    if path.lower().endswith('.npz'):
        return _import_npz(path)
    if path.lower().endswith(('.csv', '.txt')):
        return _import_csv(path)
    raise ValueError('Use a .csv or .npz file')


def _number(text):
    try:
        return float(text)
    except ValueError:
        return None


def _import_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as handle:
        sample = handle.read(4096)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
        except csv.Error:
            dialect = csv.excel
        rows = [r for r in csv.reader(handle, dialect) if any(cell.strip() for cell in r)]
    if len(rows) < 2:
        raise ValueError('The file has fewer than two rows')
    header = any(_number(c) is None and c.strip().lower() not in MISSING for c in rows[0])
    names = [c.strip() or f'column {i + 1}' for i, c in enumerate(rows[0])] if header else \
        [f'column {i + 1}' for i in range(len(rows[0]))]
    body = rows[1:] if header else rows
    width = len(names)
    body = [r + [''] * (width - len(r)) if len(r) < width else r[:width] for r in body]
    label_column = next((i for i, n in enumerate(names) if n.lower() in LABEL_NAMES), width - 1)
    labels = [r[label_column].strip() for r in body]
    keep = [i for i in range(width) if i != label_column]
    columns, text_columns = [], {}
    for out_index, i in enumerate(keep):
        cells = [r[i].strip() for r in body]
        values = [math.nan if c.lower() in MISSING else _number(c) for c in cells]
        if any(v is None for v in values):                     # text: categories become codes
            categories = sorted({c for c in cells if c.lower() not in MISSING})
            codes = {c: float(k) for k, c in enumerate(categories)}
            values = [math.nan if c.lower() in MISSING else codes[c] for c in cells]
            text_columns[out_index] = categories
        columns.append(values)
    X = np.array(columns, float).T if columns else np.empty((len(body), 0))
    classes = sorted(set(labels), key=lambda v: (_number(v) is None, _number(v) or 0, v))
    y = np.array([classes.index(v) for v in labels], int)
    return Dataset(os.path.basename(path), X, y, [names[i] for i in keep], classes,
                   f'Imported from {os.path.basename(path)}.', text_columns=text_columns)


def _import_npz(path):
    with np.load(path, allow_pickle=False) as z:
        keys = {k.lower(): k for k in z.files}
        x_key = next((keys[k] for k in ('x', 'data', 'features', 'images', 'inputs') if k in keys), None)
        y_key = next((keys[k] for k in ('y', 'labels', 'label', 'target', 'targets', 'classes') if k in keys), None)
        if x_key is None or y_key is None:
            raise ValueError(f'The file needs arrays named X and y (found: {", ".join(z.files)})')
        X, raw = np.asarray(z[x_key]), np.asarray(z[y_key]).ravel()
        names = [str(n) for n in z[keys['feature_names']]] if 'feature_names' in keys else None
    shape = None
    if X.ndim > 2:                                             # images: flatten, remember the shape
        shape = tuple(X.shape[1:3]) if X.ndim == 3 else tuple(X.shape[1:])
        X = X.reshape(len(X), -1)
    if len(X) != len(raw):
        raise ValueError(f'X has {len(X)} samples but y has {len(raw)}')
    values = [str(v) for v in raw]
    classes = sorted(set(values), key=lambda v: (_number(v) is None, _number(v) or 0, v))
    y = np.array([classes.index(v) for v in values], int)
    names = names if names and len(names) == X.shape[1] else [f'feature {i + 1}' for i in range(X.shape[1])]
    return Dataset(os.path.basename(path), X.astype(float), y, names, classes,
                   f'Imported from {os.path.basename(path)}.', image_shape=shape)


# ---- the checker ------------------------------------------------------------------------------------
@dataclass
class Finding:
    level: str              # 'ok', 'fix' (preprocessing will handle it), 'stop' (cannot be used)
    message: str
    suggestion: str = ''


@dataclass
class Recipe:
    """The preprocessing steps, in order. Every step is optional and visible."""
    classes: tuple = (0, 1)            # the two classes to separate
    missing: str = 'none'              # 'none', 'drop' rows, or 'mean' (fill with the training mean)
    text: str = 'encode'               # text columns: 'encode' (as category codes) or 'drop'
    per_class: int = 0                 # at most this many samples per class (0 = all)
    components: int = 0                # PCA down to this many features (0 = keep)
    drop_constant: bool = True
    scale: str = 'pi'                  # 'pi': each feature to [0, π] (the encoding range); 'none'
    test_fraction: float = 0.25
    seed: int = 0


def check(dataset, qubits=4, max_samples=200):
    """What stands between this dataset and a quantum classifier on `qubits` qubits, and the recipe
    that fixes it. Returns (verdict, findings, recipe); verdict is 'ready', 'preprocess' or 'stop'."""
    X, y = dataset.X, dataset.y
    findings = [Finding('ok', f'{len(X)} samples, {X.shape[1]} features, {len(dataset.classes)} classes.')]
    recipe = Recipe()
    counts = dataset.counts
    if X.shape[1] == 0:
        return 'stop', findings + [Finding('stop', 'There are no feature columns.')], recipe
    if len(dataset.classes) < 2:
        return 'stop', findings + [Finding('stop', 'Only one class: there is nothing to separate.')], recipe
    order = np.argsort(-counts, kind='stable')
    if len(dataset.classes) > 2:
        a, b = sorted(int(c) for c in order[:2])
        recipe.classes = (a, b)
        findings.append(Finding('fix', f'{len(dataset.classes)} classes; this version separates two at a time.',
                                f'Choose two classes (suggested: {dataset.classes[a]} and {dataset.classes[b]}).'))
    small = [dataset.classes[c] for c in recipe.classes if counts[c] < 10]
    if small:
        return 'stop', findings + [Finding('stop', f'Too few samples (under 10) in: {", ".join(small)}.')], recipe
    missing = int(np.isnan(X).sum())
    if missing:
        rows = int(np.isnan(X).any(axis=1).sum())
        recipe.missing = 'drop' if rows <= 0.05 * len(X) else 'mean'
        findings.append(Finding('fix', f'{missing} missing values in {rows} samples.',
                                'Drop those samples (few of them).' if recipe.missing == 'drop' else
                                'Fill each with its column\'s mean (too many samples to drop).'))
    if dataset.text_columns:
        names = ', '.join(dataset.features[i] for i in dataset.text_columns)
        findings.append(Finding('fix', f'Text columns: {names}.', 'Encode their categories as numbers, or drop them.'))
    chosen = np.isin(y, recipe.classes)
    with np.errstate(all='ignore'):
        constant = int(np.sum(np.nanstd(X[chosen], axis=0) == 0))
    if constant:
        findings.append(Finding('fix', f'{constant} features never change.', 'Drop them: they carry no information.'))
    usable = X.shape[1] - constant
    if usable > qubits:
        recipe.components = qubits
        findings.append(Finding('fix', f'{usable} features but {qubits} qubits (one feature per qubit).',
                                f'Reduce to {qubits} features with PCA (principal component analysis).'))
    total = int(sum(counts[c] for c in recipe.classes))
    if total > max_samples:
        recipe.per_class = max_samples // 2
        findings.append(Finding('fix', f'{total} samples: a quantum kernel compares every pair (N² circuits).',
                                f'Use {recipe.per_class} samples per class, chosen at random.'))
    ratio = min(counts[c] for c in recipe.classes) / max(counts[c] for c in recipe.classes)
    if ratio < 0.5 and not recipe.per_class:
        findings.append(Finding('ok', f'The two classes are unbalanced ({ratio:.0%}); accuracy alone can mislead.'))
    with np.errstate(all='ignore'):
        lo, hi = np.nanmin(X[chosen], axis=0), np.nanmax(X[chosen], axis=0)
    if np.nanmin(lo) < 0 or np.nanmax(hi) > math.pi or np.nanmax(hi - lo) > 10 * max(1e-12, np.nanmin(hi - lo)):
        findings.append(Finding('fix', 'Features are on different scales or outside the angle range.',
                                'Scale each feature to [0, π] for angle encoding.'))
    verdict = 'preprocess' if any(f.level == 'fix' for f in findings) else 'ready'
    return verdict, findings, recipe


# ---- preprocessing -----------------------------------------------------------------------------------
@dataclass
class Prepared:
    X_train: np.ndarray
    X_test: np.ndarray
    y_train: np.ndarray                # ±1 (+1 = the first chosen class)
    y_test: np.ndarray
    features: list
    classes: tuple                     # (name of +1, name of −1)
    steps: list                        # what was done, in words


def prepare(dataset, recipe):
    """Apply a recipe: choose classes, clean, split, then fit on the training split only."""
    rng = np.random.default_rng(recipe.seed)
    a, b = recipe.classes
    steps = [f'Classes: {dataset.classes[a]} (+1) and {dataset.classes[b]} (−1).']
    X, y, names = dataset.X.copy(), dataset.y, list(dataset.features)
    pick = np.isin(y, (a, b))
    X, y = X[pick], y[pick]
    if recipe.text == 'drop' and dataset.text_columns:
        keep = [i for i in range(X.shape[1]) if i not in dataset.text_columns]
        X, names = X[:, keep], [names[i] for i in keep]
        steps.append(f'Dropped {len(dataset.text_columns)} text columns.')
    elif dataset.text_columns:
        steps.append(f'Encoded {len(dataset.text_columns)} text columns as category codes.')
    if recipe.missing == 'drop':
        good = ~np.isnan(X).any(axis=1)
        steps.append(f'Dropped {int((~good).sum())} samples with missing values.')
        X, y = X[good], y[good]
    if recipe.per_class:
        chosen = np.concatenate([rng.permutation(np.flatnonzero(y == c))[:recipe.per_class] for c in (a, b)])
        X, y = X[chosen], y[chosen]
        steps.append(f'Kept at most {recipe.per_class} samples per class.')
    test = np.zeros(len(y), bool)                              # stratified split
    for c in (a, b):
        members = rng.permutation(np.flatnonzero(y == c))
        test[members[:int(round(recipe.test_fraction * len(members)))]] = True
    Xtr, Xte = X[~test], X[test]
    steps.append(f'Split: {int((~test).sum())} for training, {int(test.sum())} for testing.')
    if recipe.missing == 'mean' and (np.isnan(Xtr).any() or np.isnan(Xte).any()):   # either split
        means = np.nanmean(Xtr, axis=0)
        means = np.where(np.isnan(means), 0.0, means)
        Xtr = np.where(np.isnan(Xtr), means, Xtr)
        Xte = np.where(np.isnan(Xte), means, Xte)
        steps.append('Filled missing values with the training means.')
    if recipe.drop_constant:
        varying = np.nanstd(Xtr, axis=0) > 0
        if not varying.all():
            steps.append(f'Dropped {int((~varying).sum())} constant features.')
            Xtr, Xte, names = Xtr[:, varying], Xte[:, varying], [n for n, v in zip(names, varying) if v]
    if recipe.components and recipe.components < Xtr.shape[1]:
        mean = Xtr.mean(axis=0)
        _, s, vt = np.linalg.svd(Xtr - mean, full_matrices=False)
        k = recipe.components
        explained = float((s[:k] ** 2).sum() / max(1e-300, (s ** 2).sum()))
        Xtr, Xte = (Xtr - mean) @ vt[:k].T, (Xte - mean) @ vt[:k].T
        names = [f'PC{i + 1}' for i in range(k)]
        steps.append(f'PCA: {k} components keep {explained:.0%} of the variance.')
    if recipe.scale == 'pi':
        lo, hi = Xtr.min(axis=0), Xtr.max(axis=0)
        span = np.where(hi > lo, hi - lo, 1.0)
        Xtr, Xte = (Xtr - lo) / span * math.pi, (Xte - lo) / span * math.pi
        steps.append('Scaled each feature to [0, π] (from the training data).')
    to_pm = lambda v: np.where(v == a, 1, -1)                  # noqa: E731
    return Prepared(Xtr, Xte, to_pm(y[~test]), to_pm(y[test]), names,
                    (dataset.classes[a], dataset.classes[b]), steps)
