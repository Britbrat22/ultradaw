import numpy as np
import librosa
import soundfile as sf
from typing import Optional, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Main audio processing engine"""
    
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self.current_audio = None
        self.current_file_path = None
        
    def load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        """Load audio file"""
        try:
            logger.info(f"Loading audio file: {file_path}")
            audio, sr = librosa.load(file_path, sr=self.sample_rate, mono=True)
            self.current_audio = audio
            self.current_file_path = file_path
            
            logger.info(f"Audio loaded: {len(audio)} samples at {sr}Hz")
            return audio, sr
            
        except Exception as e:
            logger.error(f"Failed to load audio: {str(e)}")
            raise
            
    def save_audio(self, audio: np.ndarray, file_path: str, sample_rate: int = None) -> str:
        """Save audio to file"""
        if sample_rate is None:
            sample_rate = self.sample_rate
            
        try:
            logger.info(f"Saving audio to: {file_path}")
            sf.write(file_path, audio, sample_rate)
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save audio: {str(e)}")
            raise
    
    def get_audio_info(self, audio: np.ndarray = None) -> Dict[str, Any]:
        """Get audio information"""
        if audio is None:
            audio = self.current_audio
            
        if audio is None:
            return {}
            
        return {
            'duration': len(audio) / self.sample_rate,
            'samples': len(audio),
            'sample_rate': self.sample_rate,
            'rms_level': float(np.sqrt(np.mean(audio**2))),
            'peak_level': float(np.max(np.abs(audio))),
            'dynamic_range': float(np.max(np.abs(audio))) - float(np.sqrt(np.mean(audio**2)))
        }
    
    def normalize_audio(self, audio: np.ndarray, target_peak: float = 0.95) -> np.ndarray:
        """Normalize audio to target peak level"""
        peak = np.max(np.abs(audio))
        if peak > 0:
            gain = target_peak / peak
            return audio * gain
        return audio
    
    def apply_fade(self, audio: np.ndarray, fade_in: float = 0.01, fade_out: float = 0.01) -> np.ndarray:
        """Apply fade in/out"""
        fade_in_samples = int(fade_in * self.sample_rate)
        fade_out_samples = int(fade_out * self.sample_rate)
        
        if fade_in_samples > 0:
            fade_in_curve = np.linspace(0, 1, fade_in_samples)
            audio[:fade_in_samples] *= fade_in_curve
            
        if fade_out_samples > 0:
            fade_out_curve = np.linspace(1, 0, fade_out_samples)
            audio[-fade_out_samples:] *= fade_out_curve
            
        return audio
