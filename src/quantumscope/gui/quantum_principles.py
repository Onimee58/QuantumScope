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


class SpinScene(QWidget):
    """Interactive, orthographically projected Bloch sphere and clickable pair schematic."""
    electron_clicked = Signal(str)

    def __init__(self, mode='superposition', parent=None):
        super().__init__(parent)
        self.mode = mode
        self.setMinimumSize(420, 260)
        self.theta, self.phi = 90., 0.
        self.camera_yaw, self.camera_pitch = -32., 19.
        self._drag_pos = None
        self.progress = 0.
        self.alice = None
        self.bob = None
        self.setMouseTracking(True)
        self.setToolTip('Drag to rotate the Bloch sphere' if mode == 'superposition' else '')

    def _project(self, xyz, cx=350, cy=170, radius=121):
        x,y,z = xyz
        a=math.radians(self.camera_yaw); b=math.radians(self.camera_pitch)
        u=math.cos(a)*x + math.sin(a)*y
        depth=-math.sin(a)*x + math.cos(a)*y
        v=math.sin(b)*depth + math.cos(b)*z
        away=math.cos(b)*depth-math.sin(b)*z
        return QPointF(cx+radius*u, cy-radius*v), away

    def paintEvent(self, event):
        p=QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor('#101923'))
        # Preserve geometry and font aspect ratio at any window dimensions.
        # Center a uniform design canvas rather than stretching X and Y independently.
        factor = min(self.width()/700, self.height()/340)
        p.translate((self.width()-700*factor)/2, (self.height()-340*factor)/2)
        p.scale(factor, factor)
        p.setPen(QPen(QColor('#30495d'),1))
        p.drawRoundedRect(QRectF(5,5,690,330),10,10)
        if self.mode == 'superposition': self._draw_bloch(p)
        else: self._draw_pair(p)
        p.end()

    def _text(self,p,x,y,w,h,text,size=12,color='#cde2f2',align=Qt.AlignmentFlag.AlignCenter):
        p.setPen(QColor(color));p.setFont(QFont('Sans Serif',size))
        p.drawText(QRectF(x,y,w,h),align,text)

    def _draw_bloch(self,p):
        center=QPointF(350,170)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor('#55788d'),2))
        p.drawEllipse(center,121,121)
        # Orthographic projections of three orthogonal great circles.
        for plane, color in (('xy','#54899d'),('xz','#496f88'),('yz','#496f88')):
            coords=[]
            for k in range(145):
                t=2*math.pi*k/144
                v={'xy':(math.cos(t),math.sin(t),0),
                   'xz':(math.cos(t),0,math.sin(t)),
                   'yz':(0,math.cos(t),math.sin(t))}[plane]
                coords.append((self._project(v)[0],self._project(v)[1]))
            for i in range(144):
                if coords[i][1]+coords[i+1][1]<0:
                    p.setPen(QPen(QColor('#355369'),1,Qt.PenStyle.DashLine))
                else:
                    p.setPen(QPen(QColor(color),1.5))
                p.drawLine(coords[i][0],coords[i+1][0])
        for vec, label in (((0,0,1),'+z'),((0,0,-1),'−z'),((1,0,0),'+x'),((0,1,0),'+y')):
            pt,_=self._project(tuple(t*1.16 for t in vec))
            p.setPen(QPen(QColor('#6b8da3'),1,Qt.PenStyle.DashLine))
            p.drawLine(center,pt)
            self._text(p,pt.x()-19,pt.y()-13,38,26,label,11)
        th,ph=math.radians(self.theta),math.radians(self.phi)
        vector=(math.sin(th)*math.cos(ph),math.sin(th)*math.sin(ph),math.cos(th))
        endpoint,_=self._project(vector)
        p.setPen(QPen(QColor('#5cdece'),5));p.drawLine(center,endpoint)
        p.setBrush(QColor('#5cdece'));p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(endpoint,7,7)
        self._text(p,14,20,220,30,'3D Bloch sphere',16)
        self._text(p,18,58,218,75,'|ψ⟩ = cos(θ/2)|↑⟩ +\neⁱᵠ sin(θ/2)|↓⟩',13)
        self._text(p,481,54,200,75,'Drag sphere to rotate\nθ and φ set the state',12)
        self._text(p,20,288,660,29,'3D projection of a qubit state; spin is not classical rotation',10,'#9db2c3')

    def _draw_pair(self,p):
        # Three distinct scene stages. Input positions remain stable when angles change.
        stage=getattr(self,'stage','input')
        t=max(0.,min(1.,self.progress))
        inp_a,inp_b=(145.,245.)
        box_l,box_r=285.,415.
        if stage=='input':
            x1,x2=inp_a,inp_b
        elif stage=='intake':
            x1=inp_a+(310.-inp_a)*t
            x2=inp_b+(390.-inp_b)*t
        elif stage=='output':
            x1=310.-185.*t
            x2=390.+185.*t
        else:
            x1,x2=125.,575.
        p.setPen(QPen(QColor('#3b5a71'),1,Qt.PenStyle.DashLine))
        p.drawLine(QPointF(75,167),QPointF(625,167))
        if stage in ('input','intake'):
            p.setPen(QPen(QColor('#56cdd8'),2));p.setBrush(QColor('#152d3c'))
            p.drawRoundedRect(QRectF(box_l,120,box_r-box_l,95),11,11)
            self._text(p,box_l,137,box_r-box_l,28,'H(A) → CNOT',12,'#8ee3ef')
            self._text(p,box_l,169,box_r-box_l,25,'Entangle',11)
            self._text(p,15,22,670,27,'BEFORE  •  Independent electron spin states',16)
            self._text(p,28,54,644,37,'|ψ in⟩ = |ψ Alice⟩ ⊗ |ψ Bob⟩',14)
        else:
            self._text(p,15,20,670,28,'AFTER  •  Two-electron joint state',17)
            title=getattr(self,'joint_label','|Ψ out⟩ = U (|ψ A⟩ ⊗ |ψ B⟩)')
            self._text(p,25,56,650,42,title,13,'#8ee3ef')
            self._text(p,15,99,670,24,'Each electron is measured locally; correlations come from their shared state.',10,'#a0baca')
        for x, label, result in ((x1,'Alice',self.alice),(x2,'Bob',self.bob)):
            measured=result is not None
            p.setPen(QPen(QColor('#f4cb7b') if measured else QColor('#55bdcf'),3))
            p.setBrush(QColor('#465267') if measured else QColor('#27495d'))
            p.drawEllipse(QPointF(x,167),30,30)
            p.setPen(QColor('#e9f4fc'));p.setFont(QFont('Sans Serif',17))
            p.drawText(QRectF(x-24,146,48,42),Qt.AlignmentFlag.AlignCenter,'e⁻')
            self._text(p,x-63,204,126,26,label,13)
            if stage=='input':
                self._text(p,x-74,234,148,24,'|ψ'+('A' if label=='Alice' else 'B')+'⟩',12,'#9dd8ee')
            if stage=='ready':
                outcome='Ready' if result is None else ('+1 ↑' if result>0 else '−1 ↓')
                self._text(p,x-78,237,156,27,outcome,12,'#f4cb7b' if measured else '#67d9e4')
        footer=('Click an electron to measure • No physical connection or signal' if stage=='ready'
                else 'Input spin values are adjustable before running the gate sequence')
        self._text(p,15,300,670,27,footer,10,'#9db2c3')

    def mousePressEvent(self,event):
        if event.button()!=Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        pos=event.position()
        x=pos.x()*700/max(1,self.width());y=pos.y()*340/max(1,self.height())
        if self.mode=='superposition':
            self._drag_pos=pos
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif getattr(self,'stage','input')=='ready' and abs(y-167)<44:
            if abs(x-125)<47:self.electron_clicked.emit('alice')
            elif abs(x-575)<47:self.electron_clicked.emit('bob')

    def mouseMoveEvent(self,event):
        if self.mode=='superposition' and self._drag_pos is not None:
            pos=event.position();delta=pos-self._drag_pos
            self.camera_yaw=(self.camera_yaw+delta.x()*.65)%360
            self.camera_pitch=max(-85.,min(85.,self.camera_pitch+delta.y()*.55))
            self._drag_pos=pos;self.update()
        elif self.mode=='entanglement':
            x=event.position().x()*700/max(1,self.width())
            y=event.position().y()*340/max(1,self.height())
            near=getattr(self,'stage','input')=='ready' and abs(y-167)<44 and (abs(x-125)<47 or abs(x-575)<47)
            self.setCursor(Qt.CursorShape.PointingHandCursor if near else Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self,event):
        if self.mode=='superposition':
            self._drag_pos=None;self.setCursor(Qt.CursorShape.OpenHandCursor)



class EntanglementStageDiagram(QWidget):
    """Compact, scalable scientific diagrams for the persistent three-stage overview."""
    def __init__(self, number, parent=None):
        super().__init__(parent)
        self.number = number
        self.concurrence = None
        self.focused = False
        self.alice_state = None
        self.bob_state = None
        self.setMinimumHeight(158)
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(),
                           self.sizePolicy().verticalPolicy())

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Uniform fitting prevents compressed/tall text when stage cards resize.
        factor = min(self.width()/290, self.height()/158)
        p.translate((self.width()-290*factor)/2, (self.height()-158*factor)/2)
        p.scale(factor, factor)
        p.setPen(QPen(QColor('#52d3f0') if self.focused else QColor('#42627c'), 2 if self.focused else 1))
        p.setBrush(QColor('#19384a') if self.focused else QColor('#142439'))
        p.drawRoundedRect(QRectF(1, 1, 288, 156), 9, 9)
        accent = QColor('#6bd7eb')
        p.setPen(accent)
        p.setFont(QFont('Sans Serif', 10, QFont.Weight.Bold))
        titles = ('1  BEFORE  ·  Separate spins', '2  OPERATION  ·  H + CNOT',
                  '3  AFTER  ·  Joint state')
        p.drawText(QRectF(7, 8, 276, 21), Qt.AlignmentFlag.AlignCenter, titles[self.number])
        if self.number == 0:
            for x, label, state in ((79, 'Alice', self.alice_state),
                                    (211, 'Bob', self.bob_state)):
                p.setBrush(QColor('#254a60'))
                p.setPen(QPen(QColor('#67cfdf'), 2))
                p.drawEllipse(QPointF(x, 62), 18, 18)
                p.setPen(QColor('#e2f5ff'))
                p.setFont(QFont('Sans Serif', 11))
                p.drawText(QRectF(x-17, 49, 34, 26), Qt.AlignmentFlag.AlignCenter, 'e⁻')
                p.setFont(QFont('Sans Serif', 10))
                p.drawText(QRectF(x-46, 83, 92, 20), Qt.AlignmentFlag.AlignCenter, label)
                if state is not None:
                    spin_up = 100*abs(state[0])**2
                    p.setPen(QColor('#9cbbce'))
                    p.setFont(QFont('Sans Serif', 9))
                    p.drawText(QRectF(x-62, 104, 124, 19), Qt.AlignmentFlag.AlignCenter,
                               f'P(↑) = {spin_up:.1f}%')
            p.setPen(QColor('#a8c1d3'))
            p.drawText(QRectF(7, 132, 276, 17), Qt.AlignmentFlag.AlignCenter,
                       '|ψA⟩ ⊗ |ψB⟩  (product state)')
        elif self.number == 1:
            p.setPen(QPen(QColor('#8db2c9'), 2))
            for y in (65, 107):
                p.drawLine(QPointF(21, y), QPointF(270, y))
            p.setBrush(QColor('#2d637e'))
            p.setPen(QPen(QColor('#71d4e8'), 2))
            p.drawRoundedRect(QRectF(69, 45, 37, 39), 5, 5)
            p.setPen(QColor('#f1faff'))
            p.setFont(QFont('Sans Serif', 15, QFont.Weight.Bold))
            p.drawText(QRectF(69, 46, 37, 37), Qt.AlignmentFlag.AlignCenter, 'H')
            p.setPen(QPen(accent, 2))
            p.drawLine(QPointF(186, 65), QPointF(186, 107))
            p.setBrush(accent)
            p.drawEllipse(QPointF(186, 65), 5, 5)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(186, 107), 11, 11)
            p.drawLine(QPointF(175, 107), QPointF(197, 107))
            p.drawLine(QPointF(186, 96), QPointF(186, 118))
            p.setFont(QFont('Sans Serif', 9))
            p.setPen(QColor('#b6d1e0'))
            p.drawText(QRectF(8, 35, 60, 20), Qt.AlignmentFlag.AlignCenter, 'Alice')
            p.drawText(QRectF(8, 117, 60, 20), Qt.AlignmentFlag.AlignCenter, 'Bob')
        else:
            p.setPen(QPen(QColor('#6bd7eb'), 2))
            p.drawLine(QPointF(98, 71), QPointF(192, 71))
            for x in (79, 211):
                p.setBrush(QColor('#254a60'))
                p.drawEllipse(QPointF(x, 71), 19, 19)
                p.setPen(QColor('#e2f5ff'))
                p.setFont(QFont('Sans Serif', 11))
                p.drawText(QRectF(x-18, 57, 36, 27), Qt.AlignmentFlag.AlignCenter, 'e⁻')
                p.setPen(QPen(QColor('#6bd7eb'), 2))
            p.setPen(QColor('#a8c1d3'))
            p.setFont(QFont('Sans Serif', 10))
            p.drawText(QRectF(7, 99, 276, 22), Qt.AlignmentFlag.AlignCenter,
                       '|Ψout⟩  =  H(A) · CNOT(A,B) |ψin⟩')
            p.setPen(QColor('#76d9e8'))
            p.setFont(QFont('Sans Serif', 11, QFont.Weight.Bold))
            value = 'Run preparation to calculate C' if self.concurrence is None else f'Concurrence  C = {self.concurrence:.3f}'
            p.drawText(QRectF(7, 126, 276, 23), Qt.AlignmentFlag.AlignCenter, value)
        p.end()

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


class EntanglementDialog(QWidget):
    """Interactive source -> gate station -> local electron measurement demonstration."""
    def __init__(self,parent=None):
        super().__init__(parent)
        layout=QVBoxLayout(self)
        heading=QLabel('QUANTUM ENTANGLEMENT  ·  Independent spins → H(A) + CNOT(A,B) → joint state → measurements')
        heading.setWordWrap(True);layout.addWidget(heading)
        split=QSplitter(Qt.Orientation.Horizontal);layout.addWidget(split,1)
        sidebar=QWidget();form=QFormLayout(sidebar)
        self.ta=SuperpositionDialog._angle(0,0,180)
        self.pa=SuperpositionDialog._angle(0,0,360)
        self.tb=SuperpositionDialog._angle(0,0,180)
        self.pb=SuperpositionDialog._angle(0,0,360)
        form.addRow('Alice initial θ',SuperpositionDialog._slider_control(self.ta))
        form.addRow('Alice initial φ',SuperpositionDialog._slider_control(self.pa))
        form.addRow('Bob initial θ',SuperpositionDialog._slider_control(self.tb))
        form.addRow('Bob initial φ',SuperpositionDialog._slider_control(self.pb))
        self.initial=QLabel();self.initial.setWordWrap(True);form.addRow(self.initial)
        self.prepare=QPushButton('Send electrons through entangling box');form.addRow(self.prepare)
        self.reset=QPushButton('Reset to independent electrons');form.addRow(self.reset)
        self.a=SuperpositionDialog._angle(0,-180,180)
        self.b=SuperpositionDialog._angle(0,-180,180)
        form.addRow('Alice measurement axis',SuperpositionDialog._slider_control(self.a))
        form.addRow('Bob measurement axis',SuperpositionDialog._slider_control(self.b))
        self.meas_a=QPushButton('Measure Alice (or click electron)');form.addRow(self.meas_a)
        self.meas_b=QPushButton('Measure Bob (or click electron)');form.addRow(self.meas_b)
        self.meas_both=QPushButton('Measure both');form.addRow(self.meas_both)
        self.runs=QSpinBox();self.runs.setRange(10,10000);self.runs.setValue(500)
        form.addRow('Fresh pairs / trial',self.runs)
        self.sample=QPushButton('Collect correlation statistics');form.addRow(self.sample)
        self.outcome=QLabel();self.outcome.setWordWrap(True);form.addRow(self.outcome)
        note=QLabel('Educational ideal-spin model: H on Alice then CNOT creates |Φ+⟩ from |↑↑⟩. Other initial values can yield partially entangled OR separable states. This is a modeled gate operation, not a physical electron trajectory or instantaneous signaling.')
        note.setWordWrap(True);form.addRow(note)
        split.addWidget(sidebar)
        panel=QWidget();right=QVBoxLayout(panel)
        # Keep all three stages visible even after the moving scene reaches AFTER.
        overview=QWidget();overview_layout=QHBoxLayout(overview)
        overview_layout.setContentsMargins(0,0,0,0);overview_layout.setSpacing(7)
        self.stage_cards=[]
        for number in range(3):
            card=EntanglementStageDiagram(number)
            overview_layout.addWidget(card,1);self.stage_cards.append(card)
        right.addWidget(overview)
        nav=QHBoxLayout()
        self.back=QPushButton('◀ Back');self.next_step=QPushButton('Next ▶')
        self.replay=QPushButton('↻ Replay preparation')
        for control in (self.back,self.next_step,self.replay):nav.addWidget(control)
        right.addLayout(nav)
        self.stage_description=QLabel();self.stage_description.setWordWrap(True)
        self.stage_description.setStyleSheet('QLabel { font-size: 13px;  padding: 4px 2px; }')
        right.addWidget(self.stage_description)
        self.stage_focus=0
        self.back.clicked.connect(lambda:self._focus_stage(self.stage_focus-1))
        self.next_step.clicked.connect(lambda:self._focus_stage(self.stage_focus+1))
        self.replay.clicked.connect(self._replay)
        self.scene=SpinScene('entanglement');right.addWidget(self.scene,3)
        self.scene.electron_clicked.connect(self._click_electron)
        self.joint=QLabel();self.joint.setWordWrap(True)
        self.joint.setStyleSheet('QLabel {font-size: 14px;  padding: 7px 3px;}')
        right.addWidget(self.joint)
        self.prediction=QLabel();self.prediction.setWordWrap(True);right.addWidget(self.prediction)
        self.stats=QLabel('');self.stats.setWordWrap(True);right.addWidget(self.stats)
        split.addWidget(panel);split.setSizes([410,770])
        self.timer=QTimer(self);self.timer.setInterval(25);self.timer.timeout.connect(self._move)
        self.input_state=None;self.joint_state=None;self.current_state=None
        self._alice=None;self._bob=None
        self.prepare.clicked.connect(self._prepare)
        self.reset.clicked.connect(self._reset)
        self.meas_a.clicked.connect(self._measure_alice)
        self.meas_b.clicked.connect(self._measure_bob)
        self.meas_both.clicked.connect(self._measure_both)
        self.sample.clicked.connect(self._sample)
        self.a.valueChanged.connect(self._change_axes)
        self.b.valueChanged.connect(self._change_axes)
        for spin in (self.ta,self.pa,self.tb,self.pb):spin.valueChanged.connect(self._change_input)
        self._reset()

    def _focus_stage(self,index):
        # Educational inspection never rewinds an already measured quantum state.
        self.stage_focus=max(0,min(2,index))
        for n,card in enumerate(self.stage_cards):
            card.focused=(n == self.stage_focus)
            card.update()
        self.back.setEnabled(self.stage_focus>0)
        self.next_step.setEnabled(self.stage_focus<2)
        explanations=(
            'BEFORE: Alice and Bob have separate adjustable qubit states. Their joint input is a product state.',
            'GATE: Hadamard on Alice followed by controlled-NOT creates a two-qubit output; not every input becomes entangled.',
            'AFTER: Compare the final joint wavefunction and concurrence. Click the electrons in the scene to measure locally.'
        )
        self.stage_description.setText(explanations[self.stage_focus])

    def _refresh_stage_cards(self):
        self.stage_cards[0].alice_state=qubit_state(self.ta.value(),self.pa.value())
        self.stage_cards[0].bob_state=qubit_state(self.tb.value(),self.pb.value())
        self.stage_cards[2].concurrence=(None if self.joint_state is None
                                          else pair_concurrence(self.joint_state))
        for card in self.stage_cards:
            card.update()

    def _replay(self):
        # Re-prepares a fresh pair; it is not a time reversal of measurements.
        self._reset()
        self._prepare()

    @staticmethod
    def _pretty_state(state,threshold=.025):
        terms=[]
        for amplitude,ket in zip(state,('↑↑','↑↓','↓↑','↓↓')):
            if abs(amplitude)>threshold:
                terms.append(f'({amplitude.real:+.2f}{amplitude.imag:+.2f}i)|{ket}⟩')
        return ' '.join(terms) or '0'

    def _input_pair(self):
        alice=qubit_state(self.ta.value(),self.pa.value())
        bob=qubit_state(self.tb.value(),self.pb.value())
        return prepare_gate_pair(alice,bob)

    def _change_input(self,*_):
        # Inputs only change the preparation blueprint; never teleport moving particles.
        product,output=self._input_pair()
        self.initial.setText(f'Before: |ψA⟩ ⊗ |ψB⟩  |  θA={self.ta.value():g}°, φA={self.pa.value():g}°; θB={self.tb.value():g}°, φB={self.pb.value():g}°')
        if self.scene.stage=='input':
            self.input_state=product;self.joint_state=None
            self.joint.setText('Input product state: '+self._pretty_state(product))
        else:
            self.outcome.setText('Initial values edited. Reset before preparing a pair with the new values.')
        self.stats.setText('');self._refresh_stage_cards();self.scene.update()

    def _reset(self):
        self.timer.stop();self.scene.stage='input';self.scene.progress=0.
        self.scene.alice=None;self.scene.bob=None
        self._alice=None;self._bob=None
        self.input_state,self._preview=self._input_pair()
        self.joint_state=None;self.current_state=None
        self.meas_a.setEnabled(False);self.meas_b.setEnabled(False);self.meas_both.setEnabled(False)
        self.sample.setEnabled(False);self.prepare.setEnabled(True)
        for spin in (self.ta,self.pa,self.tb,self.pb):spin.setEnabled(True)
        self.initial.setText(f'Before: Alice |ψA⟩ (θ={self.ta.value():g}°, φ={self.pa.value():g}°), Bob |ψB⟩ (θ={self.tb.value():g}°, φ={self.pb.value():g}°)')
        self.joint.setText('Separate product wavefunction: '+self._pretty_state(self.input_state))
        self.prediction.setText('Set both input spins, then run H(A) → CNOT(A,B).')
        self.outcome.setText('Two independent electrons are ready at the source.');self.stats.setText('')
        self.scene.joint_label='';self._refresh_stage_cards();self._focus_stage(0);self.scene.update()

    def _prepare(self):
        if self.scene.stage!='input':return
        self.input_state,self.joint_state=self._input_pair()
        self.current_state=self.joint_state.copy()
        self.scene.stage='intake';self.scene.progress=0.
        self.prepare.setEnabled(False)
        for spin in (self.ta,self.pa,self.tb,self.pb):spin.setEnabled(False)
        self.outcome.setText('Sending two prepared spins into the entangling gate station…')
        self.timer.start();self._refresh_stage_cards();self._focus_stage(1);self.scene.update()

    def _move(self):
        self.scene.progress=min(1.,self.scene.progress+.025)
        if self.scene.progress>=1.:
            if self.scene.stage=='intake':
                self.scene.stage='output';self.scene.progress=0.
                self.outcome.setText('Gate sequence applied. Electrons separating for local measurements…')
            elif self.scene.stage=='output':
                self.scene.stage='ready';self.timer.stop()
                self.meas_a.setEnabled(True);self.meas_b.setEnabled(True);self.meas_both.setEnabled(True)
                self.sample.setEnabled(True)
                c=pair_concurrence(self.joint_state)
                self.outcome.setText('Pair ready: click each electron to measure its spin.')
                self.scene.joint_label='|Ψout⟩ = H(A) + CNOT joint output  •  C = '+f'{c:.3f}'
                self.joint.setText('After gate sequence, joint wavefunction: '+self._pretty_state(self.joint_state)+f'  |  concurrence C={c:.3f} (0=separable, 1=maximal)')
                self._prediction()
                self._refresh_stage_cards();self._focus_stage(2)
        self.scene.update()

    def _change_axes(self,*_):
        self.stats.setText('')
        if self._alice is not None or self._bob is not None:
            self.meas_a.setEnabled(False);self.meas_b.setEnabled(False);self.meas_both.setEnabled(False)
            self.outcome.setText('Measurement axis changed after measurement; reset and prepare a fresh pair.')
        elif self.scene.stage=='ready':
            self._prediction()
        self.scene.update()

    def _click_electron(self,which):
        if which=='alice':self._measure_alice()
        elif which=='bob':self._measure_bob()

    def _measure_alice(self):
        if not self.meas_a.isEnabled():return
        self._alice,self.current_state=local_measure_pair(self.current_state,self.a.value(),'alice')
        self.scene.alice=self._alice;self.meas_a.setEnabled(False);self._status()

    def _measure_bob(self):
        if not self.meas_b.isEnabled():return
        self._bob,self.current_state=local_measure_pair(self.current_state,self.b.value(),'bob')
        self.scene.bob=self._bob;self.meas_b.setEnabled(False);self._status()

    def _measure_both(self):
        self._measure_alice();self._measure_bob()

    def _status(self):
        def label(v):return 'unmeasured / hidden' if v is None else ('+1 ↑' if v>0 else '−1 ↓')
        self.outcome.setText(f'Alice: {label(self._alice)}    |    Bob: {label(self._bob)}')
        self.scene.update()

    def _prediction(self):
        if self.joint_state is None:return
        p=pair_joint_probabilities(self.joint_state,self.a.value(),self.b.value())
        corr=float(p[0,0]+p[1,1]-p[0,1]-p[1,0])
        self.prediction.setText(f'Expected correlation at selected angles: E={corr:+.3f}; P(++,+−,−+,−−)='+', '.join(f'{v:.1%}' for v in p.ravel())+'. These depend on the prepared joint state.')

    def _sample(self):
        if self.joint_state is None or self.scene.stage!='ready':return
        n=self.runs.value();p=pair_joint_probabilities(self.joint_state,self.a.value(),self.b.value())
        nums=np.random.default_rng().multinomial(n,p.ravel())
        observed=float((nums[0]+nums[3]-nums[1]-nums[2])/n)
        self.stats.setText(f'{n} fresh identically prepared pairs: ++ {nums[0]}  +− {nums[1]}  −+ {nums[2]}  −− {nums[3]}    |    observed E={observed:+.3f}')

    def hideEvent(self,event):
        self.timer.stop();super().hideEvent(event)

    def showEvent(self,event):
        super().showEvent(event)
        if self.scene.stage in ('intake','output'):self.timer.start()
