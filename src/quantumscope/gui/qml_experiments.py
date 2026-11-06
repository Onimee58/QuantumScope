"""The Quantum ML area (v0.8.0): Datasets, Quantum Kernel Classifier and Variational Classifier.

The Datasets experiment checks and prepares data; what it prepares is shared with both classifiers
("From the Datasets tab"). Each classifier can also use any built-in or synthetic dataset directly,
prepared with the checker's suggested recipe. The physics and learning live in quantumscope.ml.
"""
import math

import numpy as np
from PySide6.QtCore import QObject, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QImage, QPainter
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout,
                               QGroupBox, QHBoxLayout, QLabel, QMessageBox, QPushButton, QSpinBox, QVBoxLayout,
                               QWidget)

from quantumscope.ml import datasets as D
from quantumscope.ml import kernels as K
from quantumscope.ml import variational as V

CLASS_COLOURS = ('#5ae6ff', '#ff9a5a')                     # +1, −1


class DataStore(QObject):
    """What the Datasets experiment prepared, shared with the classifiers."""
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.dataset = self.recipe = self.prepared = None

    def publish(self, dataset, recipe, prepared):
        self.dataset, self.recipe, self.prepared = dataset, recipe, prepared
        self.changed.emit()


STORE = DataStore()


def _source_combo():
    box = QComboBox()
    for key, (title, *_rest) in D.BUILTIN.items():
        box.addItem(title, key)
    box.insertSeparator(box.count())
    for kind in D.SYNTHETIC:
        box.addItem(f'{kind.capitalize()} (synthetic, 2-D)', kind)
    return box


def _plot(title, x_label='', y_label=''):
    import pyqtgraph as pg
    plot = pg.PlotWidget()
    plot.setTitle(title)
    plot.setLabel('bottom', x_label)
    plot.setLabel('left', y_label)
    plot.showGrid(x=True, y=True, alpha=0.15)
    plot.setMinimumHeight(220)
    for side in ('left', 'bottom'):                            # plain numbers: no automatic "×0.001"
        plot.getAxis(side).enableAutoSIPrefix(False)
    return plot


def _scatter_points(plot, X, y, size=8, symbol='o', outline=None):
    import pyqtgraph as pg
    for label, colour in zip((1, -1), CLASS_COLOURS):
        chosen = y == label
        plot.addItem(pg.ScatterPlotItem(X[chosen, 0], X[chosen, 1], size=size, symbol=symbol,
                                        brush=pg.mkBrush(colour), pen=pg.mkPen(outline or '#0b1420', width=1)))


class ImageStrip(QWidget):
    """A few example images per chosen class (Digits, MNIST)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(150)
        self.rows = []                                     # (class name, [images])

    def show_images(self, dataset, classes, per_row=10):
        self.rows = []
        if dataset is not None and dataset.image_shape:
            h, w = dataset.image_shape
            for c in classes:
                picks = np.flatnonzero(dataset.y == c)[:per_row]
                self.rows.append((dataset.classes[c], [dataset.X[i].reshape(h, w) for i in picks]))
        self.setVisible(bool(self.rows))
        self.update()

    def paintEvent(self, event):
        if not self.rows:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        row_h = (self.height() - 8) / len(self.rows)
        size = min(row_h - 6, (self.width() - 90) / max(len(r[1]) for r in self.rows) - 4)
        for r, (name, images) in enumerate(self.rows):
            y = 4 + r * row_h
            p.setPen(QColor('#d8e6f3'))
            p.setFont(QFont('Sans', 10, QFont.Weight.Bold))
            p.drawText(QRectF(0, y, 80, row_h), Qt.AlignmentFlag.AlignCenter, f'class {name}')
            for k, image in enumerate(images):
                top = max(1e-9, float(image.max()))
                pixels = (255 * (image / top)).astype(np.uint8).copy()
                qimage = QImage(pixels.data, pixels.shape[1], pixels.shape[0], pixels.shape[1],
                                QImage.Format.Format_Grayscale8)
                p.drawImage(QRectF(86 + k * (size + 4), y + (row_h - size) / 2, size, size), qimage)
        p.end()


# ============================================================================================
class DatasetsExperiment(QWidget):
    """Choose or import data, see whether it fits a quantum model, and prepare it."""

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QHBoxLayout(self)
        left = QWidget()
        left.setMaximumWidth(400)
        form = QVBoxLayout(left)
        title = QLabel('DATASETS  ·  check and prepare data for a quantum classifier')
        title.setStyleSheet('font-weight:700;')
        title.setWordWrap(True)
        form.addWidget(title)
        source = QGroupBox('Data')
        sv = QFormLayout(source)
        self.source = _source_combo()
        sv.addRow('Dataset', self.source)
        self.import_button = QPushButton('Import CSV or .npz…')
        self.import_button.setToolTip('Your own data: a label column (named label, target, class … or the last '
                                      'column) and numeric or text features')
        sv.addRow(self.import_button)
        self.qubits = QSpinBox()
        self.qubits.setRange(1, D.MAX_QUBITS)
        self.qubits.setValue(4)
        self.qubits.setToolTip('One feature per qubit: the checker suggests reducing the data to this many '
                               'features, and the prepared data has that many')
        sv.addRow('Qubits (= features)', self.qubits)
        form.addWidget(source)
        self.verdict = QLabel()
        self.verdict.setWordWrap(True)
        self.verdict.setStyleSheet('font-weight:700;')
        form.addWidget(self.verdict)
        self.findings = QLabel()
        self.findings.setWordWrap(True)
        self.findings.setTextFormat(Qt.TextFormat.RichText)
        form.addWidget(self.findings)
        recipe = QGroupBox('Preprocessing')
        rv = QFormLayout(recipe)
        self.class_a, self.class_b = QComboBox(), QComboBox()
        pair = QHBoxLayout()
        pair.addWidget(self.class_a)
        pair.addWidget(QLabel('vs'))
        pair.addWidget(self.class_b)
        rv.addRow('Classes', pair)
        self.missing = QComboBox()
        for label, value in (('Keep', 'none'), ('Drop those samples', 'drop'), ('Fill with the mean', 'mean')):
            self.missing.addItem(label, value)
        rv.addRow('Missing values', self.missing)
        self.text = QComboBox()
        for label, value in (('Encode as numbers', 'encode'), ('Drop', 'drop')):
            self.text.addItem(label, value)
        rv.addRow('Text columns', self.text)
        self.per_class = QSpinBox()
        self.per_class.setRange(0, 5000)
        self.per_class.setSpecialValueText('all')
        rv.addRow('Samples per class', self.per_class)
        self.components = QSpinBox()
        self.components.setRange(0, D.MAX_QUBITS)
        self.components.setSpecialValueText('keep all')
        rv.addRow('PCA components', self.components)
        self.scale = QCheckBox('Scale each feature to [0, π]')
        self.scale.setChecked(True)
        rv.addRow(self.scale)
        self.test_fraction = QDoubleSpinBox()
        self.test_fraction.setRange(0.1, 0.5)
        self.test_fraction.setSingleStep(0.05)
        self.test_fraction.setValue(0.25)
        rv.addRow('Test share', self.test_fraction)
        buttons = QHBoxLayout()
        self.suggest = QPushButton('Apply suggestions')
        self.prepare_button = QPushButton('Prepare')
        self.prepare_button.setToolTip('Prepare the data and share it with both classifiers')
        buttons.addWidget(self.suggest)
        buttons.addWidget(self.prepare_button)
        rv.addRow(buttons)
        form.addWidget(recipe)
        self.steps = QLabel()
        self.steps.setWordWrap(True)
        self.steps.setObjectName('muted')
        form.addWidget(self.steps)
        form.addStretch()
        root.addWidget(left)
        right = QVBoxLayout()
        self.plot = _plot('Prepared training data (first two features)')
        right.addWidget(self.plot, 3)
        self.images = ImageStrip()
        right.addWidget(self.images, 2)
        root.addLayout(right, 1)
        self.dataset, self.recipe = None, None
        self.source.currentIndexChanged.connect(self._load_source)
        self.import_button.clicked.connect(self.import_file)
        self.qubits.valueChanged.connect(self._check)
        self.suggest.clicked.connect(self._check)
        self.prepare_button.clicked.connect(self.prepare)
        self._load_source()

    def _load_source(self, *_):
        self.source_key = self.source.currentData()          # a built-in or synthetic key
        self.use(D.load(self.source_key))

    def import_file(self, path=None):
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, 'Import data', '', 'Data (*.csv *.npz *.txt)')
            if not path:
                return None
        try:
            dataset = D.import_file(path)
        except (OSError, ValueError, UnicodeDecodeError) as exc:
            QMessageBox.warning(self, 'Import data', f'This file could not be read:\n{exc}')
            return None
        self.source_key = 'imported'
        self.use(dataset)
        return dataset

    def use(self, dataset):
        self.dataset = dataset
        for box in (self.class_a, self.class_b):
            box.blockSignals(True)
            box.clear()
            for k, name in enumerate(dataset.classes):
                box.addItem(f'{name} ({int(dataset.counts[k])})', k)
            box.blockSignals(False)
        self._check()

    def _check(self, *_):
        """Run the checker and fill in its suggested recipe."""
        verdict, findings, recipe = D.check(self.dataset, qubits=self.qubits.value())
        self.recipe = recipe
        colour = {'ready': '#5ad48a', 'preprocess': '#ffba50', 'stop': '#ff7a7a'}[verdict]
        text = {'ready': 'Ready: this data fits as it is.', 'preprocess': 'Usable after preprocessing (suggested below).',
                'stop': 'Cannot be used.'}[verdict]
        self.verdict.setText(f'<span style="color:{colour}">{text}</span>')
        icon = {'ok': '✓', 'fix': '⚠', 'stop': '✗'}
        self.findings.setText('<br>'.join(f'{icon[f.level]} {f.message}' + (f' <i>{f.suggestion}</i>' if f.suggestion else '')
                                          for f in findings))
        self.class_a.setCurrentIndex(self.class_a.findData(recipe.classes[0]))
        self.class_b.setCurrentIndex(self.class_b.findData(recipe.classes[1]))
        self.missing.setCurrentIndex(self.missing.findData(recipe.missing))
        self.text.setCurrentIndex(self.text.findData(recipe.text))
        self.per_class.setValue(recipe.per_class)
        self.components.setValue(recipe.components)
        self.prepare_button.setEnabled(verdict != 'stop')
        self.images.show_images(self.dataset, recipe.classes)
        if verdict != 'stop':
            self.prepare()

    def current_recipe(self):
        a, b = self.class_a.currentData(), self.class_b.currentData()
        return D.Recipe(classes=(a, b), missing=self.missing.currentData(), text=self.text.currentData(),
                        per_class=self.per_class.value(), components=self.components.value(),
                        scale='pi' if self.scale.isChecked() else 'none', test_fraction=self.test_fraction.value())

    def prepare(self):
        recipe = self.current_recipe()
        if recipe.classes[0] == recipe.classes[1]:
            self.steps.setText('Choose two different classes.')
            return None
        try:
            prepared = D.prepare(self.dataset, recipe)
        except (ValueError, np.linalg.LinAlgError) as exc:
            self.steps.setText(f'Could not prepare the data: {exc}')
            return None
        if prepared.X_train.shape[1] > D.MAX_QUBITS:
            self.steps.setText(f'{prepared.X_train.shape[1]} features remain; reduce them to at most '
                               f'{D.MAX_QUBITS} (PCA components) to use them on qubits.')
        else:
            self.steps.setText('Prepared: ' + ' '.join(prepared.steps) + '  Both classifiers can now use it.')
            STORE.publish(self.dataset, recipe, prepared)
            from quantumscope.ml import progress
            progress.prepared(self.source_key, prepared.X_train.shape[1], prepared.classes)
        self.plot.clear()
        if prepared.X_train.shape[1] >= 2:
            _scatter_points(self.plot, prepared.X_train[:, :2], prepared.y_train)
            self.plot.setLabel('bottom', prepared.features[0])
            self.plot.setLabel('left', prepared.features[1])
        self.images.show_images(self.dataset, recipe.classes)
        return prepared


# ============================================================================================
class _DataPicker(QGroupBox):
    """Which data a classifier trains on: from the Datasets tab, or a dataset with its suggested recipe."""

    def __init__(self, max_samples, parent=None):
        super().__init__('Data', parent)
        self.max_samples = max_samples
        form = QFormLayout(self)
        self.source = QComboBox()
        self.source.addItem('From the Datasets tab', 'store')
        self.source.insertSeparator(1)
        quick = _source_combo()
        for i in range(quick.count()):
            if quick.itemData(i):
                self.source.addItem(quick.itemText(i), quick.itemData(i))
        self.source.setCurrentIndex(self.source.findData('circles'))
        form.addRow('Dataset', self.source)
        self.qubits = QSpinBox()
        self.qubits.setRange(1, D.MAX_QUBITS)
        self.qubits.setValue(2)
        self.qubits.setToolTip('One feature per qubit: the data is reduced to this many features')
        form.addRow('Qubits (= features)', self.qubits)
        self.class_a, self.class_b = QComboBox(), QComboBox()          # for datasets with more than two classes
        self.class_row = QWidget()
        pair = QHBoxLayout(self.class_row)
        pair.setContentsMargins(0, 0, 0, 0)
        pair.addWidget(self.class_a)
        pair.addWidget(QLabel('vs'))
        pair.addWidget(self.class_b)
        self.class_label = QLabel('Classes')
        form.addRow(self.class_label, self.class_row)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.summary.setObjectName('muted')
        form.addRow(self.summary)
        self.source.currentIndexChanged.connect(self._classes_for_source)
        self.source.currentIndexChanged.connect(self._sync)
        STORE.changed.connect(self._sync)
        self._classes_for_source()
        self._sync()

    def _classes_for_source(self, *_):
        """Offer the dataset's classes when it has more than two (MNIST, Iris, …), defaulting to the
        checker's suggestion; hidden for two-class data and for the Datasets tab's data."""
        key = self.source.currentData()
        dataset = None if key in (None, 'store') else D.load(key)
        many = dataset is not None and len(dataset.classes) > 2
        self.class_row.setVisible(many)
        self.class_label.setVisible(many)
        if not many:
            return
        suggested = D.check(dataset, qubits=self.qubits.value(), max_samples=self.max_samples)[2].classes
        for box, default in ((self.class_a, suggested[0]), (self.class_b, suggested[1])):
            box.blockSignals(True)
            box.clear()
            for k, name in enumerate(dataset.classes):
                box.addItem(name, k)
            box.setCurrentIndex(box.findData(default))
            box.blockSignals(False)

    def _sync(self, *_):
        """From the Datasets tab, the qubit count is the prepared data's: shown, not editable here."""
        from_store = self.source.currentData() == 'store'
        self.qubits.setEnabled(not from_store)
        if from_store:
            if STORE.prepared is not None:
                self.qubits.blockSignals(True)
                self.qubits.setValue(STORE.prepared.X_train.shape[1])
                self.qubits.blockSignals(False)
                self.qubits.setToolTip('Set in the Datasets tab (one feature per qubit)')
                self.summary.setText(f'Prepared in the Datasets tab: {STORE.prepared.X_train.shape[1]} features '
                                     f'on as many qubits.')
            else:
                self.summary.setText('Nothing prepared yet: open the Datasets experiment and press Prepare.')
        else:
            self.qubits.setToolTip('One feature per qubit: the data is reduced to this many features')

    def key(self):
        """The dataset trained on: a built-in or synthetic key, or what the Datasets tab prepared."""
        key = self.source.currentData()
        if key == 'store':
            from quantumscope.ml import progress
            return progress.STATE.get('dataset')
        return key

    def prepared(self):
        key = self.source.currentData()
        if key == 'store':
            if STORE.prepared is None:
                self.summary.setText('Nothing prepared yet: open the Datasets experiment and press Prepare.')
                return None
            p = STORE.prepared
        else:
            dataset = D.load(key)
            verdict, _, recipe = D.check(dataset, qubits=self.qubits.value(), max_samples=self.max_samples)
            if verdict == 'stop':
                self.summary.setText('This dataset cannot be used.')
                return None
            if self.class_row.isVisible() or len(dataset.classes) > 2:
                a, b = self.class_a.currentData(), self.class_b.currentData()
                if a is not None and b is not None:
                    if a == b:
                        self.summary.setText('Choose two different classes.')
                        return None
                    recipe.classes = (a, b)
            p = D.prepare(dataset, recipe)
        self.summary.setText(f'{p.classes[0]} (+1) vs {p.classes[1]} (−1): {len(p.y_train)} for training, '
                             f'{len(p.y_test)} for testing, {p.X_train.shape[1]} features on {p.X_train.shape[1]} qubits.')
        return p


def _regions(plot, decision, X_train, y_train, X_test=None, y_test=None, predicted=None):
    """Decision regions for any number of features. With two features the plane is the data's own;
    with more, it is the plane of the two leading principal components of the training data (a
    slice through the n-dimensional feature space: each grid point is mapped back into it)."""
    import pyqtgraph as pg
    plot.clear()
    n = X_train.shape[1]
    if n == 1:                                                   # one feature: a line, shown flat
        to_plane = lambda X: np.c_[X[:, 0], np.zeros(len(X))]       # noqa: E731
        from_plane = lambda P: P[:, :1]                              # noqa: E731
        labels = ('feature 1', '')
    elif n == 2:
        to_plane = from_plane = lambda X: X                          # noqa: E731
        labels = ('feature 1', 'feature 2')
    else:
        mean = X_train.mean(axis=0)
        _, _, vt = np.linalg.svd(X_train - mean, full_matrices=False)
        basis = vt[:2]
        to_plane = lambda X: (X - mean) @ basis.T                    # noqa: E731
        from_plane = lambda P: mean + P @ basis                      # noqa: E731
        labels = ('principal component 1', 'principal component 2')
    plot.setLabel('bottom', labels[0])
    plot.setLabel('left', labels[1])
    plot.setTitle('Decision regions' + ('' if n <= 2 else f' in the plane of the first two principal components '
                                          f'(a slice through {n}-D)') + ': training ●, test ▲, mistakes ✕')
    P_train = to_plane(X_train)
    P_all = P_train if X_test is None or not len(X_test) else np.r_[P_train, to_plane(X_test)]
    lo, hi = P_all.min(axis=0), P_all.max(axis=0)
    pad = 0.08 * np.maximum(hi - lo, 1e-6)
    lo, hi = lo - pad, hi + pad
    if n == 1:
        lo[1], hi[1] = -1.0, 1.0
    if decision is not None:
        res = 90 if n <= 4 else 70 if n <= 6 else 50             # 2ⁿ amplitudes per grid point
        gx, gy = np.linspace(lo[0], hi[0], res), np.linspace(lo[1], hi[1], res)
        grid = np.array([(a, b) for b in gy for a in gx])
        values = np.concatenate([decision(from_plane(chunk)) for chunk in np.array_split(grid, max(1, len(grid) // 1500))])
        f = values.reshape(res, res)                             # rows: y, columns: x
        scale = max(1e-9, float(np.percentile(np.abs(f), 95)))
        strength = np.clip(np.abs(f) / scale, 0, 1)
        plus, minus = np.array((90, 230, 255), float), np.array((255, 154, 90), float)
        base = np.where((f >= 0)[..., None], plus, minus)
        rgba = np.empty((res, res, 4), np.uint8)
        rgba[..., :3] = base.astype(np.uint8)
        rgba[..., 3] = (30 + 110 * strength).astype(np.uint8)     # confidence: deeper colour
        image = pg.ImageItem(np.transpose(rgba, (1, 0, 2)))       # ImageItem wants (x, y)
        image.setRect(QRectF(lo[0], lo[1], hi[0] - lo[0], hi[1] - lo[1]))
        plot.addItem(image)
        boundary = pg.IsocurveItem(f.T, level=0.0, pen=pg.mkPen('#ffffff', width=2))
        boundary.setParentItem(image)                             # follows the image's placement
        image.setZValue(-10)
    _scatter_points(plot, P_train, y_train, size=7)
    if X_test is not None and len(X_test):
        P_test = to_plane(X_test)
        wrong = predicted != y_test
        _scatter_points(plot, P_test[~wrong], y_test[~wrong], size=11, symbol='t', outline='#ffffff')
        if wrong.any():
            plot.addItem(pg.ScatterPlotItem(P_test[wrong, 0], P_test[wrong, 1], size=14, symbol='x',
                                            brush=pg.mkBrush('#ff4d4d'), pen=pg.mkPen('#ff4d4d', width=2)))
    plot.disableAutoRange()
    plot.setRange(xRange=(lo[0], hi[0]), yRange=(lo[1], hi[1]), padding=0)


# ============================================================================================
class KernelExperiment(QWidget):
    """A quantum kernel and a classical classifier on top of it."""

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QHBoxLayout(self)
        left = QWidget()
        left.setMaximumWidth(380)
        form = QVBoxLayout(left)
        title = QLabel('QUANTUM KERNEL CLASSIFIER  ·  compare data points as quantum states')
        title.setStyleSheet('font-weight:700;')
        title.setWordWrap(True)
        form.addWidget(title)
        self.data = _DataPicker(max_samples=200)
        form.addWidget(self.data)
        model = QGroupBox('Kernel and classifier')
        mv = QFormLayout(model)
        self.feature_map = QComboBox()
        for key, label in K.FEATURE_MAPS.items():
            self.feature_map.addItem(label, key)
        mv.addRow('Feature map', self.feature_map)
        self.reps = QSpinBox()
        self.reps.setRange(1, 4)
        self.reps.setValue(2)
        mv.addRow('Repetitions (ZZ)', self.reps)
        self.bandwidth = QDoubleSpinBox()
        self.bandwidth.setRange(0.05, 2.0)
        self.bandwidth.setSingleStep(0.05)
        self.bandwidth.setValue(1.0)
        self.bandwidth.setToolTip('Scales the data before encoding: smaller is smoother')
        mv.addRow('Bandwidth', self.bandwidth)
        self.shots = QSpinBox()
        self.shots.setRange(0, 100000)
        self.shots.setSingleStep(100)
        self.shots.setSpecialValueText('exact')
        self.shots.setToolTip('Estimate each kernel entry from this many shots, as a quantum computer would')
        mv.addRow('Shots per entry', self.shots)
        self.method = QComboBox()
        self.method.addItem('Support vector machine', 'svm')
        self.method.addItem('Kernel ridge', 'ridge')
        mv.addRow('Classifier', self.method)
        self.strength = QDoubleSpinBox()
        self.strength.setRange(0.001, 100.0)
        self.strength.setDecimals(3)
        self.strength.setValue(1.0)
        self.strength.setToolTip('SVM: C (larger fits the training data harder). Ridge: λ (larger is smoother)')
        mv.addRow('C or λ', self.strength)
        self.train_button = QPushButton('Train')
        mv.addRow(self.train_button)
        form.addWidget(model)
        self.result = QLabel('Press Train.')
        self.result.setWordWrap(True)
        form.addWidget(self.result)
        form.addStretch()
        root.addWidget(left)
        right = QVBoxLayout()
        self.regions = _plot('Decision regions')
        right.addWidget(self.regions, 3)
        self.heatmap = _plot('Training kernel K(x, x′), sorted by class (dashed: where the classes meet)')
        right.addWidget(self.heatmap, 2)
        root.addLayout(right, 1)
        self.train_button.clicked.connect(self.train)

    def train(self):
        import pyqtgraph as pg
        p = self.data.prepared()
        if p is None:
            return None
        if p.X_train.shape[1] > D.MAX_QUBITS:
            self.result.setText('Too many features for the qubits: reduce them in the Datasets tab.')
            return None
        kind, reps, bandwidth = self.feature_map.currentData(), self.reps.value(), self.bandwidth.value()
        rng = np.random.default_rng(0)
        exact_train = K.kernel(p.X_train, kind=kind, reps=reps, bandwidth=bandwidth)
        Ktr = K.estimate(exact_train, self.shots.value(), rng, symmetric=True)
        Kte = K.estimate(K.kernel(p.X_test, p.X_train, kind=kind, reps=reps, bandwidth=bandwidth), self.shots.value(), rng)
        if self.method.currentData() == 'svm':
            model = K.SVM(C=self.strength.value()).fit(Ktr, p.y_train)
            extra = f', {len(model.support)} support vectors'
        else:
            model = K.KernelRidge(self.strength.value()).fit(Ktr, p.y_train)
            extra = ''
        train_acc = K.accuracy(p.y_train, model.predict(Ktr))
        predicted = model.predict(Kte)
        test_acc = K.accuracy(p.y_test, predicted)
        noise = '' if not self.shots.value() else f' Kernel estimated from {self.shots.value()} shots per entry ' \
            f'(typical error {float(np.abs(Ktr - exact_train).mean()):.3f}).'
        off = float((exact_train.sum() - len(exact_train)) / max(1, len(exact_train) * (len(exact_train) - 1)))
        hint = '' if off >= 0.05 else (f' The kernel is close to 0 for different points (average {off:.3f}): '
                                       f'kernel concentration, common for entangling maps on many qubits. '
                                       f'Try a smaller bandwidth.')
        self.result.setText(f'Training accuracy {train_acc:.0%}, test accuracy {test_acc:.0%}{extra}.{noise}{hint}')

        def decision(points):
            return model.decision(K.kernel(points, p.X_train, kind=kind, reps=reps, bandwidth=bandwidth))
        _regions(self.regions, decision, p.X_train, p.y_train, p.X_test, p.y_test, predicted)
        order = np.argsort(-p.y_train, kind='stable')
        self.heatmap.clear()
        image = pg.ImageItem(Ktr[np.ix_(order, order)])
        image.setLookupTable(pg.colormap.get('viridis').getLookupTable(0, 1, 256))
        image.setLevels((0, 1))
        self.heatmap.addItem(image)
        size = len(order)
        self.heatmap.setAspectLocked(False)                      # fill the panel
        self.heatmap.disableAutoRange()
        self.heatmap.setRange(xRange=(0, size), yRange=(0, size), padding=0)
        split = int((p.y_train == 1).sum())                      # the class border, as thin lines
        for line in (pg.InfiniteLine(split, angle=90, pen=pg.mkPen('#ffffff', width=1, style=Qt.PenStyle.DashLine)),
                     pg.InfiniteLine(split, angle=0, pen=pg.mkPen('#ffffff', width=1, style=Qt.PenStyle.DashLine))):
            line.setZValue(10)                                   # above the image
            self.heatmap.addItem(line)
        self.last = dict(train=train_acc, test=test_acc, model=model, prepared=p)
        from quantumscope.ml import progress
        progress.trained('kernel', train=train_acc, test=test_acc, map=kind, bandwidth=bandwidth,
                         shots=self.shots.value(), dataset=self.data.key())
        return self.last


# ============================================================================================
class VariationalExperiment(QWidget):
    """A trainable quantum circuit as a classifier, trained live."""

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QHBoxLayout(self)
        left = QWidget()
        left.setMaximumWidth(380)
        form = QVBoxLayout(left)
        title = QLabel('VARIATIONAL CLASSIFIER  ·  train a quantum circuit to separate the classes')
        title.setStyleSheet('font-weight:700;')
        title.setWordWrap(True)
        form.addWidget(title)
        self.data = _DataPicker(max_samples=300)
        form.addWidget(self.data)
        model = QGroupBox('Circuit and training')
        mv = QFormLayout(model)
        self.feature_map = QComboBox()
        for key, label in K.FEATURE_MAPS.items():
            self.feature_map.addItem(label, key)
        mv.addRow('Feature map', self.feature_map)
        self.layers = QSpinBox()
        self.layers.setRange(1, 8)
        self.layers.setValue(3)
        mv.addRow('Trainable layers', self.layers)
        self.method = QComboBox()
        self.method.addItem('BFGS (parameter-shift gradients)', 'BFGS')
        self.method.addItem('Adam (steady steps)', 'Adam')
        mv.addRow('Optimizer', self.method)
        self.steps = QSpinBox()
        self.steps.setRange(5, 1000)
        self.steps.setValue(80)
        mv.addRow('Steps', self.steps)
        self.seed = QSpinBox()
        self.seed.setRange(0, 9999)
        mv.addRow('Starting point (seed)', self.seed)
        buttons = QHBoxLayout()
        self.train_button, self.stop_button = QPushButton('Train'), QPushButton('Stop')
        self.stop_button.setEnabled(False)
        buttons.addWidget(self.train_button)
        buttons.addWidget(self.stop_button)
        mv.addRow(buttons)
        self.open_circuit = QPushButton('Open in circuit simulator')
        self.open_circuit.setToolTip('The trained circuit for the first test point, with the observable Z0')
        self.open_circuit.setEnabled(False)
        mv.addRow(self.open_circuit)
        form.addWidget(model)
        self.result = QLabel('Press Train.')
        self.result.setWordWrap(True)
        form.addWidget(self.result)
        form.addStretch()
        root.addWidget(left)
        right = QVBoxLayout()
        self.regions = _plot('Decision regions')
        right.addWidget(self.regions, 3)
        self.curve = _plot('Training', 'step', 'loss / accuracy')
        self.curve.addLegend(offset=(8, 4))
        self.loss_line = self.curve.plot(pen='#5ae6ff', name='loss')
        self.acc_line = self.curve.plot(pen='#5ad48a', name='training accuracy')
        right.addWidget(self.curve, 2)
        root.addLayout(right, 1)
        self.model = None
        self._stop = False
        self.train_button.clicked.connect(self.train)
        self.stop_button.clicked.connect(lambda: setattr(self, '_stop', True))
        self.open_circuit.clicked.connect(self.open_in_circuit)

    def train(self):
        p = self.data.prepared()
        if p is None:
            return None
        if p.X_train.shape[1] > D.MAX_QUBITS:
            self.result.setText('Too many features for the qubits: reduce them in the Datasets tab.')
            return None
        self.prepared = p
        self.model = V.Classifier(p.X_train.shape[1], layers=self.layers.value(),
                                  feature_map=self.feature_map.currentData(), seed=self.seed.value())
        losses, accuracies = [], []
        self._stop = False
        self.train_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        def step(index, loss, accuracy):
            losses.append(loss)
            accuracies.append(accuracy)
            self.loss_line.setData(list(range(len(losses))), losses)
            self.acc_line.setData(list(range(len(accuracies))), accuracies)
            self.result.setText(f'Step {index}: loss {loss:.4f}, training accuracy {accuracy:.0%}')
            if index % 5 == 0:
                self._draw()
            QApplication.processEvents()
            return not self._stop
        try:
            self.model.train(p.X_train, p.y_train, method=self.method.currentData(), steps=self.steps.value(),
                             callback=step)
        finally:
            self.train_button.setEnabled(True)
            self.stop_button.setEnabled(False)
        test_acc = float(np.mean(self.model.predict(p.X_test) == p.y_test))
        self.result.setText(f'{"Stopped" if self._stop else "Done"} after {len(losses) - 1} steps: training accuracy '
                            f'{accuracies[-1]:.0%}, test accuracy {test_acc:.0%}, final loss {losses[-1]:.4f}.')
        self._draw()
        self.open_circuit.setEnabled(True)
        self.last = dict(train=accuracies[-1], test=test_acc, history=list(zip(losses, accuracies)))
        from quantumscope.ml import progress
        progress.trained('variational', train=accuracies[-1], test=test_acc, map=self.feature_map.currentData(),
                         layers=self.layers.value(), dataset=self.data.key())
        return self.last

    def _draw(self):
        p, model = self.prepared, self.model
        _regions(self.regions, model.decision, p.X_train, p.y_train, p.X_test, p.y_test, model.predict(p.X_test))

    def open_in_circuit(self):
        """Load the trained circuit for the first test point into the circuit simulator."""
        if self.model is None:
            return None
        window = self.window()
        workspace = getattr(window, 'circuit_widget', None)
        if workspace is None:
            return None
        x = self.prepared.X_test[0]
        workspace.set_circuit(self.model.qubits, self.model.gates(x))
        workspace.model.set_observable('Z0')
        workspace._changed()
        launch = getattr(window, '_launch_circuits', None)
        if callable(launch):
            launch()
        return x
