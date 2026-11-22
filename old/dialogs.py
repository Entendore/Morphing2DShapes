from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, 
                               QListWidget, QPushButton, QLabel, QDialogButtonBox,
                               QAbstractItemView)
from PySide6.QtCore import Signal, Qt

class ShapeSequenceDialog(QDialog):
    def __init__(self, available_shapes, current_sequence, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sequence Manager")
        self.setMinimumWidth(400)
        self.available_shapes = available_shapes
        self.sequence = current_sequence.copy()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Available
        avail_group = QGroupBox("Library")
        avail_layout = QVBoxLayout(avail_group)
        self.avail_list = QListWidget()
        self.avail_list.addItems(self.available_shapes)
        self.avail_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        avail_layout.addWidget(self.avail_list)
        
        # Controls
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Add"); remove_btn = QPushButton("➖ Remove")
        up_btn = QPushButton("⬆️"); down_btn = QPushButton("⬇️")
        btn_layout.addWidget(add_btn); btn_layout.addWidget(remove_btn)
        btn_layout.addWidget(up_btn); btn_layout.addWidget(down_btn)
        
        # Sequence
        seq_group = QGroupBox("Current Sequence")
        seq_layout = QVBoxLayout(seq_group)
        self.seq_list = QListWidget()
        self.seq_list.addItems(self.sequence)
        self.seq_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        seq_layout.addWidget(self.seq_list)
        
        self.preview_lbl = QLabel(f"Total: {len(self.sequence)} shapes")
        
        # Dialog Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        
        layout.addWidget(avail_group); layout.addLayout(btn_layout)
        layout.addWidget(seq_group); layout.addWidget(self.preview_lbl); layout.addWidget(btns)
        
        # Signals
        add_btn.clicked.connect(self._add)
        remove_btn.clicked.connect(self._remove)
        up_btn.clicked.connect(lambda: self._move(-1))
        down_btn.clicked.connect(lambda: self._move(1))

    def _add(self):
        for item in self.avail_list.selectedItems():
            if item.text() not in self.sequence: self.sequence.append(item.text())
        self._refresh()

    def _remove(self):
        for item in self.seq_list.selectedItems():
            if item.text() in self.sequence: self.sequence.remove(item.text())
        self._refresh()

    def _move(self, dir):
        row = self.seq_list.currentRow()
        if row < 0: return
        new_row = row + dir
        if 0 <= new_row < len(self.sequence):
            self.sequence[row], self.sequence[new_row] = self.sequence[new_row], self.sequence[row]
            self._refresh(); self.seq_list.setCurrentRow(new_row)

    def _refresh(self):
        self.seq_list.clear(); self.seq_list.addItems(self.sequence)
        self.preview_lbl.setText(f"Total: {len(self.sequence)} shapes")

    def get_sequence(self): return self.sequence