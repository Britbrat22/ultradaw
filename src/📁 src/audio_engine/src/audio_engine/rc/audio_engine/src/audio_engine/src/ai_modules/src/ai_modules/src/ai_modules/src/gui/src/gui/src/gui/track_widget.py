import numpy as np
import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QSlider, 
                             QPushButton, QHBoxLayout, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
import pygame

logger = logging.getLogger(__name__)

class AudioVisualizer(QWidget):
    """Simple audio waveform visualizer"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_data = None
        self.playback_position = 0
        self.setMinimumHeight(100)
        self.setMaximumHeight(150)
        
    def set_audio(self, audio_data):
        """Set audio data for visualization"""
        self.audio_data = audio_data
        self.playback_position = 0
        self.update()
        
    def set_position(self, position):
        """Set playback position (0-1)"""
        self.playback_position = position
        self.update()
        
    def paintEvent(self, event):
        """Paint the waveform"""
        if self.audio_data is None:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Background
        painter.fillRect(0, 0, width, height, QColor(45, 45, 45))
        
        # Calculate waveform data
