"""Interactive ideal-qubit superposition and spin-singlet experiments.

The electrons are pedagogical symbols; their motion is schematic. Entanglement
is a correlation between joint quantum states, not a visible physical thread.
"""
import math
import numpy as np
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QDoubleSpinBox, QSpinBox, QGroupBox, QSplitter, QSlider, QComboBox)
from quantumscope.physics.qubits import (qubit_state, spin_probabilities,
    singlet_joint_probabilities, singlet_correlation, chsh_value,
    prepare_gate_pair, pair_concurrence, pair_joint_probabilities, local_measure_pair)


class SuperpositionDialog(QWidget):
    """Prepare a spin-½ state (drag the arrow, or use the sliders and presets), turn the measurement
    axis, and watch single collapses and the Born-rule statistics build up (v0.7.4 redesign)."""

    PRESETS = (('|0⟩', 0, 0), ('|1⟩', 180, 0), ('|+⟩', 90, 0), ('|−⟩', 90, 180), ('|+i⟩', 90, 90), ('|−i⟩', 90, 270))
    SPEEDS = (('Slow', 2, 60), ('Fast', 25, 30), ('Instant', 0, 0))   # (label, per tick, ms per tick)

    def __init__(self,parent=None):
        super().__init__(parent)
        from quantumscope.gui.principles_visuals import BlochView, TallyBars
        root=QHBoxLayout(self)
        left=QWidget();left.setMaximumWidth(360);form=QVBoxLayout(left);form.setSpacing(8)
        title=QLabel('QUANTUM SUPERPOSITION');title.setStyleSheet('font-weight:700; letter-spacing:1px;')
        form.addWidget(title)
        hint=QLabel('Drag the arrow to prepare a state, turn the amber axis, then measure.')
        hint.setWordWrap(True);hint.setObjectName('muted');form.addWidget(hint)
        prepare=QGroupBox('Prepare');pv=QFormLayout(prepare)
        self.theta=self._angle(90,0,180);self.phi=self._angle(0,0,360)
        pv.addRow('θ',self._slider_control(self.theta));pv.addRow('φ',self._slider_control(self.phi))
        presets=QHBoxLayout();presets.setSpacing(4)
        for label,theta,phi in self.PRESETS:
            button=QPushButton(label);button.setFixedWidth(46)
            button.clicked.connect(lambda _=False,t=theta,f=phi:self._preset(t,f));presets.addWidget(button)
        pv.addRow(presets)
        form.addWidget(prepare)
        measure=QGroupBox('Measure');mv=QFormLayout(measure)
        self.axis=self._angle(0,-180,180);mv.addRow('Axis',self._slider_control(self.axis))
        self.measure=QPushButton('Measure once');self.measure.setToolTip('One measurement: the state collapses to +1 or −1')
        mv.addRow(self.measure)
        many=QHBoxLayout()
        self.hits=QSpinBox();self.hits.setRange(10,10000);self.hits.setValue(500);many.addWidget(self.hits)
        self.speed=QComboBox()
        for label,_,_ in self.SPEEDS:self.speed.addItem(label)
        self.speed.setCurrentIndex(1);many.addWidget(self.speed)
        mv.addRow('Many',many)
        buttons=QHBoxLayout()
        self.sample=QPushButton('Measure many');self.sample.setToolTip('Fresh preparations, measured one after another')
        self.stop_button=QPushButton('Stop');self.stop_button.setEnabled(False)
        buttons.addWidget(self.sample);buttons.addWidget(self.stop_button);mv.addRow(buttons)
        self.prepare=QPushButton('Reset state');self.prepare.setToolTip('Return to the prepared state after a collapse')
        mv.addRow(self.prepare)
        form.addWidget(measure)
        self.result=QLabel('Ready.');self.result.setWordWrap(True);form.addWidget(self.result)
        form.addStretch()
        root.addWidget(left)
        right=QVBoxLayout()
        self.view=BlochView();right.addWidget(self.view,3)
        self.prob=QLabel();self.prob.setAlignment(Qt.AlignmentFlag.AlignCenter);right.addWidget(self.prob)
        self.tally=TallyBars(['+1 ↑','−1 ↓']);right.addWidget(self.tally,1)
        root.addLayout(right,1)
        self.scene=self.view                      # older name
        self.prepared=qubit_state()
        self._pending=0
        self._timer=QTimer(self);self._timer.timeout.connect(self._stream)
        self.view.stateChanged.connect(self._dragged)
        for spin in (self.theta,self.phi):spin.valueChanged.connect(self._prepare)
        self.axis.valueChanged.connect(self._axis_changed)
        self.measure.clicked.connect(self._measure)
        self.sample.clicked.connect(self._sample)
        self.stop_button.clicked.connect(self._stop)
        self.prepare.clicked.connect(self._prepare)
        self._prepare()

    @staticmethod
    def _angle(val,low,high):
        s=QDoubleSpinBox();s.setRange(low,high);s.setSuffix('°');s.setValue(val)
        s.setDecimals(1);return s

    @staticmethod
    def _slider_control(spin):
        container=QWidget();row=QHBoxLayout(container)
        row.setContentsMargins(0,0,0,0);row.setSpacing(5)
        slider=QSlider(Qt.Orientation.Horizontal)
        slider.setRange(round(spin.minimum()*10),round(spin.maximum()*10))
        slider.setValue(round(spin.value()*10))
        slider.valueChanged.connect(lambda v:spin.setValue(v/10))
        spin.valueChanged.connect(lambda v:slider.setValue(round(v*10)))
        spin.setFixedWidth(99)
        row.addWidget(slider,1);row.addWidget(spin)
        return container

    def _preset(self,theta,phi):
        for spin,value in ((self.theta,theta),(self.phi,phi)):
            spin.blockSignals(True);spin.setValue(value);spin.blockSignals(False)
        self._prepare(animate=True)

    def _dragged(self,theta,phi):
        for spin,value in ((self.theta,theta),(self.phi,phi % 360)):
            spin.blockSignals(True);spin.setValue(value);spin.blockSignals(False)
        self._prepare(from_drag=True)

    def _prepare(self,*_,animate=False,from_drag=False):
        self._stop()
        self.prepared=qubit_state(self.theta.value(),self.phi.value())
        if not from_drag:
            self.view.set_state(self.theta.value(),self.phi.value(),animate=animate)
        self.tally.reset()
        self.result.setText('Prepared |ψ⟩. Measure it once, or many fresh copies.')
        self._update()

    def _axis_changed(self,*_):
        self._stop()
        self.view.axis=self.axis.value();self.view.update()
        self.tally.reset()
        self._update()

    def _update(self,*_):
        probabilities=spin_probabilities(qubit_state(self.theta.value(),self.phi.value()),self.axis.value())
        self.prob.setText(f'Born rule along the axis:  +1 with {probabilities[0]:.1%},  −1 with {probabilities[1]:.1%}')
        self.tally.set_expected(probabilities)

    def _measure(self):
        """One measurement of the current state: animate the collapse and count it."""
        self._stop()
        probs=spin_probabilities(self.prepared,self.axis.value())
        choice=int(np.random.default_rng().choice(2,p=probs))
        self.prepared=qubit_state(self.axis.value()) if choice==0 else qubit_state(self.axis.value()+180)
        aa,bb=self.prepared
        theta=math.degrees(math.acos(max(-1.,min(1.,float(abs(aa)**2-abs(bb)**2)))))
        phi=math.degrees(np.angle(np.conj(aa)*bb))
        self.view.set_state(theta,phi,animate=True,flash=True)
        self.tally.add(choice)
        self.result.setText(('Measured +1 ↑' if choice==0 else 'Measured −1 ↓')+': the state collapsed onto that '
                            'direction. Measuring again along this axis repeats it; Reset state to start over.')

    def _sample(self):
        """Measure many fresh preparations, streamed into the tally at the chosen speed."""
        self._stop()
        self.prepared=qubit_state(self.theta.value(),self.phi.value())
        self.view.set_state(self.theta.value(),self.phi.value(),animate=True)
        self.tally.reset()
        _,per_tick,interval=self.SPEEDS[self.speed.currentIndex()]
        if per_tick==0:
            self._pending=self.hits.value();self._stream(all_at_once=True)
            return
        self._pending=self.hits.value()
        self._timer.start(interval)
        self.stop_button.setEnabled(True)
        self.result.setText('Measuring fresh copies of |ψ⟩…')

    def _stream(self,all_at_once=False):
        _,per_tick,_=self.SPEEDS[self.speed.currentIndex()]
        batch=self._pending if all_at_once or per_tick==0 else min(per_tick,self._pending)
        probs=spin_probabilities(self.prepared,self.axis.value())
        data=np.random.default_rng().choice(2,size=batch,p=probs)
        ups=int(np.count_nonzero(data==0))
        self.tally.add(0,ups);self.tally.add(1,batch-ups)
        self._pending-=batch
        if self._pending<=0:
            self._stop()
            counts=self.tally.counts
            self.result.setText(f'{sum(counts)} fresh copies: +1 {counts[0]} times, −1 {counts[1]} times. '
                                'Each result was random; together they follow the Born rule (dashed lines).')

    def _stop(self):
        if hasattr(self,'_timer') and self._timer.isActive():self._timer.stop()
        if hasattr(self,'stop_button'):self.stop_button.setEnabled(False)
