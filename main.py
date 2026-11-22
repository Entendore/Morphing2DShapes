import sys
import math
import random
import re
import time
from PySide6.QtWidgets import (QApplication, QWidget, QMainWindow, QTabWidget, 
                               QVBoxLayout, QHBoxLayout, QPushButton, QSlider, 
                               QLabel, QCheckBox, QRadioButton, QButtonGroup, QStatusBar, QFileDialog)
from PySide6.QtGui import (QPainter, QColor, QPen, QPolygonF, QPainterPath, 
                           QMouseEvent, QLinearGradient)
from PySide6.QtCore import Qt, QTimer, QPointF

# ==========================================
# TAB 1: Shape Morphing Logic (w/ Particles)
# ==========================================

def resample_polygon(vertices, num_points):
    if not vertices: return []
    n_verts = len(vertices)
    dists = [0.0]
    for i in range(n_verts):
        p1 = vertices[i]
        p2 = vertices[(i + 1) % n_verts]
        dists.append(dists[-1] + math.hypot(p2[0] - p1[0], p2[1] - p1[1]))

    total_len = dists[-1]
    if total_len == 0: return [vertices[0]] * num_points

    step = total_len / num_points
    points = []
    seg_idx = 0

    for i in range(num_points):
        target_dist = i * step
        while seg_idx < n_verts - 1 and dists[seg_idx + 1] < target_dist:
            seg_idx += 1
        p1 = vertices[seg_idx]
        p2 = vertices[(seg_idx + 1) % n_verts]
        seg_len = dists[seg_idx + 1] - dists[seg_idx]
        
        t = 0.0 if seg_len == 0 else (target_dist - dists[seg_idx]) / seg_len
        x = p1[0] + t * (p2[0] - p1[0])
        y = p1[1] + t * (p2[1] - p1[1])
        points.append((x, y))

    return points

def generate_shapes():
    N = 200
    shapes = []
    # Circle, Square, Triangle, Star, Hexagon, Heart, Infinity, Moon, Gear
    shapes.append(resample_polygon([(math.cos(2 * math.pi * i / 60), math.sin(2 * math.pi * i / 60)) for i in range(60)], N))
    sq = 1.0
    shapes.append(resample_polygon([(-sq, -sq), (sq, -sq), (sq, sq), (-sq, sq)], N))
    shapes.append(resample_polygon([(0, -1.1), (math.sqrt(3)/2 * 1.1, 0.55), (-math.sqrt(3)/2 * 1.1, 0.55)], N))
    star_verts = []
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        r = 1.2 if i % 2 == 0 else 0.5
        star_verts.append((math.cos(angle) * r, math.sin(angle) * r))
    shapes.append(resample_polygon(star_verts, N))
    shapes.append(resample_polygon([(math.cos(2 * math.pi * i / 6), math.sin(2 * math.pi * i / 6)) for i in range(6)], N))
    heart_verts = []
    for i in range(100):
        t = 2 * math.pi * i / 100
        x = 16 * math.sin(t)**3
        y = 13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)
        heart_verts.append((x / 16, -y / 16))
    shapes.append(resample_polygon(heart_verts, N))
    inf_verts = []
    for i in range(100):
        t = 2 * math.pi * i / 100
        denom = 1 + math.sin(t)**2
        inf_verts.append((math.cos(t) / denom * 1.5, math.sin(t) * math.cos(t) / denom * 1.5))
    shapes.append(resample_polygon(inf_verts, N))
    cres_verts = []
    for i in range(60):
        t = math.pi + math.pi * i / 60
        cres_verts.append((math.cos(t), math.sin(t)))
    for i in range(60):
        t = math.pi * i / 60
        cres_verts.append((math.cos(t) * 0.8 - 0.2, math.sin(t) * 0.8))
    shapes.append(resample_polygon(cres_verts, N))
    gear_verts = []
    teeth = 12
    for i in range(teeth * 4):
        angle = 2 * math.pi * i / (teeth * 4)
        r = 1.0 if i % 4 < 2 else 0.75
        gear_verts.append((math.cos(angle) * r, math.sin(angle) * r))
    shapes.append(resample_polygon(gear_verts, N))
    return shapes

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(-1.5, 1.5)
        self.life = 1.0
        self.color = color

class MorphWidget(QWidget):
    def __init__(self, status_bar):
        super().__init__()
        self.status_bar = status_bar
        self.shapes = generate_shapes()
        self.color_pairs = [
            (QColor(85, 170, 255), QColor(100, 255, 150)),
            (QColor(255, 100, 100), QColor(255, 200, 50)),
            (QColor(200, 100, 255), QColor(255, 100, 200)),
            (QColor(50, 200, 255), QColor(10, 10, 40)),
        ]
        
        self.shape_idx = 0
        self.t = 0.0
        self.morph_speed = 0.012
        self.rotation = 0.0
        self.rotation_speed = 0.005
        
        self.show_points = True
        self.use_gradient = True
        self.wireframe_mode = False
        self.glow_enabled = True
        self.pulse_enabled = True
        self.particles_enabled = False
        
        self.particles = []
        
    def update_animation(self):
        self.t += self.morph_speed
        self.rotation += self.rotation_speed
        if self.t >= 1.0:
            self.next_shape()
            
        # Update Particles
        if self.particles_enabled:
            # Spawn new particles
            if len(self.particles) < 150:
                # We'll use the current calculated points in paintEvent to spawn, 
                # but to keep logic simple, spawn based on bounding box center
                # For accuracy, let's spawn them in paintEvent and just update here.
                pass
                
        for p in self.particles[:]:
            p.x += p.vx
            p.y += p.vy
            p.life -= 0.02
            if p.life <= 0:
                self.particles.remove(p)
                
        self.update()

    def next_shape(self):
        self.t = 0.0
        self.shape_idx = (self.shape_idx + 1) % len(self.shapes)

    def set_speed(self, val): self.morph_speed = val / 1000.0
    def set_rotation(self, val): self.rotation_speed = val / 1000.0

    def save_image(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "morph.png", "PNG Files (*.png)")
        if file_path:
            self.grab().save(file_path)
            self.status_bar.showMessage(f"Image saved to {file_path}", 3000)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(15, 15, 25))

        shape1 = self.shapes[self.shape_idx]
        shape2 = self.shapes[(self.shape_idx + 1) % len(self.shapes)]
        c1_start, c1_end = self.color_pairs[self.shape_idx % len(self.color_pairs)]
        c2_start, c2_end = self.color_pairs[(self.shape_idx + 1) % len(self.color_pairs)]

        t_eased = 0.5 - 0.5 * math.cos(self.t * math.pi)
        
        pulse_scale = 1.0 + (0.05 * math.sin(self.t * math.pi * 2) if self.pulse_enabled else 0.0)
        scale = min(self.width(), self.height()) * 0.35 * pulse_scale
        cx, cy = self.width() / 2, self.height() / 2

        points = []
        for p1, p2 in zip(shape1, shape2):
            x = p1[0] + (p2[0] - p1[0]) * t_eased
            y = p1[1] + (p2[1] - p1[1]) * t_eased
            rx = x * math.cos(self.rotation) - y * math.sin(self.rotation)
            ry = x * math.sin(self.rotation) + y * math.cos(self.rotation)
            points.append(QPointF(cx + rx * scale, cy + ry * scale))

        def lerp_color(c1, c2, t):
            return QColor(
                int(c1.red() + (c2.red() - c1.red()) * t),
                int(c1.green() + (c2.green() - c1.green()) * t),
                int(c1.blue() + (c2.blue() - c1.blue()) * t)
            )

        start_color = lerp_color(c1_start, c2_start, t_eased)
        end_color = lerp_color(c1_end, c2_end, t_eased)
        polygon = QPolygonF(points)

        # Draw Particles (Behind Shape)
        if self.particles_enabled:
            # Spawn particles from random vertices
            if len(self.particles) < 150 and random.random() > 0.5:
                spawn_pt = random.choice(points)
                self.particles.append(Particle(spawn_pt.x(), spawn_pt.y(), QColor(start_color)))
            
            painter.setPen(Qt.NoPen)
            for p in self.particles:
                color = QColor(p.color)
                color.setAlpha(int(p.life * 200))
                painter.setBrush(color)
                painter.drawEllipse(QPointF(p.x, p.y), 4 * p.life, 4 * p.life)

        if self.wireframe_mode:
            painter.setBrush(Qt.NoBrush)
            if self.glow_enabled:
                painter.setPen(QPen(QColor(start_color.red(), start_color.green(), start_color.blue(), 50), 8))
                painter.drawPolygon(polygon)
            painter.setPen(QPen(start_color, 2.5))
            painter.drawPolygon(polygon)
        else:
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            gradient.setColorAt(0.0, start_color)
            gradient.setColorAt(1.0, end_color)
            painter.setBrush(gradient if self.use_gradient else start_color)
            
            if self.glow_enabled:
                painter.setPen(QPen(QColor(255, 255, 255, 30), 15))
                painter.drawPolygon(polygon)
                
            painter.setPen(QPen(QColor(255, 255, 255, 150), 2))
            painter.drawPolygon(polygon)

        if self.show_points:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 255, 255, 200))
            for p in points:
                if int(p.x() * 100) % 4 == 0: 
                    painter.drawEllipse(p, 2.5, 2.5)


# ==========================================
# TAB 2: B-Spline Editor Logic
# ==========================================

def find_span(n, p, u, U):
    if u >= U[n+1]: return n
    if u <= U[p]: return p
    low, high = p, n + 1
    mid = (low + high) // 2
    while u < U[mid] or u >= U[mid+1]:
        if u < U[mid]: high = mid
        else: low = mid
        mid = (low + high) // 2
    return mid

def eval_bspline_point(u, p, U, P):
    n = len(P) - 1
    span = find_span(n, p, u, U)
    d = [P[span - p + k] for k in range(p + 1)]
    for r in range(1, p + 1):
        for j in range(p, r - 1, -1):
            den = U[span + 1 + j - r] - U[span - p + j]
            alpha = 0.0 if den == 0 else (u - U[span - p + j]) / den
            d[j] = (
                (1.0 - alpha) * d[j-1][0] + alpha * d[j][0],
                (1.0 - alpha) * d[j-1][1] + alpha * d[j][1]
            )
    return d[p]

class BSplineWidget(QWidget):
    def __init__(self, status_bar):
        super().__init__()
        self.status_bar = status_bar
        self.setMinimumSize(600, 600)
        self.setMouseTracking(True)
        
        self.control_points = []
        self.degree = 3
        self.dragging_idx = -1
        self.hover_idx = -1
        self.show_polygon = True
        self.is_closed = False
        self.show_knots = True
        self.tracer_u = 0.0
        self.curve_thickness = 3.0
        
        self.load_default_shape()
        
    def update_tracer(self):
        self.tracer_u = (self.tracer_u + 0.005) % 1.0
        self.update()

    def load_default_shape(self):
        self.control_points = [
            (0.1, 0.8), (0.2, 0.2), (0.5, 0.9), 
            (0.8, 0.2), (0.9, 0.8), (0.5, 0.5)
        ]

    def generate_random_shape(self):
        self.control_points = [(random.uniform(0.1, 0.9), random.uniform(0.1, 0.9)) for _ in range(random.randint(6, 10))]

    def get_processed_points_and_knots(self):
        P = self.control_points
        p = self.degree
        n = len(P) - 1
        
        if self.is_closed and n >= p:
            P_ext = P + P[:p]
            n_ext = len(P_ext) - 1
            m_ext = n_ext + p + 1
            U = [float(i) for i in range(m_ext + 1)]
            return P_ext, U, p, n_ext
        else:
            if n < p: return None, None, p, n
            m = n + p + 1
            U = [0.0] * (p + 1)
            num_internal = m - (2 * (p + 1))
            if num_internal > 0:
                U += [i + 1 for i in range(num_internal)]
            U += [float(num_internal + 1)] * (p + 1)
            return P, U, p, n

    def copy_pts_to_clipboard(self):
        pts_str = ",\n".join([f"({p[0]:.3f}, {p[1]:.3f})" for p in self.control_points])
        QApplication.clipboard().setText(pts_str)
        self.status_bar.showMessage("Points copied to clipboard!", 3000)

    def paste_pts_from_clipboard(self):
        text = QApplication.clipboard().text()
        # Regex to find pairs like (0.5, 0.5) or .5, .5
        matches = re.findall(r'\(?([0-9\.]+)[\s,]+([0-9\.]+)\)?', text)
        if matches:
            new_pts = []
            for m in matches:
                try:
                    x = float(m[0])
                    y = float(m[1])
                    if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0:
                        new_pts.append((x, y))
                except ValueError:
                    continue
            if len(new_pts) >= 2:
                self.control_points = new_pts
                self.status_bar.showMessage(f"Imported {len(new_pts)} points from clipboard!", 3000)
            else:
                self.status_bar.showMessage("Clipboard data invalid or out of bounds (0.0-1.0).", 3000)
        else:
            self.status_bar.showMessage("No valid coordinate pairs found in clipboard.", 3000)

    def save_image(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "bspline.png", "PNG Files (*.png)")
        if file_path:
            self.grab().save(file_path)
            self.status_bar.showMessage(f"Image saved to {file_path}", 3000)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(15, 15, 25))

        w, h = self.width(), self.height()

        if self.show_polygon and len(self.control_points) > 1:
            painter.setPen(QPen(QColor(100, 100, 100, 150), 1, Qt.DashLine))
            for i in range(len(self.control_points) - 1):
                p1 = self.control_points[i]
                p2 = self.control_points[i+1]
                painter.drawLine(QPointF(p1[0]*w, p1[1]*h), QPointF(p2[0]*w, p2[1]*h))
            if self.is_closed and len(self.control_points) > 2:
                p1 = self.control_points[-1]
                p2 = self.control_points[0]
                painter.drawLine(QPointF(p1[0]*w, p1[1]*h), QPointF(p2[0]*w, p2[1]*h))

        P_ext, U, p, n = self.get_processed_points_and_knots()
        
        if P_ext and n >= p:
            u_min = U[p]
            u_max = U[n+1]
            
            points = []
            steps = 300
            for i in range(steps + 1):
                u = u_min + (i / steps) * (u_max - u_min)
                pt = eval_bspline_point(u, p, U, P_ext)
                norm_u = (u - u_min) / (u_max - u_min)
                points.append((QPointF(pt[0] * w, pt[1] * h), norm_u))
            
            for i in range(len(points) - 1):
                p1, t1 = points[i]
                p2, t2 = points[i+1]
                color = QColor(int(0 + 255*t1), int(255 - 100*t1), int(200 + 55*t1))
                painter.setPen(QPen(color, self.curve_thickness))
                painter.drawLine(p1, p2)
                
            if self.show_knots:
                unique_knots = sorted(list(set(U)))
                for knot in unique_knots:
                    if u_min <= knot <= u_max:
                        pt = eval_bspline_point(knot, p, U, P_ext)
                        pos = QPointF(pt[0] * w, pt[1] * h)
                        painter.setBrush(QColor(255, 255, 0, 200))
                        painter.setPen(QPen(QColor(255, 255, 255), 1))
                        painter.drawEllipse(pos, 4, 4)
                
            trace_idx = int(self.tracer_u * steps)
            trace_pt, _ = points[trace_idx]
            painter.setBrush(QColor(255, 255, 255, 100))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(trace_pt, 12, 12)
            painter.setBrush(QColor(255, 255, 255))
            painter.drawEllipse(trace_pt, 5, 5)

        for i, pt in enumerate(self.control_points):
            pos = QPointF(pt[0] * w, pt[1] * h)
            if i == self.dragging_idx or i == self.hover_idx:
                painter.setBrush(QColor(255, 100, 100))
                painter.setPen(QPen(QColor(255, 255, 255), 2))
                painter.drawRect(pos.x() - 7, pos.y() - 7, 14, 14)
            else:
                painter.setBrush(QColor(85, 170, 255))
                painter.setPen(QPen(QColor(255, 255, 255), 1))
                painter.drawEllipse(pos, 7, 7)

    def mousePressEvent(self, event: QMouseEvent):
        pos = event.position()
        x, y = pos.x() / self.width(), pos.y() / self.height()
        
        if event.button() == Qt.LeftButton:
            closest_idx, min_dist = -1, 0.05
            for i, pt in enumerate(self.control_points):
                dist = math.hypot(x - pt[0], y - pt[1])
                if dist < min_dist:
                    min_dist = dist
                    closest_idx = i
            if closest_idx != -1:
                self.dragging_idx = closest_idx
        elif event.button() == Qt.RightButton:
            if event.modifiers() & Qt.ShiftModifier:
                if len(self.control_points) > self.degree + 1:
                    closest_idx, min_dist = -1, 0.05
                    for i, pt in enumerate(self.control_points):
                        dist = math.hypot(x - pt[0], y - pt[1])
                        if dist < min_dist:
                            min_dist = dist
                            closest_idx = i
                    if closest_idx != -1:
                        self.control_points.pop(closest_idx)
            else:
                self.control_points.append((x, y))
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position()
        x = max(0.0, min(1.0, pos.x() / self.width()))
        y = max(0.0, min(1.0, pos.y() / self.height()))
        
        if self.dragging_idx != -1:
            self.control_points[self.dragging_idx] = (x, y)
            self.update()
        else:
            closest_idx, min_dist = -1, 0.05
            for i, pt in enumerate(self.control_points):
                dist = math.hypot(x - pt[0], y - pt[1])
                if dist < min_dist:
                    min_dist = dist
                    closest_idx = i
            if closest_idx != self.hover_idx:
                self.hover_idx = closest_idx
                self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging_idx = -1
            self.update()


# ==========================================
# TAB 3: Catmull-Rom Spline Editor Logic
# ==========================================

def eval_catmull_rom(p0, p1, p2, p3, t):
    """Evaluates a point on a Catmull-Rom spline segment."""
    t2 = t * t
    t3 = t2 * t
    x = 0.5 * ((2 * p1[0]) +
               (-p0[0] + p2[0]) * t +
               (2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0]) * t2 +
               (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0]) * t3)
    y = 0.5 * ((2 * p1[1]) +
               (-p0[1] + p2[1]) * t +
               (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]) * t2 +
               (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1]) * t3)
    return (x, y)

class CatmullRomWidget(QWidget):
    def __init__(self, status_bar):
        super().__init__()
        self.status_bar = status_bar
        self.setMinimumSize(600, 600)
        self.setMouseTracking(True)
        
        self.control_points = []
        self.dragging_idx = -1
        self.hover_idx = -1
        self.is_closed = True
        self.tracer_u = 0.0
        self.curve_thickness = 3.0
        
        self.load_default_shape()
        
    def update_tracer(self):
        self.tracer_u = (self.tracer_u + 0.005) % 1.0
        self.update()

    def load_default_shape(self):
        # A nice wave shape
        self.control_points = [
            (0.1, 0.5), (0.25, 0.8), (0.4, 0.2), 
            (0.6, 0.8), (0.75, 0.2), (0.9, 0.5)
        ]

    def generate_random_shape(self):
        self.control_points = [(random.uniform(0.1, 0.9), random.uniform(0.1, 0.9)) for _ in range(random.randint(5, 12))]

    def save_image(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "catmull_rom.png", "PNG Files (*.png)")
        if file_path:
            self.grab().save(file_path)
            self.status_bar.showMessage(f"Image saved to {file_path}", 3000)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(15, 15, 25))

        w, h = self.width(), self.height()
        n = len(self.control_points)

        if n >= 2:
            points = []
            steps_per_segment = 50
            total_segments = n if self.is_closed else n - 1

            if total_segments >= 1:
                for i in range(total_segments):
                    if self.is_closed:
                        p0 = self.control_points[(i - 1) % n]
                        p1 = self.control_points[i % n]
                        p2 = self.control_points[(i + 1) % n]
                        p3 = self.control_points[(i + 2) % n]
                    else:
                        # Duplicate ends for open splines
                        p1 = self.control_points[i]
                        p2 = self.control_points[i + 1]
                        p0 = self.control_points[i - 1] if i > 0 else p1
                        p3 = self.control_points[i + 2] if i < n - 2 else p2
                    
                    for step in range(steps_per_segment + 1):
                        t = step / steps_per_segment
                        pt = eval_catmull_rom(p0, p1, p2, p3, t)
                        norm_u = (i + t) / total_segments
                        points.append((QPointF(pt[0] * w, pt[1] * h), norm_u))

                # Draw Curve Segments
                for i in range(len(points) - 1):
                    p1, t1 = points[i]
                    p2, t2 = points[i+1]
                    # Color transitions from Green to Blue
                    color = QColor(int(50 + 205*t1), int(255 - 50*t1), int(100 + 155*t1))
                    painter.setPen(QPen(color, self.curve_thickness))
                    painter.drawLine(p1, p2)

                # Draw Tracer Dot
                trace_idx = int(self.tracer_u * len(points)) % len(points)
                trace_pt, _ = points[trace_idx]
                painter.setBrush(QColor(255, 255, 255, 100))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(trace_pt, 12, 12)
                painter.setBrush(QColor(255, 255, 255))
                painter.drawEllipse(trace_pt, 5, 5)

        # Draw Control Polygon
        painter.setPen(QPen(QColor(100, 100, 100, 150), 1, Qt.DashLine))
        for i in range(n - 1):
            p1 = self.control_points[i]
            p2 = self.control_points[i+1]
            painter.drawLine(QPointF(p1[0]*w, p1[1]*h), QPointF(p2[0]*w, p2[1]*h))
        if self.is_closed and n > 2:
            p1 = self.control_points[-1]
            p2 = self.control_points[0]
            painter.drawLine(QPointF(p1[0]*w, p1[1]*h), QPointF(p2[0]*w, p2[1]*h))

        # Draw Control Points
        for i, pt in enumerate(self.control_points):
            pos = QPointF(pt[0] * w, pt[1] * h)
            if i == self.dragging_idx or i == self.hover_idx:
                painter.setBrush(QColor(255, 100, 100))
                painter.setPen(QPen(QColor(255, 255, 255), 2))
                painter.drawRect(pos.x() - 7, pos.y() - 7, 14, 14)
            else:
                painter.setBrush(QColor(255, 200, 0)) # Yellow for Catmull
                painter.setPen(QPen(QColor(255, 255, 255), 1))
                painter.drawEllipse(pos, 7, 7)

    def mousePressEvent(self, event: QMouseEvent):
        pos = event.position()
        x, y = pos.x() / self.width(), pos.y() / self.height()
        if event.button() == Qt.LeftButton:
            closest_idx, min_dist = -1, 0.05
            for i, pt in enumerate(self.control_points):
                dist = math.hypot(x - pt[0], y - pt[1])
                if dist < min_dist:
                    min_dist = dist
                    closest_idx = i
            if closest_idx != -1:
                self.dragging_idx = closest_idx
        elif event.button() == Qt.RightButton:
            if event.modifiers() & Qt.ShiftModifier:
                if len(self.control_points) > 2:
                    closest_idx, min_dist = -1, 0.05
                    for i, pt in enumerate(self.control_points):
                        dist = math.hypot(x - pt[0], y - pt[1])
                        if dist < min_dist:
                            min_dist = dist
                            closest_idx = i
                    if closest_idx != -1:
                        self.control_points.pop(closest_idx)
            else:
                self.control_points.append((x, y))
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position()
        x = max(0.0, min(1.0, pos.x() / self.width()))
        y = max(0.0, min(1.0, pos.y() / self.height()))
        if self.dragging_idx != -1:
            self.control_points[self.dragging_idx] = (x, y)
            self.update()
        else:
            closest_idx, min_dist = -1, 0.05
            for i, pt in enumerate(self.control_points):
                dist = math.hypot(x - pt[0], y - pt[1])
                if dist < min_dist:
                    min_dist = dist
                    closest_idx = i
            if closest_idx != self.hover_idx:
                self.hover_idx = closest_idx
                self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging_idx = -1
            self.update()


# ==========================================
# MAIN WINDOW WITH UI
# ==========================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pro 2D Visualizer: Morphing, B-Splines & Catmull-Rom")
        self.resize(1100, 750)
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; }
            QTabWidget::pane { border: 1px solid #333; background: #1e1e1e; }
            QTabBar::tab { background: #2a2a2a; color: #aaa; padding: 8px 20px; border: 1px solid #333; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #1e1e1e; color: #fff; border-bottom: none; }
            QPushButton { background-color: #2a2a2a; color: #fff; border: 1px solid #444; padding: 6px; border-radius: 4px; }
            QPushButton:hover { background-color: #3a3a3a; border: 1px solid #007acc; }
            QLabel { color: #aaa; }
            QCheckBox { color: #aaa; }
            QRadioButton { color: #aaa; }
            QSlider::groove:horizontal { border: 1px solid #333; height: 4px; background: #2a2a2a; border-radius: 2px; }
            QSlider::handle:horizontal { background: #007acc; width: 12px; margin: -5px 0; border-radius: 6px; }
            QStatusBar { background-color: #1a1a1a; color: #007acc; }
            QStatusBar::item { border: none; }
        """)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.fps_label = QLabel("FPS: 0")
        self.status_bar.addPermanentWidget(self.fps_label)
        
        # Timers
        self.last_time = time.time()
        self.frames = 0
        self.fps_timer = QTimer(self)
        self.fps_timer.timeout.connect(self.update_fps)
        self.fps_timer.start(500)

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_active_tab)
        self.anim_timer.start(16)

        tabs = QTabWidget()
        tabs.currentChanged.connect(self.on_tab_changed)
        
        self.morph_canvas = MorphWidget(self.status_bar)
        self.bspline_canvas = BSplineWidget(self.status_bar)
        self.catmull_canvas = CatmullRomWidget(self.status_bar)
        
        tabs.addTab(self.create_morph_tab(), "Shape Morphing")
        tabs.addTab(self.create_bspline_tab(), "B-Spline Editor")
        tabs.addTab(self.create_catmull_tab(), "Catmull-Rom Editor")
        self.setCentralWidget(tabs)

    def update_fps(self):
        now = time.time()
        fps = self.frames / (now - self.last_time)
        self.fps_label.setText(f"FPS: {int(fps)}")
        self.last_time = now
        self.frames = 0

    def on_tab_changed(self, index):
        self.status_bar.showMessage("Tab switched.", 2000)

    def update_active_tab(self):
        # We only update the active tab to save CPU/GPU
        central = self.centralWidget()
        if isinstance(central, QTabWidget):
            widget = central.widget(central.currentIndex())
            if hasattr(widget, 'findChild'):
                # Find the canvas widget and update it
                canvas = widget.findChild(QWidget, "canvas")
                if canvas:
                    if hasattr(canvas, 'update_animation'):
                        canvas.update_animation()
                    elif hasattr(canvas, 'update_tracer'):
                        canvas.update_tracer()
                    # Wrap paint event to count frames
                    if not hasattr(canvas, '_fps_wrapped'):
                        original_paint = canvas.paintEvent
                        def counted_paint(event):
                            original_paint(event)
                            self.frames += 1
                        canvas.paintEvent = counted_paint
                        canvas._fps_wrapped = True

    def create_morph_tab(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        
        self.morph_canvas.setObjectName("canvas")
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(12)

        title = QLabel("Morphing Controls")
        title.setStyleSheet("font-weight: bold; color: #fff; font-size: 14px;")
        controls_layout.addWidget(title)

        controls_layout.addWidget(QLabel("Morph Speed"))
        speed_slider = QSlider(Qt.Horizontal)
        speed_slider.setRange(1, 50)
        speed_slider.setValue(12)
        speed_slider.valueChanged.connect(self.morph_canvas.set_speed)
        controls_layout.addWidget(speed_slider)

        controls_layout.addWidget(QLabel("Rotation Speed"))
        rot_slider = QSlider(Qt.Horizontal)
        rot_slider.setRange(-20, 20)
        rot_slider.setValue(5)
        rot_slider.valueChanged.connect(self.morph_canvas.set_rotation)
        controls_layout.addWidget(rot_slider)

        btn_points = QCheckBox("Show Vertices")
        btn_points.setChecked(True)
        btn_points.stateChanged.connect(lambda state: setattr(self.morph_canvas, 'show_points', bool(state)))
        controls_layout.addWidget(btn_points)

        btn_grad = QCheckBox("Use Gradient Fill")
        btn_grad.setChecked(True)
        btn_grad.stateChanged.connect(lambda state: setattr(self.morph_canvas, 'use_gradient', bool(state)))
        controls_layout.addWidget(btn_grad)

        btn_wire = QCheckBox("Wireframe Mode")
        btn_wire.stateChanged.connect(lambda state: setattr(self.morph_canvas, 'wireframe_mode', bool(state)))
        controls_layout.addWidget(btn_wire)

        btn_glow = QCheckBox("Enable Glow")
        btn_glow.setChecked(True)
        btn_glow.stateChanged.connect(lambda state: setattr(self.morph_canvas, 'glow_enabled', bool(state)))
        controls_layout.addWidget(btn_glow)

        btn_pulse = QCheckBox("Scale Pulsing")
        btn_pulse.setChecked(True)
        btn_pulse.stateChanged.connect(lambda state: setattr(self.morph_canvas, 'pulse_enabled', bool(state)))
        controls_layout.addWidget(btn_pulse)

        btn_particles = QCheckBox("Enable Particles")
        btn_particles.stateChanged.connect(lambda state: setattr(self.morph_canvas, 'particles_enabled', bool(state)))
        controls_layout.addWidget(btn_particles)
        
        btn_next = QPushButton("Skip to Next Shape")
        btn_next.clicked.connect(self.morph_canvas.next_shape)
        controls_layout.addWidget(btn_next)

        btn_save = QPushButton("Save as Image (PNG)")
        btn_save.clicked.connect(self.morph_canvas.save_image)
        controls_layout.addWidget(btn_save)

        controls_layout.addStretch()
        layout.addWidget(self.morph_canvas, 3)
        layout.addLayout(controls_layout, 1)
        return container

    def create_bspline_tab(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        
        self.bspline_canvas.setObjectName("canvas")
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(12)

        title = QLabel("B-Spline Controls")
        title.setStyleSheet("font-weight: bold; color: #fff; font-size: 14px;")
        controls_layout.addWidget(title)

        controls_layout.addWidget(QLabel("Spline Degree"))
        rad_layout = QHBoxLayout()
        self.radio_linear = QRadioButton("1")
        self.radio_quad = QRadioButton("2")
        self.radio_cubic = QRadioButton("3")
        self.radio_cubic.setChecked(True)
        self.radio_linear.toggled.connect(lambda: setattr(self.bspline_canvas, 'degree', 1) if self.radio_linear.isChecked() else None)
        self.radio_quad.toggled.connect(lambda: setattr(self.bspline_canvas, 'degree', 2) if self.radio_quad.isChecked() else None)
        self.radio_cubic.toggled.connect(lambda: setattr(self.bspline_canvas, 'degree', 3) if self.radio_cubic.isChecked() else None)
        rad_layout.addWidget(self.radio_linear)
        rad_layout.addWidget(self.radio_quad)
        rad_layout.addWidget(self.radio_cubic)
        controls_layout.addLayout(rad_layout)

        controls_layout.addWidget(QLabel("Curve Thickness"))
        thick_slider = QSlider(Qt.Horizontal)
        thick_slider.setRange(1, 10)
        thick_slider.setValue(3)
        thick_slider.valueChanged.connect(lambda val: setattr(self.bspline_canvas, 'curve_thickness', float(val)))
        controls_layout.addWidget(thick_slider)

        btn_poly = QCheckBox("Show Control Polygon")
        btn_poly.setChecked(True)
        btn_poly.stateChanged.connect(lambda state: setattr(self.bspline_canvas, 'show_polygon', bool(state)))
        controls_layout.addWidget(btn_poly)

        btn_closed = QCheckBox("Closed (Periodic) Spline")
        btn_closed.stateChanged.connect(lambda state: setattr(self.bspline_canvas, 'is_closed', bool(state)))
        controls_layout.addWidget(btn_closed)

        btn_knots = QCheckBox("Show Knot Markers")
        btn_knots.setChecked(True)
        btn_knots.stateChanged.connect(lambda state: setattr(self.bspline_canvas, 'show_knots', bool(state)))
        controls_layout.addWidget(btn_knots)

        btn_default = QPushButton("Load Default Shape")
        btn_default.clicked.connect(self.bspline_canvas.load_default_shape)
        controls_layout.addWidget(btn_default)

        btn_random = QPushButton("Generate Random Shape")
        btn_random.clicked.connect(self.bspline_canvas.generate_random_shape)
        controls_layout.addWidget(btn_random)

        btn_clipboard = QPushButton("Copy Points to Clipboard")
        btn_clipboard.clicked.connect(self.bspline_canvas.copy_pts_to_clipboard)
        controls_layout.addWidget(btn_clipboard)

        btn_paste = QPushButton("Paste Points from Clipboard")
        btn_paste.clicked.connect(self.bspline_canvas.paste_pts_from_clipboard)
        controls_layout.addWidget(btn_paste)

        btn_save = QPushButton("Save as Image (PNG)")
        btn_save.clicked.connect(self.bspline_canvas.save_image)
        controls_layout.addWidget(btn_save)

        btn_clear = QPushButton("Clear All Points")
        btn_clear.setStyleSheet("QPushButton { color: #ff5555; }")
        btn_clear.clicked.connect(lambda: setattr(self.bspline_canvas, 'control_points', []))
        controls_layout.addWidget(btn_clear)

        controls_layout.addStretch()
        inst = QLabel("Instructions:\n• Left-Click & Drag: Move points\n• Right-Click: Add point\n• Shift + Right-Click: Remove point")
        inst.setStyleSheet("color: #666; font-size: 11px;")
        controls_layout.addWidget(inst)

        layout.addWidget(self.bspline_canvas, 3)
        layout.addLayout(controls_layout, 1)
        return container

    def create_catmull_tab(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        
        self.catmull_canvas.setObjectName("canvas")
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(12)

        title = QLabel("Catmull-Rom Controls")
        title.setStyleSheet("font-weight: bold; color: #fff; font-size: 14px;")
        controls_layout.addWidget(title)

        controls_layout.addWidget(QLabel("Curve Thickness"))
        thick_slider = QSlider(Qt.Horizontal)
        thick_slider.setRange(1, 10)
        thick_slider.setValue(3)
        thick_slider.valueChanged.connect(lambda val: setattr(self.catmull_canvas, 'curve_thickness', float(val)))
        controls_layout.addWidget(thick_slider)

        btn_closed = QCheckBox("Closed Spline (Loop)")
        btn_closed.setChecked(True)
        btn_closed.stateChanged.connect(lambda state: setattr(self.catmull_canvas, 'is_closed', bool(state)))
        controls_layout.addWidget(btn_closed)

        btn_default = QPushButton("Load Default Shape")
        btn_default.clicked.connect(self.catmull_canvas.load_default_shape)
        controls_layout.addWidget(btn_default)

        btn_random = QPushButton("Generate Random Shape")
        btn_random.clicked.connect(self.catmull_canvas.generate_random_shape)
        controls_layout.addWidget(btn_random)

        btn_save = QPushButton("Save as Image (PNG)")
        btn_save.clicked.connect(self.catmull_canvas.save_image)
        controls_layout.addWidget(btn_save)

        btn_clear = QPushButton("Clear All Points")
        btn_clear.setStyleSheet("QPushButton { color: #ff5555; }")
        btn_clear.clicked.connect(lambda: setattr(self.catmull_canvas, 'control_points', []))
        controls_layout.addWidget(btn_clear)

        controls_layout.addStretch()
        inst = QLabel("Instructions:\n• Left-Click & Drag: Move points\n• Right-Click: Add point\n• Shift + Right-Click: Remove point\n\nNote: Catmull-Rom splines pass exactly through the control points.")
        inst.setStyleSheet("color: #666; font-size: 11px;")
        controls_layout.addWidget(inst)

        layout.addWidget(self.catmull_canvas, 3)
        layout.addLayout(controls_layout, 1)
        return container

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())