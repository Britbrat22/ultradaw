import numpy as np
import soundfile as sf
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class Exporter:
    """Audio export utilities"""
    
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self.export_dir = "exports"
        os.makedirs(self.export_dir, exist_ok=True)
        
    def export_wav(self, audio: np.ndarray, filename: str, 
                   bit_depth: int = 24, normalize: bool = True) -> str:
        """Export as WAV file"""
        try:
            if normalize:
                audio = self._normalize_for_export(audio)
                
            file_path = os.path.join(self.export_dir, f"{filename}.wav")
            
            # Convert to appropriate bit depth
            if bit_depth == 16:
                subtype = 'PCM_16'
            elif bit_depth == 24:
                subtype = 'PCM_24'
            else:  # 32-bit float
                subtype = 'FLOAT'
                
            sf.write(file_path, audio, self.sample_rate, subtype=subtype)
            logger.info(f"Exported WAV: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"WAV export failed: {str(e)}")
            raise
            
    def export_mp3(self, audio: np.ndarray, filename: str, 
                   bitrate: int = 320) -> str:
        """Export as MP3 file"""
        try:
            audio = self._normalize_for_export(audio)
            file_path = os.path.join(self.export_dir, f"{filename}.mp3")
            
            # Note: Requires ffmpeg for MP3 export
            temp_wav = os.path.join(self.export_dir, "temp_export.wav")
            sf.write(temp_wav, audio, self.sample_rate)
            
            # Convert to MP3 using ffmpeg
            cmd = f"ffmpeg -i {temp_wav} -codec:a libmp3lame -b:a {bitrate}k {file_path} -y"
            os.system(cmd)
            
            # Clean up temp file
            if os.path.exists(temp_wav):
                os.remove(temp_wav)
                
            logger.info(f"Exported MP3: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"MP3 export failed: {str(e)}")
            raise
    
    def _normalize_for_export(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio for export"""
        peak = np.max(np.abs(audio))
        if peak > 0:
            return audio * (0.95 / peak)
        return audio
