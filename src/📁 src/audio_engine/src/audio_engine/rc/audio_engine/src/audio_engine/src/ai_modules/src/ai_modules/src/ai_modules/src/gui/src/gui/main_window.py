import sys
import os
import logging
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QProgressBar,
                             QTextEdit, QSplitter, QFrame, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor

from .track_widget import TrackWidget
from .effects_panel import EffectsPanel
from .export_dialog import ExportDialog

logger = logging.getLogger(__name__)

class MasteringThread(QThread):
    """Thread for mastering process"""
    progress_updated = pyqtSignal(int)
    mastering_complete = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, mastering_engine, audio, sample_rate):
        super().__init__()
        self.mastering_engine = mastering_engine
        self.audio = audio
        self.sample_rate = sample_rate
        
    def run(self):
        try:
            self.progress_updated.emit(10)
            
            # Master the audio
            mastered_audio = self.mastering_engine.master_track(self.audio, self.sample_rate)
            
            self.progress_updated.emit(100)
            self.mastering_complete.emit("Mastering completed successfully!")
            
        except Exception as e:
            self.error_occurred.emit(str(e))

class BeatGenerationThread(QThread):
    """Thread for beat generation"""
    progress_updated = pyqtSignal(int)
    beats_generated = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, beat_generator, vocals, prompt, style):
        super().__init__()
        self.beat_generator = beat_generator
        self.vocals = vocals
        self.prompt = prompt
        self.style = style
        
    def run(self):
        try:
            self.progress_updated.emit(20)
            
            # Generate beats
            beats = self.beat_generator.generate_beats(
                self.vocals, self.prompt, self.style
            )
            
            self.progress_updated.emit(100)
            self.beats_generated.emit(beats)
            
        except Exception as e:
            self.error_occurred.emit(str(e))

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, audio_processor, vocal_separator, beat_generator, mastering_engine):
        super().__init__()
        
        # Store components
        self.audio_processor = audio_processor
        self.vocal_separator = vocal_separator
        self.beat_generator = beat_generator
        self.mastering_engine = mastering_engine
        
        # Current state
        self.current_audio = None
        self.current_vocals = None
        self.current_beats = []
        self.selected_beat = None
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("🎵 AI DAW - MacBook Air 2013 Edition")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set dark theme
        self.set_dark_theme()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Top toolbar
        toolbar = self.create_toolbar()
        main_layout.addLayout(toolbar)
        
        # Main content area
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Track controls
        left_panel = self.create_left_panel()
        content_splitter.addWidget(left_panel)
        
        # Center panel - Main controls
        center_panel = self.create_center_panel()
        content_splitter.addWidget(center_panel)
        
        # Right panel - Effects
        right_panel = self.create_right_panel()
        content_splitter.addWidget(right_panel)
        
        content_splitter.setSizes([300, 600, 300])
        main_layout.addWidget(content_splitter)
        
        # Status bar
        self.status_bar = self.create_status_bar()
        main_layout.addWidget(self.status_bar)
        
    def set_dark_theme(self):
        """Apply dark theme to application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
            QPushButton:pressed {
                background-color: #4d4d4d;
            }
            QPushButton:disabled {
                background-color: #1a1a1a;
                color: #666666;
            }
            QTextEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
            }
            QProgressBar {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        
    def create_toolbar(self):
        """Create top toolbar"""
        toolbar = QHBoxLayout()
        
        # Logo/Title
        title = QLabel("🎵 AI DAW")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        toolbar.addWidget(title)
        
        toolbar.addStretch()
        
        # File operations
        self.load_btn = QPushButton("📁 Load Audio")
        self.load_btn.clicked.connect(self.load_audio)
        toolbar.addWidget(self.load_btn)
        
        self.save_btn = QPushButton("💾 Export")
        self.save_btn.clicked.connect(self.export_audio)
        self.save_btn.setEnabled(False)
        toolbar.addWidget(self.save_btn)
        
        return toolbar
        
    def create_left_panel(self):
        """Create left panel with track controls"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Track widget
        self.track_widget = TrackWidget()
        layout.addWidget(self.track_widget)
        
        # Transport controls
        transport_frame = QFrame()
        transport_frame.setFrameStyle(QFrame.Box)
        transport_layout = QVBoxLayout(transport_frame)
        
        transport_label = QLabel("🎮 Transport")
        transport_label.setAlignment(Qt.AlignCenter)
        transport_layout.addWidget(transport_label)
        
        # Play controls
        play_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶️ Play")
        self.play_btn.clicked.connect(self.play_audio)
        play_layout.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.clicked.connect(self.stop_audio)
        play_layout.addWidget(self.stop_btn)
        
        transport_layout.addLayout(play_layout)
        
        layout.addWidget(transport_frame)
        layout.addStretch()
        
        return panel
        
    def create_center_panel(self):
        """Create center panel with main controls"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # AI Processing section
        ai_frame = QFrame()
        ai_frame.setFrameStyle(QFrame.Box)
        ai_layout = QVBoxLayout(ai_frame)
        
        ai_label = QLabel("🤖 AI Processing")
        ai_label.setAlignment(Qt.AlignCenter)
        ai_label.setFont(QFont("", 14, QFont.Bold))
        ai_layout.addWidget(ai_label)
        
        # Vocal processing
        vocal_group = QWidget()
        vocal_layout = QVBoxLayout(vocal_group)
        
        vocal_label = QLabel("🎤 Vocal Processing:")
        vocal_layout.addWidget(vocal_label)
        
        self.clean_vocals_btn = QPushButton("✨ Clean Vocals")
        self.clean_vocals_btn.clicked.connect(self.clean_vocals)
        self.clean_vocals_btn.setEnabled(False)
        vocal_layout.addWidget(self.clean_vocals_btn)
        
        self.separate_vocals_btn = QPushButton("🔊 Separate Vocals")
        self.separate_vocals_btn.clicked.connect(self.separate_vocals)
        self.separate_vocals_btn.setEnabled(False)
        vocal_layout.addWidget(self.separate_vocals_btn)
        
        ai_layout.addWidget(vocal_group)
        
        # Beat generation
        beat_group = QWidget()
        beat_layout = QVBoxLayout(beat_group)
        
        beat_label = QLabel("🥁 Beat Generation:")
        beat_layout.addWidget(beat_label)
        
        self.beat_prompt = QTextEdit()
        self.beat_prompt.setPlaceholderText("Describe your beat...\n(e.g., 'Dark trap beat with heavy 808s')")
        self.beat_prompt.setMaximumHeight(80)
        beat_layout.addWidget(self.beat_prompt)
        
        beat_controls = QHBoxLayout()
        
        self.beat_style = QTextEdit()
        self.beat_style.setPlaceholderText("Style (trap, rnb, lofi, etc.)")
        self.beat_style.setMaximumHeight(30)
        beat_controls.addWidget(self.beat_style)
        
        self.generate_beats_btn = QPushButton("🎵 Generate 3 Beats")
        self.generate_beats_btn.clicked.connect(self.generate_beats)
        self.generate_beats_btn.setEnabled(False)
        beat_controls.addWidget(self.generate_beats_btn)
        
        beat_layout.addLayout(beat_controls)
        
        # Beat selection
        self.beat_selection = QWidget()
        beat_sel_layout = QVBoxLayout(self.beat_selection)
        beat_sel_layout.addWidget(QLabel("Select Beat:"))
        
        self.beat_buttons = []
        for i in range(3):
            btn = QPushButton(f"Beat {i+1}")
            btn.clicked.connect(lambda checked, x=i: self.select_beat(x))
            btn.setEnabled(False)
            self.beat_buttons.append(btn)
            beat_sel_layout.addWidget(btn)
        
        beat_layout.addWidget(self.beat_selection)
        
        ai_layout.addWidget(beat_group)
        
        # Mastering
        master_group = QWidget()
        master_layout = QVBoxLayout(master_group)
        
        master_label = QLabel("🎚️ Mastering:")
        master_layout.addWidget(master_label)
        
        self.master_btn = QPushButton("🎯 Master to Radio Ready")
        self.master_btn.clicked.connect(self.master_track)
        self.master_btn.setEnabled(False)
        master_layout.addWidget(self.master_btn)
        
        ai_layout.addWidget(master_group)
        
        layout.addWidget(ai_frame)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status text
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(100)
        self.status_text.setPlaceholderText("Status messages will appear here...")
        layout.addWidget(self.status_text)
        
        layout.addStretch()
        
        return panel
        
    def create_right_panel(self):
        """Create right panel with effects"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Effects panel
        self.effects_panel = EffectsPanel()
        layout.addWidget(self.effects_panel)
        
        layout.addStretch()
        
        return panel
        
    def create_status_bar(self):
        """Create status bar"""
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        self.peak_meter = QLabel("Peak: -∞ dB")
        status_layout.addWidget(self.peak_meter)
        
        return status_widget
        
    def setup_connections(self):
        """Setup signal connections"""
        # Timer for peak meter updates
        self.peak_timer = QTimer()
        self.peak_timer.timeout.connect(self.update_peak_meter)
        self.peak_timer.start(100)  # Update every 100ms
        
    def load_audio(self):
        """Load audio file"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Load Audio File", "", 
                "Audio Files (*.wav *.mp3 *.flac *.m4a)"
            )
            
            if file_path:
                self.log_status(f"Loading audio: {os.path.basename(file_path)}")
                
                # Load audio
                audio, sr = self.audio_processor.load_audio(file_path)
                self.current_audio = audio
                
                # Update UI
                self.track_widget.set_audio(audio, sr)
                
                # Enable buttons
                self.clean_vocals_btn.setEnabled(True)
                self.separate_vocals_btn.setEnabled(True)
                self.generate_beats_btn.setEnabled(True)
                self.master_btn.setEnabled(True)
                self.save_btn.setEnabled(True)
                
                self.log_status(f"Audio loaded: {self.audio_processor.get_audio_info(audio)}")
                
        except Exception as e:
            self.show_error(f"Failed to load audio: {str(e)}")
            
    def clean_vocals(self):
        """Clean vocals using AI"""
        if self.current_audio is not None:
            try:
                self.log_status("Cleaning vocals...")
                self.set_processing_state(True)
                
                # This would use the vocal separator to clean the audio
                cleaned = self.vocal_separator.clean_vocals(self.current_audio)
                
                # Update current audio
                self.current_audio = cleaned
                self.track_widget.set_audio(cleaned, self.audio_processor.sample_rate)
                
                self.log_status("Vocals cleaned successfully!")
                
            except Exception as e:
                self.show_error(f"Vocal cleaning failed: {str(e)}")
            finally:
                self.set_processing_state(False)
                
    def separate_vocals(self):
        """Separate vocals from audio"""
        if self.current_audio is not None:
            try:
                self.log_status("Separating vocals...")
                self.set_processing_state(True)
                
                # This would use the vocal separator
                separated = self.vocal_separator.separate_vocals(self.audio_processor.current_file_path)
                
                if 'vocals' in separated:
                    self.current_vocals = separated['vocals']
                    self.track_widget.set_vocals(self.current_vocals)
                    self.log_status("Vocals separated successfully!")
                else:
                    self.log_status("Vocal separation completed")
                    
            except Exception as e:
                self.show_error(f"Vocal separation failed: {str(e)}")
            finally:
                self.set_processing_state(False)
                
    def generate_beats(self):
        """Generate beats using AI"""
        if self.current_audio is not None:
            try:
                prompt = self.beat_prompt.toPlainText().strip()
                if not prompt:
                    prompt = "Modern beat"  # Default prompt
                
                style = self.beat_style.toPlainText().strip()
                
                self.log_status(f"Generating beats: '{prompt}'")
                self.set_processing_state(True)
                
                # Use vocals if available, otherwise use main audio
                source_audio = self.current_vocals if self.current_vocals is not None else self.current_audio
                
                # Create and start beat generation thread
                self.beat_thread = BeatGenerationThread(
                    self.beat_generator, source_audio, prompt, style
                )
                self.beat_thread.progress_updated.connect(self.update_progress)
                self.beat_thread.beats_generated.connect(self.beats_generated)
                self.beat_thread.error_occurred.connect(self.show_error)
                self.beat_thread.start()
                
            except Exception as e:
                self.show_error(f"Beat generation failed: {str(e)}")
                self.set_processing_state(False)
                
    def beats_generated(self, beats):
        """Handle generated beats"""
        self.current_beats = beats
        self.log_status(f"Generated {len(beats)} beats")
        
        # Enable beat selection buttons
        for i, btn in enumerate(self.beat_buttons):
            if i < len(beats):
                btn.setEnabled(True)
                btn.setText(f"Beat {i+1} (Score: {beats[i]['quality_score']:.2f})")
            else:
                btn.setEnabled(False)
                
        self.set_processing_state(False)
        
    def select_beat(self, beat_index):
        """Select a generated beat"""
        if 0 <= beat_index < len(self.current_beats):
            self.selected_beat = self.current_beats[beat_index]
            self.log_status(f"Selected Beat {beat_index + 1}")
            
            # Play the selected beat
            beat_audio = self.selected_beat['audio']
            self.track_widget.set_beat(beat_audio)
            
    def master_track(self):
        """Master the current track"""
        if self.current_audio is not None:
            try:
                self.log_status("Mastering track to radio-ready quality...")
                self.set_processing_state(True)
                
                # Create and start mastering thread
                self.master_thread = MasteringThread(
                    self.mastering_engine, self.current_audio, 
                    self.audio_processor.sample_rate
                )
                self.master_thread.progress_updated.connect(self.update_progress)
                self.master_thread.mastering_complete.connect(self.mastering_complete)
                self.master_thread.error_occurred.connect(self.show_error)
                self.master_thread.start()
                
            except Exception as e:
                self.show_error(f"Mastering failed: {str(e)}")
                self.set_processing_state(False)
                
    def mastering_complete(self, message):
        """Handle mastering completion"""
        self.log_status(message)
        self.set_processing_state(False)
        
    def export_audio(self):
        """Export audio"""
        if self.current_audio is not None:
            try:
                dialog = ExportDialog(self.current_audio, self.audio_processor.sample_rate)
                dialog.exec_()
            except Exception as e:
                self.show_error(f"Export failed: {str(e)}")
                
    def play_audio(self):
        """Play current audio"""
        if self.current_audio is not None:
            self.track_widget.play()
            
    def stop_audio(self):
        """Stop audio playback"""
        self.track_widget.stop()
        
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
        
    def set_processing_state(self, processing):
        """Set UI state during processing"""
        self.progress_bar.setVisible(processing)
        if processing:
            self.progress_bar.setValue(0)
            
        # Disable/enable buttons
        buttons = [
            self.load_btn, self.clean_vocals_btn, self.separate_vocals_btn,
            self.generate_beats_btn, self.master_btn, self.save_btn
        ]
        
        for btn in buttons:
            btn.setEnabled(not processing)
            
    def log_status(self, message):
        """Log status message"""
        self.status_text.append(f"• {message}")
        self.status_label.setText(message)
        logger.info(message)
        
    def show_error(self, message):
        """Show error message"""
        self.log_status(f"ERROR: {message}")
        QMessageBox.critical(self, "Error", message)
        logger.error(message)
        
    def update_peak_meter(self):
        """Update peak meter display"""
        if self.current_audio is not None:
            peak_db = 20 * np.log10(max(np.max(np.abs(self.current_audio)), 1e-10))
            self.peak_meter.setText(f"Peak: {peak_db:.1f} dB")
