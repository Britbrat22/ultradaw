from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QSlider, 
                             QComboBox, QCheckBox, QGroupBox, QHBoxLayout)
from PyQt5.QtCore import Qt, pyqtSignal

class EffectsPanel(QWidget):
    """Panel for audio effects controls"""
    
    effect_changed = pyqtSignal(str, float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """Initialize effects panel UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("🎛️ Effects")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # EQ Section
        eq_group = QGroupBox("Equalizer")
        eq_layout = QVBoxLayout(eq_group)
        
        # Low frequency
        low_layout = QHBoxLayout()
        low_layout.addWidget(QLabel("Low:"))
        self.low_slider = QSlider(Qt.Horizontal)
        self.low_slider.setRange(-12, 12)
        self.low_slider.setValue(0)
        self.low_slider.valueChanged.connect(lambda: self.effect_changed.emit("low", self.low_slider.value()))
        low_layout.addWidget(self.low_slider)
        self.low_label = QLabel("0 dB")
        low_layout.addWidget(self.low_label)
        eq_layout.addLayout(low_layout)
        
        # Mid frequency
        mid_layout = QHBoxLayout()
        mid_layout.addWidget(QLabel("Mid:"))
        self.mid_slider = QSlider(Qt.Horizontal)
        self.mid_slider.setRange(-12, 12)
        self.mid_slider.setValue(0)
        self.mid_slider.valueChanged.connect(lambda: self.effect_changed.emit("mid", self.mid_slider.value()))
        mid_layout.addWidget(self.mid_slider)
        self.mid_label = QLabel("0 dB")
        mid_layout.addWidget(self.mid_label)
        eq_layout.addLayout(mid_layout)
        
        # High frequency
        high_layout = QHBoxLayout()
        high_layout.addWidget(QLabel("High:"))
        self.high_slider = QSlider(Qt.Horizontal)
        self.high_slider.setRange(-12, 12)
        self.high_slider.setValue(0)
        self.high_slider.valueChanged.connect(lambda: self.effect_changed.emit("high", self.high_slider.value()))
        high_layout.addWidget(self.high_slider)
        self.high_label = QLabel("0 dB")
        high_layout.addWidget(self.high_label)
        eq_layout.addLayout(high_layout)
        
        layout.addWidget(eq_group)
        
        # Dynamics Section
        dyn_group = QGroupBox("Dynamics")
        dyn_layout = QVBoxLayout(dyn_group)
        
        # Compressor
        comp_layout = QHBoxLayout()
        comp_layout.addWidget(QLabel("Compression:"))
        self.comp_slider = QSlider(Qt.Horizontal)
        self.comp_slider.setRange(0, 100)
        self.comp_slider.setValue(0)
        self.comp_slider.valueChanged.connect(lambda: self.effect_changed.emit("compression", self.comp_slider.value()))
        comp_layout.addWidget(self.comp_slider)
        self.comp_label = QLabel("0%")
        comp_layout.addWidget(self.comp_label)
        dyn_layout.addLayout(comp_layout)
        
        # Limiter
        self.limiter_check = QCheckBox("Enable Limiter")
        self.limiter_check.stateChanged.connect(lambda: self.effect_changed.emit("limiter", 1 if self.limiter_check.isChecked() else 0))
        dyn_layout.addWidget(self.limiter_check)
        
        layout.addWidget(dyn_group)
        
        # Reverb Section
        reverb_group = QGroupBox("Reverb")
        reverb_layout = QVBoxLayout(reverb_group)
        
        reverb_layout.addWidget(QLabel("Type:"))
        self.reverb_type = QComboBox()
        self.reverb_type.addItems(["None", "Room", "Hall", "Plate", "Chamber"])
        self.reverb_type.currentTextChanged.connect(lambda text: self.effect_changed.emit("reverb_type", self.reverb_type.currentIndex()))
        reverb_layout.addWidget(self.reverb_type)
        
        reverb_amount_layout = QHBoxLayout()
        reverb_amount_layout.addWidget(QLabel("Amount:"))
        self.reverb_slider = QSlider(Qt.Horizontal)
        self.reverb_slider.setRange(0, 100)
        self.reverb_slider.setValue(0)
        self.reverb_slider.valueChanged.connect(lambda: self.effect_changed.emit("reverb", self.reverb_slider.value()))
        reverb_amount_layout.addWidget(self.reverb_slider)
        self.reverb_label = QLabel("0%")
        reverb_amount_layout.addWidget(self.reverb_label)
        reverb_layout.addLayout(reverb_amount_layout)
        
        layout
