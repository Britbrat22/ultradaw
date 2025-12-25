import numpy as np
import torch
import logging
from typing import List, Dict, Any, Optional
import librosa
from .musicgen_wrapper import MusicGenWrapper

logger = logging.getLogger(__name__)

class BeatGenerator:
    """AI beat generation using MusicGen"""
    
    def __init__(self):
        self.musicgen = MusicGenWrapper()
        self.sample_rate = 22050
        self.tempos = [80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130, 140, 150, 160, 170, 180]
        
    def generate_beats(self, vocal_track: np.ndarray, 
                      prompt: str, 
                      style: str = "auto") -> List[Dict[str, Any]]:
        """
        Generate 3 unique beats for vocal track
        
        Args:
            vocal_track: Audio array of vocals
            prompt: Text description of desired beat
            style: Music genre/style
            
        Returns:
            List of 3 generated beats with metadata
        """
        try:
            logger.info(f"Generating beats for prompt: '{prompt}'")
            
            # Analyze vocal characteristics
            vocal_analysis = self._analyze_vocals(vocal_track)
            logger.info(f"Vocal analysis: tempo={vocal_analysis['tempo']:.1f} BPM, "
                       f"duration={vocal_analysis['duration']:.1f}s")
            
            # Generate 3 different beats
            beats = []
            for i in range(3):
                logger.info(f"Generating beat {i+1}/3...")
                
                # Create variation of prompt
                beat_prompt = self._create_beat_prompt(prompt, vocal_analysis, i)
                selected_tempo = self._select_tempo(vocal_analysis['tempo'], i)
                
                # Generate beat
                beat = self.musicgen.generate(
                    prompt=beat_prompt,
                    duration=vocal_analysis['duration'],
                    tempo=selected_tempo,
                    style=style if style != "auto" else vocal_analysis['style']
                )
                
                # Analyze beat quality
                quality_score = self._calculate_quality(beat, vocal_track)
                
                beat_info = {
                    'audio': beat,
                    'prompt': beat_prompt,
                    'tempo': selected_tempo,
                    'genre': style,
                    'quality_score': quality_score,
                    'variation': i + 1
                }
                
                beats.append(beat_info)
                logger.info(f"Beat {i+1} generated (quality: {quality_score:.2f})")
            
            logger.info("All beats generated successfully")
            return beats
            
        except Exception as e:
            logger.error(f"Beat generation failed: {str(e)}")
            raise
    
    def _analyze_vocals(self, vocals: np.ndarray) -> Dict[str, Any]:
        """Analyze vocal characteristics for beat matching"""
        try:
            # Extract tempo using librosa
            tempo, _ = librosa.beat.beat_track(y=vocals, sr=self.sample_rate)
            if np.isscalar(tempo):
                tempo = float(tempo)
            else:
                tempo = float(tempo[0]) if len(tempo) > 0 else 120.0
            
            # Calculate duration
            duration = len(vocals) / self.sample_rate
            
            # Calculate energy
            energy = np.sqrt(np.mean(vocals**2))
            
            # Detect key (simplified)
            key = self._detect_key(vocals)
            
            # Determine style from energy and tempo
            if tempo < 100 and energy < 0.1:
                style = "lofi"
            elif tempo > 140 and energy > 0.2:
                style = "trap"
            elif 90 < tempo < 130:
                style = "rnb"
            else:
                style = "hiphop"
            
            return {
                'tempo': tempo,
                'duration': duration,
                'energy': energy,
                'key': key,
                'style': style
            }
            
        except Exception as e:
            logger.warning(f"Vocal analysis failed, using defaults: {str(e)}")
            return {
                'tempo': 120.0,
                'duration': len(vocals) / self.sample_rate,
                'energy': 0.1,
                'key': 'C',
                'style': 'hiphop'
            }
    
    def _detect_key(self, audio: np.ndarray) -> str:
        """Simple key detection"""
        try:
            # Extract chroma features
            chroma = librosa.feature.chroma_cqt(y=audio, sr=self.sample_rate)
            
            # Find the most active pitch class
            chroma_mean = np.mean(chroma, axis=1)
            key_index = np.argmax(chroma_mean)
            
            # Map to musical key
            keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            return keys[key_index]
            
        except Exception:
            return 'C'  # Default
    
    def _create_beat_prompt(self, user_prompt: str, vocal_analysis: Dict, variation: int) -> str:
        """Create detailed prompt for beat generation"""
        base_prompts = [
            f"{user_prompt} with professional mixing and modern sound, {vocal_analysis['tempo']:.0f} BPM",
            f"{user_prompt} with creative variations and unique elements, {vocal_analysis['tempo']:.0f} BPM",
            f"{user_prompt} with experimental approach and fresh textures, {vocal_analysis['tempo']:.0f} BPM"
        ]
        
        # Add style-specific enhancements
        style_enhancements = {
            'trap': 'with heavy 808s, sharp hi-hats, and atmospheric pads',
            'lofi': 'with vintage vinyl crackle, jazzy chords, and relaxed drums',
            'rnb': 'with smooth chords, groovy bassline, and crisp snares',
            'hiphop': 'with punchy drums, deep bass, and melodic elements'
        }
        
        base = base_prompts[variation % 3]
        enhancement = style_enhancements.get(vocal_analysis['style'], '')
        
        return f"{base} {enhancement}".strip()
    
    def _select_tempo(self, vocal_tempo: float, variation: int) -> int:
        """Select tempo with slight variations"""
        tempo_options = [
            max(60, vocal_tempo - 5),  # Slightly slower
            vocal_tempo,               # Same tempo
            min(200, vocal_tempo + 5)  # Slightly faster
        ]
        
        selected = int(tempo_options[variation % 3])
        
        # Round to nearest standard tempo
        standard_tempos = self.tempos
        closest_tempo = min(standard_tempos, key=lambda x: abs(x - selected))
        
        return closest_tempo
    
    def _calculate_quality(self, beat: np.ndarray, vocals: np.ndarray) -> float:
        """Calculate quality score for beat-vocal compatibility"""
        try:
            # Calculate beat strength
            tempo1, _ = librosa.beat.beat_track(y=beat, sr=self.sample_rate)
            tempo2, _ = librosa.beat.beat_track(y=vocals, sr=self.sample_rate)
            
            # Tempo compatibility (0-1)
            if np.isscalar(tempo1) and np.isscalar(tempo2):
                tempo_diff = abs(tempo1 - tempo2) / max(tempo1, tempo2)
                tempo_score = max(0, 1 - tempo_diff)
            else:
                tempo_score = 0.5
            
            # Energy compatibility (0-1)
            beat_energy = np.sqrt(np.mean(beat**2))
            vocal_energy = np.sqrt(np.mean(vocals**2))
            
            if beat_energy > 0 and vocal_energy > 0:
                energy_ratio = min(beat_energy, vocal_energy) / max(beat_energy, vocal_energy)
                energy_score = energy_ratio
            else:
                energy_score = 0.5
            
            # Overall quality score
            quality_score = (tempo_score * 0.6) + (energy_score * 0.4)
            
            return min(1.0, max(0.0, quality_score))
            
        except Exception as e:
            logger.warning(f"Quality calculation failed: {str(e)}")
            return 0.5  # Neutral score on error
