import logging
import asyncio
import os
import tempfile
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

try:
    import speech_recognition as sr
    import numpy as np
    import audioop
except ImportError:
    sr = None
    np = None
    audioop = None

# Optional advanced libraries
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    import pocketsphinx
    SPHINX_AVAILABLE = True
except ImportError:
    SPHINX_AVAILABLE = False

try:
    from pydub import AudioSegment
    from pydub.effects import normalize, compress_dynamic_range
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

logger = logging.getLogger("SpeechToText")

class EngineType(Enum):
    """Available speech recognition engines"""
    GOOGLE = "google"
    WHISPER = "whisper"
    SPHINX = "sphinx"
    VOSK = "vosk"
    AZURE = "azure"
    AUTO = "auto"  # Automatically select best available

@dataclass
class AudioFeatures:
    """Extracted audio features for better understanding"""
    energy: float
    silence_ratio: float
    avg_frequency: float
    has_speech: bool
    noise_level: str  # low, medium, high
    language_probabilities: Dict[str, float]

@dataclass
class TranscriptionResult:
    """Enhanced transcription result with metadata"""
    text: str
    confidence: float
    engine_used: EngineType
    language: str
    duration: float
    audio_features: Optional[AudioFeatures] = None
    alternatives: List[str] = None
    word_timings: Optional[List[Dict[str, Any]]] = None

class SpeechToText:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize enhanced speech-to-text with multiple engines and features.
        
        Args:
            config: Configuration dictionary with:
                - primary_engine: EngineType or str (default: AUTO)
                - backup_engines: List of engines to try if primary fails
                - language: Default language code (default: en-IN)
                - energy_threshold: Base energy threshold (default: 300)
                - dynamic_energy: Adjust threshold dynamically (default: True)
                - vad_mode: Voice activity detection aggressiveness (0-3)
                - enable_audio_processing: Apply audio preprocessing (default: True)
                - enable_punctuation: Add punctuation to transcript (default: True)
                - wake_word_detection: Enable wake word detection (default: False)
                - wake_words: List of wake words to detect
        """
        self.config = {
            'primary_engine': EngineType.AUTO,
            'backup_engines': [EngineType.WHISPER, EngineType.GOOGLE, EngineType.SPHINX],
            'language': 'en-IN',
            'energy_threshold': 300,
            'dynamic_energy': True,
            'vad_mode': 1,
            'enable_audio_processing': True,
            'enable_punctuation': True,
            'wake_word_detection': False,
            'wake_words': ['jarvis', 'hey jarvis'],
            'timeout': 5,
            'phrase_time_limit': 10,
            'silence_threshold': 0.5,
            'min_audio_length': 0.5,  # seconds
            'max_audio_length': 30,    # seconds
        }
        
        if config:
            self.config.update(config)
            
        # Initialize recognizers
        self.recognizer = sr.Recognizer() if sr else None
        if self.recognizer:
            self.recognizer.energy_threshold = self.config['energy_threshold']
            self.recognizer.dynamic_energy_threshold = self.config['dynamic_energy']
            self.recognizer.pause_threshold = 0.8
            self.recognizer.phrase_threshold = 0.3
            self.recognizer.non_speaking_duration = 0.5
            
        # Initialize Whisper model if available
        self.whisper_model = None
        if WHISPER_AVAILABLE and self.config['primary_engine'] in [EngineType.WHISPER, EngineType.AUTO]:
            try:
                # Load tiny model for speed, can be configured to larger models
                self.whisper_model = whisper.load_model("tiny")
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load Whisper model: {e}")
                
        # Initialize Vosk if needed
        self.vosk_model = None
        if self.config['primary_engine'] == EngineType.VOSK:
            self._init_vosk()
            
        # Audio processing settings
        self.audio_processor = AudioProcessor() if PYDUB_AVAILABLE else None
        
    def _init_vosk(self):
        """Initialize Vosk model for offline recognition"""
        try:
            from vosk import Model
            model_path = self.config.get('vosk_model_path', 'model')
            if os.path.exists(model_path):
                self.vosk_model = Model(model_path)
                logger.info("Vosk model loaded successfully")
            else:
                logger.warning(f"Vosk model not found at {model_path}")
        except ImportError:
            logger.warning("Vosk not installed")
        except Exception as e:
            logger.error(f"Failed to load Vosk model: {e}")
            
    async def listen(self, timeout: Optional[int] = None) -> str:
        """
        Simple listen method for backward compatibility.
        
        Args:
            timeout: Maximum time to wait for speech
            
        Returns:
            Transcribed text or empty string
        """
        result = await self.listen_enhanced(
            timeout=timeout or self.config['timeout']
        )
        return result.text if result else ""
        
    async def listen_enhanced(self, 
                             timeout: Optional[int] = None,
                             engine: Optional[EngineType] = None,
                             enable_preprocessing: bool = True) -> Optional[TranscriptionResult]:
        """
        Enhanced listening with human-like understanding.
        
        Args:
            timeout: Maximum time to wait for speech
            engine: Specific engine to use (overrides config)
            enable_preprocessing: Apply audio preprocessing
            
        Returns:
            TranscriptionResult object or None if no speech detected
        """
        if not self.recognizer:
            logger.error("Speech recognition not available")
            return None
            
        timeout = timeout or self.config['timeout']
        
        # Run blocking IO in executor
        return await asyncio.to_thread(
            self._listen_enhanced_sync, 
            timeout, 
            engine, 
            enable_preprocessing
        )
    
    def _listen_enhanced_sync(self, 
                             timeout: int,
                             engine: Optional[EngineType],
                             enable_preprocessing: bool) -> Optional[TranscriptionResult]:
        """Synchronous version of enhanced listening"""
        try:
            with sr.Microphone() as source:
                logger.info("Listening for speech...")
                
                # Quick ambient noise adjustment
                if self.config['dynamic_energy']:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                try:
                    # Listen with voice activity detection
                    audio = self.recognizer.listen(
                        source,
                        timeout=timeout,
                        phrase_time_limit=self.config['phrase_time_limit']
                    )
                except sr.WaitTimeoutError:
                    logger.debug("Listening timeout - no speech detected")
                    return None
                
                # Get audio data as raw bytes
                audio_data = audio.get_raw_data()
                
                # Calculate audio features
                audio_features = self._extract_audio_features(audio_data)
                
                # Validate audio quality
                if not self._validate_audio(audio_data, audio_features):
                    logger.debug("Audio validation failed")
                    return None
                
                # Preprocess audio if enabled
                if enable_preprocessing and self.audio_processor:
                    audio_data = self.audio_processor.process(audio_data)
                
                # Determine which engine to use
                engine_to_use = engine or self.config['primary_engine']
                if engine_to_use == EngineType.AUTO:
                    engine_to_use = self._select_best_engine(audio_features)
                
                # Try primary engine
                result = self._recognize_with_engine(engine_to_use, audio)
                
                # If primary fails, try backup engines
                if not result and self.config['backup_engines']:
                    for backup_engine in self.config['backup_engines']:
                        if backup_engine != engine_to_use:
                            logger.info(f"Trying backup engine: {backup_engine.value}")
                            result = self._recognize_with_engine(backup_engine, audio)
                            if result:
                                break
                
                if result:
                    # Add punctuation if enabled
                    if self.config['enable_punctuation'] and result.text:
                        result.text = self._add_punctuation(result.text)
                    
                    # Add audio features to result
                    result.audio_features = audio_features
                    result.duration = len(audio_data) / 16000  # Approximate duration
                    
                    logger.info(f"Recognized: {result.text} (confidence: {result.confidence:.2f})")
                    return result
                else:
                    logger.debug("No speech recognized")
                    return None
                    
        except sr.UnknownValueError:
            logger.debug("Could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Recognition request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Microphone error: {e}", exc_info=True)
            return None
    
    def _extract_audio_features(self, audio_data: bytes) -> AudioFeatures:
        """Extract features from audio for better understanding"""
        try:
            if audioop and np:
                # Convert bytes to numpy array
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
                
                # Calculate energy
                energy = np.sqrt(np.mean(audio_array**2))
                
                # Calculate silence ratio
                silence_threshold = energy * 0.1
                silence_samples = np.sum(np.abs(audio_array) < silence_threshold)
                silence_ratio = silence_samples / len(audio_array)
                
                # Calculate average frequency (simplified)
                fft = np.fft.rfft(audio_array)
                freqs = np.fft.rfftfreq(len(audio_array), 1/16000)
                magnitude = np.abs(fft)
                avg_frequency = np.average(freqs, weights=magnitude) if len(freqs) > 0 else 0
                
                # Determine if speech is present (simple energy-based VAD)
                has_speech = energy > self.config['energy_threshold'] and silence_ratio < 0.7
                
                # Determine noise level
                if energy < 100:
                    noise_level = "low"
                elif energy < 500:
                    noise_level = "medium"
                else:
                    noise_level = "high"
                
                # Language probabilities (simplified - would need actual language detection)
                language_probabilities = {
                    'en': 0.8 if avg_frequency < 3000 else 0.3,
                    'hi': 0.2 if avg_frequency > 2000 else 0.1,
                }
                
                return AudioFeatures(
                    energy=float(energy),
                    silence_ratio=float(silence_ratio),
                    avg_frequency=float(avg_frequency),
                    has_speech=has_speech,
                    noise_level=noise_level,
                    language_probabilities=language_probabilities
                )
        except Exception as e:
            logger.debug(f"Failed to extract audio features: {e}")
            
        # Return default features if extraction fails
        return AudioFeatures(
            energy=0.0,
            silence_ratio=1.0,
            avg_frequency=0.0,
            has_speech=False,
            noise_level="unknown",
            language_probabilities={'en': 0.5}
        )
    
    def _validate_audio(self, audio_data: bytes, features: AudioFeatures) -> bool:
        """Validate if audio is suitable for recognition"""
        # Check minimum audio length
        if len(audio_data) < self.config['min_audio_length'] * 16000 * 2:  # 16kHz, 16-bit
            logger.debug("Audio too short")
            return False
            
        # Check maximum audio length
        if len(audio_data) > self.config['max_audio_length'] * 16000 * 2:
            logger.debug("Audio too long")
            return False
            
        # Check if speech is present
        if not features.has_speech:
            logger.debug("No speech detected in audio")
            return False
            
        return True
    
    def _select_best_engine(self, features: AudioFeatures) -> EngineType:
        """Select best engine based on audio features and available engines"""
        # If high noise, use more robust engines
        if features.noise_level in ["medium", "high"]:
            if WHISPER_AVAILABLE:
                return EngineType.WHISPER
            elif self.vosk_model:
                return EngineType.VOSK
                
        # For non-English detection, use Google (better language support)
        top_lang = max(features.language_probabilities.items(), key=lambda x: x[1])
        if top_lang[0] != 'en' and top_lang[1] > 0.6:
            return EngineType.GOOGLE
            
        # Default to fastest available
        if self.vosk_model:
            return EngineType.VOSK
        elif WHISPER_AVAILABLE:
            return EngineType.WHISPER
        else:
            return EngineType.GOOGLE
    
    def _recognize_with_engine(self, engine: EngineType, audio: sr.AudioData) -> Optional[TranscriptionResult]:
        """Recognize speech using specified engine"""
        try:
            if engine == EngineType.GOOGLE:
                text = self.recognizer.recognize_google(audio, language=self.config['language'])
                confidence = 0.8  # Google doesn't provide confidence
                return TranscriptionResult(
                    text=text,
                    confidence=confidence,
                    engine_used=EngineType.GOOGLE,
                    language=self.config['language'],
                    duration=0,
                    alternatives=[text]
                )
                
            elif engine == EngineType.WHISPER and WHISPER_AVAILABLE and self.whisper_model:
                # Save audio temporarily
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    f.write(audio.get_wav_data())
                    temp_path = f.name
                
                try:
                    result = self.whisper_model.transcribe(
                        temp_path,
                        language=self.config['language'].split('-')[0],
                        task="transcribe",
                        fp16=False
                    )
                    
                    os.unlink(temp_path)
                    
                    if result and result.get('text'):
                        return TranscriptionResult(
                            text=result['text'].strip(),
                            confidence=result.get('confidence', 0.9),
                            engine_used=EngineType.WHISPER,
                            language=result.get('language', self.config['language']),
                            duration=result.get('duration', 0),
                            alternatives=[seg['text'] for seg in result.get('segments', [])],
                            word_timings=result.get('segments')
                        )
                except Exception as e:
                    logger.error(f"Whisper recognition failed: {e}")
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                        
            elif engine == EngineType.SPHINX and SPHINX_AVAILABLE:
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    return TranscriptionResult(
                        text=text,
                        confidence=0.6,  # Sphinx confidence is unreliable
                        engine_used=EngineType.SPHINX,
                        language='en-US',
                        duration=0,
                        alternatives=[text]
                    )
                except Exception as e:
                    logger.debug(f"Sphinx recognition failed: {e}")
                    
            elif engine == EngineType.VOSK and self.vosk_model:
                # Implement Vosk recognition here if needed
                pass
                
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            logger.error(f"{engine.value} request error: {e}")
        except Exception as e:
            logger.error(f"Error with {engine.value}: {e}")
            
        return None
    
    def _add_punctuation(self, text: str) -> str:
        """Add basic punctuation to transcribed text"""
        # Simple rule-based punctuation
        text = text.strip()
        
        # Capitalize first letter
        if text and not text[0].isupper():
            text = text[0].upper() + text[1:]
        
        # Add period at end if missing
        if text and text[-1] not in ['.', '!', '?']:
            # Check if it's a question
            if any(word in text.lower() for word in ['what', 'why', 'how', 'where', 'when', 'who', 'can you', 'could you']):
                text += '?'
            else:
                text += '.'
        
        return text
    
    async def detect_wake_word(self, wake_word: Optional[str] = None) -> bool:
        """
        Listen for wake word and return True if detected.
        
        Args:
            wake_word: Specific wake word to listen for (uses config if None)
            
        Returns:
            True if wake word detected, False otherwise
        """
        if not self.config['wake_word_detection']:
            return True  # Wake word detection disabled
            
        words_to_detect = [wake_word] if wake_word else self.config['wake_words']
        
        # Listen briefly for wake word
        result = await self.listen_enhanced(
            timeout=2,
            enable_preprocessing=True
        )
        
        if result and result.text:
            detected_text = result.text.lower().strip()
            for word in words_to_detect:
                if word.lower() in detected_text:
                    logger.info(f"Wake word detected: {word}")
                    return True
                    
        return False
    
    async def listen_with_context(self, context: Optional[str] = None, timeout: int = 5) -> str:
        """
        Listen with contextual understanding for better accuracy.
        
        Args:
            context: Previous context to improve recognition
            timeout: Maximum time to wait for speech
            
        Returns:
            Transcribed text
        """
        result = await self.listen_enhanced(timeout=timeout)
        
        if result and result.text:
            # Use context to improve recognition
            if context:
                # Simple context-based correction
                # Could be enhanced with NLP models
                pass
                
            return result.text
        return ""
    
    def set_language(self, language_code: str):
        """Set recognition language"""
        self.config['language'] = language_code
        logger.info(f"Language set to {language_code}")
        
    def get_available_engines(self) -> List[str]:
        """Get list of available recognition engines"""
        engines = []
        
        if self.recognizer:
            engines.append(EngineType.GOOGLE.value)
            
        if WHISPER_AVAILABLE and self.whisper_model:
            engines.append(EngineType.WHISPER.value)
            
        if SPHINX_AVAILABLE:
            engines.append(EngineType.SPHINX.value)
            
        if self.vosk_model:
            engines.append(EngineType.VOSK.value)
            
        return engines


class AudioProcessor:
    """Audio preprocessing for better recognition"""
    
    def __init__(self):
        if not PYDUB_AVAILABLE:
            logger.warning("pydub not available - audio processing disabled")
            self.enabled = False
            return
            
        self.enabled = True
        
    def process(self, audio_data: bytes) -> bytes:
        """Apply audio preprocessing"""
        if not self.enabled:
            return audio_data
            
        try:
            # Convert to AudioSegment
            audio = AudioSegment(
                data=audio_data,
                sample_width=2,  # 16-bit
                frame_rate=16000,
                channels=1
            )
            
            # Apply normalization
            audio = normalize(audio)
            
            # Apply compression for better clarity
            audio = compress_dynamic_range(audio)
            
            # Remove silence
            audio = self.strip_silence(audio)
            
            # Convert back to raw data
            return audio.raw_data
            
        except Exception as e:
            logger.error(f"Audio processing failed: {e}")
            return audio_data
    
    def strip_silence(self, audio: 'AudioSegment', silence_thresh: int = -50) -> 'AudioSegment':
        """Remove silence from beginning and end"""
        try:
            # Strip leading/trailing silence
            start_trim = self.detect_leading_silence(audio, silence_thresh)
            end_trim = self.detect_leading_silence(audio.reverse(), silence_thresh)
            
            duration = len(audio)
            trimmed = audio[start_trim:duration - end_trim]
            
            # Only return if we have at least 0.5 seconds of audio
            if len(trimmed) > 500:  # 500ms
                return trimmed
            return audio
            
        except Exception as e:
            logger.error(f"Silence stripping failed: {e}")
            return audio
    
    def detect_leading_silence(self, audio: 'AudioSegment', silence_thresh: int = -50, chunk_size: int = 10) -> int:
        """Detect leading silence in audio"""
        trim_ms = 0
        while trim_ms < len(audio):
            if audio[trim_ms:trim_ms + chunk_size].dBFS > silence_thresh:
                return trim_ms
            trim_ms += chunk_size
        return trim_ms


# Example usage and testing
async def main():
    """Example usage of enhanced speech-to-text"""
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create speech-to-text instance with configuration
    stt = SpeechToText({
        'primary_engine': EngineType.AUTO,
        'language': 'en-IN',
        'enable_audio_processing': True,
        'wake_word_detection': True,
        'wake_words': ['jarvis', 'hey jarvis'],
        'dynamic_energy': True,
        'vad_mode': 1
    })
    
    print("Enhanced Speech-to-Text initialized")
    print(f"Available engines: {stt.get_available_engines()}")
    
    # Check for wake word
    print("\nSay wake word (or press Ctrl+C to exit)...")
    if await stt.detect_wake_word():
        print("Wake word detected! Listening for command...")
        
        # Listen for actual command
        result = await stt.listen_enhanced(timeout=5)
        if result:
            print(f"\nRecognized: {result.text}")
            print(f"Confidence: {result.confidence:.2f}")
            print(f"Engine used: {result.engine_used.value}")
            print(f"Audio features: {result.audio_features}")
        else:
            print("No command detected")
    else:
        print("Wake word not detected")
    
    # Continuous listening example
    print("\nContinuous listening mode (say 'exit' to stop)...")
    while True:
        result = await stt.listen_enhanced(timeout=3)
        if result:
            print(f"You said: {result.text}")
            if "exit" in result.text.lower():
                break
        else:
            print("No speech detected")
    
    print("Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())