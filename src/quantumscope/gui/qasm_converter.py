"""Dedicated OpenQASM 2 / QuantumScope native converter."""
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QTextEdit,QFileDialog,QComboBox,QMessageBox
from quantumscope.physics.circuit_files import convert,from_native_layout,from_qasm_layout

class QasmConverter(QWidget):
    def __init__(self,open_in_editor=None,parent=None):
        super().__init__(parent);self.open_in_editor=open_in_editor;self.source_path=None
        layout=QVBoxLayout(self)
        title=QLabel('QASM CONVERTER  ·  OpenQASM 2 unitary subset ↔ .qscope v1');layout.addWidget(title)
        row=QHBoxLayout();layout.addLayout(row)
        self.direction=QComboBox();self.direction.addItems(['QASM → .qscope','.qscope → QASM']);row.addWidget(self.direction)
        for name,fn in [('Load source',self.load),('Convert',self.transform),('Save output',self.save),('Open in circuit editor',self.open_editor)]:
            b=QPushButton(name);b.clicked.connect(fn);row.addWidget(b)
        self.source=QTextEdit();self.source.setPlaceholderText('Paste OpenQASM 2 source here');layout.addWidget(QLabel('SOURCE'));layout.addWidget(self.source,1)
        self.output=QTextEdit();self.output.setReadOnly(True);layout.addWidget(QLabel('CONVERTED OUTPUT'));layout.addWidget(self.output,1)
        self.status=QLabel('Unitary gates and terminal q[i] → c[i] measurements supported; mid-circuit measurements are rejected.');self.status.setWordWrap(True);layout.addWidget(self.status)
        self.direction.currentIndexChanged.connect(lambda _:self.output.clear())
    def load(self):
        ext='OpenQASM 2 (*.qasm *.qasm2);;Text (*.txt)' if self.direction.currentIndex()==0 else 'QuantumScope (*.qscope)'
        path,_=QFileDialog.getOpenFileName(self,'Load circuit','',ext)
        if path:
            self.source_path=path
            try:
                with open(path,encoding='utf-8') as f:self.source.setPlainText(f.read())
            except OSError as exc:QMessageBox.warning(self,'Load failed',str(exc))
    def transform(self):
        self.output.clear()
        try:
            notes=[]
            result=convert(self.source.toPlainText(),'qasm' if self.direction.currentIndex()==0 else 'qscope',notes)
            self.output.setPlainText(result)
            self.status.setText('Converted successfully. Executable circuit operations preserved.'+(' Note: '+' '.join(notes) if notes else ''))
        except ValueError as exc:self.status.setText('Conversion rejected: '+str(exc))
    def save(self):
        if not self.output.toPlainText():self.status.setText('Convert first before saving.');return
        ext='QuantumScope (*.qscope)' if self.direction.currentIndex()==0 else 'OpenQASM 2 (*.qasm *.qasm2)'
        from pathlib import Path
        basename=Path(self.source_path).stem if self.source_path else 'untitled'
        suffix='.qscope' if self.direction.currentIndex()==0 else '.qasm'
        path,_=QFileDialog.getSaveFileName(self,'Save converted circuit',basename+suffix,ext)
        if path:
            if not path.lower().endswith(('.qscope',) if self.direction.currentIndex()==0 else ('.qasm','.qasm2')):path+=suffix
            try:
                with open(path,'w',encoding='utf-8') as f:f.write(self.output.toPlainText())
            except OSError as exc:QMessageBox.warning(self,'Save failed',str(exc))
    def open_editor(self):
        if not self.output.toPlainText():self.transform()
        if not self.output.toPlainText():return
        try:
            if self.direction.currentIndex()==0:n,gates,measured,layout=from_native_layout(self.output.toPlainText())
            else:n,gates,measured,layout,_=from_qasm_layout(self.output.toPlainText())
            if self.open_in_editor:self.open_in_editor(n,gates,measured,layout)
        except ValueError as exc:self.status.setText(str(exc))
