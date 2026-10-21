"""Educational reference dialog for the existing gate palette."""
import math
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog,QVBoxLayout,QLabel,QTabWidget,QWidget,QTextBrowser,QTableWidget,QTableWidgetItem,QHBoxLayout,QDoubleSpinBox,QPushButton
from quantumscope.physics.gate_education import gate_information,transformation_rows
from quantumscope.physics.circuits import Gate,unitary,SINGLE

class GateExplorer(QDialog):
    def __init__(self,name,parent=None):
        super().__init__(parent)
        self.name=name.upper();self.info=gate_information(name)
        self.setWindowTitle(f'Quantum Gate Explorer — {self.name}')
        self.resize(720,550)
        body=QVBoxLayout(self)
        head=QLabel(f'{self.info["title"]} ({self.name})')
        head.setStyleSheet('font-size:19px;font-weight:bold;')
        body.addWidget(head)
        self.tabs=QTabWidget();body.addWidget(self.tabs)
        self.overview=QTextBrowser();self.tabs.addTab(self.overview,'Overview & matrix')
        tab=QWidget();row=QVBoxLayout(tab)
        self.transforms=QTableWidget(0,2);self.transforms.setHorizontalHeaderLabels(['Input','Output state'])
        self.transforms.horizontalHeader().setStretchLastSection(True)
        row.addWidget(self.transforms)
        self.tabs.addTab(tab,'Basis transformations')
        controls=QHBoxLayout();body.addLayout(controls)
        controls.addWidget(QLabel('Example angle (radians):'))
        self.angle=QDoubleSpinBox();self.angle.setRange(-1000,1000);self.angle.setDecimals(5)
        self.angle.setValue(math.pi/2);self.angle.setSingleStep(.1);controls.addWidget(self.angle)
        self.angle.setEnabled(self.name in ('RX','RY','RZ','P','U'))
        self.angle.valueChanged.connect(self.update_reference)
        close=QPushButton('Close');close.clicked.connect(self.accept);controls.addStretch();controls.addWidget(close)
        self.update_reference()

    def update_reference(self):
        info=self.info;angle=self.angle.value()
        heading=f'<h3>q0 ── [{self.name}] ──</h3>' if info['qubits']==1 else f'<h3>{self.name}: {info["qubits"]}-qubit operation</h3>'
        matrix=''
        if self.name in SINGLE:
            u=unitary(Gate(self.name,(0,),angle))
            def fmt(x):return f'{x.real:.4f}{x.imag:+.4f}i'
            matrix='<table border="1" cellpadding="7">'+''.join('<tr>'+''.join('<td>'+fmt(v)+'</td>' for v in line)+'</tr>' for line in u)+'</table>'
        elif self.name=='M':matrix='<p>Measurement is not unitary. It uses computational-basis projectors |0⟩⟨0| and |1⟩⟨1|.</p>'
        else:matrix='<p>See the complete computational-basis mapping in the Transformations tab.</p>'
        self.overview.setHtml('<div style="font-size:14px">'+heading+f'<p>{info["description"]}</p><p><b>Qubits:</b> {info["qubits"]}<br><b>Parameters:</b> {info["parameters"]}<br><b>Applications:</b> {info["applications"]}</p><h3>Matrix or operation</h3>'+matrix+'<p>The example transformation table below uses computational-basis inputs; for parameterized gates the angle control changes the example values. U also has φ and λ set to zero in this demonstration.</p></div>')
        rows=transformation_rows(self.name,angle)
        self.transforms.setRowCount(len(rows))
        for r,(before,after) in enumerate(rows):
            self.transforms.setItem(r,0,QTableWidgetItem(before));self.transforms.setItem(r,1,QTableWidgetItem(after))
        self.transforms.resizeColumnsToContents()
