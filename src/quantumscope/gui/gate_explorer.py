"""Educational reference dialog for the existing gate palette."""
import math
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog,QVBoxLayout,QLabel,QTabWidget,QWidget,QTextBrowser,QTableWidget,QTableWidgetItem,QHBoxLayout,QLineEdit,QPushButton
from quantumscope.physics.gate_education import angle_text,worked_identity,try_it_circuit,parse_angle,gate_information,transformation_rows,gate_matrix,gate_properties,format_amplitude

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
        self.overview=QTextBrowser();self.tabs.addTab(self.overview,'Overview && matrix')
        tab=QWidget();row=QVBoxLayout(tab)
        self.transforms=QTableWidget(0,2);self.transforms.setHorizontalHeaderLabels(['Input','Output state'])
        self.transforms.horizontalHeader().setStretchLastSection(True)
        row.addWidget(self.transforms)
        self.tabs.addTab(tab,'Basis transformations')
        worked=worked_identity(self.name)
        if worked:
            self.tabs.addTab(self._worked_tab(worked),'Worked identity')
        controls=QHBoxLayout();body.addLayout(controls)
        parameterized=self.name in ('RX','RY','RZ','P','U','CP')
        # Angle fields accept exact expressions such as pi/2 or -3*pi/4, so
        # special angles are represented exactly (a 5-decimal spin box is not).
        self._values={}
        def field(label,text,key):
            controls.addWidget(QLabel(label))
            box=QLineEdit(text);box.setMaximumWidth(110);box.setEnabled(parameterized)
            box.setToolTip('Radians. Examples: pi/2, -pi/4, 2*pi/3, 0.75')
            box.editingFinished.connect(self.update_reference);controls.addWidget(box)
            self._values[key]=parse_angle(text)
            return box
        self.angle=field(('λ' if self.name in ('P','CP') else 'θ')+' (radians):' if parameterized else 'Parameters: none','pi/2','angle')
        self.phi=field('φ:','0','phi') if self.name=='U' else None
        self.lam=field('λ:','0','lam') if self.name=='U' else None
        if not parameterized:self.angle.hide()
        self.param_status=QLabel('');controls.addWidget(self.param_status)
        controls.addStretch()
        if self.name!='M' and hasattr(parent,'try_gate'):
            self.try_button=QPushButton('Try it in the circuit')
            self.try_button.setToolTip('Load this gate into a small circuit with starting states that show its effect')
            self.try_button.clicked.connect(self._try_it);controls.addWidget(self.try_button)
        close=QPushButton('Close');close.clicked.connect(self.accept);controls.addWidget(close)
        self.update_reference()

    def _params(self):
        """Parse the angle fields; keep the last valid value if one is invalid."""
        problems=[]
        for key,box in (('angle',self.angle),('phi',self.phi),('lam',self.lam)):
            if box is None:continue
            try:self._values[key]=parse_angle(box.text())
            except ValueError as exc:problems.append(str(exc))
        self.param_status.setText(('⚠ '+problems[0]) if problems else '')
        v=self._values
        return (v['angle'],v.get('phi',0.0),v.get('lam',0.0))

    def update_reference(self):
        info=self.info;angle,phi,lam=self._params()
        heading=f'<h3>q0 ── [{self.name}] ──</h3>' if info['qubits']==1 else f'<h3>{self.name}: {info["qubits"]}-qubit operation</h3>'
        if self.name=='M':
            matrix='<p>Measurement is not unitary. It uses computational-basis projectors |0⟩⟨0| and |1⟩⟨1|.</p>'
        else:
            u=gate_matrix(self.name,angle,phi,lam);n=info['qubits']
            labels=[f'|{i:0{n}b}⟩' for i in range(1<<n)]
            head_row='<tr><td></td>'+''.join(f'<td><b>{l}</b></td>' for l in labels)+'</tr>'
            body=''.join('<tr><td><b>'+labels[r]+'</b></td>'+''.join(f'<td align="center">{format_amplitude(v)}</td>' for v in u[r])+'</tr>' for r in range(len(u)))
            note='' if n==1 else '<p>Qubit order: q0 is the leftmost bit; for controlled gates q0 is the first control.</p>'
            matrix='<table border="1" cellpadding="6" cellspacing="0">'+head_row+body+'</table>'+note
        props=gate_properties(self.name,angle,phi,lam)
        def yn(v):return '—' if v is None else ('Yes' if v else 'No')
        rows=[('Unitary',yn(props['unitary'])),('Hermitian (self-inverse)',yn(props['hermitian'])),
              ('Clifford gate',props['clifford'] or '—'),('Inverse',props['inverse'])]
        if props['eigenvalues']:rows.append(('Eigenvalues',',&nbsp; '.join(props['eigenvalues'])))
        if props['on_zero'] is not None:
            x,y,z=props['on_zero'];rows.append(('Applied to |0⟩: Bloch vector',f'({x:g}, {y:g}, {z:g})'))
        if props['identity']:rows.append(('Useful identity',props['identity']))
        if props['related']:rows.append(('Related gates',', '.join(props['related'])))
        properties='<table cellpadding="4">'+''.join(f'<tr><td><b>{k}</b></td><td>{v}</td></tr>' for k,v in rows)+'</table>'
        demo=('<p>Change the parameter controls below to see the matrix, properties and transformations update.'
              +(' U(θ, φ, λ) uses the OpenQASM u3 convention.' if self.name=='U' else '')+'</p>') if self.name in ('RX','RY','RZ','P','U','CP') else ''
        self.overview.setHtml('<div style="font-size:14px">'+heading+f'<p>{info["description"]}</p><p><b>Qubits:</b> {info["qubits"]}<br><b>Parameters:</b> {info["parameters"]}<br><b>Applications:</b> {info["applications"]}</p>'
            +'<h3>Matrix</h3>'+matrix+'<h3>Properties</h3>'+properties+demo+'</div>')
        rows=transformation_rows(self.name,angle,phi,lam)
        self.transforms.setRowCount(len(rows))
        for r,(before,after) in enumerate(rows):
            self.transforms.setItem(r,0,QTableWidgetItem(before));self.transforms.setItem(r,1,QTableWidgetItem(after))
        self.transforms.resizeColumnsToContents()

    def _worked_tab(self,worked):
        tab=QWidget();v=QVBoxLayout(tab)
        title=QLabel(f'<b>{worked["title"]}</b> — each basis state is followed through the sequence, '
                     f'then compared with {worked["target"]} applied directly.')
        title.setWordWrap(True);v.addWidget(title)
        steps=worked['steps']
        table=QTableWidget(len(worked['rows']),len(steps)+3)
        table.setHorizontalHeaderLabels(['Input',*[f'after {s}' for s in steps],f'{worked["target"]} directly','Equal'])
        table.verticalHeader().setVisible(False)
        for r,(start,after,reference,equal) in enumerate(worked['rows']):
            for c,text in enumerate([start,*after,reference,'✓ yes' if equal else '✗ no']):
                item=QTableWidgetItem(text);item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable);table.setItem(r,c,item)
        table.resizeColumnsToContents();v.addWidget(table)
        return tab

    def _try_it(self):
        angle,phi,lam=self._params() if hasattr(self,'_params') else (math.pi/2,0.0,0.0)
        self.parent().try_gate(self.name,angle,phi,lam)
        self.accept()


class BlockExplorer(QDialog):
    """Read-only view of a block: what it contains and, for small blocks, its matrix."""
    def __init__(self,block,parent=None):
        super().__init__(parent)
        import numpy as np
        from quantumscope.physics.circuits import apply_gate, Gate
        self.setWindowTitle(f'{block.label} block')
        self.resize(720,560)
        v=QVBoxLayout(self)
        params=', '.join(f'{k} = {val}' for k,val in block.params if k not in ('inputs','search','size'))
        v.addWidget(QLabel(f'<h3>{block.label}</h3>Acts on {", ".join(f"q{q}" for q in block.qubits)} · '
                           f'{len(block.gates)} gates' + (f' · {params}' if params else '')))
        tabs=QTabWidget();v.addWidget(tabs)
        table=QTableWidget(len(block.gates),3);table.setHorizontalHeaderLabels(['#','Gate','Qubits'])
        table.verticalHeader().setVisible(False)
        for r,g in enumerate(block.gates):
            label=g.name+(f'({angle_text(g.angle)})' if g.name in ('RX','RY','RZ','P','CP') else '')
            for c,text in enumerate([str(r+1),label,', '.join(f'q{q}' for q in g.targets)]):
                item=QTableWidgetItem(text);item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable);table.setItem(r,c,item)
        table.horizontalHeader().setStretchLastSection(True);tabs.addTab(table,'Gates')
        if len(block.qubits)<=3:
            local={q:i for i,q in enumerate(block.qubits)};k=len(block.qubits)
            cols=[]
            for index in range(1<<k):
                state=np.zeros(1<<k,complex);state[index]=1
                for g in block.gates:
                    state=apply_gate(state,k,Gate(g.name,tuple(local[q] for q in g.targets),g.angle,g.phi,g.lam))
                cols.append(state)
            u=np.array(cols).T
            labels=[f'|{i:0{k}b}⟩' for i in range(1<<k)]
            html='<table border="1" cellpadding="5" cellspacing="0"><tr><td></td>'+''.join(f'<td><b>{l}</b></td>' for l in labels)+'</tr>'
            html+=''.join('<tr><td><b>'+labels[r]+'</b></td>'+''.join(f'<td align="center">{format_amplitude(x)}</td>' for x in u[r])+'</tr>' for r in range(1<<k))
            matrix=QTextBrowser();matrix.setHtml('<p>Basis order lists '+', '.join(f'q{q}' for q in block.qubits)+' (first = leftmost bit).</p>'+html+'</table>')
            tabs.addTab(matrix,'Matrix')
        else:
            note=QLabel(f'The matrix of a {len(block.qubits)}-qubit block is {2**len(block.qubits)}×{2**len(block.qubits)}; '
                        'use the State Inspector to see its effect on a state.');note.setWordWrap(True)
            tabs.addTab(note,'Matrix')
        close=QPushButton('Close');close.clicked.connect(self.accept);v.addWidget(close)
