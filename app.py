#!/usr/bin/env python3
"""
Shape Morphing Studio — Professional Edition
A comprehensive shape morphing animation tool built with PySide6.

Features:
  • 12 built-in shapes with visual previews
  • 5 morphing algorithms (Linear, Ease In-Out, Elastic, Back, Bounce)
  • 3 animation directions (Forward, Ping-Pong, Reverse)
  • FREEHAND & POINT-BY-POINT drawing
  • SVG import / export
  • PNG, GIF, SVG, PNG-sequence export
  • Solid, Linear, Radial, and Conical GRADIENTS
  • Dark professional theme with colour swatches
  • Keyboard shortcuts

Requirements:
    pip install PySide6 numpy Pillow
"""

import sys, random, re
import numpy as np
import xml.etree.ElementTree as ET

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QComboBox, QSlider, QPushButton, QCheckBox,
    QSpinBox, QFileDialog, QMessageBox, QProgressDialog, QColorDialog,
    QSplitter, QStatusBar, QFrame, QScrollArea, QToolBar,
    QDialog, QDialogButtonBox, QListWidget, QListWidgetItem,
    QAbstractItemView, QSizePolicy, QTabWidget, QGridLayout,
)
from PySide6.QtCore import Signal, Qt, QTimer, QPointF, QSize
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPainterPath, QImage, QPixmap,
    QAction, QFont, QIcon, QKeySequence, QRadialGradient, QShortcut,
    QLinearGradient, QConicalGradient
)

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

DEFAULT_RESOLUTION = 120
DEFAULT_FPS       = 24
CANVAS_BG         = QColor(30, 30, 30)
GRID_COLOR        = QColor(50, 50, 50)

COLORS = {
    "fill":             QColor(79, 195, 247),
    "outline":          QColor(210, 210, 210),
    "drawing_line":     QColor(255, 100, 100),
    "snap_indicator":   QColor(50, 205, 50),
    "freehand_preview": QColor(100, 149, 237),
    "crosshair":        QColor(55, 55, 55),
    "accent":           QColor(79, 195, 247),
}

PRESET_COLORS = [
    QColor(79,195,247), QColor(129,199,132), QColor(255,183,77),
    QColor(240,98,146), QColor(149,117,205), QColor(255,138,101),
    QColor(77,208,225), QColor(255,241,118), QColor(220,220,220),
    QColor(239,83,80),
]

PRESET_SEQUENCES = {
    "Circle → Star":          ["Circle","Star-5"],
    "Heart → Circle":         ["Heart","Circle"],
    "Triangle → Octagon":     ["Triangle","Octagon"],
    "Star Tour":              ["Star-4","Star-5","Star-6","Star-8"],
    "Shape Shift":            ["Circle","Triangle","Square","Pentagon","Hexagon"],
    "Full Tour":              ["Circle","Triangle","Square","Pentagon",
                               "Hexagon","Star-5","Heart","Blob"],
}

DARK_STYLE = """
QMainWindow{background:#2b2b2b}
QWidget{background:#2b2b2b;color:#d4d4d4;font-family:'Segoe UI',Arial,sans-serif;font-size:12px}
QGroupBox{font-weight:bold;border:1px solid #444;border-radius:6px;margin-top:14px;
          padding:16px 8px 8px 8px;background:#333}
QGroupBox::title{subcontrol-origin:margin;left:12px;padding:0 6px;color:#4fc3f7}
QPushButton{background:#3c3f41;border:1px solid #555;border-radius:4px;
            padding:5px 12px;color:#d4d4d4;min-height:20px}
QPushButton:hover{background:#4a4d50;border-color:#4fc3f7}
QPushButton:pressed{background:#2a4a5a}
QPushButton:checked{background:#1a3a4a;border-color:#4fc3f7;color:#4fc3f7}
QPushButton:disabled{color:#666;border-color:#3a3a3a}
QSlider::groove:horizontal{height:6px;background:#444;border-radius:3px}
QSlider::handle:horizontal{width:16px;height:16px;margin:-5px 0;background:#4fc3f7;border-radius:8px}
QSlider::sub-page:horizontal{background:#29b6f6;border-radius:3px}
QComboBox{background:#3c3f41;border:1px solid #555;border-radius:4px;padding:4px 8px;color:#d4d4d4}
QComboBox::drop-down{border:none;width:20px}
QComboBox::down-arrow{image:none;border-left:5px solid transparent;border-right:5px solid transparent;
                      border-top:6px solid #aaa}
QComboBox QAbstractItemView{background:#3c3f41;border:1px solid #555;color:#d4d4d4;
                            selection-background-color:#1a3a4a}
QCheckBox{spacing:8px;color:#d4d4d4}
QCheckBox::indicator{width:16px;height:16px;border:1px solid #555;border-radius:3px;background:#3c3f41}
QCheckBox::indicator:checked{background:#4fc3f7;border-color:#4fc3f7}
QSpinBox{background:#3c3f41;border:1px solid #555;border-radius:4px;padding:4px;color:#d4d4d4}
QLabel{color:#d4d4d4;background:transparent}
QScrollArea{border:none;background:transparent}
QTabWidget::pane{border:1px solid #444;background:#2b2b2b;border-radius:4px;top:-1px}
QTabBar::tab{background:#333;border:1px solid #444;padding:7px 14px;margin-right:2px;
             border-top-left-radius:4px;border-top-right-radius:4px;color:#aaa}
QTabBar::tab:selected{background:#2b2b2b;border-bottom-color:#2b2b2b;color:#4fc3f7}
QTabBar::tab:hover:!selected{background:#3a3a3a}
QStatusBar{background:#1e1e1e;color:#888;border-top:1px solid #444;font-size:11px}
QToolBar{background:#333;border-bottom:1px solid #444;spacing:6px;padding:3px}
QToolBar QToolButton{background:transparent;border:1px solid transparent;border-radius:4px;
                     padding:4px 8px;color:#d4d4d4;font-size:13px}
QToolBar QToolButton:hover{background:#444;border-color:#555}
QToolBar QToolButton:checked{background:#1a3a4a;border-color:#4fc3f7;color:#4fc3f7}
QListWidget{background:#1e1e1e;border:1px solid #444;border-radius:4px;color:#d4d4d4}
QListWidget::item{padding:4px 6px}
QListWidget::item:selected{background:#1a3a4a;color:#4fc3f7}
QDialog{background:#2b2b2b}
QDialogButtonBox QPushButton{min-width:80px}
QToolTip{background:#333;color:#d4d4d4;border:1px solid #555;padding:4px;border-radius:3px}
QMenuBar{background:#333;color:#d4d4d4;border-bottom:1px solid #444}
QMenuBar::item:selected{background:#444}
QMenu{background:#333;border:1px solid #555;color:#d4d4d4}
QMenu::item:selected{background:#1a3a4a}
QSplitter::handle{background:#444;width:3px}
QSplitter::handle:hover{background:#4fc3f7}
QScrollBar:vertical{background:#2b2b2b;width:10px;margin:0}
QScrollBar::handle:vertical{background:#555;min-height:30px;border-radius:5px}
QScrollBar::handle:vertical:hover{background:#666}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0}
QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{background:none}
QProgressBar{background:#444;border-radius:3px;text-align:center;color:#d4d4d4;height:18px}
QProgressBar::chunk{background:#4fc3f7;border-radius:3px}
"""


# ═══════════════════════════════════════════════════════════════
# GEOMETRY
# ═══════════════════════════════════════════════════════════════

def _interpolate_polygon(corners, n_points):
    dists = np.cumsum(np.sqrt(np.sum(np.diff(corners, axis=0)**2, axis=1)))
    dists = np.insert(dists, 0, 0)
    if dists[-1] == 0:
        return np.tile(corners[0], (n_points, 1))
    dists /= dists[-1]
    t = np.linspace(0, 1, n_points)
    return np.column_stack([np.interp(t, dists, corners[:, 0]),
                            np.interp(t, dists, corners[:, 1])])

def generate_circle(n=100, radius=1.0):
    t = np.linspace(0, 2*np.pi, n, endpoint=False)
    return np.column_stack([radius*np.cos(t), radius*np.sin(t)])

def generate_polygon(n=100, radius=1.0, sides=6):
    angles = np.linspace(0, 2*np.pi, sides, endpoint=False)
    corners = np.column_stack([radius*np.cos(angles), radius*np.sin(angles)])
    return _interpolate_polygon(np.vstack([corners, corners[0]]), n)

def generate_star(n=100, radius=1.0, points=5):
    inner = 0.4*radius
    angles = np.linspace(0, 2*np.pi, points*2, endpoint=False)
    radii  = np.tile([radius, inner], points)
    corners = np.column_stack([radii*np.cos(angles), radii*np.sin(angles)])
    return _interpolate_polygon(np.vstack([corners, corners[0]]), n)

def generate_heart(n=100, radius=1.0):
    t = np.linspace(0, 2*np.pi, n, endpoint=False)
    x = 16*np.sin(t)**3
    y = 13*np.cos(t) - 5*np.cos(2*t) - 2*np.cos(3*t) - np.cos(4*t)
    x = x/np.max(np.abs(x))*radius
    y = y/np.max(np.abs(y))*radius
    return np.column_stack([x, y])

def generate_blob(n=100, radius=1.0, seed=42):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 2*np.pi, n, endpoint=False)
    r = radius + rng.uniform(-0.2, 0.2, n)*radius
    return np.column_stack([r*np.cos(t), r*np.sin(t)])

def catmull_rom_smooth(points, density=3):
    if len(points) < 4:
        return points
    result = [points[0]]
    for i in range(len(points)-3):
        p0, p1, p2, p3 = points[i:i+4]
        for t in np.linspace(0, 1, density, endpoint=False):
            t2, t3 = t*t, t*t*t
            x = 0.5*((2*p1[0])+(-p0[0]+p2[0])*t+(2*p0[0]-5*p1[0]+4*p2[0]-p3[0])*t2+(-p0[0]+3*p1[0]-3*p2[0]+p3[0])*t3)
            y = 0.5*((2*p1[1])+(-p0[1]+p2[1])*t+(2*p0[1]-5*p1[1]+4*p2[1]-p3[1])*t2+(-p0[1]+3*p1[1]-3*p2[1]+p3[1])*t3)
            result.append([x, y])
    result.append(points[-1])
    return np.array(result)

SHAPE_REGISTRY = {
    "Circle":   generate_circle,
    "Triangle": lambda n, radius: generate_polygon(n, radius, 3),
    "Square":   lambda n, radius: generate_polygon(n, radius, 4),
    "Pentagon": lambda n, radius: generate_polygon(n, radius, 5),
    "Hexagon":  lambda n, radius: generate_polygon(n, radius, 6),
    "Octagon":  lambda n, radius: generate_polygon(n, radius, 8),
    "Star-4":   lambda n, radius: generate_star(n, radius, 4),
    "Star-5":   lambda n, radius: generate_star(n, radius, 5),
    "Star-6":   lambda n, radius: generate_star(n, radius, 6),
    "Star-8":   lambda n, radius: generate_star(n, radius, 8),
    "Heart":    generate_heart,
    "Blob":     generate_blob,
}


# ═══════════════════════════════════════════════════════════════
# MORPHING
# ═══════════════════════════════════════════════════════════════

def resample_shape(shape, n):
    if shape is None or len(shape) == 0:
        return generate_circle(n, 1.0)
    if len(shape) == n:
        return shape.copy()
    s = shape.copy()
    if not np.allclose(s[0], s[-1]):
        s = np.vstack([s, s[0]])
    return _interpolate_polygon(s, n)

def morph_linear(s1, s2, t):
    return (1-t)*s1 + t*s2

def morph_ease_in_out(s1, s2, t):
    e = 2*t*t if t < 0.5 else 1 - 2*(1-t)**2
    return morph_linear(s1, s2, e)

def morph_elastic(s1, s2, t):
    if t == 0: return s1
    if t == 1: return s2
    c4 = (2*np.pi)/3
    if t < 0.5:
        e = -pow(2, 20*t-10)*np.sin((20*t-11.125)*c4)
    else:
        e = pow(2, -20*t+10)*np.sin((20*t-11.125)*c4)/2 + 1
    return morph_linear(s1, s2, e)

def morph_back(s1, s2, t):
    c1 = 1.70158; c3 = c1 + 1
    e = 1 + c3*pow(t-1, 3) + c1*pow(t-1, 2)
    return morph_linear(s1, s2, e)

def morph_bounce(s1, s2, t):
    n1, d1 = 7.5625, 2.75
    tt = t
    if tt < 1/d1:
        e = n1*tt*tt
    elif tt < 2/d1:
        tt -= 1.5/d1; e = n1*tt*tt + 0.75
    elif tt < 2.5/d1:
        tt -= 2.25/d1; e = n1*tt*tt + 0.9375
    else:
        tt -= 2.625/d1; e = n1*tt*tt + 0.984375
    return morph_linear(s1, s2, e)

def morph_sequence(shapes, t, morph_fn=morph_linear):
    if not shapes:
        return None
    if len(shapes) == 1:
        return shapes[0].copy()
    n_seg  = len(shapes) - 1
    seg    = min(int(t*n_seg), n_seg-1)
    local  = np.clip(t*n_seg - seg, 0, 1)
    s1, s2 = shapes[seg], shapes[seg+1]
    target = max(s1.shape[0], s2.shape[0])
    return morph_fn(resample_shape(s1, target), resample_shape(s2, target), local)

MORPH_MODES = {
    "Linear":      morph_linear,
    "Ease In-Out": morph_ease_in_out,
    "Elastic":     morph_elastic,
    "Back":        morph_back,
    "Bounce":      morph_bounce,
}


# ═══════════════════════════════════════════════════════════════
# SVG TOOLS
# ═══════════════════════════════════════════════════════════════

def parse_svg_content(svg_content, n_points=120):
    try:
        root = ET.fromstring(svg_content)
    except ET.ParseError:
        return None
    all_coords = []
    token_re = re.compile(r'([MLCQHVZmlcqhvz])|([+-]?\d*\.?\d+(?:e[+-]?\d+)?)')
    for elem in root.iter():
        tag = elem.tag.split('}')[-1].lower()
        d = elem.get('d', '')
        if tag == 'path' and d:
            tokens = [t[0] if t[0] else float(t[1]) for t in token_re.findall(d)]
            pts, i = [], 0
            cx, cy, sx, sy = 0., 0., 0., 0.
            while i < len(tokens):
                cmd = tokens[i]; i += 1
                is_rel = isinstance(cmd, str) and cmd.islower()
                if isinstance(cmd, str):
                    cmd = cmd.upper()
                else:
                    cmd, i = 'L', i-1
                try:
                    if cmd == 'M':
                        cx, cy = tokens[i], tokens[i+1]; i += 2
                        if is_rel and pts: cx += pts[-1][0]; cy += pts[-1][1]
                        sx, sy = cx, cy; pts.append((cx, cy))
                    elif cmd == 'L':
                        x, y = tokens[i], tokens[i+1]; i += 2
                        cx, cy = (cx+x, cy+y) if is_rel else (x, y)
                        pts.append((cx, cy))
                    elif cmd == 'C':
                        x1,y1,x2,y2,x,y = tokens[i:i+6]; i += 6
                        if is_rel: x1+=cx;y1+=cy;x2+=cx;y2+=cy;x+=cx;y+=cy
                        for tt in np.linspace(0, 1, 10):
                            xt=(1-tt)**3*cx+3*(1-tt)**2*tt*x1+3*(1-tt)*tt**2*x2+tt**3*x
                            yt=(1-tt)**3*cy+3*(1-tt)**2*tt*y1+3*(1-tt)*tt**2*y2+tt**3*y
                            pts.append((xt, yt))
                        cx, cy = x, y
                    elif cmd == 'Z' and pts:
                        if not (abs(pts[-1][0]-sx)<1e-5 and abs(pts[-1][1]-sy)<1e-5):
                            pts.append((sx, sy))
                except IndexError:
                    break
            all_coords.extend(pts)
        elif tag in ('polygon', 'polyline'):
            coords = re.findall(r'[+-]?\d*\.?\d+', elem.get('points', ''))
            pts = [(float(coords[j]), float(coords[j+1])) for j in range(0, len(coords)-1, 2)]
            all_coords.extend(pts)
    if len(all_coords) < 3:
        return None
    arr = np.array(all_coords)
    center = np.mean(arr, axis=0); arr -= center
    mx = np.max(np.sqrt(np.sum(arr**2, axis=1)))
    if mx > 0:
        arr /= (mx/0.8)
    return resample_shape(arr, n_points)

def export_shape_to_svg(points, filename, gradient_type="Solid", grad_color1=None, grad_color2=None):
    if points is None or len(points) == 0:
        return
    
    scale, offset = 200, 200
    pts_svg = [(p[0]*scale+offset, -p[1]*scale+offset) for p in points]
    path_d = (f"M {pts_svg[0][0]:.2f} {pts_svg[0][1]:.2f} " +
              "".join(f"L {x:.2f} {y:.2f} " for x, y in pts_svg[1:]) + "Z")
    
    defs = ""
    fill_attr = f"fill=\"{grad_color1.name() if grad_color1 else '#4fc3f7'}\""
    
    if gradient_type != "Solid" and grad_color1 and grad_color2:
        grad_id = "morphGrad"
        c1_rgb = f"rgb({grad_color1.red()},{grad_color1.green()},{grad_color1.blue()})"
        c2_rgb = f"rgb({grad_color2.red()},{grad_color2.green()},{grad_color2.blue()})"
        
        xs = [p[0] for p in pts_svg]; ys = [p[1] for p in pts_svg]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        w = max_x - min_x if max_x > min_x else 1
        h = max_y - min_y if max_y > min_y else 1
        
        if gradient_type == "Linear":
            defs = f"""<defs>
      <linearGradient id="{grad_id}" x1="{min_x}" y1="{min_y}" x2="{max_x}" y2="{max_y}" gradientUnits="userSpaceOnUse">
        <stop offset="0%" stop-color="{c1_rgb}" />
        <stop offset="100%" stop-color="{c2_rgb}" />
      </linearGradient>
    </defs>\n"""
        elif gradient_type == "Radial":
            cx, cy = (min_x+max_x)/2, (min_y+max_y)/2
            r = max(w, h)/2
            defs = f"""<defs>
      <radialGradient id="{grad_id}" cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" gradientUnits="userSpaceOnUse">
        <stop offset="0%" stop-color="{c1_rgb}" />
        <stop offset="100%" stop-color="{c2_rgb}" />
      </radialGradient>
    </defs>\n"""
        elif gradient_type == "Conical":
            # SVG standard doesn't natively support conical easily, fallback to linear for SVG export
            defs = f"""<defs>
      <linearGradient id="{grad_id}" x1="{min_x}" y1="{min_y}" x2="{max_x}" y2="{max_y}" gradientUnits="userSpaceOnUse">
        <stop offset="0%" stop-color="{c1_rgb}" />
        <stop offset="50%" stop-color="{c2_rgb}" />
        <stop offset="100%" stop-color="{c1_rgb}" />
      </linearGradient>
    </defs>\n"""
            
        fill_attr = f"fill=\"url(#{grad_id})\""
        
    svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
           f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" '
           f'width="400" height="400">\n'
           f'  {defs}'
           f'  <path d="{path_d}" {fill_attr} stroke="#2c3e50" stroke-width="2"/>\n'
           f'</svg>')
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(svg)


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def create_shape_icon(shape_func, size=32, color=QColor(79,195,247)):
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    try:
        pts = shape_func(n=60, radius=1.0)
    except Exception:
        pts = generate_circle(60, 1.0)
    path = QPainterPath()
    s = size*0.35; cx = cy = size/2
    path.moveTo(cx+pts[0,0]*s, cy-pts[0,1]*s)
    for i in range(1, len(pts)):
        path.lineTo(cx+pts[i,0]*s, cy-pts[i,1]*s)
    path.closeSubpath()
    painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 80)))
    painter.setPen(QPen(color, 1.2))
    painter.drawPath(path)
    painter.end()
    return pixmap

def create_app_icon():
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    cx = cy = 32
    for i in range(10):
        a = i*36*np.pi/180 - np.pi/2
        r = 26 if i%2 == 0 else 12
        x, y = cx+r*np.cos(a), cy+r*np.sin(a)
        if i == 0: path.moveTo(x, y)
        else:       path.lineTo(x, y)
    path.closeSubpath()
    grad = QLinearGradient(0, 0, 64, 64)
    grad.setColorAt(0, QColor(129, 199, 132))
    grad.setColorAt(1, QColor(79, 195, 247))
    painter.setBrush(QBrush(grad))
    painter.setPen(QPen(QColor(220,220,220), 2))
    painter.drawPath(path)
    painter.end()
    return pixmap


# ═══════════════════════════════════════════════════════════════
# CANVAS WIDGET
# ═══════════════════════════════════════════════════════════════

class MorphCanvas(QWidget):
    drawing_finished = Signal()
    point_added      = Signal(int)
    mouse_moved      = Signal(float, float)

    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 400)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        self.points        = np.array([])
        self.fill_color    = COLORS["fill"]
        self.outline_color = COLORS["outline"]
        self.bg_color      = QColor(CANVAS_BG)
        self.line_width    = 2
        self.show_fill     = True
        self.show_outline  = True
        self.show_grid     = False
        self.show_crosshair= True
        self.rotation      = 0.0

        # Gradient properties
        self.gradient_type  = "Solid"
        self.gradient_color1 = QColor(129, 199, 132)  # Light Green
        self.gradient_color2 = QColor(79, 195, 247)   # Light Blue

        # Drawing state
        self.is_drawing      = False
        self.draw_points     = []
        self.freehand_points = []
        self.draw_finished   = False
        self.auto_close      = True
        self.smooth_curve    = False
        self.freehand_mode   = False
        self.snap_to_start   = False

    def start_drawing(self, freehand=False):
        self.is_drawing    = True
        self.freehand_mode = freehand
        self.draw_points.clear()
        self.freehand_points.clear()
        self.draw_finished = False
        self.update()

    def clear_drawing(self):
        self.draw_points.clear()
        self.freehand_points.clear()
        self.draw_finished = False
        self.point_added.emit(0)
        self.update()

    def get_normalized_numpy(self, n_points):
        if len(self.draw_points) < 3:
            return None
        pts = np.array([(p.x(), p.y()) for p in self.draw_points])
        if self.smooth_curve and len(pts) >= 4:
            pts = catmull_rom_smooth(pts, density=3)
        if self.auto_close and not np.allclose(pts[0], pts[-1]):
            pts = np.vstack([pts, pts[0]])
        center = np.mean(pts, axis=0); pts -= center
        mx = np.max(np.sqrt(np.sum(pts**2, axis=1)))
        if mx > 0:
            pts /= (mx/0.8)
        return resample_shape(pts, n_points)

    def update_points(self, pts):
        self.points = pts
        self.update()

    def apply_rotation(self, points, angle_deg):
        if angle_deg == 0 or points is None or len(points) == 0:
            return points
        a = np.radians(angle_deg)
        c, s = np.cos(a), np.sin(a)
        rot = np.array([[c, -s], [s, c]])
        return points @ rot.T

    # ── events ──────────────────────────────────────────────

    def mousePressEvent(self, event):
        if self.is_drawing and not self.draw_finished:
            pos = event.position()
            if event.button() == Qt.MouseButton.LeftButton:
                if self.freehand_mode:
                    self.freehand_points.append(pos)
                else:
                    self.draw_points.append(pos)
                    self.point_added.emit(len(self.draw_points))
                self.update()
            elif event.button() == Qt.MouseButton.RightButton:
                if self.draw_points:
                    self.draw_points.pop()
                    self.point_added.emit(len(self.draw_points))
                self.update()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = event.position()
        self.mouse_moved.emit(pos.x(), pos.y())
        if self.is_drawing and not self.draw_finished:
            if self.freehand_mode and event.buttons() & Qt.MouseButton.LeftButton:
                self.freehand_points.append(pos)
                if len(self.freehand_points) % 3 == 0:
                    self.draw_points.append(self.freehand_points[-1])
                self.update()
            else:
                self.snap_to_start = False
                if self.draw_points:
                    start = self.draw_points[0]
                    dist = np.hypot(pos.x()-start.x(), pos.y()-start.y())
                    self.snap_to_start = dist < 15
                self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_drawing and self.freehand_mode and not self.draw_finished:
            self.draw_finished = True
            self.drawing_finished.emit()
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.is_drawing and len(self.draw_points) >= 3 and not self.draw_finished:
            self.draw_finished = True
            self.drawing_finished.emit()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_C):
            if self.is_drawing and len(self.draw_points) >= 3 and not self.draw_finished:
                self.draw_finished = True
                self.drawing_finished.emit()
        elif event.key() == Qt.Key.Key_Escape:
            self.clear_drawing()
        elif event.key() == Qt.Key.Key_S:
            self.smooth_curve = not self.smooth_curve
            self.update()

    # ── painting ────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background with subtle radial gradient
        grad = QRadialGradient(self.rect().center(), max(self.width(), self.height())/2)
        grad.setColorAt(0, self.bg_color.lighter(115))
        grad.setColorAt(1, self.bg_color)
        painter.fillRect(self.rect(), grad)

        # Grid
        if self.show_grid:
            painter.setPen(QPen(GRID_COLOR, 1, Qt.PenStyle.DotLine))
            for x in range(0, self.width(), 40):
                painter.drawLine(x, 0, x, self.height())
            for y in range(0, self.height(), 40):
                painter.drawLine(0, y, self.width(), y)

        # Crosshair
        if self.show_crosshair:
            cx, cy = self.width()//2, self.height()//2
            painter.setPen(QPen(COLORS["crosshair"], 1, Qt.PenStyle.DotLine))
            painter.drawLine(cx-30, cy, cx+30, cy)
            painter.drawLine(cx, cy-30, cx, cy+30)

        # Drawing mode overlay
        if self.is_drawing:
            self._paint_drawing_ui(painter)
            mode_text = "FREEHAND MODE" if self.freehand_mode else "POINT-BY-POINT MODE"
            painter.setPen(QPen(QColor(255,100,100,180), 1))
            painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            painter.drawText(10, 20, mode_text)
            if not self.draw_finished:
                painter.setPen(QPen(QColor(180,180,180,120)))
                painter.setFont(QFont("Segoe UI", 9))
                hint = "Double-click / Enter to finish · Right-click to undo · Esc to clear"
                painter.drawText(10, self.height()-10, hint)
            return

        # View mode – no data
        if self.points is None or self.points.size == 0:
            painter.setPen(QPen(QColor(100,100,100), 14))
            painter.setFont(QFont("Segoe UI", 14))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                             "Select a preset or draw a shape")
            painter.end()
            return

        # Draw shape
        rotated = self.apply_rotation(self.points, self.rotation)
        w, h = self.width(), self.height()
        scale = min(w, h)/2*0.85
        path = QPainterPath()
        path.moveTo(w/2+rotated[0,0]*scale, h/2-rotated[0,1]*scale)
        for i in range(1, len(rotated)):
            path.lineTo(w/2+rotated[i,0]*scale, h/2-rotated[i,1]*scale)
        path.closeSubpath()

        if self.show_fill:
            rect = path.boundingRect()
            if self.gradient_type == "Linear":
                g = QLinearGradient(rect.topLeft(), rect.bottomRight())
                g.setColorAt(0.0, self.gradient_color1)
                g.setColorAt(1.0, self.gradient_color2)
                painter.setBrush(QBrush(g))
            elif self.gradient_type == "Radial":
                g = QRadialGradient(rect.center(), max(rect.width(), rect.height())/2)
                g.setColorAt(0.0, self.gradient_color1)
                g.setColorAt(1.0, self.gradient_color2)
                painter.setBrush(QBrush(g))
            elif self.gradient_type == "Conical":
                g = QConicalGradient(rect.center(), 0)
                g.setColorAt(0.0, self.gradient_color1)
                g.setColorAt(1.0, self.gradient_color2)
                painter.setBrush(QBrush(g))
            else: # Solid
                painter.setBrush(QBrush(self.fill_color))
        else:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            
        if self.show_outline:
            painter.setPen(QPen(self.outline_color, self.line_width))
        else:
            painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)
        painter.end()

    def _paint_drawing_ui(self, painter):
        if self.freehand_mode and self.freehand_points:
            painter.setPen(QPen(COLORS["freehand_preview"], 2))
            path = QPainterPath()
            path.moveTo(self.freehand_points[0])
            for p in self.freehand_points[1:]:
                path.lineTo(p)
            painter.drawPath(path)

        if self.draw_points:
            painter.setPen(QPen(COLORS["drawing_line"], 2))
            painter.setBrush(QBrush(COLORS["drawing_line"]))
            for i, p in enumerate(self.draw_points):
                r = 6 if i == 0 else 4
                painter.drawEllipse(p, r, r)
            path = QPainterPath()
            path.moveTo(self.draw_points[0])
            for p in self.draw_points[1:]:
                path.lineTo(p)
            if self.snap_to_start:
                painter.setPen(QPen(COLORS["snap_indicator"], 2, Qt.PenStyle.DashDotLine))
                path.lineTo(self.draw_points[0])
                painter.setBrush(QBrush(QColor(50,205,50,100)))
                painter.drawEllipse(self.draw_points[0], 14, 14)
            else:
                painter.setPen(QPen(COLORS["drawing_line"], 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

    def to_image(self):
        img = QImage(self.size(), QImage.Format.Format_ARGB32)
        img.fill(self.bg_color)
        p = QPainter(img); self.render(p); p.end()
        return img


# ═══════════════════════════════════════════════════════════════
# DIALOGS
# ═══════════════════════════════════════════════════════════════

class ShapeSequenceDialog(QDialog):
    def __init__(self, available_shapes, current_sequence, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sequence Manager")
        self.setMinimumWidth(460)
        self.setMinimumHeight(400)
        self.available = available_shapes
        self.sequence  = current_sequence.copy()
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)

        left = QVBoxLayout()
        left.addWidget(QLabel("Library"))
        self.avail_list = QListWidget()
        self.avail_list.addItems(self.available)
        self.avail_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        left.addWidget(self.avail_list)

        btns = QVBoxLayout()
        btns.addStretch()
        add_btn    = QPushButton("➕ Add")
        remove_btn = QPushButton("➖ Remove")
        up_btn     = QPushButton("⬆")
        down_btn   = QPushButton("⬇")
        for b in (add_btn, remove_btn, up_btn, down_btn):
            b.setFixedWidth(90)
            btns.addWidget(b)
        btns.addStretch()

        right = QVBoxLayout()
        right.addWidget(QLabel("Current Sequence"))
        self.seq_list = QListWidget()
        self.seq_list.addItems(self.sequence)
        self.seq_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        right.addWidget(self.seq_list)
        self.count_lbl = QLabel(f"Total: {len(self.sequence)} shapes")
        right.addWidget(self.count_lbl)

        dlg_btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dlg_btns.accepted.connect(self.accept)
        dlg_btns.rejected.connect(self.reject)
        right.addWidget(dlg_btns)

        layout.addLayout(left, 1)
        layout.addLayout(btns, 0)
        layout.addLayout(right, 1)

        add_btn.clicked.connect(self._add)
        remove_btn.clicked.connect(self._remove)
        up_btn.clicked.connect(lambda: self._move(-1))
        down_btn.clicked.connect(lambda: self._move(1))

    def _add(self):
        for item in self.avail_list.selectedItems():
            self.sequence.append(item.text())
        self._refresh()

    def _remove(self):
        for item in self.seq_list.selectedItems():
            self.sequence.remove(item.text())
        self._refresh()

    def _move(self, d):
        row = self.seq_list.currentRow()
        if row < 0: return
        nr = row + d
        if 0 <= nr < len(self.sequence):
            self.sequence[row], self.sequence[nr] = self.sequence[nr], self.sequence[row]
            self._refresh()
            self.seq_list.setCurrentRow(nr)

    def _refresh(self):
        self.seq_list.clear()
        self.seq_list.addItems(self.sequence)
        self.count_lbl.setText(f"Total: {len(self.sequence)} shapes")

    def get_sequence(self):
        return self.sequence


# ═══════════════════════════════════════════════════════════════
# MAIN WINDOW
# ═══════════════════════════════════════════════════════════════

class MorphApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shape Morphing Studio")
        self.resize(1220, 760)
        self.setStyleSheet(DARK_STYLE)
        self.setWindowIcon(QIcon(create_app_icon()))

        self.n_points         = DEFAULT_RESOLUTION
        self.custom_shapes    = {}
        self.custom_counter   = 1
        self.morph_seq_names  = ["Circle", "Star-5"]
        self.preloaded_shapes = []
        self.is_random_seq    = False
        self.ping_pong_dir    = 1

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._advance)

        self._build_menubar()
        self._build_toolbar()
        self._build_central()
        self._build_statusbar()
        self._connect_all()
        self._update_shapes()

    # ── menu bar ────────────────────────────────────────────

    def _build_menubar(self):
        mb = self.menuBar()

        file_menu = mb.addMenu("&File")
        file_menu.addAction("Import SVG…", self._import_svg, QKeySequence("Ctrl+I"))
        file_menu.addSeparator()
        file_menu.addAction("Export PNG…", self._save_png, QKeySequence("Ctrl+S"))
        file_menu.addAction("Export GIF…", self._save_gif, QKeySequence("Ctrl+G"))
        file_menu.addAction("Export SVG…", self._save_svg, QKeySequence("Ctrl+E"))
        file_menu.addAction("Export PNG Sequence…", self._save_png_seq)
        file_menu.addSeparator()
        file_menu.addAction("Quit", self.close, QKeySequence("Ctrl+Q"))

        view_menu = mb.addMenu("&View")
        view_menu.addAction("Toggle Grid", self._toggle_grid, QKeySequence("G"))
        view_menu.addAction("Toggle Crosshair", self._toggle_crosshair)

        help_menu = mb.addMenu("&Help")
        help_menu.addAction("About…", self._show_about)

    # ── toolbar ─────────────────────────────────────────────

    def _build_toolbar(self):
        tb = QToolBar("Transport")
        tb.setMovable(False)
        tb.setIconSize(QSize(20, 20))
        self.addToolBar(tb)

        self.tb_play = QPushButton("▶")
        self.tb_play.setCheckable(True)
        self.tb_play.setFixedSize(34, 30)
        self.tb_play.setToolTip("Play / Pause  (Space)")
        self.tb_play.setStyleSheet(
            "QPushButton{font-size:14px;font-weight:bold}"
            "QPushButton:checked{color:#4fc3f7}")
        tb.addWidget(self.tb_play)

        self.tb_stop = QPushButton("⏹")
        self.tb_stop.setFixedSize(34, 30)
        self.tb_stop.setToolTip("Reset to start  (Home)")
        self.tb_stop.setStyleSheet("QPushButton{font-size:13px}")
        tb.addWidget(self.tb_stop)

        tb.addSeparator()
        tb.addWidget(QLabel("  Progress "))
        self.tb_slider = QSlider(Qt.Orientation.Horizontal)
        self.tb_slider.setRange(0, 100)
        self.tb_slider.setValue(0)
        self.tb_slider.setMinimumWidth(200)
        tb.addWidget(self.tb_slider)
        self.tb_pct = QLabel("  0% ")
        self.tb_pct.setFixedWidth(48)
        tb.addWidget(self.tb_pct)

        tb.addSeparator()
        tb.addWidget(QLabel(" FPS "))
        self.tb_fps = QSpinBox()
        self.tb_fps.setRange(1, 60)
        self.tb_fps.setValue(DEFAULT_FPS)
        self.tb_fps.setFixedWidth(56)
        tb.addWidget(self.tb_fps)

    # ── central widget ──────────────────────────────────────

    def _build_central(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(splitter)

        self.canvas = MorphCanvas()
        splitter.addWidget(self.canvas)

        right_panel = QWidget()
        right_panel.setMaximumWidth(340)
        right_panel.setMinimumWidth(260)
        rp_layout = QVBoxLayout(right_panel)
        rp_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        rp_layout.addWidget(self.tabs)

        self._build_sequence_tab()
        self._build_morph_tab()
        self._build_style_tab()
        self._build_tools_tab()

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)

    # ── Tab: Sequence ───────────────────────────────────────

    def _build_sequence_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setSpacing(8)

        lib_grp = QGroupBox("Shape Library")
        grid = QGridLayout(lib_grp)
        grid.setSpacing(4)
        names = list(SHAPE_REGISTRY.keys())
        cols = 3
        for idx, name in enumerate(names):
            icon = create_shape_icon(SHAPE_REGISTRY[name], 28)
            btn = QPushButton(name)
            btn.setIcon(QIcon(icon))
            btn.setIconSize(QSize(22, 22))
            btn.setToolTip(f"Add {name} to sequence")
            btn.clicked.connect(lambda checked, n=name: self._add_shape_to_seq(n))
            grid.addWidget(btn, idx//cols, idx%cols)
        lay.addWidget(lib_grp)

        pre_grp = QGroupBox("Presets")
        pre_lay = QVBoxLayout(pre_grp)
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("— choose preset —")
        self.preset_combo.addItems(PRESET_SEQUENCES.keys())
        pre_lay.addWidget(self.preset_combo)
        lay.addWidget(pre_grp)

        seq_grp = QGroupBox("Current Sequence")
        seq_lay = QVBoxLayout(seq_grp)
        self.seq_list = QListWidget()
        self.seq_list.setMaximumHeight(140)
        self.seq_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        seq_lay.addWidget(self.seq_list)

        btn_row = QHBoxLayout()
        self.seq_edit_btn  = QPushButton("Edit…")
        self.seq_remove_btn= QPushButton("Remove")
        self.seq_clear_btn = QPushButton("Clear")
        btn_row.addWidget(self.seq_edit_btn)
        btn_row.addWidget(self.seq_remove_btn)
        btn_row.addWidget(self.seq_clear_btn)
        seq_lay.addLayout(btn_row)
        lay.addWidget(seq_grp)

        rnd_grp = QGroupBox("Random Sequence")
        rnd_lay = QHBoxLayout(rnd_grp)
        self.rand_count = QSpinBox(); self.rand_count.setRange(2, 20); self.rand_count.setValue(5)
        self.rand_btn = QPushButton("🎲 Generate")
        rnd_lay.addWidget(QLabel("Count:"))
        rnd_lay.addWidget(self.rand_count)
        rnd_lay.addWidget(self.rand_btn)
        lay.addWidget(rnd_grp)

        lay.addStretch()
        scroll.setWidget(content)
        self.tabs.addTab(scroll, "Sequence")
        self._refresh_seq_list()

    # ── Tab: Morph ──────────────────────────────────────────

    def _build_morph_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setSpacing(8)

        alg_grp = QGroupBox("Algorithm")
        alg_lay = QVBoxLayout(alg_grp)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(MORPH_MODES.keys())
        alg_lay.addWidget(self.mode_combo)
        lay.addWidget(alg_grp)

        res_grp = QGroupBox("Resolution")
        res_lay = QVBoxLayout(res_grp)
        self.res_slider = QSlider(Qt.Orientation.Horizontal)
        self.res_slider.setRange(20, 300)
        self.res_slider.setValue(self.n_points)
        self.res_lbl = QLabel(f"{self.n_points} points")
        res_lay.addWidget(self.res_slider)
        res_lay.addWidget(self.res_lbl)
        lay.addWidget(res_grp)

        rot_grp = QGroupBox("Rotation")
        rot_lay = QVBoxLayout(rot_grp)
        self.rot_slider = QSlider(Qt.Orientation.Horizontal)
        self.rot_slider.setRange(-180, 180)
        self.rot_slider.setValue(0)
        self.rot_lbl = QLabel("0°")
        rot_lay.addWidget(self.rot_slider)
        rot_lay.addWidget(self.rot_lbl)
        lay.addWidget(rot_grp)

        dir_grp = QGroupBox("Animation Direction")
        dir_lay = QVBoxLayout(dir_grp)
        self.dir_combo = QComboBox()
        self.dir_combo.addItems(["Forward", "Ping-Pong", "Reverse"])
        dir_lay.addWidget(self.dir_combo)
        lay.addWidget(dir_grp)

        lay.addStretch()
        scroll.setWidget(content)
        self.tabs.addTab(scroll, "Morph")

    # ── Tab: Style ──────────────────────────────────────────

    def _build_style_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setSpacing(8)

        # Fill & Gradient
        fill_grp = QGroupBox("Fill & Gradient")
        fill_lay = QVBoxLayout(fill_grp)
        
        self.fill_cb = QCheckBox("Show Fill", checked=True)
        fill_lay.addWidget(self.fill_cb)
        
        grad_type_lay = QHBoxLayout()
        grad_type_lay.addWidget(QLabel("Type:"))
        self.gradient_combo = QComboBox()
        self.gradient_combo.addItems(["Solid", "Linear", "Radial", "Conical"])
        grad_type_lay.addWidget(self.gradient_combo)
        fill_lay.addLayout(grad_type_lay)

        fill_lay.addWidget(QLabel("Color 1 (Inner/Start):"))
        self.c1_btn = QPushButton("Choose Color 1…")
        fill_lay.addWidget(self.c1_btn)
        fill_lay.addLayout(self._swatch_row(self._set_grad_color1))

        fill_lay.addWidget(QLabel("Color 2 (Outer/End):"))
        self.c2_btn = QPushButton("Choose Color 2…")
        fill_lay.addWidget(self.c2_btn)
        fill_lay.addLayout(self._swatch_row(self._set_grad_color2))
        
        lay.addWidget(fill_grp)

        # Outline
        out_grp = QGroupBox("Outline")
        out_lay = QVBoxLayout(out_grp)
        self.out_cb = QCheckBox("Show Outline", checked=True)
        out_lay.addWidget(self.out_cb)
        self.out_btn = QPushButton("Choose Color…")
        out_lay.addWidget(self.out_btn)
        out_lay.addLayout(self._swatch_row(self._set_outline_color))
        hl = QHBoxLayout()
        hl.addWidget(QLabel("Width:"))
        self.lw_slider = QSlider(Qt.Orientation.Horizontal)
        self.lw_slider.setRange(1, 10); self.lw_slider.setValue(2)
        self.lw_lbl = QLabel("2")
        hl.addWidget(self.lw_slider); hl.addWidget(self.lw_lbl)
        out_lay.addLayout(hl)
        lay.addWidget(out_grp)

        # Background
        bg_grp = QGroupBox("Background")
        bg_lay = QVBoxLayout(bg_grp)
        self.bg_btn = QPushButton("Choose Color…")
        bg_lay.addWidget(self.bg_btn)
        bg_lay.addLayout(self._swatch_row(self._set_bg_color, dark=False))
        lay.addWidget(bg_grp)

        # Grid / Crosshair
        disp_grp = QGroupBox("Display")
        disp_lay = QVBoxLayout(disp_grp)
        self.grid_cb = QCheckBox("Show Grid")
        self.cross_cb = QCheckBox("Show Crosshair", checked=True)
        disp_lay.addWidget(self.grid_cb)
        disp_lay.addWidget(self.cross_cb)
        lay.addWidget(disp_grp)

        lay.addStretch()
        scroll.setWidget(content)
        self.tabs.addTab(scroll, "Style")

    # ── Tab: Tools ──────────────────────────────────────────

    def _build_tools_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setSpacing(8)

        draw_grp = QGroupBox("Drawing Tools")
        draw_lay = QVBoxLayout(draw_grp)
        self.draw_btn = QPushButton("✏️  Point-by-Point")
        self.draw_btn.setCheckable(True)
        self.draw_btn.setToolTip("Click to place points. Double-click or Enter to finish.")
        draw_lay.addWidget(self.draw_btn)
        self.freehand_btn = QPushButton("🖊️  Freehand")
        self.freehand_btn.setCheckable(True)
        self.freehand_btn.setToolTip("Click and drag to draw freely.")
        draw_lay.addWidget(self.freehand_btn)

        self.draw_info = QLabel("Points: 0")
        draw_lay.addWidget(self.draw_info)

        db = QHBoxLayout()
        self.undo_pt_btn = QPushButton("↩ Undo")
        self.clear_draw_btn = QPushButton("✕ Clear")
        db.addWidget(self.undo_pt_btn); db.addWidget(self.clear_draw_btn)
        draw_lay.addLayout(db)

        self.save_shape_btn = QPushButton("💾 Save as Shape")
        self.save_shape_btn.setEnabled(False)
        draw_lay.addWidget(self.save_shape_btn)

        self.import_btn = QPushButton("📄 Import SVG…")
        draw_lay.addWidget(self.import_btn)
        lay.addWidget(draw_grp)

        exp_grp = QGroupBox("Export")
        exp_lay = QVBoxLayout(exp_grp)
        self.exp_png_btn = QPushButton("📸  Export PNG…")
        self.exp_gif_btn = QPushButton("🎞️  Export GIF…")
        self.exp_svg_btn = QPushButton("📤  Export SVG…")
        self.exp_seq_btn = QPushButton("📁  Export PNG Sequence…")
        exp_lay.addWidget(self.exp_png_btn)
        exp_lay.addWidget(self.exp_gif_btn)
        exp_lay.addWidget(self.exp_svg_btn)
        exp_lay.addWidget(self.exp_seq_btn)
        lay.addWidget(exp_grp)

        lay.addStretch()
        scroll.setWidget(content)
        self.tabs.addTab(scroll, "Tools")

    # ── status bar ──────────────────────────────────────────

    def _build_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.coord_lbl = QLabel("")
        self.coord_lbl.setFixedWidth(140)
        self.status.addPermanentWidget(self.coord_lbl)
        self.status.showMessage("Ready")

    # ── swatch helper ───────────────────────────────────────

    def _swatch_row(self, callback, dark=True):
        row = QHBoxLayout()
        row.setSpacing(3)
        row.setContentsMargins(0, 4, 0, 0)
        for c in PRESET_COLORS:
            btn = QPushButton()
            btn.setFixedSize(22, 22)
            border = "#555" if dark else "#333"
            btn.setStyleSheet(
                f"QPushButton{{background:{c.name()};border:2px solid {border};"
                f"border-radius:3px;padding:0}}"
                f"QPushButton:hover{{border-color:#4fc3f7}}")
            btn.clicked.connect(lambda _, color=c: callback(color))
            row.addWidget(btn)
        row.addStretch()
        return row

    # ── connections ─────────────────────────────────────────

    def _connect_all(self):
        # Toolbar
        self.tb_play.toggled.connect(self._toggle_anim)
        self.tb_stop.clicked.connect(self._stop_anim)
        self.tb_slider.valueChanged.connect(self._on_progress)
        self.tb_fps.valueChanged.connect(self._on_fps_change)

        # Sequence tab
        self.preset_combo.currentTextChanged.connect(self._load_preset)
        self.seq_edit_btn.clicked.connect(self._edit_sequence)
        self.seq_remove_btn.clicked.connect(self._remove_selected_seq)
        self.seq_clear_btn.clicked.connect(self._clear_sequence)
        self.rand_btn.clicked.connect(self._generate_random)

        # Morph tab
        self.mode_combo.currentTextChanged.connect(self._update_morph)
        self.res_slider.valueChanged.connect(self._on_res_change)
        self.rot_slider.valueChanged.connect(self._on_rotation)

        # Style tab
        self.fill_cb.toggled.connect(lambda v: (setattr(self.canvas, 'show_fill', v), self.canvas.update()))
        self.gradient_combo.currentTextChanged.connect(lambda t: (setattr(self.canvas, 'gradient_type', t), self.canvas.update()))
        self.c1_btn.clicked.connect(lambda: self._pick_color('grad1'))
        self.c2_btn.clicked.connect(lambda: self._pick_color('grad2'))
        
        self.out_cb.toggled.connect(lambda v: (setattr(self.canvas, 'show_outline', v), self.canvas.update()))
        self.out_btn.clicked.connect(lambda: self._pick_color('outline'))
        self.bg_btn.clicked.connect(lambda: self._pick_color('bg'))
        self.lw_slider.valueChanged.connect(self._on_linewidth)
        self.grid_cb.toggled.connect(lambda v: (setattr(self.canvas, 'show_grid', v), self.canvas.update()))
        self.cross_cb.toggled.connect(lambda v: (setattr(self.canvas, 'show_crosshair', v), self.canvas.update()))

        # Tools tab
        self.draw_btn.toggled.connect(self._toggle_draw_point)
        self.freehand_btn.toggled.connect(self._toggle_draw_freehand)
        self.undo_pt_btn.clicked.connect(self._undo_point)
        self.clear_draw_btn.clicked.connect(self.canvas.clear_drawing)
        self.save_shape_btn.clicked.connect(self._save_custom)
        self.import_btn.clicked.connect(self._import_svg)
        self.canvas.drawing_finished.connect(self._on_draw_finished)
        self.canvas.point_added.connect(lambda n: self.draw_info.setText(f"Points: {n}"))

        # Export
        self.exp_png_btn.clicked.connect(self._save_png)
        self.exp_gif_btn.clicked.connect(self._save_gif)
        self.exp_svg_btn.clicked.connect(self._save_svg)
        self.exp_seq_btn.clicked.connect(self._save_png_seq)

        # Canvas mouse tracking
        self.canvas.mouse_moved.connect(self._on_canvas_mouse)

        # Keyboard shortcuts
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, lambda: self.tb_play.toggle())
        QShortcut(QKeySequence(Qt.Key.Key_Home),  self, self._stop_anim)
        QShortcut(QKeySequence(Qt.Key.Key_R),      self, self._generate_random)

    # ── sequence logic ──────────────────────────────────────

    def _add_shape_to_seq(self, name):
        self.is_random_seq = False
        self.morph_seq_names.append(name)
        self._refresh_seq_list()
        self._update_shapes()

    def _load_preset(self, text):
        if text in PRESET_SEQUENCES:
            self.is_random_seq = False
            self.morph_seq_names = PRESET_SEQUENCES[text].copy()
            self._refresh_seq_list()
            self._update_shapes()
            self.status.showMessage(f"Loaded preset: {text}")

    def _edit_sequence(self):
        avail = list(SHAPE_REGISTRY.keys()) + list(self.custom_shapes.keys())
        dlg = ShapeSequenceDialog(avail, self.morph_seq_names, self)
        if dlg.exec() and len(dlg.get_sequence()) >= 2:
            self.is_random_seq = False
            self.morph_seq_names = dlg.get_sequence()
            self._refresh_seq_list()
            self._update_shapes()

    def _remove_selected_seq(self):
        row = self.seq_list.currentRow()
        if 0 <= row < len(self.morph_seq_names):
            self.morph_seq_names.pop(row)
            self._refresh_seq_list()
            self._update_shapes()

    def _clear_sequence(self):
        self.morph_seq_names.clear()
        self.preloaded_shapes.clear()
        self._refresh_seq_list()
        self.canvas.update_points(np.array([]))

    def _generate_random(self):
        length = self.rand_count.value()
        names  = list(SHAPE_REGISTRY.keys())
        self.preloaded_shapes = []
        desc = []
        for _ in range(length):
            name = random.choice(names)
            func = SHAPE_REGISTRY[name]
            rnd_pts = random.randint(5, 80)
            try:
                shape = func(n=rnd_pts, radius=1.0)
            except Exception:
                shape = func(rnd_pts, 1.0)
            self.preloaded_shapes.append(shape)
            desc.append(f"{name}({rnd_pts})")
        self.is_random_seq = True
        self.morph_seq_names = desc
        self._refresh_seq_list()
        self.tb_slider.setValue(0)
        self._update_morph()
        self.status.showMessage(f"Random sequence: {len(desc)} shapes")

    def _refresh_seq_list(self):
        self.seq_list.clear()
        for i, name in enumerate(self.morph_seq_names):
            self.seq_list.addItem(f"{i+1}. {name}")

    # ── shape loading ───────────────────────────────────────

    def _load_shape(self, name):
        if name in self.custom_shapes:
            return self.custom_shapes[name]
        if name in SHAPE_REGISTRY:
            return SHAPE_REGISTRY[name](self.n_points, radius=1.0)
        return None

    def _update_shapes(self):
        if self.is_random_seq and self.preloaded_shapes:
            self._update_morph()
            return
        self.preloaded_shapes = []
        for name in self.morph_seq_names:
            shape = self._load_shape(name)
            if shape is not None:
                self.preloaded_shapes.append(shape)
        self._update_morph()

    # ── morph / animation ───────────────────────────────────

    def _update_morph(self):
        t  = self.tb_slider.value() / 100.0
        fn = MORPH_MODES[self.mode_combo.currentText()]
        morphed = morph_sequence(self.preloaded_shapes, t, fn)
        if morphed is not None:
            self.canvas.rotation = self.rot_slider.value()
            self.canvas.update_points(morphed)

    def _on_progress(self, v):
        self.tb_pct.setText(f"  {v}% ")
        self._update_morph()
        self._update_status()

    def _toggle_anim(self, checked):
        if checked:
            self.anim_timer.start()
            self.tb_play.setText("⏸")
            self.status.showMessage("Playing…")
        else:
            self.anim_timer.stop()
            self.tb_play.setText("▶")
            self.status.showMessage("Paused")

    def _stop_anim(self):
        self.tb_play.setChecked(False)
        self.tb_slider.setValue(0)

    def _advance(self):
        direction = self.dir_combo.currentText()
        val = self.tb_slider.value()
        if direction == "Forward":
            val = (val + 1) % 101
        elif direction == "Reverse":
            val = (val - 1) % 101
            if val < 0: val = 100
        elif direction == "Ping-Pong":
            val += self.ping_pong_dir
            if val >= 100:
                val = 100; self.ping_pong_dir = -1
            elif val <= 0:
                val = 0; self.ping_pong_dir = 1
        self.tb_slider.setValue(val)

    def _on_fps_change(self, v):
        self.anim_timer.setInterval(1000 // v)

    # ── controls ────────────────────────────────────────────

    def _on_res_change(self, v):
        self.n_points = v
        self.res_lbl.setText(f"{v} points")
        if not self.is_random_seq:
            self._update_shapes()

    def _on_rotation(self, v):
        self.rot_lbl.setText(f"{v}°")
        self._update_morph()

    def _on_linewidth(self, v):
        self.lw_lbl.setText(str(v))
        self.canvas.line_width = v
        self.canvas.update()

    # ── colour helpers ──────────────────────────────────────

    def _set_grad_color1(self, c):
        self.canvas.gradient_color1 = c; self.canvas.update()

    def _set_grad_color2(self, c):
        self.canvas.gradient_color2 = c; self.canvas.update()

    def _set_outline_color(self, c):
        self.canvas.outline_color = c; self.canvas.update()

    def _set_bg_color(self, c):
        self.canvas.bg_color = c; self.canvas.update()

    def _pick_color(self, target):
        if target == 'grad1':
            init_c = self.canvas.gradient_color1
        elif target == 'grad2':
            init_c = self.canvas.gradient_color2
        elif target == 'outline':
            init_c = self.canvas.outline_color
        else:
            init_c = self.canvas.bg_color
        c = QColorDialog.getColor(init_c, self, "Choose Color")
        if c.isValid():
            if target == 'grad1':    self.canvas.gradient_color1 = c
            elif target == 'grad2':  self.canvas.gradient_color2 = c
            elif target == 'outline':self.canvas.outline_color = c
            else:                   self.canvas.bg_color = c
            self.canvas.update()

    # ── drawing ─────────────────────────────────────────────

    def _toggle_draw_point(self, checked):
        if checked:
            self.freehand_btn.setChecked(False)
            self._enter_draw_mode(freehand=False)
        else:
            if not self.freehand_btn.isChecked():
                self._exit_draw_mode()

    def _toggle_draw_freehand(self, checked):
        if checked:
            self.draw_btn.setChecked(False)
            self._enter_draw_mode(freehand=True)
        else:
            if not self.draw_btn.isChecked():
                self._exit_draw_mode()

    def _enter_draw_mode(self, freehand=False):
        self.anim_timer.stop(); self.tb_play.setChecked(False)
        self.canvas.start_drawing(freehand=freehand)
        self.save_shape_btn.setEnabled(False)
        self.status.showMessage("Drawing mode — double-click or Enter to finish")

    def _exit_draw_mode(self):
        self.canvas.is_drawing = False
        self.canvas.update()
        self._update_shapes()
        self.status.showMessage("Ready")

    def _on_draw_finished(self):
        self.save_shape_btn.setEnabled(True)
        self.draw_btn.setChecked(False)
        self.freehand_btn.setChecked(False)
        self.status.showMessage("Drawing finished — save or clear")

    def _undo_point(self):
        if self.canvas.draw_points:
            self.canvas.draw_points.pop()
            self.canvas.point_added.emit(len(self.canvas.draw_points))
            self.canvas.update()

    def _save_custom(self):
        arr = self.canvas.get_normalized_numpy(self.n_points)
        if arr is None:
            QMessageBox.warning(self, "Cannot Save", "Need at least 3 points.")
            return
        name = f"Custom {self.custom_counter}"
        self.custom_shapes[name] = arr
        self.custom_counter += 1
        QMessageBox.information(self, "Saved", f"Shape '{name}' saved to library!")
        self.draw_btn.setChecked(False)
        self.freehand_btn.setChecked(False)
        self._exit_draw_mode()

    def _import_svg(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import SVG", "", "SVG (*.svg)")
        if not path: return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                arr = parse_svg_content(f.read(), self.n_points)
            if arr is not None:
                name = f"SVG {self.custom_counter}"
                self.custom_shapes[name] = arr
                self.custom_counter += 1
                QMessageBox.information(self, "Imported", f"Shape '{name}' imported!")
                self.status.showMessage(f"Imported {name}")
            else:
                QMessageBox.warning(self, "Error", "Could not extract shapes from SVG.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to import SVG:\n{e}")

    # ── view toggles ────────────────────────────────────────

    def _toggle_grid(self):
        self.grid_cb.toggle()

    def _toggle_crosshair(self):
        self.cross_cb.toggle()

    # ── export ──────────────────────────────────────────────

    def _save_png(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save PNG", "morph.png", "PNG (*.png)")
        if path:
            self.canvas.to_image().save(path)
            self.status.showMessage(f"Saved PNG: {path}")

    def _save_gif(self):
        if not self.preloaded_shapes:
            QMessageBox.warning(self, "No Shapes", "Add shapes to the sequence first.")
            return
        try:
            from PIL import Image as PILImage
        except ImportError:
            QMessageBox.warning(self, "Missing Package",
                                "Install Pillow for GIF export:\n  pip install Pillow")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save GIF", "morph.gif", "GIF (*.gif)")
        if not path: return

        frames = []
        fn = MORPH_MODES[self.mode_combo.currentText()]
        total = 100
        prog = QProgressDialog("Rendering GIF frames…", "Cancel", 0, total, self)
        prog.setWindowModality(Qt.WindowModality.WindowModal)
        prog.show()

        for i in range(total):
            if prog.wasCanceled(): break
            t = i / 100.0
            morphed = morph_sequence(self.preloaded_shapes, t, fn)
            if morphed is not None:
                self.canvas.update_points(morphed)
            img = self.canvas.to_image()
            frames.append(PILImage.fromarray(
                np.array(img.convertToFormat(QImage.Format.Format_RGB888))))
            prog.setValue(i)
            QApplication.processEvents()

        prog.close()
        if frames:
            frames[0].save(path, save_all=True, append_images=frames[1:],
                           duration=50, loop=0)
            self.status.showMessage(f"Saved GIF: {path} ({len(frames)} frames)")

    def _save_svg(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save SVG", "morph.svg", "SVG (*.svg)")
        if path:
            export_shape_to_svg(
                self.canvas.points, path, 
                self.canvas.gradient_type, 
                self.canvas.gradient_color1, 
                self.canvas.gradient_color2
            )
            self.status.showMessage(f"Saved SVG: {path}")

    def _save_png_seq(self):
        if not self.preloaded_shapes:
            QMessageBox.warning(self, "No Shapes", "Add shapes to the sequence first.")
            return
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if not folder: return

        fn = MORPH_MODES[self.mode_combo.currentText()]
        total = 100
        prog = QProgressDialog("Rendering PNG sequence…", "Cancel", 0, total, self)
        prog.setWindowModality(Qt.WindowModality.WindowModal)
        prog.show()

        count = 0
        for i in range(total):
            if prog.wasCanceled(): break
            t = i / 100.0
            morphed = morph_sequence(self.preloaded_shapes, t, fn)
            if morphed is not None:
                self.canvas.update_points(morphed)
            self.canvas.to_image().save(f"{folder}/frame_{i:04d}.png")
            count += 1
            prog.setValue(i)
            QApplication.processEvents()

        prog.close()
        QMessageBox.information(self, "Done", f"Saved {count} frames to:\n{folder}")
        self.status.showMessage(f"Saved {count} PNG frames to {folder}")

    # ── misc ────────────────────────────────────────────────

    def _on_canvas_mouse(self, x, y):
        w, h = self.canvas.width(), self.canvas.height()
        divisor = min(w, h) / 2 * 0.85
        if divisor > 0:
            nx = (x - w / 2) / divisor
            ny = -(y - h / 2) / divisor
            self.coord_lbl.setText(f"X: {nx:+.2f}  Y: {ny:+.2f}")

    def _update_status(self):
        n_shapes = len(self.preloaded_shapes)
        t = self.tb_slider.value()
        mode = self.mode_combo.currentText()
        self.status.showMessage(
            f"Shapes: {n_shapes} | Progress: {t}% | "
            f"Resolution: {self.n_points} pts | Algorithm: {mode}"
        )

    def _show_about(self):
        QMessageBox.about(
            self,
            "About Shape Morphing Studio",
            "<h3>Shape Morphing Studio</h3>"
            "<p>A professional desktop tool for generating shape morphing "
            "animations and vector graphics.</p>"
            "<p>Built with <b>PySide6</b> and <b>NumPy</b>.</p>"
            "<hr>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>12 built-in shapes with visual library</li>"
            "<li>5 morphing algorithms (Linear, Ease, Elastic, Back, Bounce)</li>"
            "<li>Linear, Radial, and Conical Gradients</li>"
            "<li>Freehand & Point-by-Point drawing modes</li>"
            "<li>SVG import and export</li>"
            "<li>PNG, GIF, and PNG-sequence export</li>"
            "<li>Customizable styles and animation directions</li>"
            "</ul>"
            "<p><b>Shortcuts:</b></p>"
            "<ul>"
            "<li><b>Space</b> - Play/Pause</li>"
            "<li><b>Home</b> - Reset to Start</li>"
            "<li><b>R</b> - Generate Random Sequence</li>"
            "<li><b>G</b> - Toggle Grid</li>"
            "<li><b>Ctrl+I</b> - Import SVG</li>"
            "<li><b>Ctrl+S</b> - Export PNG</li>"
            "<li><b>Ctrl+G</b> - Export GIF</li>"
            "</ul>",
        )


# ═══════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MorphApp()
    window.show()
    
    sys.exit(app.exec())