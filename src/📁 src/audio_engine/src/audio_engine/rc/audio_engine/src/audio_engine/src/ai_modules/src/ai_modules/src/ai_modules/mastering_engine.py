import numpy as np
from scipy import signal
import librosa
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MasteringEngine:
    """AI-powered audio mastering engine"""
    
    def __init__(self, target_lufs: float = -14.0, target_peak: float = -1.0):
        self.target_lufs = target_lufs
        self.target_peak = target_peak
        self.sample_rate = 22050
        
        # Mastering chain parameters
        self.eq_params = self._init_eq_params()
        self.compressor_params = self._init_compressor_params()
        self.limiter_params = self._init_limiter_params()
        
    def master_track(self, audio: np.ndarray, sample_rate: int = 22050) -> np.ndarray:
        """
        Master audio to radio-ready quality
        
        Process chain:
        1. Input validation and preparation
        2. EQ balancing (multi-band)
        3. Dynamic range compression
        4. Stereo enhancement
        5. Harmonic excitation
        6. Peak limiting
        7. Loudness normalization
        """
        
        try:
            logger.info("Starting mastering process...")
            logger.info(f"Input audio: {len(audio)} samples, peak: {np.max(np.abs(audio)):.3f}")
            
            # Step 1: Input validation
            audio = self._validate_input(audio)
            
            # Step 2: Multi-band EQ
            logger.info("Applying multi-band EQ...")
            audio = self._apply_multiband_eq(audio, sample_rate)
            
            # Step 3: Dynamic compression
            logger.info("Applying dynamic compression...")
            audio = self._apply_compression(audio)
            
            # Step 4: Stereo enhancement
            logger.info("Applying stereo enhancement...")
            audio = self._enhance_stereo(audio)
            
            # Step 5: Harmonic excitation
            logger.info("Applying harmonic excitation...")
            audio = self._apply_harmonic_excitation(audio)
            
            # Step 6: Peak limiting
            logger.info("Applying peak limiting...")
            audio = self._apply_limiting(audio)
            
            # Step 7: Loudness normalization
            logger.info("Normalizing loudness...")
            audio = self._normalize_loudness(audio, sample_rate)
            
            logger.info(f"Mastering completed. Final peak: {np.max(np.abs(audio)):.3f}")
            return audio
            
        except Exception as e:
            logger.error(f"Mastering failed: {str(e)}")
            raise
    
    def _validate_input(self, audio: np.ndarray) -> np.ndarray:
        """Validate and prepare input audio"""
        # Remove any NaN or infinite values
        audio = np.nan_to_num(audio, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Ensure audio is not silent
        if np.max(np.abs(audio)) < 1e-10:
            raise ValueError("Input audio is silent")
            
        # Normalize to prevent extreme values
        peak = np.max(np.abs(audio))
        if peak > 1.0:
            audio = audio / peak * 0.95
            
        return audio
    
    def _init_eq_params(self) -> Dict[str, Any]:
        """Initialize EQ parameters"""
        return {
            'low_shelf': {'freq': 100, 'gain': 0.0, 'q': 0.7},
            'low_mid': {'freq': 250, 'gain': 0.0, 'q': 0.8},
            'mid': {'freq': 1000, 'gain': 0.0, 'q': 1.0},
            'high_mid': {'freq': 4000, 'gain': 0.0, 'q': 0.8},
            'high_shelf': {'freq': 8000, 'gain': 0.0, 'q': 0.7}
        }
    
    def _init_compressor_params(self) -> Dict[str, Any]:
        """Initialize compressor parameters"""
        return {
            'threshold': -18.0,  # dB
            'ratio': 2.5,
            'attack': 0.01,      # seconds
            'release': 0.1,      # seconds
            'knee': 3.0,         # dB
            'makeup_gain': 2.0   # dB
        }
    
    def _init_limiter_params(self) -> Dict[str, Any]:
        """Initialize limiter parameters"""
        return {
            'threshold': -0.5,   # dBFS
            'release': 0.005,    # seconds
            'lookahead': 0.002   # seconds
        }
    
    def _apply_multiband_eq(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply multi-band EQ"""
        # Analyze frequency content
        spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sample_rate)[0]
        avg_centroid = np.mean(spectral_centroid)
        
        # Adjust EQ based on spectral analysis
        if avg_centroid < 1000:  # Dark audio
            self.eq_params['high_mid']['gain'] = 1.5
            self.eq_params['high_shelf']['gain'] = 2.0
        elif avg_centroid > 4000:  # Bright audio
            self.eq_params['low_mid']['gain'] = 1.0
        
        # Apply EQ bands
        audio = self._apply_low_shelf(audio, sample_rate)
        audio = self._apply_peaking_filters(audio, sample_rate)
        audio = self._apply_high_shelf(audio, sample_rate)
        
        return audio
    
    def _apply_low_shelf(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply low shelf filter"""
        freq = self.eq_params['low_shelf']['freq']
        gain = self.eq_params['low_shelf']['gain']
        
        if abs(gain) > 0.1:
            w0 = 2 * np.pi * freq / sample_rate
            A = 10**(gain/40)
            alpha = np.sin(w0) / 2 * np.sqrt((A + 1/A) * (1/0.7 - 1) + 2)
            
            # Shelf filter coefficients
            b0 = A * ((A + 1) - (A - 1) * np.cos(w0) + 2 * np.sqrt(A) * alpha)
            b1 = 2 * A * ((A - 1) - (A + 1) * np.cos(w0))
            b2 = A * ((A + 1) - (A - 1) * np.cos(w0) - 2 * np.sqrt(A) * alpha)
            a0 = (A + 1) + (A - 1) * np.cos(w0) + 2 * np.sqrt(A) * alpha
            a1 = -2 * ((A - 1) + (A + 1) * np.cos(w0))
            a2 = (A + 1) + (A - 1) * np.cos(w0) - 2 * np.sqrt(A) * alpha
            
            b = [b0/a0, b1/a0, b2/a0]
            a = [1, a1/a0, a2/a0]
            
            return signal.filtfilt(b, a, audio)
        
        return audio
    
    def _apply_peaking_filters(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply peaking filters for mid frequencies"""
        for band in ['low_mid', 'mid', 'high_mid']:
            params = self.eq_params[band]
            if abs(params['gain']) > 0.1:
                audio = self._peaking_filter(audio, sample_rate, params)
        return audio
    
    def _peaking_filter(self, audio: np.ndarray, sample_rate: int, params: Dict) -> np.ndarray:
        """Apply peaking filter"""
        freq = params['freq']
        gain = params['gain']
        q = params['q']
        
        w0 = 2 * np.pi * freq / sample_rate
        A = 10**(gain/40)
        alpha = np.sin(w0) / (2 * q)
        
        # Peaking filter coefficients
        b0 = 1 + alpha * A
        b1 = -2 * np.cos(w0)
        b2 = 1 - alpha * A
        a0 = 1 + alpha / A
        a1 = -2 * np.cos(w0)
        a2 = 1 - alpha / A
        
        b = [b0/a0, b1/a0, b2/a0]
        a = [1, a1/a0, a2/a0]
        
        return signal.filtfilt(b, a, audio)
    
    def _apply_high_shelf(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply high shelf filter"""
        freq = self.eq_params['high_shelf']['freq']
        gain = self.eq_params['high_shelf']['gain']
        
        if abs(gain) > 0.1:
            w0 = 2 * np.pi * freq / sample_rate
            A = 10**(gain/40)
            alpha = np.sin(w0) / 2 * np.sqrt((A + 1/A) * (1/0.7 - 1) + 2)
            
            # High shelf filter coefficients
            b0 = A * ((A + 1) + (A - 1) * np.cos(w0) + 2 * np.sqrt(A) * alpha)
            b1 = -2 * A * ((A - 1) + (A + 1) * np.cos(w0))
            b2 = A * ((A + 1) + (A - 1) * np.cos(w0) - 2 * np.sqrt(A) * alpha)
            a0 = (A + 1) - (A - 1) * np.cos(w0) + 2 * np.sqrt(A) * alpha
            a1 = 2 * ((A - 1) - (A + 1) * np.cos(w0))
            a2 = (A + 1) - (A - 1) * np.cos(w0) - 2 * np.sqrt(A) * alpha
            
            b = [b0/a0, b1/a0, b2/a0]
            a = [1, a1/a0, a2/a0]
            
            return signal.filtfilt(b, a, audio)
        
        return audio
    
    def _apply_compression(self, audio: np.ndarray) -> np.ndarray:
        """Apply dynamic range compression"""
        params = self.compressor_params
        
        # Convert parameters
        threshold = 10**(params['threshold']/20)  # Linear
        ratio = params['ratio']
        attack_samples = int(params['attack'] * self.sample_rate)
        release_samples = int(params['release'] * self.sample_rate)
        knee = 10**(params['knee']/20)  # Linear
        
        # Simple peak detector
        envelope = np.abs(audio)
        
        # Apply attack and release
        alpha_attack = np.exp(-1/attack_samples)
        alpha_release = np.exp(-1/release_samples)
        
        smoothed_envelope = np.zeros_like(envelope)
        smoothed_envelope[0] = envelope[0]
        
        for i in range(1, len(envelope)):
            if envelope[i] > smoothed_envelope[i-1]:
                # Attack
                smoothed_envelope[i] = alpha_attack * smoothed_envelope[i-1] + \
                                      (1 - alpha_attack) * envelope[i]
            else:
                # Release
                smoothed_envelope[i] = alpha_release * smoothed_envelope[i-1] + \
                                      (1 - alpha_release) * envelope[i]
        
        # Apply compression with soft knee
        gain_reduction = np.ones_like(smoothed_envelope)
        
        above_threshold = smoothed_envelope > threshold
        below_knee = smoothed_envelope < (threshold / knee)
        
        # Hard compression above threshold + knee
        hard_compressed = (smoothed_envelope - threshold) / ratio + threshold
        
        # Soft compression in knee region
        knee_region = ~below_knee & ~above_threshold
        soft_compressed = smoothed_envelope + \
                         (1/ratio - 1) * (smoothed_envelope - threshold)**2 / \
                         (2 * threshold * (knee - 1))
        
        gain_reduction = np.where(above_threshold, hard_compressed / smoothed_envelope, gain_reduction)
        gain_reduction = np.where(knee_region, soft_compressed / smoothed_envelope, gain_reduction)
        
        # Apply gain reduction
        compressed = audio * gain_reduction
        
        # Apply makeup gain
        makeup_gain = 10**(params['makeup_gain']/20)
        compressed = compressed * makeup_gain
        
        return compressed
    
    def _enhance_stereo(self, audio: np.ndarray) -> np.ndarray:
        """Enhance stereo width (mono to pseudo-stereo)"""
        # For mono audio, create stereo enhancement
        if len(audio.shape) == 1:
            # Create stereo signal
            stereo = np.zeros((2, len(audio)))
            
            # Slight delay and EQ difference for stereo width
            delay_samples = int(0.001 * self.sample_rate)  # 1ms delay
            
            # Left channel
            stereo[0, delay_samples:] = audio[:-delay_samples]
            stereo[0, :delay_samples] = audio[:delay_samples]
            
            # Right channel (slightly different)
            stereo[1, :] = audio
            
            # Apply subtle EQ difference
            # Left: slight low boost
            b_low = [1.0, 0, 0]
            a_low = [1.0, -0.5, 0.1]
            stereo[0] = signal.filtfilt(b_low, a_low, stereo[0])
            
            # Right: slight high boost
            b_high = [0.8, -0.8, 0]
            a_high = [1.0, -0.7, 0.2]
            stereo[1] = signal.filtfilt(b_high, a_high, stereo[1])
            
            # Convert back to mono for further processing
            return np.mean(stereo, axis=0)
        
        return audio
    
    def _apply_harmonic_excitation(self, audio: np.ndarray) -> np.ndarray:
        """Apply harmonic excitation for brightness"""
        # Simple harmonic generation using non-linear processing
        harmonic = audio * (1 + 0.1 * np.tanh(audio * 3))
        
        # Blend with original
        excited = audio + 0.3 * (harmonic - audio)
        
        return excited
    
    def _apply_limiting(self, audio: np.ndarray) -> np.ndarray:
        """Apply peak limiting"""
        params = self.limiter_params
        
        threshold = 10**(params['threshold']/20)  # Linear
        release_samples = int(params['release'] * self.sample_rate)
        lookahead_samples = int(params['lookahead'] * self.sample_rate)
        
        # Simple peak limiter
        limited = np.copy(audio)
        
        for i in range(len(audio)):
            # Look ahead for peaks
            look_ahead_end = min(i + lookahead_samples, len(audio))
            current_peak = np.max(np.abs(audio[i:look_ahead_end]))
            
            if current_peak > threshold:
                # Calculate gain reduction
                gain_reduction = threshold / current_peak
                
                # Apply with smooth release
                if i > 0:
                    alpha = np.exp(-1/release_samples)
                    gain_reduction = alpha * gain_reduction + (1 - alpha) * 1.0
                
                limited[i] = audio[i] * gain_reduction
        
        return limited
    
    def _normalize_loudness(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Normalize to target LUFS"""
        current_lufs = self._calculate_lufs(audio, sample_rate)
        gain_needed = self.target_lufs - current_lufs
        
        # Convert gain from dB to linear
        linear_gain = 10**(gain_needed/20)
        
        logger.info(f"Loudness normalization: {current_lufs:.1f} LUFS -> {self.target_lufs:.1f} LUFS "
                   f"(gain: {gain_needed:.1f} dB)")
        
        return audio * linear_gain
    
    def _calculate_lufs(self, audio: np.ndarray, sample_rate: int) -> float:
        """Calculate integrated loudness in LUFS"""
        # Simplified LUFS calculation
        # Apply K-weighting filter
        k_weighted = self._k_weighting(audio, sample_rate)
        
        # Calculate mean square
        mean_square = np.mean(k_weighted**2)
        
        # Convert to LUFS
        lufs = -0.691 + 10 * np.log10(mean_square + 1e-12)
        
        return lufs
    
    def _k_weighting(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply K-weighting filter for loudness measurement"""
        # Pre-filtering
        b_pre = [1.53512485958697, -2.69169618940638, 1.19839281085285]
        a_pre = [1.0, -1.69065929318241, 0.73248077421585]
        
        audio_pre = signal.filtfilt(b_pre, a_pre, audio)
        
        # High-pass filter
        b_hp = [1.0, -2.0, 1.0]
        a_hp = [1.0, -1.99004745483398, 0.99007225036621]
        
        audio_hp = signal.filtfilt(b_hp, a_hp, audio_pre)
        
        return audio_hp
