# AI Modules Package
from .vocal_separator import VocalSeparator
from .noise_reduction import NoiseReducer
from .beat_generator import BeatGenerator
from .mastering_engine import MasteringEngine
from .musicgen_wrapper import MusicGenWrapper

__all__ = ['VocalSeparator', 'NoiseReducer', 'BeatGenerator', 'MasteringEngine', 'MusicGenWrapper']
📁 src/ai_modules/vocal_separator.py
Python
Copy
import numpy as np
import torch
import os
import logging
from typing import Dict, Optional
import librosa
from demucs import separate
from demucs.pretrained import get_model

logger = logging.getLogger(__name__)

class VocalSeparator:
    """AI-powered vocal separation using Demucs"""
    
    def __init__(self, model_name: str = "htdemucs"):
        self.model_name = model_name
        self.model = None
        self.sample_rate = 22050
        self._load_model()
        
    def _load_model(self):
        """Load Demucs model"""
        try:
            logger.info(f"Loading Demucs model: {self.model_name}")
            self.model = get_model(self.model_name)
            logger.info("Demucs model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Demucs model: {str(e)}")
            raise
            
    def separate_vocals(self, audio_path: str) -> Dict[str, np.ndarray]:
        """
        Separate audio into stems using Demucs
        
        Returns:
            Dictionary with keys: vocals, drums, bass, other
        """
        try:
            logger.info(f"Separating audio: {audio_path}")
            
            # Create output directory
            output_dir = "temp_separated"
            os.makedirs(output_dir, exist_ok=True)
            
            # Run separation
            separate.main(
                ["--mp3", "--two-stems", "vocals", "-n", self.model_name, 
                 audio_path, "-o", output_dir]
            )
            
            # Load separated files
            base_name = os.path.splitext(os.path.basename(audio_path))[0]
            separated_dir = os.path.join(output_dir, base_name)
            
            # Load separated stems
            vocals, _ = librosa.load(
                os.path.join(separated_dir, "vocals.mp3"), 
                sr=self.sample_rate
            )
            accompaniment, _ = librosa.load(
                os.path.join(separated_dir, "no_vocals.mp3"), 
                sr=self.sample_rate
            )
            
            # Clean up temp files
            import shutil
            shutil.rmtree(output_dir)
            
            logger.info("Vocal separation completed")
            
            return {
                'vocals': vocals,
                'accompaniment': accompaniment
            }
            
        except Exception as e:
            logger.error(f"Vocal separation failed: {str(e)}")
            raise
    
    def clean_vocals(self, vocals: np.ndarray) -> np.ndarray:
        """Clean vocals using spectral processing"""
        try:
            logger.info("Cleaning vocals...")
            
            # Apply spectral gating for noise reduction
            cleaned = self._spectral_gate(vocals)
            
            # Apply gentle de-essing
            cleaned = self._de_ess(cleaned)
            
            # Apply light compression
            cleaned = self._compress(cleaned)
            
            logger.info("Vocal cleaning completed")
            return cleaned
            
        except Exception as e:
            logger.error(f"Vocal cleaning failed: {str(e)}")
            raise
    
    def _spectral_gate(self, audio: np.ndarray, threshold: float = 0.01) -> np.ndarray:
        """Apply spectral gating for noise reduction"""
        # Compute STFT
        stft = librosa.stft(audio)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Estimate noise floor
        noise_floor = np.percentile(magnitude, 10, axis=1, keepdims=True)
        
        # Apply gate
        gated_magnitude = np.where(magnitude > noise_floor * threshold, magnitude, 0)
        
        # Reconstruct signal
        gated_stft = gated_magnitude * np.exp(1j * phase)
        cleaned = librosa.istft(gated_stft)
        
        return cleaned
    
    def _de_ess(self, audio: np.ndarray) -> np.ndarray:
        """Apply gentle de-essing"""
        # Simple high-frequency compression
        stft = librosa.stft(audio)
        magnitude = np.abs(stft)
        
        # Find high-frequency components (4-8kHz)
        freqs = librosa.fft_frequencies(sr=self.sample_rate)
        hf_mask = (freqs >= 4000) & (freqs <= 8000)
        
        # Compress high frequencies
        magnitude[hf_mask] = magnitude[hf_mask] ** 0.8
        
        # Reconstruct
        phase = np.angle(stft)
        de_essed_stft = magnitude * np.exp(1j * phase)
        return librosa.istft(de_essed_stft)
    
    def _compress(self, audio: np.ndarray, ratio: float = 2.0) -> np.ndarray:
        """Apply gentle compression"""
        # Simple peak compression
        threshold = 0.5
        compressed = np.where(
            np.abs(audio) > threshold,
            threshold + (np.abs(audio) - threshold) / ratio,
            np.abs(audio)
        )
        
        # Preserve sign
        return np.sign(audio) * compressed
