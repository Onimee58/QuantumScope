"""Interactive gate circuit editor and exact simulator."""
import math
import numpy as np
from PySide6.QtCore import Qt, QMimeData, QPoint, QEvent, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QDrag, QFont, QBrush, QWheelEvent
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QSplitter,
    QLabel, QPushButton, QListWidget, QTableWidget, QTableWidgetItem, QSpinBox,
    QSlider, QTextEdit, QFileDialog, QMessageBox, QAbstractItemView, QComboBox, QScrollArea, QCheckBox, QInputDialog, QMenu, QGroupBox, QToolButton, QSizePolicy)
from quantumscope.physics.circuit_files import to_native,from_native,to_qasm, to_native_measured, from_native_measured, to_qasm_measured, from_qasm_measured
from quantumscope.physics.circuit_verification import verify_example, inspect_basis
from quantumscope.physics.circuits import (MAX_QUBITS, Gate, ALL, DUAL, TRIPLE, evolution,
    bloch, sample, parse_qasm, distribution, measurement_marginal)


class Palette(QListWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
    def startDrag(self, actions):
        item=self.currentItem()
        if item is None:return
        drag=QDrag(self); mime=QMimeData();mime.setText('QS_GATE:'+item.text());drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)


class Grid(QTableWidget):
    def __init__(self, owner):
        super().__init__(owner);self.owner=owner;self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.viewport().installEventFilter(self)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self._pan_origin=None
        self._zoom=1.0
        self.setToolTip("Middle-drag or Shift+drag empty space to pan; Ctrl+wheel to zoom")
    def paintEvent(self,event):
        super().paintEvent(event)
        if not hasattr(self.owner, 'gates'):
            return
        p=QPainter(self.viewport())
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect=self.viewport().rect()
        rows=self.rowCount()
        p.setPen(QPen(QColor('#567895'), 1.7))
        for row in range(rows):
            y=self.visualRect(self.model().index(row,0)).center().y()
            if 0 <= y <= rect.height():
                p.drawLine(0,y,rect.width(),y)
        for (row,col),g in self.owner.gates.items():
            if row>=rows or col>=self.columnCount(): continue
            cell=self.visualRect(self.model().index(row,col))
            if not cell.isValid() or cell.right()<0 or cell.left()>rect.width():continue
            x=cell.center().x()
            if len(g.targets)>1:
                ys=[self.visualRect(self.model().index(q,col)).center().y() for q in g.targets]
                p.setPen(QPen(QColor('#b3d0e7'),2.4))
                p.drawLine(x,min(ys),x,max(ys))
                # A control dot and standard targets, including multi-controlled gates.
                if g.name in ('CX','CZ','CCX','CSWAP'):
                    controls=g.targets[:-1] if g.name in ('CX','CZ','CCX') else g.targets[:1]
                    for q in controls:
                        cy=self.visualRect(self.model().index(q,col)).center().y()
                        p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor('#d5f5ff'))
                        p.drawEllipse(QPoint(x,cy),5,5)
            p.setBrush(QColor('#193c56'))
            p.setPen(QPen(QColor('#60bddb'),1.7))
            box=cell.adjusted(9,6,-9,-6)
            if g.name in ('CX','CCX'):
                target=g.targets[-1]
                cy=self.visualRect(self.model().index(target,col)).center().y()
                p.setBrush(QColor('#11283c'));p.drawEllipse(QPoint(x,cy),12,12)
                p.drawLine(x-8,cy,x+8,cy);p.drawLine(x,cy-8,x,cy+8)
            elif g.name=='SWAP' or g.name=='CSWAP':
                for q in (g.targets if g.name=='SWAP' else g.targets[1:]):
                    cy=self.visualRect(self.model().index(q,col)).center().y()
                    p.drawLine(x-7,cy-7,x+7,cy+7);p.drawLine(x-7,cy+7,x+7,cy-7)
            elif g.name=='CZ':
                cy=self.visualRect(self.model().index(g.targets[-1],col)).center().y()
                p.setBrush(QColor('#d5f5ff'));p.setPen(Qt.PenStyle.NoPen);p.drawEllipse(QPoint(x,cy),5,5)
            else:
                p.setBrush(QColor('#174865'));p.drawRoundedRect(box,5,5)
                p.setPen(QColor('#effaff'))
                p.setFont(QFont('Sans',10,QFont.Weight.DemiBold))
                p.drawText(box,Qt.AlignmentFlag.AlignCenter,g.name)
        # Terminal measurement indicators are annotations, not unitary gates.
        for row,col in getattr(self.owner,'measurements',{}).items():
            if row>=rows or col>=self.columnCount(): continue
            cell=self.visualRect(self.model().index(row,col))
            if cell.isValid() and cell.right()>=0 and cell.left()<=rect.width():
                box=cell.adjusted(9,6,-9,-6)
                p.setPen(QPen(QColor('#ffd58e'),2));p.setBrush(QColor('#273747'))
                p.drawRoundedRect(box,5,5)
                p.setPen(QColor('#ffe9bc'));p.setFont(QFont('Sans',11,QFont.Weight.Bold))
                p.drawText(box,Qt.AlignmentFlag.AlignCenter,'M')
        p.end()

    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.MiddleButton or (event.button()==Qt.MouseButton.LeftButton and event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self._pan_origin=event.position().toPoint();self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor);event.accept();return
        super().mousePressEvent(event)
    def mouseMoveEvent(self,event):
        if self._pan_origin is not None:
            point=event.position().toPoint();delta=point-self._pan_origin;self._pan_origin=point
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value()-delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value()-delta.y())
            event.accept();return
        super().mouseMoveEvent(event)
    def mouseReleaseEvent(self,event):
        if self._pan_origin is not None:
            self._pan_origin=None;self.viewport().unsetCursor();event.accept();return
        super().mouseReleaseEvent(event)
    def wheelEvent(self,event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.zoom_by(1.12 if event.angleDelta().y()>0 else 1/1.12)
            event.accept();return
        # The surrounding workspace owns ordinary vertical scrolling.
        # Keep Ctrl+wheel exclusively for circuit zoom.
        event.ignore()
    def zoom_by(self,multiplier):
        self._zoom=max(0.55,min(2.5,self._zoom*multiplier))
        self.horizontalHeader().setDefaultSectionSize(round(82*self._zoom))
        self.verticalHeader().setDefaultSectionSize(round(54*self._zoom))
        self.owner.inline_blochs.update()
    def fit_view(self):
        # Fit occupied columns where practical, but never distort text.
        occupied=max((c for _,c in self.owner.gates),default=5)+2
        occupied=max(6,min(occupied,30))
        width=max(45,min(115,self.viewport().width()//occupied))
        height=max(37,min(78,self.viewport().height()//max(1,self.owner.n)))
        self.horizontalHeader().setDefaultSectionSize(width)
        self.verticalHeader().setDefaultSectionSize(height)
        self._zoom=width/82
        self.owner.inline_blochs.update()

    def eventFilter(self,obj,event):
        if obj is self.viewport() and event.type() in (QEvent.Type.DragEnter,QEvent.Type.DragMove,QEvent.Type.Drop):
            if event.mimeData().text().startswith('QS_GATE:'):
                if event.type()==QEvent.Type.Drop:
                    idx=self.indexAt(event.position().toPoint())
                    if idx.isValid():self.owner.place(event.mimeData().text().split(':',1)[1],idx.row(),idx.column())
                event.acceptProposedAction()
                return True
        return super().eventFilter(obj,event)
    def dragEnterEvent(self,event):
        if event.mimeData().text().startswith('QS_GATE:'):event.acceptProposedAction()
        else:super().dragEnterEvent(event)
    def dragMoveEvent(self,event):
        if event.mimeData().text().startswith('QS_GATE:'):event.acceptProposedAction()
        else:super().dragMoveEvent(event)
    def dropEvent(self,event):
        txt=event.mimeData().text()
        if txt.startswith('QS_GATE:'):
            idx=self.indexAt(event.position().toPoint())
            if idx.isValid():self.owner.place(txt.split(':',1)[1],idx.row(),idx.column())
            event.acceptProposedAction()
        else:super().dropEvent(event)


class BlochPanel(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent);self.vecs=[];self.setMinimumHeight(185)
    def set_vectors(self,vectors):
        self.vecs=vectors
        self._fit_rows()
        self.update()
    def _fit_rows(self):
        columns=max(1,min(5,max(1,self.width())//150))
        rows=math.ceil(len(self.vecs)/columns)
        self.setMinimumHeight(max(185,rows*170))
    def resizeEvent(self,event):
        super().resizeEvent(event)
        self._fit_rows()
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w=self.width();cols=max(1,min(5,w//150));rows=math.ceil(len(self.vecs)/cols)
        cellw=w/cols; cellh=max(170,self.height()/max(1,rows));radius=min(47,cellw*.33,cellh*.33)
        p.setFont(QFont('Sans',9))
        for k,(x,y,z) in enumerate(self.vecs):
            col,row=k%cols,k//cols; cx=(col+.5)*cellw;cy=row*cellh+cellh*.46
            p.setPen(QPen(QColor('#6687a6'),1.4));p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPoint(int(cx),int(cy)),int(radius),int(radius))
            p.drawEllipse(int(cx-radius),int(cy-radius*.29),int(2*radius),int(radius*.58))
            p.setPen(QPen(QColor('#4f6c89'),1));p.drawLine(int(cx-radius),int(cy),int(cx+radius),int(cy))
            p.drawLine(int(cx),int(cy-radius),int(cx),int(cy+radius))
            # Fixed isometric camera: x to right, y to upper-right, z vertical.
            endx=cx+radius*(.87*x+.34*y);endy=cy-radius*(z+.28*y)
            p.setPen(QPen(QColor('#52d4df'),3));p.drawLine(int(cx),int(cy),int(endx),int(endy))
            p.setBrush(QColor('#52d4df'));p.drawEllipse(QPoint(int(endx),int(endy)),4,4)
            p.setPen(QColor('#ddefff'));p.drawText(int(cx-radius),int(cy+radius+12),int(2*radius),18,
                Qt.AlignmentFlag.AlignCenter,f'q{k}  |r|={math.sqrt(x*x+y*y+z*z):.2f}')
        p.end()



class InlineBlochs(QWidget):
    """Fixed-size qubit glyphs aligned with the table's row centers."""
    def __init__(self,grid,parent=None):
        super().__init__(parent);self.grid=grid;self.vecs=[];self.setFixedWidth(105)
    def set_vectors(self,vecs):self.vecs=vecs;self.update()
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        header=self.grid.horizontalHeader().height()
        for q,(x,y,z) in enumerate(self.vecs):
            ymid=header+q*self.grid.verticalHeader().defaultSectionSize()+23-self.grid.verticalScrollBar().value()
            if ymid<15 or ymid>self.height()-10:continue
            cx=36;r=16
            p.setPen(QPen(QColor('#7b9eb7'),1));p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPoint(cx,int(ymid)),r,r)
            p.drawEllipse(cx-r,int(ymid-5),r*2,10)
            p.setPen(QPen(QColor('#55d5df'),2.5))
            p.drawLine(cx,int(ymid),int(cx+r*(.85*x+.25*y)),int(ymid-r*(z+.25*y)))
            p.setPen(QColor('#d9f3ff'));p.setFont(QFont('Sans',8))
            p.drawText(56,int(ymid+4),f'{math.sqrt(x*x+y*y+z*z):.2f}')
        p.end()

class ProbabilityBars(QWidget):
    """Compact vertical histogram with paired theoretical and sampled bars."""
    def __init__(self,parent=None):
        super().__init__(parent)
        self.theory=[];self.counts=None;self.n=1;self.title="Full quantum-state probabilities (before measurement) · cyan: theory"
        self.setMinimumHeight(180)
    def set_data(self,state,n,counts=None):
        probs=distribution(state);self.n=n
        scores=probs.copy()
        if counts is not None:scores=np.maximum(scores,counts/max(1,counts.sum()))
        inds=np.argsort(scores)[::-1]
        selected=[int(i) for i in inds if scores[i]>1e-9][:10]
        if not selected:selected=[0]
        self.theory=[(format(i,f'0{n}b'),float(probs[i])) for i in selected]
        self.counts={format(i,f'0{n}b'):float(counts[i]/max(1,counts.sum())) for i in selected} if counts is not None else None
        self.update()
    def set_probabilities(self,probs,n,counts=None):
        self.n=n
        scores=np.array(probs,dtype=float)
        if counts is not None:scores=np.maximum(scores,counts/max(1,counts.sum()))
        inds=np.argsort(scores)[::-1]
        selected=[int(i) for i in inds if scores[i]>1e-9][:10] or [0]
        self.theory=[(format(i,f'0{n}b'),float(probs[i])) for i in selected]
        self.counts={format(i,f'0{n}b'):float(counts[i]/max(1,counts.sum())) for i in selected} if counts is not None else None
        self.update()
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w,h=self.width(),self.height()
        p.setFont(QFont('Sans',9));p.setPen(QColor('#dceeff'))
        p.drawText(12,16,self.title)
        left,right,top,bottom=48,12,34,37
        pw=max(1,w-left-right);ph=max(1,h-top-bottom)
        p.setPen(QPen(QColor('#547089'),1));p.drawLine(left,top,left,top+ph);p.drawLine(left,top+ph,left+pw,top+ph)
        p.drawText(6,top+10,'100%');p.drawText(16,top+ph,'0%')
        gap=pw/max(1,len(self.theory))
        for i,(name,val) in enumerate(self.theory):
            center=left+(i+.5)*gap
            bw=max(3,min(20,gap*.30))
            p.fillRect(int(center-bw-1),int(top+ph*(1-val)),int(bw),max(1,int(ph*val)),QColor('#52c8e5'))
            if self.counts is not None:
                v=self.counts[name]
                p.fillRect(int(center+1),int(top+ph*(1-v)),int(bw),max(1,int(ph*v)),QColor('#f6b05e'))
            p.setPen(QColor('#dceeff'))
            text=name if len(name)<=5 else (name[:3]+'…'+name[-2:])
            p.drawText(int(center-gap*.46),top+ph+5,int(gap*.92),17,Qt.AlignmentFlag.AlignCenter,text)
            p.drawText(int(center-gap*.46),max(top+2,int(top+ph*(1-max(val,self.counts[name] if self.counts is not None else 0))-18)),int(gap*.92),15,Qt.AlignmentFlag.AlignCenter,f'{val*100:.0f}%')
        p.end()

class CircuitWorkspace(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent);self.n=3;self.columns=2;self.gates={};self.measurements={};self._syncing=False;self.undo_stack=[];self.redo_stack=[];self._restoring=False;self.current_path=None;self._play_timer=QTimer(self);self._play_timer.timeout.connect(self._advance)
        page_layout=QVBoxLayout(self)
        page_layout.setContentsMargins(0,0,0,0)
        self.page_scroll=QScrollArea(self)
        self.page_scroll.setWidgetResizable(True)
        self.page_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        page_layout.addWidget(self.page_scroll)
        page=QWidget()
        self.page_scroll.setWidget(page)
        outer=QVBoxLayout(page);outer.setSpacing(8)
        heading=QLabel('QUANTUM CIRCUITS  ·  Drag gates from the palette onto empty cells; click a placed gate to select it')
        outer.addWidget(heading)
        top=QHBoxLayout();outer.addLayout(top)
        top.addWidget(QLabel('Qubits'))
        self.qubits=QSpinBox();self.qubits.setRange(1,MAX_QUBITS);self.qubits.setValue(self.n);top.addWidget(self.qubits)
        top.addWidget(QLabel('Gate'))
        self.gate=QComboBox();self.gate.addItems(list(ALL)+['M']);top.addWidget(self.gate)
        top.addWidget(QLabel('Rotation (°)'))
        self.angle=QSpinBox();self.angle.setRange(-360,360);self.angle.setValue(90);top.addWidget(self.angle)
        self.phi=QSpinBox();self.phi.setRange(-360,360);self.phi.setValue(0);self.phi.setPrefix('φ ');self.phi.setToolTip('U gate phase φ in degrees');top.addWidget(self.phi)
        self.lam=QSpinBox();self.lam.setRange(-360,360);self.lam.setValue(0);self.lam.setPrefix('λ ');self.lam.setToolTip('U gate phase λ in degrees');top.addWidget(self.lam)
        self.second_label=QLabel('Target');top.addWidget(self.second_label)
        self.target=QSpinBox();self.target.setRange(0,self.n-1);top.addWidget(self.target)
        self.third_label=QLabel('Target (third qubit)')
        self.target3=QSpinBox();self.target3.setRange(0,self.n-1);self.target3.setValue(2);self.target3.setToolTip('CCX: third qubit is the target; CSWAP: third qubit is the second swap operand.')
        top.addWidget(self.third_label);top.addWidget(self.target3)
        self.gate.currentTextChanged.connect(self._update_operand_labels)
        self._update_operand_labels(self.gate.currentText())
        for text,cb in [('Clear',self.clear),('Bell example',self.example),('Import QASM 2',self.load_qasm),('Export QASM',self.export_qasm),('Open .qscope',self.load_native),('Save .qscope',self.save_native)]:
            btn=QPushButton(text);btn.clicked.connect(cb);top.addWidget(btn)
        edits=QHBoxLayout();outer.addLayout(edits)
        for text,cb in [('Undo',self.undo),('Redo',self.redo)]:
            button=QPushButton(text);button.clicked.connect(cb);edits.addWidget(button)
        self.show_blochs=QCheckBox('Show Bloch spheres beside wires');self.show_blochs.setChecked(True);edits.addWidget(self.show_blochs)
        self.examples=QComboBox();self.examples.addItems(['Examples…','Bell pair','GHZ','Half adder (a=1,b=1)','Half subtractor (a=1,b=1)','2-bit ripple-carry adder (1+1)']);self.examples.currentIndexChanged.connect(self.load_example);edits.addWidget(self.examples)
        edits.addStretch()
        split=QSplitter(Qt.Orientation.Horizontal)
        # A whole-page scroll area, not a shrinking circuit editor, handles
        # limited vertical space on Windows and older Ubuntu releases.
        outer.addWidget(split)
        self.palette=Palette();self.palette.addItems(list(ALL)+['M']);self.palette.setMinimumWidth(85);self.palette.setMaximumWidth(130)
        # Palette clicks only select palette entries; they never place or replace gates.
        self.palette.setToolTip('Drag a gate onto an empty cell; click existing gates to select')
        self.palette.setStyleSheet('''QListWidget {background:#101e31; border:1px solid #304c66; border-radius:9px; padding:5px; spacing:4px; color:#dfecfb; font-size:12px;} QListWidget::item {background:#203750; border:1px solid #3b5975; border-radius:5px; padding:7px 4px; min-height:19px;} QListWidget::item:selected {background:#155b80; border:1px solid #55c8e5; color:white;} QListWidget::item:hover {background:#2a4c6a;}''')
        split.addWidget(self.palette)
        center=QWidget();v=QVBoxLayout(center);split.addWidget(center)
        self.grid=Grid(self);self.grid.setRowCount(self.n);self.grid.setColumnCount(self.columns)
        self.grid.setHorizontalHeaderLabels([f'{i+1}' for i in range(self.columns)]);self.grid.setVerticalHeaderLabels([f'q{i} ─' for i in range(self.n)])
        self.grid.verticalHeader().setDefaultSectionSize(54);self.grid.horizontalHeader().setDefaultSectionSize(82)
        # Reserve room for ten wires at the default scale.  The model still
        # contains only active qubits, leaving the remaining canvas blank.
        # Keep the circuit's panning/zoom mechanics, but no internal scrollbars.
        self.grid.setFixedHeight(10 * 54 + self.grid.horizontalHeader().height()
                                 + 2 * self.grid.frameWidth() + 12)
        self.grid.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.grid.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.grid.setShowGrid(False)
        self.grid.setAlternatingRowColors(False)
        self.grid.setStyleSheet('''QTableWidget {background:#101c2c; color:#cce6f7; border:1px solid #304962; selection-background-color:#224661;} QTableWidget::item {background:#101c2c; border:0;} QHeaderView::section {background:#1b3047; color:#d9eeff; border:0; border-right:1px solid #34516d; padding:5px;} QTableCornerButton::section {background:#1b3047;}''')
        self.grid.setToolTip('Drag gates onto empty cells; click to select. Middle-drag to pan, Ctrl+wheel to zoom.')
        nav=QHBoxLayout();v.addLayout(nav)
        for label,callback in [('− Zoom',lambda:self.grid.zoom_by(1/1.15)),('+ Zoom',lambda:self.grid.zoom_by(1.15)),('Fit Circuit',lambda:self.grid.fit_view())]:
            b=QPushButton(label);b.clicked.connect(callback);nav.addWidget(b)
        nav.addStretch()
        self.grid.horizontalHeader().sectionClicked.connect(lambda col:self.step.setValue(col+1))
        wires=QHBoxLayout();v.addLayout(wires);wires.addWidget(self.grid,1)
        self.inline_blochs=InlineBlochs(self.grid);wires.addWidget(self.inline_blochs)
        self.show_blochs.toggled.connect(self.inline_blochs.setVisible)
        self.grid.verticalScrollBar().valueChanged.connect(lambda _:self.inline_blochs.update())
        helptext=QLabel('Two-qubit gates: place on control wire and select the second qubit above. Right-click to remove a gate. Up to 10 qubits; ideal statevector (no hardware noise).')
        helptext.setWordWrap(True);v.addWidget(helptext)
        self.grid.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.grid.customContextMenuRequested.connect(self.remove_at)
        self.status=QLabel('Ready');v.addWidget(self.status)
        playback=QHBoxLayout();v.addLayout(playback)
        self.prev_step=QPushButton('◀');self.prev_step.clicked.connect(lambda:self.step.setValue(max(0,self.step.value()-1)));playback.addWidget(self.prev_step)
        self.play_button=QPushButton('▶ Play');self.play_button.clicked.connect(self.toggle_play);playback.addWidget(self.play_button)
        self.next_step=QPushButton('▶');self.next_step.clicked.connect(lambda:self.step.setValue(min(self.step.maximum(),self.step.value()+1)));playback.addWidget(self.next_step)
        self.step=QSlider(Qt.Orientation.Horizontal);self.step.setRange(0,0)
        self.step.setToolTip('Circuit column 0 is initial state. Move through gate columns.')
        self.step.setMaximumWidth(200);playback.addWidget(self.step)
        self.step_label=QLabel();playback.addWidget(self.step_label);playback.addStretch()
        self.speed=QSpinBox();self.speed.setRange(100,2000);self.speed.setValue(650);self.speed.setSuffix(' ms');self.speed.setToolTip('Playback interval');self.speed.valueChanged.connect(lambda val:self._play_timer.setInterval(val));playback.addWidget(self.speed)
        self.grid.horizontalScrollBar().valueChanged.connect(lambda _:self._sync_timeline())
        self.blochs=BlochPanel()
        self.bloch_scroller=QScrollArea()
        self.bloch_scroller.setWidgetResizable(True)
        self.bloch_scroller.setWidget(self.blochs)
        self.bloch_scroller.setMinimumHeight(190)
        self.bloch_scroller.setToolTip('Scroll to inspect all qubit Bloch vectors if the window is narrow')
        self.bloch_scroller.hide() # Inline per-wire view replaces separate stacked sphere panel
        self.bars=ProbabilityBars();self.bars.setMinimumHeight(165);v.addWidget(self.bars,2)
        self.result=QTextEdit();self.result.setReadOnly(True);self.result.setMaximumHeight(105);v.addWidget(self.result)
        self.verify_panel=QGroupBox('Circuit Verification & Truth Table')
        verify_layout=QVBoxLayout(self.verify_panel)
        controls=QHBoxLayout()
        self.verify_button=QPushButton('Verify circuit / Show truth table');self.verify_button.clicked.connect(self.verify_circuit);controls.addWidget(self.verify_button)
        self.verify_status=QLabel('Select an example to verify arithmetic, or inspect basis-state inputs.');self.verify_status.setWordWrap(True);controls.addWidget(self.verify_status,1)
        verify_layout.addLayout(controls)
        self.verify_table=QTableWidget(0,4);self.verify_table.setHorizontalHeaderLabels(['Input','Simulated output','Expected','Probability / Result'])
        self.verify_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.verify_table.setMinimumHeight(130);self.verify_table.setMaximumHeight(230)
        self.verify_table.horizontalHeader().setStretchLastSection(True)
        verify_layout.addWidget(self.verify_table)
        v.addWidget(self.verify_panel)
        shots=QHBoxLayout();v.addLayout(shots);shots.addWidget(QLabel('Shots'))
        self.shots=QSpinBox();self.shots.setRange(1,100000);self.shots.setValue(1024);shots.addWidget(self.shots)
        run=QPushButton('Run measurement shots');run.clicked.connect(self.measure);shots.addWidget(run)
        # Maintain the complete ten-wire canvas even when the host tab is short.
        # The page scrolls instead of allowing the splitter to compress it.
        center.setMinimumHeight(center.sizeHint().height())
        split.setMinimumHeight(center.minimumHeight() + 8)
        split.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        split.setStretchFactor(1,1)
        self.qubits.valueChanged.connect(self.resize_qubits);self.step.valueChanged.connect(self.show_step)
        self.active_example=None
        self.example()

    def _update_operand_labels(self,name):
        multi=name in DUAL or name in TRIPLE
        triple=name in TRIPLE
        self.target.setVisible(multi)
        self.second_label.setVisible(multi)
        self.target3.setVisible(triple)
        self.third_label.setVisible(triple)
        if name=='CCX':
            self.second_label.setText('Control 2')
            self.third_label.setText('Target')
        elif name=='CSWAP':
            self.second_label.setText('Swap 1')
            self.third_label.setText('Swap 2')
        elif multi:
            self.second_label.setText('Target' if name in ('CX','CZ') else 'Swap partner')

    def snapshot(self):
        if not self._restoring:
            self.undo_stack.append((self.n,self.columns,dict(self.gates),dict(self.measurements)))
            self.undo_stack=self.undo_stack[-80:];self.redo_stack.clear()
    def _restore(self,record):
        n,columns,gates,measurements=record
        self._restoring=True
        self.n=n;self.columns=columns;self.qubits.blockSignals(True);self.qubits.setValue(n);self.qubits.blockSignals(False)
        self.target.setRange(0,n-1);self.target3.setRange(0,n-1);self.grid.setRowCount(n);self.grid.setColumnCount(columns)
        self.grid.setHorizontalHeaderLabels([str(i+1) for i in range(columns)])
        self.grid.setVerticalHeaderLabels([f'q{i} ─' for i in range(n)])
        self.gates=dict(gates);self.measurements=dict(measurements);self._sync_columns();self.refresh();self._restoring=False
    def undo(self):
        if self.undo_stack:
            self.redo_stack.append((self.n,self.columns,dict(self.gates),dict(self.measurements)));self._restore(self.undo_stack.pop())
    def redo(self):
        if self.redo_stack:
            self.undo_stack.append((self.n,self.columns,dict(self.gates),dict(self.measurements)));self._restore(self.redo_stack.pop())
    def resize_qubits(self,n):
        if n<self.n and any(any(q>=n for q in g.targets) for g in self.gates.values()):
            choice=QMessageBox.question(self,'Remove qubits?',
                'Gates targeting removed qubits will be deleted. Continue?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if choice!=QMessageBox.StandardButton.Yes:
                self.qubits.blockSignals(True);self.qubits.setValue(self.n);self.qubits.blockSignals(False);return
        self.snapshot()
        self.gates={pos:g for pos,g in self.gates.items() if all(q<n for q in g.targets)}
        self.measurements={q:c for q,c in self.measurements.items() if q<n}
        self.n=n;self.target.setRange(0,n-1);self.target3.setRange(0,n-1);self.grid.setRowCount(n)
        self.grid.setVerticalHeaderLabels([f'q{i} ─' for i in range(n)]);self.refresh()
    def clear(self):self.snapshot();self.active_example=None;self.gates={};self.measurements={};self._sync_columns();self.refresh()
    def example(self):
        if self.n<2:self.qubits.setValue(2)
        self.snapshot();self.active_example='Bell pair';self.gates={(0,0):Gate('H',(0,)),(0,1):Gate('CX',(0,1))};self.measurements={};self._sync_columns();self.refresh()
    def _sync_columns(self):
        """Keep precisely one trailing empty operation slot (two when empty)."""
        last=max([c for _,c in self.gates]+list(self.measurements.values()),default=-1)
        needed=max(2,last+2)
        if needed!=self.columns:
            offset=self.grid.horizontalScrollBar().value()
            self.columns=needed
            self.grid.setColumnCount(needed)
            self.grid.setHorizontalHeaderLabels([str(i+1) for i in range(needed)])
            self.grid.horizontalScrollBar().setValue(offset)

    def _expand_columns(self,needed):
        # Retained for existing load/import callers; the model decides size.
        self._sync_columns()
    def place(self,name,row,col):
        if not (0<=row<self.n and 0<=col<self.columns):return
        if (row,col) in self.gates or self.measurements.get(row)==col:
            self.status.setText('Cell occupied: select or remove the existing gate first')
            return
        if name=='M':
            if row in self.measurements:
                self.status.setText('This qubit already has a terminal measurement');return
            if any(c>=col for (r,c),g in self.gates.items()):
                self.status.setText('M must be terminal on its measured qubit');return
            if self.measurements and any(c!=col for c in self.measurements.values()):
                self.status.setText('All measurement gates must be in the final circuit column');return
            self.snapshot();self.measurements[row]=col;self._sync_columns();self.refresh();return
        if name not in ALL:return
        if row in self.measurements:
            self.status.setText('Remove this qubit’s terminal measurement before adding gates');return
        if self.measurements and col>=min(self.measurements.values()):
            self.status.setText('Unitary gates must be before terminal measurements');return
        ids=(row,)
        if name in DUAL or name in TRIPLE:
            b=self.target.value()
            if b==row:
                b=(row+1)%self.n
            if b==row:
                self.status.setText('A two-qubit gate needs two different qubits');return
            ids=(row,b)
            if name in TRIPLE:
                c=self.target3.value()
                if c in ids:c=next((q for q in range(self.n) if q not in ids),-1)
                if c<0:self.status.setText('Three distinct qubits required');return
                ids=(row,b,c)
        # Reject overlapping operations within a parallel column.
        for (r,c),gate in self.gates.items():
            if c==col and (r,c)!=(row,col) and set(gate.targets)&set(ids):
                self.status.setText('Qubit collision in column; choose another column');return
        self.snapshot()
        self.active_example=None
        self.gates[(row,col)]=Gate(name,ids,math.radians(self.angle.value()) if name in ('RX','RY','RZ','P','U') else 0.0,math.radians(self.phi.value()) if name=='U' else 0.0,math.radians(self.lam.value()) if name=='U' else 0.0)
        self._sync_columns()
        self.refresh()
    def cell_click(self,r,c):
        # Click selects; never place or replace a gate.
        return
    def remove_at(self,pos):
        idx=self.grid.indexAt(pos)
        if idx.isValid():
            self.snapshot();self.active_example=None;self.gates.pop((idx.row(),idx.column()),None);self.measurements.pop(idx.row(),None) if self.measurements.get(idx.row())==idx.column() else None;self._sync_columns();self.refresh()
    def ordered(self):
        return [g for (r,c),g in sorted(self.gates.items(),key=lambda x:(x[0][1],x[0][0]))]
    def refresh(self):
        saved_offset=self.grid.horizontalScrollBar().value()
        self.grid.clearContents()
        self.grid.viewport().update()
        for row,col in self.measurements.items():
            item=QTableWidgetItem('');item.setToolTip('Terminal measurement on q'+str(row));self.grid.setItem(row,col,item)
        for (r,c),g in self.gates.items():
            title=g.name + (('→'+','.join('q'+str(q) for q in g.targets[1:])) if len(g.targets)>1 else '')
            if g.name in ('RX','RY','RZ','P','U'):title+=f'({math.degrees(g.angle):g}°)' 
            item=QTableWidgetItem('');item.setToolTip(title);item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid.setItem(r,c,item)
        try:
            # One state per occupied *column*, including simultaneous disjoint gates.
            self.column_ops={}
            for (r,c),g in sorted(self.gates.items(),key=lambda item:(item[0][1],item[0][0])):
                self.column_ops.setdefault(c,[]).append(g)
            self.occupied_columns=sorted(self.column_ops)
            self.states=evolution(self.n,[g for c in self.occupied_columns for g in self.column_ops[c]])
            from quantumscope.physics.circuits import zero,apply_gate
            state=zero(self.n);self.column_states=[state]
            for c in self.occupied_columns:
                for g in self.column_ops[c]:state=apply_gate(state,self.n,g)
                self.column_states.append(state)
        except Exception as exc:self.status.setText(str(exc));return
        last=max(self.occupied_columns,default=-1)
        self.step.setRange(0,last+1)
        self.step.setValue(last+1)
        self.show_step(self.step.value())
        self.grid.horizontalScrollBar().setValue(saved_offset)
        self.status.setText(f'{self.n} qubits • {len(self.gates)} gates • {len(self.occupied_columns)} occupied columns • exact ideal simulation')
    def _sync_timeline(self):
        self.inline_blochs.update()
    def toggle_play(self):
        if self._play_timer.isActive():self._play_timer.stop();self.play_button.setText('▶ Play')
        else:
            if self.step.value()>=self.step.maximum():self.step.setValue(0)
            self._play_timer.start(self.speed.value());self.play_button.setText('Ⅱ Pause')
    def _advance(self):
        if self.step.value()>=self.step.maximum():self.toggle_play()
        else:self.step.setValue(self.step.value()+1)
    def show_step(self,k):
        if not hasattr(self,'column_states'):return
        completed=sum(1 for c in self.occupied_columns if c<k)
        state=self.column_states[completed]
        self.step_label.setText(f'Column {k}/{self.step.maximum()}  •  {completed} occupied layers executed')
        # Do not pan as a side effect of stepping, placement, or refresh.
        for col in range(self.grid.columnCount()):
            self.grid.horizontalHeaderItem(col).setBackground(QColor('#1c6987' if col==k-1 else '#223648' if col<k-1 else '#29313c'))
        vectors=[bloch(state,self.n,q) for q in range(self.n)]
        self.inline_blochs.set_vectors(vectors);self.blochs.set_vectors(vectors)
        self.bars.set_data(state,self.n)
        self.bars.title='Full quantum-state probabilities (before measurement) · cyan: theory'
        probs=distribution(state);inds=np.argsort(probs)[-8:][::-1]
        self.result.setPlainText('At column '+str(k)+':  '+'  '.join(f'|{i:0{self.n}b}⟩ {probs[i]*100:.1f}%' for i in inds if probs[i]>1e-8))
    def _temporary_item(self,col):
        item=self.grid.item(0,col)
        if item is None:item=QTableWidgetItem('');self.grid.setItem(0,col,item)
        return item
    def measure(self):
        counts=sample(self.states[-1],self.shots.value())
        measured=sorted(self.measurements)
        if measured:
            theoretical,marginal=measurement_marginal(distribution(self.states[-1]),self.n,measured,counts)
            self.bars.set_probabilities(theoretical,len(measured),marginal)
            self.bars.title='Measured '+', '.join('q'+str(q) for q in measured)+' · cyan: theory · orange: shots'
            self.bars.update()
            detail='   '.join(f'|{i:0{len(measured)}b}⟩ {int(amount)}' for i,amount in enumerate(marginal) if amount)
            self.result.setPlainText('Measured classical outcomes ('+', '.join('q'+str(q) for q in measured)+'):\n'+detail+'\nFull quantum state remains available in the simulation step view (before measurement).')
        else:
            self.bars.set_data(self.states[-1],self.n,counts)
            self.bars.title='All-qubit diagnostic sampling (no M gates) · cyan: theory · orange: shots'
            self.bars.update()
            ids=np.argsort(counts)[-12:][::-1]
            self.result.setPlainText('No M gates: diagnostic sampling of all qubits, not circuit measurement.\n'+'   '.join(f'|{i:0{self.n}b}⟩ {counts[i]}' for i in ids if counts[i]))
    def load_example(self,index):
        if index==0:return
        choice=self.examples.itemText(index)
        if choice=='Bell pair':n,ops=2,[Gate('H',(0,)),Gate('CX',(0,1))]
        elif choice=='GHZ':n,ops=3,[Gate('H',(0,)),Gate('CX',(0,1)),Gate('CX',(1,2))]
        elif choice=='Half adder (a=1,b=1)':
            n,ops=3,[Gate('X',(0,)),Gate('X',(1,)),Gate('CCX',(0,1,2)),Gate('CX',(0,1))]
        elif choice=='Half subtractor (a=1,b=1)':
            # Difference in q1 = a xor b, borrow in q2 = not(a) and b.
            n,ops=3,[Gate('X',(0,)),Gate('X',(1,)),Gate('X',(0,)),Gate('CCX',(0,1,2)),Gate('X',(0,)),Gate('CX',(0,1))]
        else:
            # Input a=01 in q0,q1 and b=01 in q2,q3.
            # Reversible 2-bit sum, q4/q5 are carry work bits.
            n,ops=6,[Gate('X',(1,)),Gate('X',(3,)),Gate('CCX',(1,3,4)),Gate('CX',(3,1)),Gate('CCX',(0,2,5)),Gate('CX',(0,2)),Gate('CCX',(2,4,5)),Gate('CX',(4,2))]
        self.set_circuit(n,ops)
        self.active_example=choice
        self.verify_circuit()
        self.status.setText('Loaded '+choice+' • illustrative reversible circuit; input bits and work registers shown as gates.')
        self.examples.blockSignals(True);self.examples.setCurrentIndex(0);self.examples.blockSignals(False)
    def set_circuit(self,n,ops):
        from quantumscope.physics.circuit_files import validate
        validate(n,ops)
        self.snapshot()
        self.active_example=None
        self._restoring=True
        self.n=n
        self.qubits.blockSignals(True);self.qubits.setValue(n);self.qubits.blockSignals(False)
        self.target.setRange(0,n-1);self.target3.setRange(0,n-1)
        self.columns=max(2,len(ops)+1)
        self.grid.setRowCount(n)
        self.grid.setVerticalHeaderLabels([f'q{i} ─' for i in range(n)])
        self.grid.setColumnCount(self.columns)
        self.grid.setHorizontalHeaderLabels([str(i+1) for i in range(self.columns)])
        self.gates={(g.targets[0],i):g for i,g in enumerate(ops)}
        self.measurements={}
        self._sync_columns()
        self._restoring=False
        self.grid.horizontalScrollBar().setValue(0)
        self.refresh()
    def verify_circuit(self):
        if self.active_example and self.active_example.startswith(('Half adder','Half subtractor','2-bit ripple-carry')):
            rows,note=verify_example(self.active_example,self.n,self.ordered())
        else:
            rows,note=inspect_basis(self.n,self.ordered())
        self.verify_table.setRowCount(len(rows))
        for i,row in enumerate(rows):
            values=(row.input_label,row.output_label,row.expected_label,
                    f'{row.probability*100:.1f}%  ' + ('PASS' if row.passed else 'FAIL' if row.passed is False else 'inspection'))
            for j,value in enumerate(values):
                item=QTableWidgetItem(value)
                if row.passed is not None:
                    item.setForeground(QColor('#77e6a1' if row.passed else '#ff8d87'))
                self.verify_table.setItem(i,j,item)
        self.verify_status.setText(note + (f'  {sum(r.passed is True for r in rows)}/{len(rows)} PASS' if rows and rows[0].passed is not None else ''))

    def load_native(self):
        path,_=QFileDialog.getOpenFileName(self,'Open QuantumScope circuit','','QuantumScope (*.qscope)')
        if not path:return
        try:
            with open(path,encoding='utf-8') as f:n,ops,ms=from_native_measured(f.read())
            self.set_circuit(n,ops);self.measurements={q:max((c for _,c in self.gates),default=-1)+1 for q in ms};self._expand_columns(max(self.measurements.values(),default=0));self.refresh();self.current_path=path
        except (OSError,ValueError) as exc:QMessageBox.warning(self,'Native import failed',str(exc))
    def save_native(self):
        path,_=QFileDialog.getSaveFileName(self,'Save QuantumScope circuit',self.current_path or 'untitled.qscope','QuantumScope (*.qscope)')
        if not path:return
        if not path.lower().endswith('.qscope'):path+='.qscope'
        self.current_path=path
        try:
            with open(path,'w',encoding='utf-8') as f:f.write(to_native_measured(self.n,self.ordered(),sorted(self.measurements)))
        except (OSError,ValueError) as exc:QMessageBox.warning(self,'Save failed',str(exc))
    def load_qasm(self):
        path,_=QFileDialog.getOpenFileName(self,'Open OpenQASM 2 file','','OpenQASM 2 (*.qasm *.qasm2);;Text files (*.txt)')
        if not path:return
        try:
            with open(path,encoding='utf-8') as f:n,ops,ms=from_qasm_measured(f.read())
            self.set_circuit(n,ops);self.measurements={q:max((c for _,c in self.gates),default=-1)+1 for q in ms};self._expand_columns(max(self.measurements.values(),default=0));self.refresh()
        except (OSError,ValueError) as exc:QMessageBox.warning(self,'QASM import rejected',str(exc))
    def export_qasm(self):
        path,_=QFileDialog.getSaveFileName(self,'Export OpenQASM 2','untitled.qasm','OpenQASM 2 (*.qasm *.qasm2)')
        if not path:return
        if not path.lower().endswith(('.qasm','.qasm2')):path+='.qasm'
        lines=to_qasm_measured(self.n,self.ordered(),sorted(self.measurements))
        try:
            with open(path,'w',encoding='utf-8') as f:f.write(lines)
        except OSError as exc:QMessageBox.warning(self,'Export failed',str(exc))
