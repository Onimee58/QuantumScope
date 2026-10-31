"""Viewport-independent vector PDF exports for QuantumScope circuits."""
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPdfWriter, QPainter, QColor, QPen, QFont, QPageSize
from quantumscope.physics.circuits import evolution
from quantumscope.physics.gate_education import angle_text
from quantumscope.physics.initial_states import defaults, product_state

def write_circuit_pdf(filename,n,gates,measurements,include_report=False,initial_states=None,blocks=()):
    """Render the full circuit with scalable Qt vector primitives, not a screenshot.
    Each wire is labeled with its initial state (|0⟩ unless given). blocks are
    BlockPlacement objects: collapsed ones draw as labeled boxes, expanded ones
    as their gates inside a dashed outline."""
    from quantumscope.physics.blocks import placed_items
    initial_states=list(initial_states) if initial_states is not None else defaults(n)
    blocks=list(blocks)
    ordered=[g for *_,g,_ in placed_items(((r,c,g) for (r,c),g in gates.items()),blocks)]
    gates=dict(gates)
    for pl in blocks:
        if pl.expanded:
            gates.update({(g.targets[0],c):g for g,c in pl.placed_gates()})
    columns=max([c for _,c in gates]+list(measurements.values())+[pl.end for pl in blocks],default=0)+1
    writer=QPdfWriter(str(filename));writer.setResolution(96)
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A3))
    painter=QPainter(writer)
    if not painter.isActive():raise OSError('Could not open PDF output')
    try:
        width=writer.width();height=writer.height()
        margin=48
        lane=72
        graph_width=max(400,columns*110)
        scale=min(1.0,(width-2*margin-125)/graph_width)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(0,0,width,height,QColor('white'))
        painter.setPen(QColor('#152536'));painter.setFont(QFont('Sans',17,QFont.Weight.Bold))
        painter.drawText(margin,65,'QuantumScope Circuit')
        painter.setFont(QFont('Sans',9))
        painter.drawText(margin,90,f'{n} qubits   •   {len(ordered)} unitary gates'+(f' ({len(blocks)} blocks)' if blocks else '')+f'   •   {len(measurements)} terminal measurements')
        painter.save();painter.translate(margin+95,125);painter.scale(scale,scale)
        painter.setFont(QFont('Sans',12))
        for q in range(n):
            y=35+q*lane
            painter.setPen(QPen(QColor('#273c4e'),2))
            state=initial_states[q]
            painter.drawText(-92,y+5,f'q{q}  {state.label}')
            if state.preset_key is None:
                painter.setFont(QFont('Sans',8))
                painter.drawText(-92,y+21,f'θ={angle_text(state.theta)}, φ={angle_text(state.phi)}')
                painter.setFont(QFont('Sans',12))
            painter.drawLine(0,y,graph_width,y)
        for (r,c),gate in sorted(gates.items(),key=lambda x:(x[0][1],x[0][0])):
            x=55+110*c;y=35+lane*r
            if len(gate.targets)>1:
                ys=[35+lane*q for q in gate.targets]
                painter.setPen(QPen(QColor('#2c5974'),2));painter.drawLine(x,min(ys),x,max(ys))
                for q in gate.targets[:-1]:
                    painter.setBrush(QColor('#2c5974'));painter.drawEllipse(QRectF(x-5,35+lane*q-5,10,10))
            if gate.name in ('CX','CCX'):
                y=35+lane*gate.targets[-1]
                painter.setPen(QPen(QColor('#116182'),2));painter.setBrush(QColor('white'))
                painter.drawEllipse(QRectF(x-12,y-12,24,24));painter.drawLine(x-9,y,x+9,y);painter.drawLine(x,y-9,x,y+9)
            elif gate.name in ('SWAP','CSWAP'):
                for q in (gate.targets if gate.name=='SWAP' else gate.targets[1:]):
                    yy=35+lane*q;painter.drawLine(x-8,yy-8,x+8,yy+8);painter.drawLine(x+8,yy-8,x-8,yy+8)
            elif gate.name in ('CZ','CP'):
                yy=35+lane*gate.targets[-1];painter.setBrush(QColor('#2c5974'));painter.drawEllipse(QRectF(x-5,yy-5,10,10))
                if gate.name=='CP':
                    painter.setFont(QFont('Sans',9));painter.setPen(QColor('#12658b'))
                    painter.drawText(QRectF(x+6,(35+lane*min(gate.targets)+yy)/2-10,60,20),Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter,'P('+angle_text(gate.angle)+')')
                    painter.setFont(QFont('Sans',12))
            else:
                painter.setPen(QPen(QColor('#12658b'),2));painter.setBrush(QColor('#eff8fc'))
                rect=QRectF(x-26,y-22,52,44);painter.drawRoundedRect(rect,4,4)
                painter.drawText(rect,Qt.AlignmentFlag.AlignCenter,gate.name)
                if gate.name in ('RX','RY','RZ','P','U','CP'):
                    painter.setFont(QFont('Sans',8));painter.drawText(QRectF(x-48,y+23,96,18),Qt.AlignmentFlag.AlignCenter,f'{gate.angle:.3g} rad');painter.setFont(QFont('Sans',12))
        for pl in blocks:
            top=35+lane*pl.block.low-30;bottom=35+lane*pl.block.high+30
            left=55+110*pl.col-45;right=55+110*pl.end+45
            if pl.expanded:
                painter.setPen(QPen(QColor('#7a62c9'),1.5,Qt.PenStyle.DashLine));painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(QRectF(left,top,right-left,bottom-top),8,8)
                painter.setFont(QFont('Sans',9));painter.setPen(QColor('#4b3299'))
                painter.drawText(QRectF(left+6,top-18,right-left,16),Qt.AlignmentFlag.AlignLeft,pl.block.label)
                painter.setFont(QFont('Sans',12))
            else:
                painter.setPen(QPen(QColor('#5a3eb4'),2));painter.setBrush(QColor('#ebe5fb'))
                box=QRectF(left+12,top+8,right-left-24,bottom-top-16)
                painter.drawRoundedRect(box,6,6);painter.setPen(QColor('#2b1869'))
                painter.drawText(box,Qt.AlignmentFlag.AlignCenter,pl.block.label)
        for q,c in measurements.items():
            x=55+110*c;y=35+lane*q
            painter.setPen(QPen(QColor('#ae7221'),2));painter.setBrush(QColor('#fff4dc'))
            rect=QRectF(x-25,y-22,50,44);painter.drawRoundedRect(rect,4,4)
            painter.drawText(rect,Qt.AlignmentFlag.AlignCenter,'M')
        painter.restore()
        if include_report:
            state=evolution(n,ordered,product_state(initial_states))[-1]
            probs=abs(state)**2
            order=sorted(range(len(probs)),key=lambda i:-probs[i])[:16]
            painter.setPen(QColor('#152536'));painter.setFont(QFont('Sans',11,QFont.Weight.Bold))
            y=min(height-360,145+int((35+(n-1)*lane)*scale)+55)
            if y+310>=height:
                writer.newPage();y=70
            painter.drawText(margin,y,'Final state probabilities (up to 16 largest outcomes)')
            painter.setFont(QFont('Sans',10))
            for index in order:
                if probs[index]<1e-11:continue
                y+=20
                from quantumscope.physics.display import ket
                painter.drawText(margin,y,f'{ket(index,n,True)}    {100*probs[index]:.4f}%')
            y+=30
            if y+30<height:
                painter.drawText(margin,y,'Terminal measurements: '+(', '.join('q'+str(q) for q in sorted(measurements)) if measurements else 'none'))
    finally:
        painter.end()
