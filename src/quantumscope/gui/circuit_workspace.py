"""Interactive gate circuit editor and exact simulator."""
import math
import html
import numpy as np
from PySide6.QtCore import Qt, QMimeData, QPoint, QEvent, QTimer, QRectF, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QDrag, QFont, QBrush, QWheelEvent, QPdfWriter, QPageSize
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QSplitter,
    QLabel, QPushButton, QListWidget, QTableWidget, QTableWidgetItem, QSpinBox,
    QSlider, QTextEdit, QFileDialog, QMessageBox, QAbstractItemView, QComboBox, QScrollArea, QCheckBox, QInputDialog, QMenu, QGroupBox, QToolButton, QSizePolicy, QDialog, QDialogButtonBox, QLineEdit, QTabWidget, QApplication)
from quantumscope.physics.circuit_files import to_native,from_native,to_qasm, to_native_measured, from_native_measured, to_qasm_measured, from_qasm_measured, from_native_layout, from_qasm_layout
from quantumscope.physics.circuit_layout import pack_and_order
from quantumscope.gui.theme import canvas_color
from quantumscope.editor.circuit_model import CircuitModel, EditorError
from quantumscope.physics.initial_states import InitialState, PRESETS, PRESET_ORDER
from quantumscope.physics.gate_education import angle_text
from quantumscope.physics.circuit_examples import EXAMPLE_NAMES, example_circuit, has_specification
from quantumscope.physics.circuit_verification import verify_example, inspect_basis
from quantumscope.physics.gate_education import parse_angle, gate_information, transformation_rows
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
        # Editing is exclusively through the gate parameter dialog, never the Qt cell editor.
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._pan_origin=None
        self._move_origin=None
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
        p.setPen(QPen(canvas_color('wire'), 1.7))
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
                p.setPen(QPen(canvas_color('connector'),2.4))
                p.drawLine(x,min(ys),x,max(ys))
                # A control dot and standard targets, including multi-controlled gates.
                if g.name in ('CX','CZ','CCX','CSWAP'):
                    controls=g.targets[:-1] if g.name in ('CX','CZ','CCX') else g.targets[:1]
                    for q in controls:
                        cy=self.visualRect(self.model().index(q,col)).center().y()
                        p.setPen(Qt.PenStyle.NoPen);p.setBrush(canvas_color('control'))
                        p.drawEllipse(QPoint(x,cy),5,5)
            p.setBrush(canvas_color('gate_fill'))
            p.setPen(QPen(canvas_color('target_stroke'),1.9))
            box=cell.adjusted(9,6,-9,-6)
            if g.name in ('CX','CCX'):
                target=g.targets[-1]
                cy=self.visualRect(self.model().index(target,col)).center().y()
                p.setBrush(canvas_color('target_fill'));p.drawEllipse(QPoint(x,cy),12,12)
                p.drawLine(x-8,cy,x+8,cy);p.drawLine(x,cy-8,x,cy+8)
            elif g.name=='SWAP' or g.name=='CSWAP':
                for q in (g.targets if g.name=='SWAP' else g.targets[1:]):
                    cy=self.visualRect(self.model().index(q,col)).center().y()
                    p.drawLine(x-7,cy-7,x+7,cy+7);p.drawLine(x-7,cy+7,x+7,cy-7)
            elif g.name=='CZ':
                cy=self.visualRect(self.model().index(g.targets[-1],col)).center().y()
                p.setBrush(canvas_color('control'));p.setPen(Qt.PenStyle.NoPen);p.drawEllipse(QPoint(x,cy),5,5)
            else:
                p.setPen(QPen(canvas_color('gate_border'),1.7))
                p.setBrush(canvas_color('gate_fill'));p.drawRoundedRect(box,5,5)
                p.setPen(canvas_color('gate_text'))
                p.setFont(QFont('Sans',10,QFont.Weight.DemiBold))
                p.drawText(box,Qt.AlignmentFlag.AlignCenter,g.name)
        # Draw incomplete multi-qubit placement as a preview, not a committed gate.
        pending = getattr(self.owner, '_pending_gate', None)
        if pending:
            name, col, ids = pending
            if 0 <= col < self.columnCount() and ids:
                anchor = self.visualRect(self.model().index(ids[0], col))
                if anchor.isValid():
                    x = anchor.center().x()
                    ys = [self.visualRect(self.model().index(q,col)).center().y() for q in ids]
                    p.setPen(QPen(canvas_color('preview_line'), 2, Qt.PenStyle.DashLine))
                    if len(ys)>1:p.drawLine(x,min(ys),x,max(ys))
                    for i,q in enumerate(ids):
                        cy = ys[i]
                        p.setBrush(canvas_color('preview_fill'))
                        p.setPen(QPen(canvas_color('preview_stroke'), 2))
                        if (name in ('CX','CCX') and i == 0):
                            p.drawEllipse(QPoint(x,cy),11,11)
                            p.drawLine(x-7,cy,x+7,cy);p.drawLine(x,cy-7,x,cy+7)
                        elif name in ('SWAP','CSWAP') and (name=='SWAP' or i<=1):
                            p.drawLine(x-8,cy-8,x+8,cy+8);p.drawLine(x-8,cy+8,x+8,cy-8)
                        else:
                            p.drawEllipse(QPoint(x,cy),5,5)
                    p.setPen(canvas_color('preview_text'))
                    p.drawText(anchor.adjusted(12,-22,60,-8),Qt.AlignmentFlag.AlignLeft, f'{name} preview')
        # Terminal measurement indicators are annotations, not unitary gates.
        for row,col in getattr(self.owner,'measurements',{}).items():
            if row>=rows or col>=self.columnCount(): continue
            cell=self.visualRect(self.model().index(row,col))
            if cell.isValid() and cell.right()>=0 and cell.left()<=rect.width():
                box=cell.adjusted(9,6,-9,-6)
                p.setPen(QPen(canvas_color('measure_border'),2));p.setBrush(canvas_color('measure_fill'))
                p.drawRoundedRect(box,5,5)
                p.setPen(canvas_color('measure_text'));p.setFont(QFont('Sans',11,QFont.Weight.Bold))
                p.drawText(box,Qt.AlignmentFlag.AlignCenter,'M')
        p.end()

    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.MiddleButton or (event.button()==Qt.MouseButton.LeftButton and event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self._pan_origin=event.position().toPoint();self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor);event.accept();return
        if event.button()==Qt.MouseButton.LeftButton:
            idx=self.indexAt(event.position().toPoint())
            self._move_origin=(idx.row(),idx.column(),event.position().toPoint()) if idx.isValid() and self.owner.operation_at(idx.row(),idx.column()) else None
        super().mousePressEvent(event)
    def mouseMoveEvent(self,event):
        if self._pan_origin is not None:
            point=event.position().toPoint();delta=point-self._pan_origin;self._pan_origin=point
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value()-delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value()-delta.y())
            event.accept();return
        if self._move_origin is not None and (event.buttons() & Qt.MouseButton.LeftButton):
            row,col,origin=self._move_origin
            if (event.position().toPoint()-origin).manhattanLength()>=QApplication.startDragDistance():
                self._move_origin=None
                operation=self.owner.operation_at(row,col)
                if operation:
                    drag=QDrag(self)
                    mime=QMimeData();mime.setText(f'QS_MOVE:{row}:{col}')
                    drag.setMimeData(mime)
                    drag.exec(Qt.DropAction.MoveAction)
                    event.accept();return
        super().mouseMoveEvent(event)
    def mouseReleaseEvent(self,event):
        if self._pan_origin is not None:
            self._pan_origin=None;self.viewport().unsetCursor();event.accept();return
        self._move_origin=None
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
        # Fit the circuit when practical while retaining legible gates on long circuits.
        # For longer circuits the viewport shows a readable subset; users pan to the rest.
        occupied=max((c for _,c in self.owner.gates),default=0)+2
        occupied=max(2,occupied)
        width=max(64,min(115,self.viewport().width()//occupied))
        height=max(45,min(78,self.viewport().height()//max(1,self.owner.n)))
        self.horizontalHeader().setDefaultSectionSize(width)
        self.verticalHeader().setDefaultSectionSize(height)
        self._zoom=width/82
        self.owner.inline_blochs.update()

    def reset_zoom(self):
        self._zoom=1.0
        self.horizontalHeader().setDefaultSectionSize(82)
        self.verticalHeader().setDefaultSectionSize(54)
        self.owner.inline_blochs.update()

    def eventFilter(self,obj,event):
        if obj is self.viewport() and event.type() in (QEvent.Type.DragEnter,QEvent.Type.DragMove,QEvent.Type.Drop):
            if event.mimeData().text().startswith(('QS_GATE:', 'QS_MOVE:')):
                if event.type()==QEvent.Type.Drop:
                    idx=self.indexAt(event.position().toPoint())
                    if idx.isValid():self._handle_drop(event.mimeData().text(),idx.row(),idx.column())
                event.acceptProposedAction()
                return True
        return super().eventFilter(obj,event)
    def dragEnterEvent(self,event):
        if event.mimeData().text().startswith(('QS_GATE:', 'QS_MOVE:')):event.acceptProposedAction()
        else:super().dragEnterEvent(event)
    def dragMoveEvent(self,event):
        if event.mimeData().text().startswith(('QS_GATE:', 'QS_MOVE:')):event.acceptProposedAction()
        else:super().dragMoveEvent(event)
    def dropEvent(self,event):
        txt=event.mimeData().text()
        if txt.startswith(('QS_GATE:', 'QS_MOVE:')):
            idx=self.indexAt(event.position().toPoint())
            if idx.isValid():self._handle_drop(txt,idx.row(),idx.column())
            event.acceptProposedAction()
        else:super().dropEvent(event)

    def _handle_drop(self, text, row, col):
        if text.startswith('QS_MOVE:'):
            _, r, c = text.split(':')
            self.owner.move_operation(int(r),int(c),row,col)
        elif text.startswith('QS_GATE:'):
            self.owner.place(text.split(':',1)[1],row,col)


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
            p.setPen(QPen(canvas_color('bloch_outline'),1.4));p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPoint(int(cx),int(cy)),int(radius),int(radius))
            p.drawEllipse(int(cx-radius),int(cy-radius*.29),int(2*radius),int(radius*.58))
            p.setPen(QPen(canvas_color('bloch_axis'),1));p.drawLine(int(cx-radius),int(cy),int(cx+radius),int(cy))
            p.drawLine(int(cx),int(cy-radius),int(cx),int(cy+radius))
            # Fixed isometric camera: x to right, y to upper-right, z vertical.
            endx=cx+radius*(.87*x+.34*y);endy=cy-radius*(z+.28*y)
            p.setPen(QPen(canvas_color('bloch_vector'),3));p.drawLine(int(cx),int(cy),int(endx),int(endy))
            p.setBrush(canvas_color('bloch_vector'));p.drawEllipse(QPoint(int(endx),int(endy)),4,4)
            p.setPen(canvas_color('bloch_text'));p.drawText(int(cx-radius),int(cy+radius+12),int(2*radius),18,
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
            p.setPen(QPen(canvas_color('bloch_outline'),1));p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPoint(cx,int(ymid)),r,r)
            p.drawEllipse(cx-r,int(ymid-5),r*2,10)
            p.setPen(QPen(canvas_color('bloch_vector'),2.5))
            p.drawLine(cx,int(ymid),int(cx+r*(.85*x+.25*y)),int(ymid-r*(z+.25*y)))
            p.setPen(canvas_color('bloch_text'));p.setFont(QFont('Sans',8))
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
        ink = canvas_color('chart_text')
        p.setFont(QFont('Sans',9));p.setPen(ink)
        p.drawText(12,16,self.title)
        left,right,top,bottom=48,12,34,37
        pw=max(1,w-left-right);ph=max(1,h-top-bottom)
        p.setPen(QPen(canvas_color('chart_axis'),1));p.drawLine(left,top,left,top+ph);p.drawLine(left,top+ph,left+pw,top+ph)
        p.drawText(6,top+10,'100%');p.drawText(16,top+ph,'0%')
        gap=pw/max(1,len(self.theory))
        for i,(name,val) in enumerate(self.theory):
            center=left+(i+.5)*gap
            bw=max(3,min(20,gap*.30))
            p.fillRect(int(center-bw-1),int(top+ph*(1-val)),int(bw),max(1,int(ph*val)),canvas_color('chart_theory'))
            if self.counts is not None:
                v=self.counts[name]
                p.fillRect(int(center+1),int(top+ph*(1-v)),int(bw),max(1,int(ph*v)),canvas_color('chart_sampled'))
            p.setPen(ink)
            text=name if len(name)<=5 else (name[:3]+'…'+name[-2:])
            p.drawText(int(center-gap*.46),top+ph+5,int(gap*.92),17,Qt.AlignmentFlag.AlignCenter,text)
            p.drawText(int(center-gap*.46),max(top+2,int(top+ph*(1-max(val,self.counts[name] if self.counts is not None else 0))-18)),int(gap*.92),15,Qt.AlignmentFlag.AlignCenter,f'{val*100:.0f}%')
        p.end()

class CircuitWorkspace(QWidget):
    # Emitted whenever the displayed state changes (edit, step, initial state).
    state_changed=Signal()

    def __init__(self,parent=None):
        super().__init__(parent);self.model=CircuitModel(3);self.current_path=None;self._inspector=None;self._play_timer=QTimer(self);self._play_timer.timeout.connect(self._advance)
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
        self.rotation_label=QLabel('New gate angle (°)');top.addWidget(self.rotation_label)
        self.angle=QSpinBox();self.angle.setRange(-360,360);self.angle.setValue(90);top.addWidget(self.angle)
        self.phi=QSpinBox();self.phi.setRange(-360,360);self.phi.setValue(0);self.phi.setPrefix('φ ');self.phi.setToolTip('U gate phase φ in degrees');top.addWidget(self.phi)
        self.lam=QSpinBox();self.lam.setRange(-360,360);self.lam.setValue(0);self.lam.setPrefix('λ ');self.lam.setToolTip('U gate phase λ in degrees');top.addWidget(self.lam)
        self.second_label=QLabel('Target');top.addWidget(self.second_label)
        self.target=QSpinBox();self.target.setRange(0,self.n-1);top.addWidget(self.target)
        self.third_label=QLabel('Target (third qubit)')
        self.target3=QSpinBox();self.target3.setRange(0,self.n-1);self.target3.setValue(2);self.target3.setToolTip('CCX: third qubit is the target; CSWAP: third qubit is the second swap operand.')
        top.addWidget(self.third_label);top.addWidget(self.target3)
        self.gate.currentTextChanged.connect(self._update_operand_labels)
        self.gate.hide()
        self.target.hide();self.target3.hide();self.second_label.hide();self.third_label.hide()
        self._update_operand_labels(self.gate.currentText())
        self.gate.hide();self.target.hide();self.target3.hide();self.second_label.hide();self.third_label.hide()
        for text,cb in [('Clear',self.clear),('Bell example',self.example),('Import QASM 2',self.load_qasm),('Export QASM',self.export_qasm),('Export PDF',self.export_pdf),('Open .qscope',self.load_native),('Save .qscope',self.save_native)]:
            btn=QPushButton(text);btn.clicked.connect(cb);top.addWidget(btn)
        edits=QHBoxLayout();outer.addLayout(edits)
        for text,cb in [('Undo',self.undo),('Redo',self.redo)]:
            button=QPushButton(text);button.clicked.connect(cb);edits.addWidget(button)
        self.inspector_button=QPushButton('State Inspector…')
        self.inspector_button.setToolTip('Open amplitudes, statevector, reduced density matrices and circuit statistics')
        self.inspector_button.clicked.connect(self.open_state_inspector);edits.addWidget(self.inspector_button)
        self.show_blochs=QCheckBox('Show Bloch spheres beside wires');self.show_blochs.setChecked(True);edits.addWidget(self.show_blochs)
        self.examples=QComboBox();self.examples.addItems(['Examples…',*EXAMPLE_NAMES]);self.examples.currentIndexChanged.connect(self.load_example);edits.addWidget(self.examples)
        edits.addStretch()
        split=QSplitter(Qt.Orientation.Horizontal)
        # A whole-page scroll area, not a shrinking circuit editor, handles
        # limited vertical space on Windows and older Ubuntu releases.
        outer.addWidget(split)
        self.palette=Palette();self.palette.addItems(list(ALL)+['M']);self.palette.setMinimumWidth(85);self.palette.setMaximumWidth(130)
        # Palette clicks only select palette entries; they never place or replace gates.
        self.palette.setToolTip('Drag to place a gate; double-click for the Gate Explorer')
        self.palette.itemDoubleClicked.connect(lambda item:self.show_gate_explorer(item.text()))
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
        self.grid.setToolTip('Drag gates onto empty cells; click to select. Middle-drag to pan, Ctrl+wheel to zoom.')
        nav=QHBoxLayout();v.addLayout(nav)
        for label,callback in [('− Zoom',lambda:self.grid.zoom_by(1/1.15)),('+ Zoom',lambda:self.grid.zoom_by(1.15)),('Fit Circuit',lambda:self.grid.fit_view()),('Reset Zoom',lambda:self.grid.reset_zoom())]:
            b=QPushButton(label);b.clicked.connect(callback);nav.addWidget(b)
        nav.addStretch()
        self.grid.horizontalHeader().sectionClicked.connect(lambda col:self.step.setValue(col+1))
        self.grid.verticalHeader().sectionClicked.connect(self._initial_state_menu)
        self.grid.verticalHeader().setToolTip('Click a qubit label to choose its initial state')
        self.grid.horizontalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.grid.horizontalHeader().customContextMenuRequested.connect(self.header_menu)
        wires=QHBoxLayout();v.addLayout(wires);wires.addWidget(self.grid,1)
        self.inline_blochs=InlineBlochs(self.grid);wires.addWidget(self.inline_blochs)
        self.show_blochs.toggled.connect(self.inline_blochs.setVisible)
        self.grid.verticalScrollBar().valueChanged.connect(lambda _:self.inline_blochs.update())
        helptext=QLabel('Drag a multi-qubit gate to its first operand, then click remaining qubits in the same column. Right-click to remove a gate. Up to 10 qubits; ideal statevector.')
        helptext.setWordWrap(True);v.addWidget(helptext)
        self.grid.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.grid.customContextMenuRequested.connect(self.gate_context_menu)
        self.grid.cellDoubleClicked.connect(self.edit_gate_at)
        self.grid.cellClicked.connect(self.cell_click)
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

    # ---- state lives in the Qt-free CircuitModel; these keep the widget API ----
    n=property(lambda self:self.model.n,lambda self,v:setattr(self.model,'n',v))
    gates=property(lambda self:self.model.gates,lambda self,v:setattr(self.model,'gates',v))
    measurements=property(lambda self:self.model.measurements,lambda self,v:setattr(self.model,'measurements',v))
    columns=property(lambda self:self.model.columns)
    _reserved_columns=property(lambda self:self.model.reserved_columns,lambda self,v:setattr(self.model,'reserved_columns',v))
    _pending_gate=property(lambda self:self.model.pending,lambda self,v:setattr(self.model,'pending',v))
    active_example=property(lambda self:self.model.active_example,lambda self,v:setattr(self.model,'active_example',v))
    _example_ops=property(lambda self:self.model.example_ops,lambda self,v:setattr(self.model,'example_ops',v))
    undo_stack=property(lambda self:self.model.undo_stack)
    redo_stack=property(lambda self:self.model.redo_stack)

    def _sync_view(self):
        """Match qubit controls, wires and columns to the model."""
        n=self.model.n
        if self.qubits.value()!=n:
            self.qubits.blockSignals(True);self.qubits.setValue(n);self.qubits.blockSignals(False)
        self.target.setRange(0,n-1);self.target3.setRange(0,n-1)
        if self.grid.rowCount()!=n:
            self.grid.setRowCount(n)
        self.grid.setVerticalHeaderLabels([f'q{i} {s.label} ─' for i,s in enumerate(self.model.initial_states)])
        needed=self.model.columns
        if needed!=self.grid.columnCount():
            offset=self.grid.horizontalScrollBar().value()
            self.grid.setColumnCount(needed)
            self.grid.setHorizontalHeaderLabels([str(i+1) for i in range(needed)])
            self.grid.horizontalScrollBar().setValue(offset)
    _sync_columns=_sync_view
    def _expand_columns(self,needed=None):self._sync_view()
    def _changed(self):
        self._sync_view();self.refresh()
    def _rejected(self,exc):
        self.status.setText(str(exc))

    def snapshot(self):self.model.snapshot()

    # ---- initial states ----------------------------------------------------------
    def set_initial_state(self,qubit,state):
        try:changed=self.model.set_initial_state(qubit,state)
        except EditorError as exc:self._rejected(exc);return
        if changed:self._changed()
    def _initial_state_menu(self,qubit):
        from PySide6.QtGui import QCursor
        if not 0<=qubit<self.model.n:return
        current=self.model.initial_states[qubit]
        menu=QMenu(self);menu.setToolTip('Initial state of q'+str(qubit))
        title=menu.addAction(f'Initial state of q{qubit}');title.setEnabled(False)
        actions={}
        for key in PRESET_ORDER:
            action=menu.addAction(PRESETS[key][2]);action.setCheckable(True)
            action.setChecked(current.preset_key==key);actions[action]=key
        menu.addSeparator()
        custom=menu.addAction('Custom (θ, φ)…');custom.setCheckable(True);custom.setChecked(current.preset_key is None)
        chosen=menu.exec(QCursor.pos())
        if chosen in actions:self.set_initial_state(qubit,InitialState.preset(actions[chosen]))
        elif chosen is custom:self._custom_initial_state(qubit)
    def _custom_initial_state(self,qubit):
        current=self.model.initial_states[qubit]
        dialog=QDialog(self);dialog.setWindowTitle(f'Custom initial state for q{qubit}')
        layout=QVBoxLayout(dialog)
        layout.addWidget(QLabel('|ψ⟩ = cos(θ/2)|0⟩ + e^{iφ} sin(θ/2)|1⟩      (θ from 0 to π, φ from 0 to 2π, in radians)'))
        form=QFormLayout();layout.addLayout(form)
        theta=QLineEdit(angle_text(current.theta) if current.theta else '0');phi=QLineEdit(angle_text(current.phi) if current.phi else '0')
        for field in (theta,phi):field.setToolTip('Radians. Examples: pi/3, 2*pi/3, 0.75')
        form.addRow('θ (polar angle)',theta);form.addRow('φ (phase)',phi)
        preview=BlochPanel();preview.setMinimumHeight(185);layout.addWidget(preview)
        info=QLabel();info.setWordWrap(True);layout.addWidget(info)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel);layout.addWidget(buttons)
        result={}
        def update():
            try:
                state=InitialState(parse_angle(theta.text()),parse_angle(phi.text()))
            except ValueError as exc:
                info.setText('⚠ '+str(exc));buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False);return
            result['state']=state
            x,y,z=state.bloch();preview.set_vectors([(x,y,z)])
            a,b=state.vector()
            from quantumscope.physics.gate_education import format_amplitude
            info.setText(f'{state.label}   amplitudes: |0⟩ {format_amplitude(a)},  |1⟩ {format_amplitude(b)}'
                         +('   (same as a preset)' if state.preset_key else ''))
            buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        theta.textChanged.connect(update);phi.textChanged.connect(update)
        buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject)
        update()
        if dialog.exec()==QDialog.DialogCode.Accepted and 'state' in result:
            self.set_initial_state(qubit,result['state'])

    # ---- State Inspector ------------------------------------------------------------
    def open_state_inspector(self):
        from quantumscope.gui.state_inspector import StateInspector
        if self._inspector is None:
            self._inspector=StateInspector(self)
        self._inspector.show();self._inspector.raise_();self._inspector.activateWindow()
        self._inspector.refresh()
    def inspected_view(self):
        """What the State Inspector shows: the state at the current step."""
        k=self.step.value()
        completed=sum(1 for c in getattr(self,'occupied_columns',[]) if c<k)
        states=getattr(self,'column_states',None) or [self.model.initial_vector()]
        return {'state':states[min(completed,len(states)-1)],'n':self.model.n,'step':k,
                'steps':self.step.maximum(),'layers_done':completed,'model':self.model}
    def undo(self):
        if self.model.undo():self._changed()
    def redo(self):
        if self.model.redo():self._changed()
    def resize_qubits(self,n):
        if self.model.removes_gates(n):
            choice=QMessageBox.question(self,'Remove qubits?',
                'Gates targeting removed qubits will be deleted. Continue?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if choice!=QMessageBox.StandardButton.Yes:
                self.qubits.blockSignals(True);self.qubits.setValue(self.model.n);self.qubits.blockSignals(False);return
        try:self.model.resize(n)
        except EditorError as exc:self._rejected(exc);return
        self._changed()
    def clear(self):self.model.clear();self._changed()
    def example(self):self.model.load_bell();self._changed()
    def operation_at(self,row,col):return self.model.operation_at(row,col)
    def move_operation(self,src_row,src_col,dst_row,dst_col):
        try:moved=self.model.move(src_row,src_col,dst_row,dst_col)
        except EditorError as exc:self._rejected(exc);return
        if moved:self._changed()
    def insert_column(self,index):
        if self.model.insert_column(index):self._changed()
    def delete_empty_column(self,index):
        try:deleted=self.model.delete_empty_column(index)
        except EditorError as exc:self._rejected(exc);return
        if deleted:self._changed()

    def header_menu(self,point):
        index=self.grid.horizontalHeader().logicalIndexAt(point)
        if index<0:return
        menu=QMenu(self)
        before=menu.addAction('Insert column before')
        after=menu.addAction('Insert column after')
        delete=menu.addAction('Delete column (if empty)')
        chosen=menu.exec(self.grid.horizontalHeader().mapToGlobal(point))
        if chosen is before:self.insert_column(index)
        elif chosen is after:self.insert_column(index+1)
        elif chosen is delete:self.delete_empty_column(index)

    def cancel_pending(self):
        self.model.cancel_pending()
        if hasattr(self,'status'):self.status.setText('Placement cancelled');self.grid.viewport().update()

    def keyPressEvent(self,event):
        if event.key()==Qt.Key.Key_Escape and self.model.pending:
            self.cancel_pending();event.accept();return
        super().keyPressEvent(event)

    def place(self,name,row,col,operands=None):
        try:
            result=self.model.place(name,row,col,operands,math.radians(self.angle.value()),
                                    math.radians(self.phi.value()),math.radians(self.lam.value()))
        except EditorError as exc:self._rejected(exc);return
        if isinstance(result,str):
            self.status.setText(result);self.grid.viewport().update();return
        if result:self._changed()
    def cell_click(self,r,c):
        if not self.model.pending:return
        try:result=self.model.add_operand(r,c)
        except EditorError as exc:
            self._rejected(exc);self.grid.viewport().update();return
        self.grid.viewport().update()
        if isinstance(result,str):self.status.setText(result);return
        if result:self._changed()

    def remove_at(self,pos):
        idx=self.grid.indexAt(pos)
        if idx.isValid() and self.model.remove(idx.row(),idx.column()):self._changed()
    def edit_gate_at(self,row,col):
        found=self.model.editable_gate(row,col)
        if found is None:
            return
        _,gate=found
        dialog=QDialog(self)
        dialog.setWindowTitle(f'Edit {gate.name} gate on q{gate.targets[0]}')
        layout=QFormLayout(dialog)
        edits={}
        params=[('angle','θ' if gate.name!='P' else 'λ')]
        if gate.name=='U':params.extend([('phi','φ'),('lam','λ')])
        for attr,label in params:
            field=QLineEdit(f'{getattr(gate,attr):.12g}')
            field.setToolTip('Angle in radians. Examples: pi/2, -pi/4, 2*pi')
            layout.addRow(f'{label} (radians)',field)
            edits[attr]=field
        layout.addRow(QLabel('Use pi, arithmetic, and parentheses; angles are in radians.'))
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addRow(buttons)
        buttons.rejected.connect(dialog.reject)
        def commit():
            try:
                values={key:parse_angle(field.text()) for key,field in edits.items()}
            except ValueError as exc:
                QMessageBox.warning(dialog,'Invalid gate parameter',str(exc));return
            self.model.edit_parameters(row,col,values['angle'],values.get('phi'),values.get('lam'))
            self._changed()
            dialog.accept()
        buttons.accepted.connect(commit)
        dialog.exec()

    def gate_context_menu(self,pos):
        idx=self.grid.indexAt(pos)
        if not idx.isValid():return
        row,col=idx.row(),idx.column()
        found=self.model.operation_at(row,col)
        if found is None:return
        menu=QMenu(self)
        if self.model.pending:
            cancel=menu.addAction('Cancel multi-qubit placement')
            if menu.exec(self.grid.viewport().mapToGlobal(pos)) is cancel:self.cancel_pending()
            return
        edit=menu.addAction('Edit parameters…') if self.model.editable_gate(row,col) else None
        delete=menu.addAction('Remove measurement' if found[0]=='measurement' else 'Remove gate')
        chosen=menu.exec(self.grid.viewport().mapToGlobal(pos))
        if chosen is edit and edit is not None:self.edit_gate_at(row,col)
        elif chosen is delete:self.remove_at(pos)

    def show_gate_explorer(self,name):
        from quantumscope.gui.gate_explorer import GateExplorer
        dlg=GateExplorer(name,self)
        dlg.exec()

    def export_pdf(self):
        path,_=QFileDialog.getSaveFileName(self,'Export circuit to PDF','circuit.pdf','PDF files (*.pdf)')
        if not path:return
        if not path.lower().endswith('.pdf'):path+='.pdf'
        report=(QMessageBox.question(self,'PDF export contents','Include a summary of the final state probabilities?',QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes)
        try:
            from quantumscope.gui.circuit_pdf import write_circuit_pdf
            write_circuit_pdf(path,self.n,self.gates,self.measurements,
                              include_report=report,initial_states=self.model.initial_states)
        except Exception as exc:
            QMessageBox.warning(self,'PDF export failed',str(exc))

    def ordered(self):
        return self.model.ordered()
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
            sim=self.model.simulate()
            self.occupied_columns,self.column_states,self.states=sim.occupied_columns,sim.column_states,sim.states
        except Exception as exc:self.status.setText(str(exc));return
        last=max(self.occupied_columns,default=-1)
        self.step.setRange(0,last+1)
        self.step.setValue(last+1)
        self.show_step(self.step.value())
        self.grid.horizontalScrollBar().setValue(saved_offset)
        self.status.setText(f'{self.n} qubits • {len(self.gates)} gates • {len(self.occupied_columns)} occupied columns • exact ideal simulation')
        if has_specification(self.active_example) and hasattr(self,'verify_table'):self.verify_circuit()
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
    def _color_header(self,k):
        for col in range(self.grid.columnCount()):
            item=self.grid.horizontalHeaderItem(col)
            if item is not None:
                item.setBackground(canvas_color('header_current' if col==k-1 else 'header_past' if col<k-1 else 'header_future'))
    def show_step(self,k):
        if not hasattr(self,'column_states'):return
        completed=sum(1 for c in self.occupied_columns if c<k)
        state=self.column_states[completed]
        self.step_label.setText(f'Column {k}/{self.step.maximum()}  •  {completed} occupied layers executed')
        # Do not pan as a side effect of stepping, placement, or refresh.
        self._color_header(k)
        vectors=[bloch(state,self.n,q) for q in range(self.n)]
        self.inline_blochs.set_vectors(vectors);self.blochs.set_vectors(vectors)
        self.bars.set_data(state,self.n)
        self.bars.title='Full quantum-state probabilities (before measurement) · cyan: theory'
        probs=distribution(state);inds=np.argsort(probs)[-8:][::-1]
        self.result.setPlainText('At column '+str(k)+':  '+'  '.join(f'|{i:0{self.n}b}⟩ {probs[i]*100:.1f}%' for i in inds if probs[i]>1e-8))
        self.state_changed.emit()
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
        self.model.load_example(choice)
        self._sync_view();self.grid.horizontalScrollBar().setValue(0);self.refresh()
        self.verify_circuit()
        self.status.setText('Loaded '+choice+' • illustrative reversible circuit; input bits and work registers shown as gates.'
            +(' Edits are checked against this example’s specification.' if has_specification(choice) else ''))
        self.examples.blockSignals(True);self.examples.setCurrentIndex(0);self.examples.blockSignals(False)
    def set_circuit(self,n,ops,columns=None,measured=(),measurement_column=None,total_columns=None,initial_states=None):
        """Load a circuit. Without stored columns, gates are packed so that
        simultaneous gates share a column (simulation order is unchanged)."""
        self.model.set_circuit(n,ops,columns,measured,measurement_column,total_columns,initial_states)
        self._sync_view();self.grid.horizontalScrollBar().setValue(0);self.refresh()
    def _layout(self):
        """Gates in simulation order with their columns, for saving."""
        gates,columns,_,_=self.model.layout()
        return gates,columns
    def apply_theme(self):
        """Recolor theme-dependent content after an appearance change."""
        for r in range(self.verify_table.rowCount()):
            for c in range(self.verify_table.columnCount()):
                item=self.verify_table.item(r,c)
                if item is not None and item.data(Qt.ItemDataRole.UserRole) is not None:
                    item.setForeground(canvas_color('pass' if item.data(Qt.ItemDataRole.UserRole) else 'fail'))
        self._color_header(self.step.value())
        for widget in (self.grid.viewport(),self.inline_blochs,self.blochs,self.bars):
            widget.update()
        if self._inspector is not None:self._inspector.apply_theme()
    def _show_notes(self,title,notes):
        if notes:QMessageBox.information(self,title,'\n\n'.join(notes))
    def verify_circuit(self):
        rows,note=self.model.verification()
        self.verify_table.setRowCount(len(rows))
        for i,row in enumerate(rows):
            values=(row.input_label,row.output_label,row.expected_label,
                    f'{row.probability*100:.1f}%  ' + ('PASS' if row.passed else 'FAIL' if row.passed is False else 'inspection'))
            for j,value in enumerate(values):
                item=QTableWidgetItem(value)
                if row.passed is not None:
                    item.setData(Qt.ItemDataRole.UserRole,bool(row.passed))
                    item.setForeground(canvas_color('pass' if row.passed else 'fail'))
                self.verify_table.setItem(i,j,item)
        self.verify_status.setText(note + (f'  {sum(r.passed is True for r in rows)}/{len(rows)} PASS' if rows and rows[0].passed is not None else ''))

    def load_native(self):
        path,_=QFileDialog.getOpenFileName(self,'Open QuantumScope circuit','','QuantumScope (*.qscope)')
        if not path:return
        try:
            with open(path,encoding='utf-8') as f:n,ops,ms,layout=from_native_layout(f.read())
            self.set_circuit(n,ops,layout['columns'],ms,layout['measurement_column'],layout['total_columns'],layout['initial_states']);self.current_path=path
        except (OSError,ValueError) as exc:QMessageBox.warning(self,'Native import failed',str(exc))
    def save_native(self):
        path,_=QFileDialog.getSaveFileName(self,'Save QuantumScope circuit',self.current_path or 'untitled.qscope','QuantumScope (*.qscope)')
        if not path:return
        if not path.lower().endswith('.qscope'):path+='.qscope'
        self.current_path=path
        try:
            gates,columns,mcol,total=self.model.layout()
            layout={'columns':columns,'measurement_column':mcol,'total_columns':total,'initial_states':self.model.initial_states}
            with open(path,'w',encoding='utf-8') as f:f.write(to_native_measured(self.n,gates,sorted(self.measurements),layout=layout))
        except (OSError,ValueError) as exc:QMessageBox.warning(self,'Save failed',str(exc))
    def load_qasm(self):
        path,_=QFileDialog.getOpenFileName(self,'Open OpenQASM 2 file','','OpenQASM 2 (*.qasm *.qasm2);;Text files (*.txt)')
        if not path:return
        try:
            with open(path,encoding='utf-8') as f:n,ops,ms,layout,notes=from_qasm_layout(f.read())
            self.set_circuit(n,ops,layout['columns'],ms,layout['measurement_column'])
            self._show_notes('QASM import notes',notes)
        except (OSError,ValueError) as exc:QMessageBox.warning(self,'QASM import rejected',str(exc))
    def export_qasm(self):
        path,_=QFileDialog.getSaveFileName(self,'Export OpenQASM 2','untitled.qasm','OpenQASM 2 (*.qasm *.qasm2)')
        if not path:return
        if not path.lower().endswith(('.qasm','.qasm2')):path+='.qasm'
        lines=to_qasm_measured(self.n,self.ordered(),sorted(self.measurements),self.model.initial_states)
        try:
            with open(path,'w',encoding='utf-8') as f:f.write(lines)
        except OSError as exc:QMessageBox.warning(self,'Export failed',str(exc))
