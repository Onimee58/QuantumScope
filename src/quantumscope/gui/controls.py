"""Small reusable controls for experiment panels."""
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QToolButton, QWidget


def with_quick_values(field, values, tooltip_prefix='Set to'):
    """Return a row with `field` followed by one small button per (label, value).

    Clicking a button sets the field to that value, e.g. ('Max', field.maximum()).
    The field stops reacting to every keystroke (keyboard tracking off), so
    typing a number triggers one update when you finish rather than several.
    """
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    field.setKeyboardTracking(False)
    field.setMinimumWidth(112)
    layout.addWidget(field, 1)
    row.quick_buttons = {}
    for label, value in values:
        button = QToolButton()
        button.setObjectName('quickValue')
        button.setText(label)
        button.setToolTip(f'{tooltip_prefix} {value:g}{field.suffix()}')
        button.clicked.connect(lambda _=False, v=value: field.setValue(v))
        layout.addWidget(button)
        row.quick_buttons[label] = button
    return row


def with_action(field, label, action, tooltip):
    """Return a row with `field` and one action button (e.g. 'Fit to states')."""
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    field.setKeyboardTracking(False)
    field.setMinimumWidth(112)
    layout.addWidget(field, 1)
    button = QToolButton()
    button.setObjectName('quickValue')
    button.setText(label)
    button.setToolTip(tooltip)
    button.clicked.connect(lambda _=False: action())
    layout.addWidget(button)
    row.action_button = button
    return row


class Debouncer:
    """Run `callback` once, `delay_ms` after the last request (coalesces bursts)."""

    def __init__(self, parent, callback, delay_ms=180):
        self.timer = QTimer(parent)
        self.timer.setSingleShot(True)
        self.timer.setInterval(delay_ms)
        self.timer.timeout.connect(callback)

    def __call__(self, *_):
        self.timer.start()

    def flush(self):
        if self.timer.isActive():
            self.timer.stop()
            self.timer.timeout.emit()
