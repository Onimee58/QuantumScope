"""Shared visuals for the Quantum Principles experiments (v0.7.4).

BlochView  — a shaded Bloch sphere: drag the arrow to set a state, an amber measurement axis,
             smooth animated changes and a flash on collapse.
TallyBars  — outcome counts as bars that grow smoothly, with dashed Born-rule targets.
Drawn with Qt alone; the physics stays in quantumscope.physics.
"""
import math

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QApplication, QWidget


def _dark():
    app = QApplication.instance()
    return app is None or app.palette().window().color().lightness() < 128


def direction(theta, phi):
    """Unit Bloch vector for polar angle θ and azimuth φ (degrees)."""
    t, p = math.radians(theta), math.radians(phi)
    return np.array([math.sin(t) * math.cos(p), math.sin(t) * math.sin(p), math.cos(t)])


def angles(vector):
    """(θ, φ) in degrees of a vector (φ in (−180, 180])."""
    x, y, z = vector / max(np.linalg.norm(vector), 1e-12)
    return math.degrees(math.acos(max(-1.0, min(1.0, z)))), math.degrees(math.atan2(y, x))


class BlochView(QWidget):
    """A shaded, interactive Bloch sphere. stateChanged(θ, φ) fires while the arrow is dragged."""

    stateChanged = Signal(float, float)
    axisChanged = Signal(float)                # degrees, while the measurement axis is dragged (axis mode)

    # Default camera: slightly above, x to the lower left, y to the right — chosen so the presets
    # and 45° states all read clearly. Right-drag (or Shift + left-drag) turns it like a turntable.
    AZIMUTH, ELEVATION = math.degrees(math.atan2(-0.32, 0.78)), math.degrees(math.asin(0.42 / math.hypot(0.78, 0.32, 0.42)))
    _F = np.array([0.78, -0.32, 0.42]) / math.hypot(0.78, 0.32, 0.42)       # class default (tests use it)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 320)
        self.theta, self.phi = 90.0, 0.0
        self.axis = 0.0                    # measurement axis, in the x–z plane, degrees from +z towards +x
        self.show_axis = True
        self.draggable = True
        self.drag_mode = 'state'           # 'state': left-drag sets the state; 'axis': it turns the measurement axis
        self.caption = ''                  # a short label under the sphere (e.g. "Alice")
        self.length = 1.0                  # arrow length (shorter than 1 for mixed states)
        self._from = self._to = None
        self._t = 1.0
        self._flash = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self.setMouseTracking(False)
        self.setToolTip('Left-drag: set the state  ·  Right-drag or Shift + left-drag: turn the sphere  ·  '
                        'Double-click: reset the view')
        self.reset_view()

    # ---- the camera ---------------------------------------------------------------------------
    def set_view(self, azimuth, elevation):
        """Look from azimuth (degrees about z) and elevation (kept within ±80°, |0⟩ always on top)."""
        self.azimuth, self.elevation = azimuth % 360, max(-80.0, min(80.0, elevation))
        a, e = math.radians(self.azimuth), math.radians(self.elevation)
        self._F = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])
        up = np.array([0.0, 0.0, 1.0]) - math.sin(e) * self._F
        self._U = up / np.linalg.norm(up)
        self._R = np.cross(self._U, self._F)
        self.update()

    def reset_view(self):
        self.set_view(self.AZIMUTH, self.ELEVATION)

    def mouseDoubleClickEvent(self, event):
        self.reset_view()

    # ---- geometry --------------------------------------------------------------------------
    def _frame(self):
        r = 0.40 * min(self.width(), self.height())
        return self.width() / 2, self.height() / 2 + 6, r

    def project(self, v):
        cx, cy, r = self._frame()
        return QPointF(cx + r * float(np.dot(v, self._R)), cy - r * float(np.dot(v, self._U))), float(np.dot(v, self._F))

    def unproject(self, point, side=1):
        """The point on the sphere under a screen position: on the front (side=1) or the back
        (side=−1), clamped to the rim."""
        cx, cy, r = self._frame()
        sx, sy = (point.x() - cx) / r, -(point.y() - cy) / r
        norm = math.hypot(sx, sy)
        if norm > 1:
            sx, sy = sx / norm, sy / norm
        depth = side * math.sqrt(max(0.0, 1 - sx * sx - sy * sy))
        return sx * self._R + sy * self._U + depth * self._F

    def _rim(self, point):
        cx, cy, r = self._frame()
        return math.hypot(point.x() - cx, point.y() - cy) / r

    # ---- state and animation -------------------------------------------------------------------
    def set_state(self, theta, phi, animate=False, flash=False, length=1.0):
        self.length = length
        if animate:
            self._from, self._to = direction(self.theta, self.phi), direction(theta, phi)
            self._target = (theta, phi)
            self._t = 0.0
            self._timer.start()
        else:
            self.theta, self.phi, self._t = theta, phi, 1.0
        if flash:
            self._flash = 1.0
            self._timer.start()
        self.update()

    def animating(self):
        return self._timer.isActive()

    def _tick(self):
        if self._t < 1.0:
            self._t = min(1.0, self._t + 0.07)
            s = 1 - (1 - self._t) ** 3                                   # ease out
            a, b = self._from, self._to
            omega = math.acos(max(-1.0, min(1.0, float(np.dot(a, b)))))
            if omega < 1e-6:
                v = b
            elif abs(omega - math.pi) < 1e-6:                            # opposite: go over a meridian
                mid = np.cross(a, [0.0, 1.0, 0.0])
                mid = mid / (np.linalg.norm(mid) or 1)
                v = a * math.cos(math.pi * s) + mid * math.sin(math.pi * s)
            else:
                v = (math.sin((1 - s) * omega) * a + math.sin(s * omega) * b) / math.sin(omega)
            self.theta, self.phi = angles(v)
            if self._t >= 1.0:
                self.theta, self.phi = self._target
        if self._flash > 0:
            self._flash = max(0.0, self._flash - 0.04)
        if self._t >= 1.0 and self._flash <= 0:
            self._timer.stop()
        self.update()

    # ---- dragging -------------------------------------------------------------------------------
    def _turning(self, event):
        return event.buttons() & Qt.MouseButton.RightButton or (
            event.buttons() & Qt.MouseButton.LeftButton and event.modifiers() & Qt.KeyboardModifier.ShiftModifier)

    def contextMenuEvent(self, event):
        event.accept()                          # right-drag turns the sphere: no context menu

    def mousePressEvent(self, event):
        """Grabbing the arrow keeps its side of the sphere (front or back); elsewhere, the front.
        Right button (or Shift + left) starts turning the sphere instead."""
        if self._turning(event):
            self._turn_from = (event.position(), self.azimuth, self.elevation)
            return
        self._turn_from = None
        if self.draggable and event.button() == Qt.MouseButton.LeftButton:
            tip, depth = self.project(self.length * direction(self.theta, self.phi))
            near = math.hypot(event.position().x() - tip.x(), event.position().y() - tip.y()) < 28
            self._side = -1 if near and depth < 0 else 1
            self._beyond = self._rim(event.position()) >= 1
            self._drag(event.position())

    def mouseMoveEvent(self, event):
        start = getattr(self, '_turn_from', None)
        if start is not None and self._turning(event):
            point, azimuth, elevation = start
            dx, dy = event.position().x() - point.x(), event.position().y() - point.y()
            self.set_view(azimuth - dx * 0.5, elevation + dy * 0.5)       # drag the sphere round
            return
        if self.draggable and event.buttons() & Qt.MouseButton.LeftButton:
            self._drag(event.position())

    def mouseReleaseEvent(self, event):
        self._turn_from = None

    def _drag(self, point):
        """Follow the pointer; crossing the rim carries the arrow round to the other side."""
        rim = self._rim(point)
        if rim >= 1 and not getattr(self, '_beyond', False):
            self._side, self._beyond = -getattr(self, '_side', 1), True
        elif rim < 0.97:
            self._beyond = False
        if self.drag_mode == 'axis':                                   # turn the detector, in the x–z plane
            v = self.unproject(point, getattr(self, '_side', 1))
            self.axis = round(math.degrees(math.atan2(v[0], v[2])))
            self.update()
            self.axisChanged.emit(float(self.axis))
            return
        self._timer.stop()
        self._t, self._flash = 1.0, 0.0
        self.theta, self.phi = angles(self.unproject(point, getattr(self, '_side', 1)))
        self.length = 1.0
        self.update()
        self.stateChanged.emit(self.theta, self.phi)

    # ---- drawing --------------------------------------------------------------------------------
    def _circle(self, p, normal, colour, width=1.0):
        """A great circle: the front half solid, the back half faint and dashed."""
        normal = np.asarray(normal, float)
        a = np.cross(normal, [0.0, 0.0, 1.0]) if abs(normal[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
        a = a / np.linalg.norm(a)
        b = np.cross(normal, a)
        points = [self.project(math.cos(t) * a + math.sin(t) * b) for t in np.linspace(0, 2 * math.pi, 121)]
        for (p1, d1), (p2, d2) in zip(points, points[1:]):
            front = d1 + d2 > 0
            c = QColor(colour)
            c.setAlpha(150 if front else 55)
            pen = QPen(c, width, Qt.PenStyle.SolidLine if front else Qt.PenStyle.DashLine)
            p.setPen(pen)
            p.drawLine(p1, p2)

    def paintEvent(self, event):
        dark = _dark()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy, r = self._frame()
        lit = QRadialGradient(QPointF(cx - 0.38 * r, cy - 0.42 * r), 1.55 * r)
        if dark:
            lit.setColorAt(0.0, QColor(70, 130, 185, 235))
            lit.setColorAt(0.55, QColor(24, 58, 96, 235))
            lit.setColorAt(1.0, QColor(8, 20, 36, 240))
        else:
            lit.setColorAt(0.0, QColor(250, 253, 255, 245))
            lit.setColorAt(0.6, QColor(190, 216, 238, 245))
            lit.setColorAt(1.0, QColor(132, 168, 200, 245))
        p.setPen(QPen(QColor(120, 175, 220) if dark else QColor(70, 115, 155), 1.4))
        p.setBrush(QBrush(lit))
        p.drawEllipse(QPointF(cx, cy), r, r)
        grid = QColor(150, 200, 240) if dark else QColor(55, 95, 135)
        self._circle(p, [0, 0, 1], grid)                                   # equator
        self._circle(p, [0, 1, 0], grid)                                   # x–z meridian
        self._circle(p, [1, 0, 0], grid, 0.8)                              # y–z meridian
        text = QColor(220, 235, 250) if dark else QColor(25, 50, 75)
        p.setFont(QFont('Sans', 10, QFont.Weight.DemiBold))
        for vec, label in (([0, 0, 1.13], '|0⟩'), ([0, 0, -1.16], '|1⟩'), ([1.18, 0, 0], 'x'), ([0, 1.14, 0], 'y')):
            point, _ = self.project(np.array(vec, float))
            p.setPen(text)
            p.drawText(QRectF(point.x() - 22, point.y() - 10, 44, 20), Qt.AlignmentFlag.AlignCenter, label)
        if self.show_axis:                                                  # the measurement axis
            a = math.radians(self.axis)
            m = np.array([math.sin(a), 0.0, math.cos(a)])
            top, _ = self.project(1.06 * m)
            bottom, _ = self.project(-1.06 * m)
            amber = QColor(255, 186, 80)
            p.setPen(QPen(amber, 2.2, Qt.PenStyle.DashLine))
            p.drawLine(bottom, top)
            p.setFont(QFont('Sans', 9, QFont.Weight.Bold))
            p.setPen(amber)
            for point, label in ((self.project(1.24 * m)[0], '+1'), (self.project(-1.24 * m)[0], '−1')):
                p.drawText(QRectF(point.x() - 16, point.y() - 9, 32, 18), Qt.AlignmentFlag.AlignCenter, label)
        v = self.length * direction(self.theta, self.phi)
        tip, depth = self.project(v)
        centre = QPointF(cx, cy)
        if self.caption:
            p.setPen(text)
            p.setFont(QFont('Sans', 11, QFont.Weight.Bold))
            p.drawText(QRectF(0, self.height() - 24, self.width(), 22), Qt.AlignmentFlag.AlignCenter, self.caption)
        if self.length < 0.04 and self._flash <= 0:                     # no arrow: completely random
            p.setPen(QPen(QColor(90, 230, 255) if dark else QColor(0, 120, 190), 2, Qt.PenStyle.DashLine))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(centre, 11, 11)
            p.setFont(QFont('Sans', 9, QFont.Weight.Bold))
            p.drawText(QRectF(cx - 50, cy + 14, 100, 18), Qt.AlignmentFlag.AlignCenter, 'random')
            p.end()
            return
        shadow, _ = self.project(np.array([v[0], v[1], 0.0]))
        p.setPen(QPen(QColor(text.red(), text.green(), text.blue(), 90), 1.2, Qt.PenStyle.DotLine))
        p.drawLine(centre, shadow)
        p.drawLine(shadow, tip)
        arrow = QColor(90, 230, 255) if dark else QColor(0, 120, 190)
        glow = QColor(arrow)
        glow.setAlpha(70)
        p.setPen(QPen(glow, 11, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(centre, tip)
        p.setPen(QPen(arrow, 3.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(centre, tip)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(arrow)
        p.drawEllipse(tip, 6.5, 6.5)
        if self._flash > 0:                                                 # collapse flash
            ring = QColor(255, 255, 255, int(220 * self._flash))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(ring, 3))
            radius = 8 + 26 * (1 - self._flash)
            p.drawEllipse(tip, radius, radius)
        p.end()


class TallyBars(QWidget):
    """Outcome bars that grow smoothly as counts come in, with dashed Born-rule targets."""

    def __init__(self, labels, colours=None, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(150)
        self.labels = list(labels)
        self.colours = colours or [QColor(90, 230, 255), QColor(255, 150, 120)]
        self.counts = [0] * len(self.labels)
        self.expected = None
        self._shown = [0.0] * len(self.labels)
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)

    def set_expected(self, probabilities):
        self.expected = list(probabilities) if probabilities is not None else None
        self.update()

    def set_counts(self, counts):
        self.counts = list(counts)
        self._timer.start()

    def add(self, index, amount=1):
        self.counts[index] += amount
        self._timer.start()

    def reset(self):
        self.counts = [0] * len(self.labels)
        self._shown = [0.0] * len(self.labels)
        self.update()

    def fractions(self):
        total = sum(self.counts)
        return [c / total if total else 0.0 for c in self.counts]

    def _tick(self):
        targets = self.fractions()
        done = True
        for i, t in enumerate(targets):
            self._shown[i] += (t - self._shown[i]) * 0.25
            if abs(t - self._shown[i]) > 1e-3:
                done = False
            else:
                self._shown[i] = t
        if done:
            self._timer.stop()
        self.update()

    def paintEvent(self, event):
        dark = _dark()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        text = QColor(220, 235, 250) if dark else QColor(25, 50, 75)
        w, h = self.width(), self.height()
        top, bottom = 26, h - 30
        n = len(self.labels)
        slot = w / n
        bar = min(120, slot * 0.5)
        p.setFont(QFont('Sans', 9))
        total = sum(self.counts)
        p.setPen(text)
        p.drawText(QRectF(0, 2, w, 18), Qt.AlignmentFlag.AlignCenter,
                   f'{total} measurement{"s" if total != 1 else ""}' if total else 'No measurements yet')
        for i, label in enumerate(self.labels):
            x = slot * i + (slot - bar) / 2
            height = (bottom - top) * self._shown[i]
            colour = QColor(self.colours[i % len(self.colours)])
            p.setPen(Qt.PenStyle.NoPen)
            faint = QColor(colour)
            faint.setAlpha(40)
            p.setBrush(faint)
            p.drawRoundedRect(QRectF(x, top, bar, bottom - top), 6, 6)
            p.setBrush(colour)
            if height > 0.5:
                p.drawRoundedRect(QRectF(x, bottom - height, bar, height), 6, 6)
            if self.expected is not None:                                  # Born-rule target
                y = bottom - (bottom - top) * self.expected[i]
                p.setPen(QPen(text, 1.6, Qt.PenStyle.DashLine))
                p.drawLine(QPointF(x - 8, y), QPointF(x + bar + 8, y))
            p.setPen(text)
            p.setFont(QFont('Sans', 10, QFont.Weight.Bold))
            share = self.fractions()[i]
            p.drawText(QRectF(slot * i, bottom + 4, slot, 22), Qt.AlignmentFlag.AlignCenter,
                       f'{label}   {self.counts[i]}' + (f'  ({share:.1%})' if total else ''))
        p.end()


def wavelength_colour(nm):
    """An approximate colour for light of wavelength nm; outside 380–750 nm (invisible) a false colour.
    Returns (QColor, visible?)."""
    nm = float(nm)
    if nm < 380:
        return QColor(170, 120, 255), False                    # ultraviolet: false-colour violet
    if nm > 750:
        return QColor(255, 90, 70), False                      # infrared: false-colour red
    if nm < 440:
        r, g, b = -(nm - 440) / 60, 0.0, 1.0
    elif nm < 490:
        r, g, b = 0.0, (nm - 440) / 50, 1.0
    elif nm < 510:
        r, g, b = 0.0, 1.0, -(nm - 510) / 20
    elif nm < 580:
        r, g, b = (nm - 510) / 70, 1.0, 0.0
    elif nm < 645:
        r, g, b = 1.0, -(nm - 645) / 65, 0.0
    else:
        r, g, b = 1.0, 0.0, 0.0
    edge = 0.35 + 0.65 * (nm - 380) / 40 if nm < 420 else 0.35 + 0.65 * (750 - nm) / 50 if nm > 700 else 1.0
    lift = 0.25                                                 # keep dark ends visible on a dark screen
    return QColor(*[int(255 * min(1.0, lift + (1 - lift) * c * edge)) for c in (r, g, b)]), True


class DetectorScreen(QWidget):
    """Particles landing one by one as glowing dots; fringes emerge where they pile up."""

    def __init__(self, parent=None):
        from PySide6.QtGui import QImage
        super().__init__(parent)
        self.setMinimumHeight(110)
        self._image = QImage(900, 160, QImage.Format.Format_ARGB32_Premultiplied)
        self._image.fill(Qt.GlobalColor.transparent)
        self.halfwidth = 40.0
        self.colour = QColor(90, 230, 255)
        self.count = 0
        self._rng = np.random.default_rng()

    def set_halfwidth(self, halfwidth):
        self.halfwidth = float(halfwidth)

    def set_colour(self, colour):
        self.colour = QColor(colour)

    def clear(self):
        self._image.fill(Qt.GlobalColor.transparent)
        self.count = 0
        self.update()

    def add_hits(self, positions_mm):
        """Add detections at screen positions (mm); each gets a random height on the screen."""
        positions = np.asarray(positions_mm, float)
        if positions.size == 0:
            return
        w, h = self._image.width(), self._image.height()
        p = QPainter(self._image)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)    # dense places glow brighter
        dot = QColor(self.colour)
        dot.setAlpha(150)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(dot)
        xs = (positions / (2 * self.halfwidth) + 0.5) * w
        ys = self._rng.uniform(8, h - 8, positions.size)
        for x, y in zip(xs, ys):
            p.drawEllipse(QPointF(float(x), float(y)), 1.6, 1.6)
        p.end()
        self.count += positions.size
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        dark = _dark()
        p.fillRect(self.rect(), QColor(6, 10, 16) if dark else QColor(28, 34, 44))   # a dark screen in both themes
        p.drawImage(QRectF(self.rect()), self._image)
        p.setPen(QColor(200, 215, 230))
        p.setFont(QFont('Sans', 9))
        p.drawText(QRectF(8, 4, self.width() - 16, 16), Qt.AlignmentFlag.AlignLeft,
                   f'Detector screen  ·  {self.count:,} particle{"s" if self.count != 1 else ""}')
        p.drawText(QRectF(8, self.height() - 18, self.width() - 16, 16), Qt.AlignmentFlag.AlignLeft, f'−{self.halfwidth:g} mm')
        p.drawText(QRectF(8, self.height() - 18, self.width() - 16, 16), Qt.AlignmentFlag.AlignRight, f'+{self.halfwidth:g} mm')
        p.end()
