"""A small form built from algorithm/block parameter descriptions (physics.algorithms.Param)."""
from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit, QSpinBox,
                               QVBoxLayout)

from quantumscope.physics.algorithms import validate_params


class ParameterDialog(QDialog):
    def __init__(self, title, params, values, parent=None, description='', locked=()):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.params = params
        self.fields = {}
        layout = QVBoxLayout(self)
        if description:
            text = QLabel(description)
            text.setWordWrap(True)
            layout.addWidget(text)
        form = QFormLayout()
        layout.addLayout(form)
        for p in params:
            value = values.get(p.key, p.default)
            if p.kind == 'int':
                field = QSpinBox()
                field.setRange(p.minimum, p.maximum)
                if p.minimum == -1:
                    field.setSpecialValueText('Optimal')   # −1 means "choose the best value"
                field.setValue(int(value))
                field.valueChanged.connect(self._resize_bits)
            elif p.kind == 'choice':
                field = QComboBox()
                for label, v in p.choices:
                    field.addItem(label, v)
                field.setCurrentIndex(max(0, [c[1] for c in p.choices].index(value) if value in [c[1] for c in p.choices] else 0))
            else:
                field = QLineEdit(str(value))
                field.setValidator(QRegularExpressionValidator(QRegularExpression('[01]{0,10}'), field))
                field.setToolTip('Bits of 0 and 1, q0 first')
            field.setEnabled(p.key not in locked)
            if p.help:
                field.setToolTip(p.help)
            form.addRow(p.label, field)
            self.fields[p.key] = field
        self.error = QLabel('')
        self.error.setWordWrap(True)
        layout.addWidget(self.error)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _resize_bits(self, *_):
        """Keep bit-string fields as long as the qubit count they depend on."""
        for p in self.params:
            if p.kind == 'bits' and p.length_of in self.fields:
                length = self.fields[p.length_of].value()
                field = self.fields[p.key]
                text = field.text()
                field.setText((text + '0' * length)[:length] if len(text) < length else text[:length])

    def values(self):
        out = {}
        for p in self.params:
            field = self.fields[p.key]
            if p.kind == 'int':
                out[p.key] = field.value()
            elif p.kind == 'choice':
                out[p.key] = field.currentData()
            else:
                out[p.key] = field.text()
        return out

    def _accept(self):
        try:
            validate_params(self.params, self.values())
        except ValueError as exc:
            self.error.setText('⚠ ' + str(exc))
            return
        self.accept()
