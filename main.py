#!/usr/bin/env python3
"""
AI-Powered DAW Main Application
Optimized for MacBook Air 2013
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gui.main_window import MainWindow
from audio_engine.audio_processor import AudioProcessor
from ai_modules.beat_generator import BeatGenerator
from ai_modules.mastering_engine import MasteringEngine
from ai_modules.vocal_separator import VocalSeparator
from utils.logger import setup_logger

def main():
    """Main application entry point"""
    
    # Setup logging
    logger = setup_logger()
    logger.info("Starting AI DAW for MacBook Air 2013")
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("AI DAW")
    app.setApplicationVersion("1.0.0")
    
    # Set application-wide font for better readability
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)
    
    try:
        # Initialize core components
        logger.info("Initializing audio processor...")
        audio_processor = AudioProcessor()
        
        logger.info("Initializing AI modules...")
        vocal_separator = VocalSeparator()
        beat_generator = BeatGenerator()
        mastering_engine = MasteringEngine()
        
        # Create main window
        logger.info("Creating main window...")
        window = MainWindow(
            audio_processor=audio_processor,
            vocal_separator=vocal_separator,
            beat_generator=beat_generator,
            mastering_engine=mastering_engine
        )
        
        window.show()
        logger.info("Application started successfully")
        
        # Start event loop
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
📄 setup_macbook_air.sh
bash
Copy
#!/bin/bash
# setup_macbook_air.sh - Optimized for MacBook Air 2013

set -e  # Exit on error

echo "🎵 Setting up AI DAW for MacBook Air 2013..."
echo "================================================"

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]]; then
    echo "❌ Python 3.8+ required. Found: $python_version"
    exit 1
fi

echo "✅ Python $python_version detected"

# Create virtual environment
echo "🏗️  Creating virtual environment..."
python3 -m venv ai-daw-env
source ai-daw-env/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install PyTorch CPU version (optimized for MacBook Air)
echo "🔥 Installing PyTorch (CPU optimized)..."
pip install torch==2.0.0+cpu torchvision==2.0.0+cpu torchaudio==2.0.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Install other requirements
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p models/demucs models/musicgen models/mastering
mkdir -p exports backups
mkdir -p logs

# Download AI models (optimized versions)
echo "🤖 Downloading AI models..."
python scripts/download_models.py

# Set permissions
echo "🔐 Setting permissions..."
chmod +x main.py
chmod +x scripts/*.py

# Create desktop shortcut
echo "🎯 Creating desktop shortcut..."
cat > "AI DAW.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=AI DAW
Comment=AI-Powered Digital Audio Workstation
Exec=$(pwd)/ai-daw-env/bin/python $(pwd)/main.py
Icon=$(pwd)/assets/icon.png
Terminal=false
Categories=Audio;Music;AudioVideo;
EOF

echo "✅ Setup complete!"
echo ""
echo "🚀 To launch the application:"
echo "   source ai-daw-env/bin/activate"
echo "   python main.py"
echo ""
echo "📁 Desktop shortcut created: 'AI DAW.desktop'"
echo "🎵 Enjoy your AI-powered DAW!"
