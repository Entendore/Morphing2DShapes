from PySide6.QtGui import QColor

# Default Settings
DEFAULT_RESOLUTION = 120
DEFAULT_FPS = 24
CANVAS_BG_COLOR = QColor(255, 255, 255)
GRID_COLOR = QColor(220, 220, 220)

# Styling
STYLESHEET = """
QGroupBox { font-weight: bold; border: 1px solid #ccc; border-radius: 5px; margin-top: 10px; padding-top: 10px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }
QPushButton { padding: 5px 10px; }
"""

# Utility Colors
COLORS = {
    "fill": QColor(52, 152, 219),
    "outline": QColor(44, 62, 80),
    "drawing_line": QColor(255, 100, 100),
    "snap_indicator": QColor(50, 205, 50),
    "freehand_preview": QColor(100, 149, 237)
}