import numpy as np
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Signal, Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QImage
from config import COLORS, CANVAS_BG_COLOR, GRID_COLOR
from geometry import catmull_rom_smooth
from morphing import resample_shape

class MorphCanvas(QWidget):
    drawing_finished = Signal()
    point_added = Signal(int)

    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 400)
        self.points = np.array([])
        self.fill_color = COLORS["fill"]
        self.outline_color = COLORS["outline"]
        self.show_fill = True
        self.show_outline = True
        self.show_grid = False
        
        # State
        self.is_drawing = False
        self.draw_points = []
        self.freehand_points = []
        self.draw_finished = False
        self.auto_close = True
        self.smooth_curve = False
        self.freehand_mode = False
        self.snap_to_start = False

    def start_drawing(self, freehand=False):
        self.is_drawing = True
        self.freehand_mode = freehand
        self.draw_points.clear()
        self.freehand_points.clear()
        self.draw_finished = False
        self.update()

    def clear_drawing(self):
        self.draw_points.clear()
        self.freehand_points.clear()
        self.draw_finished = False
        self.update()

    def get_normalized_numpy(self, n_points):
        if len(self.draw_points) < 3: return None
        pts = np.array([(p.x(), p.y()) for p in self.draw_points])
        
        if self.smooth_curve and len(pts) >= 4:
            pts = catmull_rom_smooth(pts, density=3)
        
        if self.auto_close and not np.allclose(pts[0], pts[-1]): 
            pts = np.vstack([pts, pts[0]])
            
        center = np.mean(pts, axis=0); pts -= center
        max_r = np.max(np.sqrt(np.sum(pts**2, axis=1)))
        if max_r > 0: pts /= (max_r / 0.8)
        return resample_shape(pts, n_points)

    def update_points(self, pts):
        self.points = pts
        self.update()

    # --- Events ---
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
                if self.draw_points: self.draw_points.pop()
                self.point_added.emit(len(self.draw_points))
                self.update()
        else: super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_drawing and not self.draw_finished:
            if self.freehand_mode and event.buttons() & Qt.MouseButton.LeftButton:
                self.freehand_points.append(event.position())
                # Downsample during movement
                if len(self.freehand_points) % 3 == 0:
                    self.draw_points.append(self.freehand_points[-1])
                self.update()
            else:
                # Snap logic
                self.snap_to_start = False
                if self.draw_points:
                    start = self.draw_points[0]
                    dist = np.hypot(event.position().x() - start.x(), event.position().y() - start.y())
                    self.snap_to_start = dist < 15
                self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_drawing and self.freehand_mode and not self.draw_finished:
            # Finalize freehand
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

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), CANVAS_BG_COLOR)
        
        # Grid
        if self.show_grid:
            painter.setPen(QPen(GRID_COLOR, 1, Qt.PenStyle.DotLine))
            for x in range(0, self.width(), 40): painter.drawLine(x, 0, x, self.height())
            for y in range(0, self.height(), 40): painter.drawLine(0, y, self.width(), y)
        
        # Drawing Mode
        if self.is_drawing:
            self._paint_drawing_ui(painter)
            return
            
        # View Mode
        if self.points is None or self.points.size == 0:
            painter.setPen(QPen(QColor(150, 150, 150), 14))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Select or Draw shapes")
            return

        w, h = self.width(), self.height()
        scale = min(w, h) / 2 * 0.85
        path = QPainterPath()
        path.moveTo(w/2 + self.points[0, 0] * scale, h/2 - self.points[0, 1] * scale)
        for i in range(1, len(self.points)):
            path.lineTo(w/2 + self.points[i, 0] * scale, h/2 - self.points[i, 1] * scale)
        path.closeSubpath()
        
        if self.show_fill: painter.setBrush(QBrush(self.fill_color))
        else: painter.setBrush(Qt.BrushStyle.NoBrush)
        if self.show_outline: painter.setPen(QPen(self.outline_color, 2))
        else: painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)

    def _paint_drawing_ui(self, painter):
        # Draw freehand preview
        if self.freehand_mode and self.freehand_points:
            painter.setPen(QPen(COLORS["freehand_preview"], 2))
            path = QPainterPath()
            path.moveTo(self.freehand_points[0])
            for p in self.freehand_points[1:]: path.lineTo(p)
            painter.drawPath(path)
            
        # Draw points
        if self.draw_points:
            painter.setPen(QPen(COLORS["drawing_line"], 2))
            painter.setBrush(QBrush(COLORS["drawing_line"]))
            for i, p in enumerate(self.draw_points):
                painter.drawEllipse(p, 5 if i == 0 else 4, 5 if i == 0 else 4)
            
            # Connecting lines
            path = QPainterPath()
            path.moveTo(self.draw_points[0])
            for p in self.draw_points[1:]: path.lineTo(p)
            
            if self.snap_to_start:
                painter.setPen(QPen(COLORS["snap_indicator"], 2, Qt.PenStyle.DashDotLine))
                path.lineTo(self.draw_points[0])
                painter.setBrush(QBrush(QColor(50, 205, 50, 100)))
                painter.drawEllipse(self.draw_points[0], 12, 12)
            else:
                painter.setPen(QPen(COLORS["drawing_line"], 2, Qt.PenStyle.DashLine))
            painter.drawPath(path)

    def to_image(self):
        img = QImage(self.size(), QImage.Format.Format_ARGB32)
        img.fill(CANVAS_BG_COLOR)
        p = QPainter(img); self.render(p); p.end()
        return img