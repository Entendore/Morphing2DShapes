import sys
import random
import numpy as np
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QGroupBox, QLabel, QComboBox, QSlider, QPushButton, 
                               QCheckBox, QSpinBox, QFileDialog, QMessageBox, 
                               QProgressDialog, QApplication, QColorDialog)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage
from canvas import MorphCanvas
from dialogs import ShapeSequenceDialog
from geometry import SHAPE_REGISTRY
from morphing import MORPH_MODES, morph_sequence
from svg_tools import parse_svg_content, export_shape_to_svg
from config import COLORS, DEFAULT_RESOLUTION, DEFAULT_FPS, STYLESHEET

class MorphApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shape Morphing Studio")
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet(STYLESHEET)
        
        self.n_points = DEFAULT_RESOLUTION
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self._advance)
        self.custom_shapes = {}
        self.custom_counter = 1
        
        # State
        self.morph_sequence_names = ["Circle", "Star"] # For named sequences
        self.preloaded_shapes = [] # Stores actual numpy arrays for morphing
        self.is_random_sequence = False # Flag to track current mode
        
        self._build_ui()
        self._update_shapes() # Initial load

    def _build_ui(self):
        central = QWidget(); layout = QHBoxLayout(central); ctrl = QVBoxLayout()
        
        def group(title, items):
            g = QGroupBox(title); gl = QVBoxLayout(g)
            for w in items: gl.addWidget(w)
            return g

        # --- SEQUENCE CONTROLS ---
        self.seq_btn = QPushButton("🎬 Edit Manual Sequence")
        self.seq_preview = QLabel("Circle → Star"); self.seq_preview.setWordWrap(True)
        
        # Random Sequence UI
        self.rand_seq_len = QSpinBox() # Fixed variable name
        self.rand_seq_len.setRange(2, 20)
        self.rand_seq_len.setValue(5)
        self.rand_gen_btn = QPushButton("🎲 Generate Random Sequence")
        
        ctrl.addWidget(group("Sequence", [
            self.seq_btn, self.seq_preview, 
            QLabel("Random Count:"), self.rand_seq_len, self.rand_gen_btn
        ]))

        # --- MORPHING CONTROLS ---
        self.mode_combo = QComboBox(); self.mode_combo.addItems(MORPH_MODES.keys())
        self.progress_slider = QSlider(Qt.Orientation.Horizontal); self.progress_slider.setRange(0, 100)
        self.progress_lbl = QLabel("0%")
        self.n_pts_slider = QSlider(Qt.Orientation.Horizontal); self.n_pts_slider.setRange(20, 300)
        self.n_pts_slider.setValue(self.n_points)
        ctrl.addWidget(group("Controls", [
            QLabel("Algorithm:"), self.mode_combo, 
            QLabel("Progress:"), self.progress_slider, self.progress_lbl,
            QLabel("Base Resolution:"), self.n_pts_slider
        ]))

        # --- ANIMATION ---
        self.play_btn = QPushButton("▶ Play"); self.play_btn.setCheckable(True)
        self.speed_slider = QSlider(Qt.Orientation.Horizontal); self.speed_slider.setRange(1, 60)
        self.speed_slider.setValue(DEFAULT_FPS); self.speed_lbl = QLabel(f"{DEFAULT_FPS} FPS")
        ctrl.addWidget(group("Animation", [self.play_btn, QLabel("Speed:"), self.speed_slider, self.speed_lbl]))

        # --- APPEARANCE ---
        self.fill_cb = QCheckBox("Fill", checked=True); self.outline_cb = QCheckBox("Outline", checked=True)
        self.grid_cb = QCheckBox("Grid")
        self.color_btn = QPushButton("Fill Color")
        ctrl.addWidget(group("View", [self.fill_cb, self.outline_cb, self.grid_cb, self.color_btn]))

        # --- CUSTOM TOOLS ---
        self.draw_btn = QPushButton("✏️ Draw Mode"); self.draw_btn.setCheckable(True)
        self.draw_info = QLabel("Points: 0")
        self.clear_btn = QPushButton("Clear")
        self.save_shape_btn = QPushButton("Save Shape")
        self.import_btn = QPushButton("Import SVG")
        ctrl.addWidget(group("Custom", [self.draw_btn, self.draw_info, self.clear_btn, self.save_shape_btn, self.import_btn]))

        # --- EXPORT ---
        self.export_png_btn = QPushButton("📸 PNG")
        self.export_gif_btn = QPushButton("🎞️ GIF")
        self.export_svg_btn = QPushButton("📤 SVG")
        ctrl.addStretch()
        ctrl.addWidget(group("Export", [self.export_png_btn, self.export_gif_btn, self.export_svg_btn]))

        layout.addLayout(ctrl, 1)
        self.canvas = MorphCanvas()
        layout.addWidget(self.canvas, 3)
        self.setCentralWidget(central)
        
        self._connect()

    def _connect(self):
        # Sequence
        self.seq_btn.clicked.connect(self._edit_sequence)
        self.rand_gen_btn.clicked.connect(self._generate_random_sequence)
        
        # Controls
        self.mode_combo.currentTextChanged.connect(self._update_morph)
        self.progress_slider.valueChanged.connect(self._on_progress)
        self.n_pts_slider.valueChanged.connect(self._on_base_res_change)
        
        # Animation
        self.play_btn.toggled.connect(self._toggle_anim)
        self.speed_slider.valueChanged.connect(lambda v: (self.speed_lbl.setText(f"{v} FPS"), self.anim_timer.setInterval(1000//v)))
        
        # View
        self.fill_cb.toggled.connect(lambda v: setattr(self.canvas, 'show_fill', v) or self.canvas.update())
        self.outline_cb.toggled.connect(lambda v: setattr(self.canvas, 'show_outline', v) or self.canvas.update())
        self.grid_cb.toggled.connect(lambda v: setattr(self.canvas, 'show_grid', v) or self.canvas.update())
        self.color_btn.clicked.connect(lambda: self._pick_color())
        
        # Drawing
        self.draw_btn.toggled.connect(self._toggle_draw)
        self.clear_btn.clicked.connect(self.canvas.clear_drawing)
        self.save_shape_btn.clicked.connect(self._save_custom)
        self.import_btn.clicked.connect(self._import_svg)
        self.canvas.drawing_finished.connect(lambda: self.save_shape_btn.setEnabled(True))
        self.canvas.point_added.connect(lambda n: self.draw_info.setText(f"Points: {n}"))
        
        # Export
        self.export_png_btn.clicked.connect(self._save_png)
        self.export_gif_btn.clicked.connect(self._save_gif)
        self.export_svg_btn.clicked.connect(self._save_svg)

    # --- LOGIC ---

    def _edit_sequence(self):
        """Open dialog to define specific named shapes sequence."""
        avail = list(SHAPE_REGISTRY.keys()) + list(self.custom_shapes.keys())
        dlg = ShapeSequenceDialog(avail, self.morph_sequence_names, self)
        if dlg.exec():
            seq = dlg.get_sequence()
            if len(seq) >= 2:
                self.is_random_sequence = False
                self.morph_sequence_names = seq
                self._update_shapes()
                self.seq_preview.setText(" → ".join(seq))

    def _generate_random_sequence(self):
        """Generate a sequence of random shapes with random point counts."""
        # BUGFIX: Use self.rand_seq_len instead of self.rand_gen_btn
        length = self.rand_seq_len.value()
        shape_names = list(SHAPE_REGISTRY.keys())
        
        self.preloaded_shapes = []
        description = []
        
        for _ in range(length):
            # 1. Pick random shape type
            name = random.choice(shape_names)
            func = SHAPE_REGISTRY[name]
            
            # 2. Pick random number of points (e.g., between 5 and 80)
            # This creates interesting topology changes
            random_pts = random.randint(5, 80)
            
            # 3. Generate
            try:
                shape = func(n=random_pts, radius=1.0)
            except:
                shape = func(random_pts, 1.0)
                
            self.preloaded_shapes.append(shape)
            description.append(f"{name}({random_pts})")
        
        self.is_random_sequence = True
        # Update UI
        if len(description) > 4:
            txt = f"Random {length}: {description[0]} → ... → {description[-1]}"
        else:
            txt = " → ".join(description)
        self.seq_preview.setText(txt)
        
        self.progress_slider.setValue(0)
        self._update_morph()

    def _load_shape(self, name):
        if name in self.custom_shapes: return self.custom_shapes[name]
        if name in SHAPE_REGISTRY: 
            return SHAPE_REGISTRY[name](self.n_points, radius=1.0)
        return None

    def _update_shapes(self):
        """Load shapes based on current mode (Random or Named)."""
        # If we are in random mode, the shapes are already generated in self.preloaded_shapes
        if self.is_random_sequence and self.preloaded_shapes:
            self._update_morph()
            return

        # Otherwise, load named shapes using the base resolution
        self.preloaded_shapes = []
        for name in self.morph_sequence_names:
            shape = self._load_shape(name)
            if shape is not None: self.preloaded_shapes.append(shape)
        self._update_morph()

    def _on_base_res_change(self, val):
        self.n_points = val
        # If we change base resolution in random mode, we usually don't want to overwrite the random shapes
        # But in manual mode, we do.
        if not self.is_random_sequence:
            self._update_shapes()

    def _update_morph(self):
        t = self.progress_slider.value() / 100.0
        fn = MORPH_MODES[self.mode_combo.currentText()]
        morphed = morph_sequence(self.preloaded_shapes, t, fn)
        if morphed is not None: self.canvas.update_points(morphed)

    def _on_progress(self, v):
        self.progress_lbl.setText(f"{v}%"); self._update_morph()

    def _toggle_anim(self, checked):
        if checked: self.anim_timer.start(); self.play_btn.setText("⏸ Pause")
        else: self.anim_timer.stop(); self.play_btn.setText("▶ Play")

    def _advance(self):
        self.progress_slider.setValue((self.progress_slider.value() + 1) % 101)

    def _toggle_draw(self, checked):
        if checked:
            self.anim_timer.stop(); self.play_btn.setChecked(False)
            self.canvas.start_drawing()
            self.save_shape_btn.setEnabled(False)
        else:
            self.canvas.is_drawing = False
            self._update_shapes()

    def _save_custom(self):
        arr = self.canvas.get_normalized_numpy(self.n_points)
        if arr is None: return
        name = f"Custom {self.custom_counter}"
        self.custom_shapes[name] = arr
        self.custom_counter += 1
        QMessageBox.information(self, "Saved", f"Shape '{name}' saved!")
        self.draw_btn.setChecked(False)

    def _import_svg(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import SVG", "", "SVG (*.svg)")
        if not path: return
        with open(path, 'r', encoding='utf-8') as f: arr = parse_svg_content(f.read(), self.n_points)
        if arr is not None:
            self.custom_shapes[f"SVG {self.custom_counter}"] = arr
            self.custom_counter += 1
            QMessageBox.information(self, "Done", "Imported!")

    def _pick_color(self):
        c = QColorDialog.getColor(self.canvas.fill_color, self)
        if c.isValid(): self.canvas.fill_color = c; self.canvas.update()

    def _save_png(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save PNG", "", "PNG (*.png)")
        if path: self.canvas.to_image().save(path)

    def _save_gif(self):
        try: from PIL import Image as PILImage
        except: QMessageBox.warning(self, "Error", "Install Pillow"); return
        
        path, _ = QFileDialog.getSaveFileName(self, "Save GIF", "", "GIF (*.gif)")
        if not path: return
        
        frames = []
        prog = QProgressDialog("Rendering...", None, 0, 100, self)
        prog.setWindowModality(Qt.WindowModality.WindowModal); prog.show()
        
        for i in range(100):
            t = i / 100.0
            morphed = morph_sequence(self.preloaded_shapes, t, MORPH_MODES[self.mode_combo.currentText()])
            if morphed is not None: self.canvas.update_points(morphed)
            img = self.canvas.to_image()
            frames.append(PILImage.fromarray(np.array(img.convertToFormat(QImage.Format.Format_RGB888))))
            prog.setValue(i); QApplication.processEvents()
            
        prog.close()
        frames[0].save(path, save_all=True, append_images=frames[1:], duration=50, loop=0)

    def _save_svg(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save SVG", "", "SVG (*.svg)")
        if path: export_shape_to_svg(self.canvas.points, path)