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
        samples_per_pixel = max(1, len(self.audio_data) // width)
        waveform = []
        
        for i in range(0, len(self.audio_data), samples_per_pixel):
            chunk = self.audio_data[i:i + samples_per_pixel]
            if len(chunk) > 0:
                waveform.append(np.max(np.abs(chunk)))
        
        if not waveform:
            return
            
        # Draw waveform
        pen = QPen(QColor(100, 200, 100))
        pen.setWidth(1)
        painter.setPen(pen)
        
        center_y = height // 2
        max_amplitude = max(waveform) if max(waveform) > 0 else 1
        
        for x, amplitude in enumerate(waveform):
            y = int((amplitude / max_amplitude) * (height // 2 - 10))
            painter.drawLine(x, center_y - y, x, center_y + y)
        
        # Draw playback position
        if self.playback_position > 0:
            x_pos = int(self.playback_position * width)
            painter.setPen(QPen(QColor(255, 255, 0), 2))
            painter.drawLine(x_pos, 0, x_pos, height)
        
        painter.end()

class TrackWidget(QWidget):
    """Widget for audio track control and visualization"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Audio state
        self.audio_data = None
        self.vocals_data = None
        self.beat_data = None
        self.sample_rate = 22050
        self.is_playing = False
        self.playback_position = 0
        
        # pygame for audio playback
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        
        self.init_ui()
        self.setup_timers()
        
    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # Track label
        self.track_label = QLabel("No Track Loaded")
        self.track_label.setAlignment(Qt.AlignCenter)
        self.track_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.track_label)
        
        # Visualizer
        self.visualizer = AudioVisualizer()
        layout.addWidget(self.visualizer)
        
        # Playback controls
        controls_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶️")
        self.play_btn.setFixedSize(40, 40)
        self.play_btn.clicked.connect(self.play)
        controls_layout.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton("⏹️")
        self.stop_btn.setFixedSize(40, 40)
        self.stop_btn.clicked.connect(self.stop)
        controls_layout.addWidget(self.stop_btn)
        
        # Volume slider
        controls_layout.addWidget(QLabel("Volume:"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.valueChanged.connect(self.update_volume)
        controls_layout.addWidget(self.volume_slider)
        
        layout.addLayout(controls_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Info labels
        info_layout = QHBoxLayout()
        
        self.duration_label = QLabel("Duration: 0:00")
        info_layout.addWidget(self.duration_label)
        
        self.position_label = QLabel("Position: 0:00")
        info_layout.addWidget(self.position_label)
        
        self.peak_label = QLabel("Peak: -∞ dB")
        info_layout.addWidget(self.peak_label)
        
        layout.addLayout(info_layout)
        
    def setup_timers(self):
        """Setup playback timers"""
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.update_playback)
        self.playback_timer.setInterval(50)  # 20 updates per second
        
    def set_audio(self, audio_data, sample_rate=22050):
        """Set main audio data"""
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        
        duration = len(audio_data) / sample_rate
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        
        self.track_label.setText(f"Main Track - {minutes}:{seconds:02d}")
        self.visualizer.set_audio(audio_data)
        self.duration_label.setText(f"Duration: {minutes}:{seconds:02d}")
        
        # Calculate peak
        if len(audio_data) > 0:
            peak_db = 20 * np.log10(max(np.max(np.abs(audio_data)), 1e-10))
            self.peak_label.setText(f"Peak: {peak_db:.1f} dB")
        
    def set_vocals(self, vocals_data):
        """Set vocals data"""
        self.vocals_data = vocals_data
        # Could implement vocal-specific controls here
        
    def set_beat(self, beat_data):
        """Set beat data"""
        self.beat_data = beat_data
        # Could implement beat-specific controls here
        
    def play(self):
        """Start playback"""
        if self.audio_data is not None:
            try:
                # Convert to pygame format
                audio_int = (self.audio_data * 32767).astype(np.int16)
                
                # Create sound object
                sound = pygame.sndarray.make_sound(audio_int)
                
                # Play
                sound.play()
                self.is_playing = True
                self.play_btn.setText("⏸️")
                
                # Start timer
                self.playback_position = 0
                self.playback_timer.start()
                
                logger.info("Playback started")
                
            except Exception as e:
                logger.error(f"Playback failed: {str(e)}")
                
    def stop(self):
        """Stop playback"""
        pygame.mixer.stop()
        self.is_playing = False
        self.play_btn.setText("▶️")
        self.playback_timer.stop()
        self.playback_position = 0
        self.visualizer.set_position(0)
        self.position_label.setText("Position: 0:00")
        logger.info("Playback stopped")
        
    def update_playback(self):
        """Update playback position"""
        if self.is_playing and self.audio_data is not None:
            # Simulate playback position (in real app, get from pygame)
            self.playback_position += 0.05  # Rough estimate
            
            if self.playback_position >= 1.0:
                self.stop()
            else:
                self.visualizer.set_position(self.playback_position)
                
                # Update position label
                duration = len(self.audio_data) / self.sample_rate
                current_time = self.playback_position * duration
                minutes = int(current_time // 60)
                seconds = int(current_time % 60)
                self.position_label.setText(f"Position: {minutes}:{seconds:02d}")
                
    def update_volume(self):
        """Update playback volume"""
        volume = self.volume_slider.value() / 100.0
        pygame.mixer.set_volume(volume)
        
    def set_progress(self, progress):
        """Set progress bar value (0-100)"""
        self.progress_bar.setValue(int(progress))
        self.progress_bar.setVisible(progress > 0 and progress < 100)
        
    def get_mixed_audio(self):
        """Get mixed audio (main + vocals + beat)"""
        if self.audio_data is None:
            return None
            
        mixed = self.audio_data.copy()
        
        # Add vocals if available
        if self.vocals_data is not None and len(self.vocals_data) == len(mixed):
            mixed = mixed + self.vocals_data * 0.8  # Mix at 80% volume
            
        # Add beat if available
        if self.beat_data is not None and len(self.beat_data) == len(mixed):
            mixed = mixed + self.beat_data * 0.6  # Mix at 60% volume
            
        # Prevent clipping
        max_val = np.max(np.abs(mixed))
        if max_val > 0.95:
            mixed = mixed * (0.95 / max_val)
            
        return mixed
