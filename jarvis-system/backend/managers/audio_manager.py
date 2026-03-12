"""
Enhanced Audio System for macOS
Handles high-quality text-to-speech, audio management, and voice processing
"""

import os
import time
import asyncio
import threading
import queue
import tempfile
import wave
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import subprocess
import shutil

import numpy as np
import sounddevice as sd
import soundfile as sf
import pyaudio
import pygame
from colorama import Fore, Style
from gtts import gTTS
import azure.cognitiveservices.speech as speechsdk
import edge_tts
import pyttsx3
from pydub import AudioSegment
from pydub.playback import play as pydub_play
import noisereduce as nr
import librosa
import scipy.io.wavfile as wavfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from elevenlabs import generate, play, set_api_key, Voice
except (ImportError, Exception):
    logger.warning("elevenlabs API is incompatible or not installed. Using mock functions.")
    def generate(*args, **kwargs): return None
    def play(*args, **kwargs): pass
    def set_api_key(*args, **kwargs): pass
    class Voice: pass

JARVIS_NAME = "Jarvis"


class TTSProvider(Enum):
    """Supported TTS providers"""
    EDGE = "edge"
    AZURE = "azure"
    ELEVENLABS = "elevenlabs"
    PYTTTSX3 = "pyttsx3"
    GTTS = "gtts"
    SYSTEM = "system"
    GOOGLE_CLOUD = "google_cloud"
    AMAZON_POLLY = "amazon_polly"
    IBM_WATSON = "ibm_watson"


class VoiceGender(Enum):
    """Voice gender options"""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class VoiceStyle(Enum):
    """Voice style/emotion options"""
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    EXCITED = "excited"
    SYMPATHETIC = "sympathetic"
    URGENT = "urgent"
    WHISPER = "whisper"
    SAD = "sad"
    HAPPY = "happy"
    ANGRY = "angry"
    CUSTOM = "custom"


class AudioEffect(Enum):
    """Audio effects for processing"""
    NORMALIZE = "normalize"
    COMPRESS = "compress"
    EQ = "eq"
    REVERB = "reverb"
    ECHO = "echo"
    PITCH_SHIFT = "pitch_shift"
    TIME_STRETCH = "time_stretch"
    NOISE_REDUCE = "noise_reduce"
    ROBOTIC = "robotic"
    DEEP = "deep"
    CHIPMUNK = "chipmunk"
    CUSTOM = "custom"


class SpeechEvent(Enum):
    """Speech synthesis events"""
    START = "start"
    WORD = "word"
    SENTENCE = "sentence"
    END = "end"
    ERROR = "error"
    CANCEL = "cancel"
    PAUSE = "pause"
    RESUME = "resume"


@dataclass
class VoiceConfig:
    """Voice configuration settings"""
    provider: TTSProvider = TTSProvider.EDGE
    voice_name: str = "en-US-ChristopherNeural"
    language: str = "en-US"
    gender: VoiceGender = VoiceGender.MALE
    style: VoiceStyle = VoiceStyle.NEUTRAL
    rate: int = 175  # words per minute
    pitch: float = 1.0  # 0.5-2.0
    volume: float = 0.9  # 0.0-1.0
    emphasis: str = "normal"
    effects: List[AudioEffect] = field(default_factory=list)
    custom_voice_path: Optional[Path] = None


@dataclass
class AudioDevice:
    """Audio device information"""
    id: int
    name: str
    max_input_channels: int
    max_output_channels: int
    default_sample_rate: float
    is_default_input: bool = False
    is_default_output: bool = False
    host_api: str = ""


@dataclass
class SpeechSegment:
    """Speech segment for queued playback"""
    text: str
    config: VoiceConfig
    priority: int = 0
    callback: Optional[Callable] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def __lt__(self, other):
        if not isinstance(other, SpeechSegment):
            return NotImplemented
        # Lower priority number = higher priority first
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.timestamp < other.timestamp


class SpeechSynthesisError(Exception):
    """Custom exception for speech synthesis errors"""
    pass


class AudioSystem:
    """
    Enhanced Audio System with comprehensive features:
    - Multiple TTS providers (Edge, Azure, ElevenLabs, etc.)
    - Voice customization and effects
    - Audio queue management
    - Speech rate and volume control
    - Audio device management
    - Speech events and callbacks
    - Audio file I/O (save/load)
    - Background noise reduction
    - Real-time audio effects
    - Cross-platform support
    """
    
    def __init__(self, websocket_manager=None, loop=None, config_path: Optional[Path] = None):
        """
        Initialize the Audio System
        
        Args:
            websocket_manager: WebSocket manager for frontend communication
            loop: Async event loop
            config_path: Path to configuration file
        """
        self.websocket_manager = websocket_manager
        self.loop = loop
        self.config_path = config_path or Path.home() / ".config" / "audio_system.json"
        
        # Core components
        self.engines: Dict[TTSProvider, Any] = {}
        self.current_config = VoiceConfig()
        self.audio_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.is_speaking = False
        self.is_paused = False
        self.current_thread: Optional[threading.Thread] = None
        self.queue_thread: Optional[threading.Thread] = None
        
        # Audio devices
        self.input_devices: List[AudioDevice] = []
        self.output_devices: List[AudioDevice] = []
        self.default_input: Optional[AudioDevice] = None
        self.default_output: Optional[AudioDevice] = None
        
        # Audio processing
        self.audio_cache_dir = Path.home() / ".cache" / "jarvis_audio"
        self.audio_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Event callbacks
        self.event_callbacks: Dict[SpeechEvent, List[Callable]] = {
            event: [] for event in SpeechEvent
        }
        
        # Configuration
        self.volume_level = 80
        self.speech_rate = 175
        self.max_queue_size = 100
        self.cache_enabled = True
        self.debug_mode = False
        
        # Initialize
        self._load_config()
        self._initialize_audio_devices()
        self._initialize_engines()
        self._start_queue_processor()
        
        print(f"{Fore.GREEN}🔊 Audio System initialized successfully")
    
    def _load_config(self):
        """Load configuration from file"""
        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    
                    self.volume_level = config.get('volume_level', 80)
                    self.speech_rate = config.get('speech_rate', 175)
                    self.max_queue_size = config.get('max_queue_size', 100)
                    self.cache_enabled = config.get('cache_enabled', True)
                    
                    # Load voice config
                    voice_config = config.get('voice_config', {})
                    self.current_config.voice_name = voice_config.get('voice_name', 'en-US-ChristopherNeural')
                    self.current_config.rate = voice_config.get('rate', 175)
                    self.current_config.volume = voice_config.get('volume', 0.9)
                    
                    logger.info(f"Loaded config from {self.config_path}")
            except Exception as e:
                logger.error(f"Error loading config: {e}")
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            config = {
                'volume_level': self.volume_level,
                'speech_rate': self.speech_rate,
                'max_queue_size': self.max_queue_size,
                'cache_enabled': self.cache_enabled,
                'voice_config': {
                    'voice_name': self.current_config.voice_name,
                    'rate': self.current_config.rate,
                    'volume': self.current_config.volume,
                    'provider': self.current_config.provider.value,
                    'language': self.current_config.language
                }
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Saved config to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def _initialize_audio_devices(self):
        """Initialize and detect audio devices"""
        try:
            # Get all audio devices
            devices = sd.query_devices()
            
            for i, device in enumerate(devices):
                audio_device = AudioDevice(
                    id=i,
                    name=device['name'],
                    max_input_channels=device['max_input_channels'],
                    max_output_channels=device['max_output_channels'],
                    default_sample_rate=device['default_samplerate'],
                    host_api=device['hostapi']
                )
                
                if device['max_output_channels'] > 0:
                    self.output_devices.append(audio_device)
                    if device.get('default', False):
                        self.default_output = audio_device
                        audio_device.is_default_output = True
                
                if device['max_input_channels'] > 0:
                    self.input_devices.append(audio_device)
                    if device.get('default', False):
                        self.default_input = audio_device
                        audio_device.is_default_input = True
            
            logger.info(f"Found {len(self.output_devices)} output devices, {len(self.input_devices)} input devices")
            
        except Exception as e:
            logger.error(f"Error initializing audio devices: {e}")
    
    def _initialize_engines(self):
        """Initialize TTS engines"""
        # Edge TTS (Default, highest quality)
        try:
            # Edge TTS doesn't need initialization, we'll create instances on demand
            self.engines[TTSProvider.EDGE] = {"available": True, "engine": None}
            logger.info("✅ Edge TTS available")
        except Exception as e:
            logger.warning(f"❌ Edge TTS not available: {e}")
        
        # pyttsx3 (Fallback)
        try:
            engine = pyttsx3.init()
            self.engines[TTSProvider.PYTTTSX3] = {"available": True, "engine": engine}
            logger.info("✅ pyttsx3 available")
        except Exception as e:
            logger.warning(f"❌ pyttsx3 not available: {e}")
        
        # gTTS (Google TTS)
        try:
            self.engines[TTSProvider.GTTS] = {"available": True, "engine": None}
            logger.info("✅ gTTS available")
        except Exception as e:
            logger.warning(f"❌ gTTS not available: {e}")
        
        # Try to load premium engines if credentials exist
        self._initialize_premium_engines()
    
    def _initialize_premium_engines(self):
        """Initialize premium TTS engines if credentials available"""
        # Azure Cognitive Services
        azure_key = os.environ.get('AZURE_SPEECH_KEY')
        azure_region = os.environ.get('AZURE_SPEECH_REGION', 'eastus')
        
        if azure_key:
            try:
                speech_config = speechsdk.SpeechConfig(subscription=azure_key, region=azure_region)
                self.engines[TTSProvider.AZURE] = {"available": True, "engine": speech_config}
                logger.info("✅ Azure TTS available")
            except Exception as e:
                logger.warning(f"❌ Azure TTS not available: {e}")
        
        # ElevenLabs
        elevenlabs_key = os.environ.get('ELEVENLABS_API_KEY')
        if elevenlabs_key:
            try:
                set_api_key(elevenlabs_key)
                self.engines[TTSProvider.ELEVENLABS] = {"available": True, "engine": None}
                logger.info("✅ ElevenLabs available")
            except Exception as e:
                logger.warning(f"❌ ElevenLabs not available: {e}")
    
    def _start_queue_processor(self):
        """Start the audio queue processing thread"""
        def process_queue():
            while True:
                try:
                    priority, segment = self.audio_queue.get()
                    
                    if segment is None:  # Poison pill
                        self.audio_queue.task_done()
                        break
                    
                    try:
                        self.is_speaking = True
                        
                        # Process speech segment
                        self._speak_sync(segment.text, segment.config, segment.callback)
                        
                    finally:
                        self.is_speaking = False
                        self.audio_queue.task_done()
                        
                except queue.Empty:
                    time.sleep(0.1)
                except Exception as e:
                    logger.error(f"Queue processor error: {e}")
        
        self.queue_thread = threading.Thread(target=process_queue, daemon=True)
        self.queue_thread.start()
    
    def speak(self, text: str, 
             config: Optional[Union[VoiceConfig, Dict]] = None,
             priority: int = 0,
             on_start: Optional[Callable] = None,
             on_word: Optional[Callable] = None,
             on_end: Optional[Callable] = None,
             wait: bool = False) -> bool:
        """
        Speak text with advanced options
        
        Args:
            text: Text to speak
            config: Voice configuration
            priority: Queue priority (lower = higher priority)
            on_start: Callback when speech starts
            on_word: Callback per word
            on_end: Callback when speech ends
            wait: Wait for speech to complete
            
        Returns:
            Success status
        """
        try:
            if not text or not text.strip():
                return False
            
            # Prepare configuration
            if config is None:
                voice_config = self.current_config
            elif isinstance(config, dict):
                voice_config = VoiceConfig(**config)
            else:
                voice_config = config
            
            # Set up callbacks
            def combined_on_start():
                self._trigger_event(SpeechEvent.START, text)
                if on_start:
                    on_start()
            
            def combined_on_end():
                self._trigger_event(SpeechEvent.END, text)
                if on_end:
                    on_end()
            
            # Create speech segment
            segment = SpeechSegment(
                text=text,
                config=voice_config,
                priority=priority,
                callback=combined_on_end
            )
            
            # Add to queue
            self.audio_queue.put((priority, segment))
            
            # Send to frontend
            config_dict = {}
            for k, v in voice_config.__dict__.items():
                if isinstance(v, Enum):
                    config_dict[k] = v.value
                else:
                    config_dict[k] = v

            self._broadcast_to_frontend({
                "type": "speech",
                "text": text,
                "config": config_dict,
                "timestamp": datetime.now().isoformat()
            })
            
            # Print to console
            self._print_speech(text, voice_config)
            
            # Trigger start event
            combined_on_start()
            
            # Wait if requested
            if wait:
                while self.is_speaking:
                    time.sleep(0.1)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in speak: {e}")
            self._trigger_event(SpeechEvent.ERROR, str(e))
            return False
    
    def _speak_sync(self, text: str, config: VoiceConfig, callback: Optional[Callable] = None):
        """
        Synchronous speech synthesis
        
        Args:
            text: Text to speak
            config: Voice configuration
            callback: Completion callback
        """
        try:
            provider = config.provider
            
            # Try specified provider first
            if provider in self.engines and self.engines[provider]["available"]:
                if self._synthesize_with_provider(provider, text, config):
                    if callback:
                        callback()
                    return
            
            # Fallback through providers
            fallback_providers = [
                TTSProvider.EDGE,
                TTSProvider.AZURE,
                TTSProvider.ELEVENLABS,
                TTSProvider.GTTS,
                TTSProvider.PYTTTSX3
            ]
            
            for fallback in fallback_providers:
                # Check if speech was cancelled (is_speaking is False when stop_speech is called)
                if not self.is_speaking:
                    logger.info("Speech cancelled, aborting fallback chain.")
                    return
                
                if fallback in self.engines and self.engines[fallback]["available"]:
                    logger.info(f"Falling back to {fallback.value}")
                    if self._synthesize_with_provider(fallback, text, config):
                        if callback:
                            callback()
                        return
            
            # Ultimate fallback: system beep
            self.play_beep("error")
            logger.error("No TTS provider available")
            
        except Exception as e:
            logger.error(f"Speech synthesis error: {e}")
        finally:
            if callback:
                callback()
    
    def _synthesize_with_provider(self, provider: TTSProvider, text: str, config: VoiceConfig) -> bool:
        """Synthesize speech with specific provider"""
        try:
            if provider == TTSProvider.EDGE:
                return self._synthesize_edge(text, config)
            elif provider == TTSProvider.PYTTTSX3:
                return self._synthesize_pyttsx3(text, config)
            elif provider == TTSProvider.GTTS:
                return self._synthesize_gtts(text, config)
            elif provider == TTSProvider.AZURE:
                return self._synthesize_azure(text, config)
            elif provider == TTSProvider.ELEVENLABS:
                return self._synthesize_elevenlabs(text, config)
            else:
                return False
        except Exception as e:
            logger.error(f"Provider {provider.value} synthesis error: {e}")
            return False
    
    def _synthesize_edge(self, text: str, config: VoiceConfig) -> bool:
        """Synthesize with Edge TTS"""
        try:
            # Create temporary file
            temp_file = self.audio_cache_dir / f"edge_{int(time.time())}.mp3"
            
            # Run async synthesis in sync context
            async def synthesize():
                communicate = edge_tts.Communicate(text, config.voice_name)
                await communicate.save(str(temp_file))
            
            asyncio.run(synthesize())
            
            # Fast exit if speech was cancelled
            if not self.is_speaking:
                return True
                
            # Play audio
            self._play_audio_file(temp_file)
            
            # Cleanup
            if not self.cache_enabled:
                temp_file.unlink(missing_ok=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Edge TTS error: {e}")
            return False
    
    def _synthesize_pyttsx3(self, text: str, config: VoiceConfig) -> bool:
        """Synthesize with pyttsx3"""
        try:
            engine = self.engines[TTSProvider.PYTTTSX3]["engine"]
            
            # Configure voice
            engine.setProperty('rate', config.rate)
            engine.setProperty('volume', config.volume)
            
            # Select voice by gender
            voices = engine.getProperty('voices')
            for voice in voices:
                if config.gender == VoiceGender.MALE and 'male' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
                elif config.gender == VoiceGender.FEMALE and 'female' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
            
            # Speak
            engine.say(text)
            engine.runAndWait()
            
            return True
            
        except Exception as e:
            logger.error(f"pyttsx3 error: {e}")
            return False
    
    def _synthesize_gtts(self, text: str, config: VoiceConfig) -> bool:
        """Synthesize with Google TTS"""
        try:
            # Generate speech
            tts = gTTS(text=text, lang=config.language[:2], slow=False)
            
            # Save to temp file
            temp_file = self.audio_cache_dir / f"gtts_{int(time.time())}.mp3"
            tts.save(str(temp_file))
            
            # Play audio
            self._play_audio_file(temp_file)
            
            # Cleanup
            if not self.cache_enabled:
                temp_file.unlink(missing_ok=True)
            
            return True
            
        except Exception as e:
            logger.error(f"gTTS error: {e}")
            return False
    
    def _synthesize_azure(self, text: str, config: VoiceConfig) -> bool:
        """Synthesize with Azure Cognitive Services"""
        try:
            speech_config = self.engines[TTSProvider.AZURE]["engine"]
            
            # Configure voice
            speech_config.speech_synthesis_voice_name = config.voice_name
            
            # Create synthesizer
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
            
            # Synthesize
            result = synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # Play audio data
                audio_data = result.audio_data
                self._play_audio_data(audio_data)
                return True
            else:
                logger.error(f"Azure synthesis failed: {result.reason}")
                return False
                
        except Exception as e:
            logger.error(f"Azure TTS error: {e}")
            return False
    
    def _synthesize_elevenlabs(self, text: str, config: VoiceConfig) -> bool:
        """Synthesize with ElevenLabs"""
        try:
            # Map to ElevenLabs voices
            voice_map = {
                "en-US-ChristopherNeural": "Adam",
                "en-US-JennyNeural": "Bella",
                "en-GB-RyanNeural": "Elliott"
            }
            
            voice_name = voice_map.get(config.voice_name, "Adam")
            
            # Generate audio
            audio = generate(
                text=text,
                voice=voice_name,
                model="eleven_monolingual_v1"
            )
            
            # Play audio
            play(audio)
            
            return True
            
        except Exception as e:
            logger.error(f"ElevenLabs error: {e}")
            return False
    
    def _play_audio_file(self, file_path: Path):
        """Play audio file"""
        import platform
        
        # Fast exit if speech was cancelled before playback
        if not self.is_speaking:
            return

        try:
            # Bypass pygame on macOS to prevent SDL initialization conflicts with OpenCV
            if platform.system() == "Darwin":
                subprocess.run(['afplay', str(file_path)], check=False)
                return

            # Use pygame for playback on other systems
            pygame.mixer.init()
            pygame.mixer.music.load(str(file_path))
            pygame.mixer.music.play()
            
            # Wait for playback to complete
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            pygame.mixer.quit()
            
        except Exception as e:
            logger.error(f"Audio playback error: {e}")
            
            # Fallback to system command
            try:
                if file_path.suffix == '.mp3':
                    subprocess.run(['afplay', str(file_path)], check=False)
                else:
                    subprocess.run(['play', str(file_path)], check=False)
            except:
                pass
    
    def _play_audio_data(self, audio_data: bytes):
        """Play raw audio data"""
        try:
            # Save to temp file
            temp_file = self.audio_cache_dir / f"audio_{int(time.time())}.wav"
            
            with open(temp_file, 'wb') as f:
                f.write(audio_data)
            
            # Play
            self._play_audio_file(temp_file)
            
            # Cleanup
            temp_file.unlink(missing_ok=True)
            
        except Exception as e:
            logger.error(f"Audio data playback error: {e}")
    
    def _print_speech(self, text: str, config: VoiceConfig):
        """Print speech to console"""
        # Truncate long text
        display_text = text[:100] + "..." if len(text) > 100 else text
        
        # Add voice/style indicators
        indicators = []
        if config.provider != TTSProvider.EDGE:
            indicators.append(config.provider.value)
        if config.style != VoiceStyle.NEUTRAL:
            indicators.append(config.style.value)
        
        indicator_str = f"[{', '.join(indicators)}] " if indicators else ""
        
        print(f"{Fore.GREEN}{JARVIS_NAME}: {indicator_str}{display_text}{Style.RESET_ALL}")
    
    def _broadcast_to_frontend(self, data: Dict):
        """Broadcast data to frontend via WebSocket"""
        if self.websocket_manager and self.loop:
            try:
                asyncio.run_coroutine_threadsafe(
                    self.websocket_manager.broadcast(data),
                    self.loop
                )
            except Exception as e:
                logger.error(f"WebSocket broadcast error: {e}")
    
    def _trigger_event(self, event: SpeechEvent, data: Any = None):
        """Trigger event callbacks"""
        for callback in self.event_callbacks.get(event, []):
            try:
                if data:
                    callback(data)
                else:
                    callback()
            except Exception as e:
                logger.error(f"Event callback error: {e}")
    
    def register_event_callback(self, event: SpeechEvent, callback: Callable):
        """Register callback for speech event"""
        if event not in self.event_callbacks:
            self.event_callbacks[event] = []
        self.event_callbacks[event].append(callback)
    
    def play_beep(self, beep_type: str = "response", frequency: int = 440, duration: float = 0.1):
        """Play beep sound with various types"""
        try:
            beep_configs: Dict[str, Dict[str, Any]] = {
                "response": {"frequency": 523, "duration": 0.1},  # C5
                "listening": {"frequency": 659, "duration": 0.15},  # E5
                "processing": {"frequency": 392, "duration": 0.2},  # G4
                "error": {"frequency": 220, "duration": 0.3},  # A3
                "success": {"frequency": 784, "duration": 0.2},  # G5
                "notification": {"frequency": 880, "duration": 0.1},  # A5
                "warning": {"frequency": 440, "duration": 0.3, "pattern": [0.1, 0.1, 0.1]},  # A4 pattern
                "startup": {"frequency": 523, "duration": 0.2, "pattern": [0.1, 0.1, 0.1, 0.1]},
                "shutdown": {"frequency": 392, "duration": 0.2, "pattern": [0.1, 0.1]}
            }
            
            config = beep_configs.get(beep_type, beep_configs["response"])
            
            # Generate beep audio
            sample_rate = 44100
            t = np.linspace(0, config["duration"], int(sample_rate * config["duration"]))
            
            if "pattern" in config:
                # Create patterned beep
                audio = np.array([])
                for i, pause in enumerate(config["pattern"]):
                    if i % 2 == 0:
                        beep = 0.3 * np.sin(2 * np.pi * config["frequency"] * t[:int(sample_rate * pause)])
                        audio = np.concatenate([audio, beep])
                    else:
                        audio = np.concatenate([audio, np.zeros(int(sample_rate * pause))])
            else:
                # Simple beep
                audio = 0.3 * np.sin(2 * np.pi * config["frequency"] * t)
            
            # Play beep
            sd.play(audio, sample_rate)
            sd.wait()
            
        except Exception as e:
            # Fallback to system beep
            print('\a', end='', flush=True)
            logger.error(f"Beep error: {e}")
    
    def set_volume(self, level: int) -> int:
        """
        Set speech volume
        
        Args:
            level: Volume level (0-100)
            
        Returns:
            New volume level
        """
        self.volume_level = max(0, min(100, level))
        self.current_config.volume = self.volume_level / 100.0
        self._save_config()
        
        self.speak(f"Volume set to {self.volume_level} percent")
        return self.volume_level
    
    def get_volume(self) -> float:
        """Get current volume as a float between 0.0 and 1.0"""
        return self.volume_level / 100.0
    
    def set_rate(self, rate: int) -> int:
        """
        Set speech rate
        
        Args:
            rate: Words per minute (100-300)
            
        Returns:
            New rate
        """
        self.speech_rate = max(100, min(300, rate))
        self.current_config.rate = self.speech_rate
        self._save_config()
        
        self.speak(f"Speech rate set to {self.speech_rate} words per minute")
        return self.speech_rate
    
    def set_voice(self, voice_name: str, provider: Optional[TTSProvider] = None):
        """
        Set voice by name
        
        Args:
            voice_name: Voice identifier
            provider: TTS provider
        """
        if provider:
            self.current_config.provider = provider
        self.current_config.voice_name = voice_name
        self._save_config()
        
        self.speak(f"Voice changed to {voice_name}")
    
    def set_voice_gender(self, gender: Union[str, VoiceGender]):
        """Set voice by gender"""
        if isinstance(gender, str):
            gender = VoiceGender(gender.lower())
        
        self.current_config.gender = gender
        self._save_config()
        
        self.speak(f"Voice gender set to {gender.value}")
    
    def set_voice_style(self, style: Union[str, VoiceStyle]):
        """Set voice style/emotion"""
        if isinstance(style, str):
            style = VoiceStyle(style.lower())
        
        self.current_config.style = style
        self._save_config()
        
        self.speak(f"Voice style set to {style.value}", config=VoiceConfig(style=style))
    
    def pause_speech(self):
        """Pause current speech"""
        self.is_paused = True
        self._trigger_event(SpeechEvent.PAUSE)
        
        try:
            pygame.mixer.music.pause()
        except:
            pass
    
    def resume_speech(self):
        """Resume paused speech"""
        self.is_paused = False
        self._trigger_event(SpeechEvent.RESUME)
        
        try:
            pygame.mixer.music.unpause()
        except:
            pass
    
    def stop_speech(self):
        """Stop current speech and clear queue"""
        # Clear queue
        with self.audio_queue.mutex:
            self.audio_queue.queue.clear()
        
        # Stop current playback
        try:
            import platform
            if platform.system() == "Darwin":
                import subprocess
                subprocess.run(['pkill', '-f', 'afplay'], capture_output=True)
            pygame.mixer.music.stop()
        except:
            pass
        
        self.is_speaking = False
        self._trigger_event(SpeechEvent.CANCEL)
    
    def get_available_voices(self, provider: Optional[TTSProvider] = None) -> List[Dict]:
        """Get list of available voices"""
        voices = []
        
        try:
            # Edge TTS voices
            if provider is None or provider == TTSProvider.EDGE:
                async def get_edge_voices():
                    voice_list = await edge_tts.list_voices()
                    return [
                        {
                            "name": v['ShortName'],
                            "locale": v['Locale'],
                            "gender": v['Gender'],
                            "provider": "edge"
                        }
                        for v in voice_list
                    ]
                
                edge_voices = asyncio.run(get_edge_voices())
                voices.extend(edge_voices)
            
            # pyttsx3 voices
            if provider is None or provider == TTSProvider.PYTTTSX3:
                if TTSProvider.PYTTTSX3 in self.engines:
                    engine = self.engines[TTSProvider.PYTTTSX3]["engine"]
                    for v in engine.getProperty('voices'):
                        voices.append({
                            "name": v.name,
                            "id": v.id,
                            "provider": "pyttsx3"
                        })
            
            # Azure voices (predefined list)
            if provider is None or provider == TTSProvider.AZURE:
                azure_voices = [
                    {"name": "en-US-JennyNeural", "locale": "en-US", "gender": "Female"},
                    {"name": "en-US-GuyNeural", "locale": "en-US", "gender": "Male"},
                    {"name": "en-GB-RyanNeural", "locale": "en-GB", "gender": "Male"},
                    {"name": "en-GB-LibbyNeural", "locale": "en-GB", "gender": "Female"}
                ]
                for v in azure_voices:
                    v["provider"] = "azure"
                voices.extend(azure_voices)
            
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
        
        return voices
    
    def get_audio_devices(self, device_type: str = "all") -> List[Dict]:
        """Get available audio devices"""
        devices = []
        
        if device_type in ["all", "output"]:
            for dev in self.output_devices:
                devices.append({
                    "id": dev.id,
                    "name": dev.name,
                    "type": "output",
                    "default": dev.is_default_output,
                    "channels": dev.max_output_channels
                })
        
        if device_type in ["all", "input"]:
            for dev in self.input_devices:
                devices.append({
                    "id": dev.id,
                    "name": dev.name,
                    "type": "input",
                    "default": dev.is_default_input,
                    "channels": dev.max_input_channels
                })
        
        return devices
    
    def set_output_device(self, device_id: int) -> bool:
        """Set default output device"""
        try:
            device = next((d for d in self.output_devices if d.id == device_id), None)
            if device:
                sd.default.device[1] = device_id
                self.default_output = device
                self.speak(f"Output device set to {device.name}")
                return True
        except Exception as e:
            logger.error(f"Error setting output device: {e}")
        return False
    
    def save_audio(self, text: str, file_path: Union[str, Path], 
                  config: Optional[VoiceConfig] = None) -> bool:
        """
        Save speech to audio file
        
        Args:
            text: Text to synthesize
            file_path: Output file path
            config: Voice configuration
            
        Returns:
            Success status
        """
        try:
            file_path = Path(file_path)
            config = config or self.current_config
            
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use appropriate provider for saving
            if config.provider == TTSProvider.EDGE:
                async def save_edge():
                    communicate = edge_tts.Communicate(text, config.voice_name)
                    await communicate.save(str(file_path))
                
                asyncio.run(save_edge())
                return True
            
            elif config.provider == TTSProvider.GTTS:
                tts = gTTS(text=text, lang=config.language[:2])
                tts.save(str(file_path))
                return True
            
            else:
                # For other providers, synthesize and save
                temp_file = self.audio_cache_dir / "temp_audio.mp3"
                
                if self._synthesize_with_provider(config.provider, text, config):
                    if temp_file.exists():
                        shutil.copy2(temp_file, file_path)
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error saving audio: {e}")
            return False
    
    def apply_audio_effect(self, audio_file: Path, effect: AudioEffect, 
                          output_file: Optional[Path] = None) -> Optional[Path]:
        """
        Apply audio effect to file
        
        Args:
            audio_file: Input audio file
            effect: Effect to apply
            output_file: Output file path
            
        Returns:
            Path to processed file or None
        """
        try:
            output_file = output_file or audio_file.parent / f"processed_{audio_file.name}"
            
            # Load audio
            y, sr = librosa.load(str(audio_file))
            
            if effect == AudioEffect.NORMALIZE:
                # Normalize amplitude
                y = y / np.max(np.abs(y))
            
            elif effect == AudioEffect.NOISE_REDUCE:
                # Reduce noise
                y = nr.reduce_noise(y=y, sr=sr)
            
            elif effect == AudioEffect.PITCH_SHIFT:
                # Shift pitch up
                y = librosa.effects.pitch_shift(y, sr=sr, n_steps=2)
            
            elif effect == AudioEffect.TIME_STRETCH:
                # Stretch time
                y = librosa.effects.time_stretch(y, rate=1.2)
            
            elif effect == AudioEffect.ROBOTIC:
                # Apply robotic effect
                y = np.sign(y) * np.sqrt(np.abs(y))
            
            elif effect == AudioEffect.DEEP:
                # Deepen voice
                y = librosa.effects.pitch_shift(y, sr=sr, n_steps=-3)
            
            # Save processed audio
            sf.write(str(output_file), y, sr)
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error applying audio effect: {e}")
            return None
    
    def test_speakers(self, test_all: bool = False) -> bool:
        """
        Test speaker system
        
        Args:
            test_all: Test all speakers or just default
            
        Returns:
            Success status
        """
        print(f"\n{Fore.CYAN}🔊 Testing Audio System...{Style.RESET_ALL}")
        
        # Test beeps
        for beep_type in ["response", "listening", "processing", "success", "error"]:
            print(f"{Fore.CYAN}Testing {beep_type} beep...{Style.RESET_ALL}")
            self.play_beep(beep_type)
            time.sleep(0.3)
        
        # Test speech
        test_phrases = [
            "Audio system test one. This is a standard voice test.",
            "Audio system test two. Testing with different voice settings.",
            "Audio system test three. All systems are functioning properly.",
            "Audio system verification complete. Jarvis is ready to assist you."
        ]
        
        for i, phrase in enumerate(test_phrases, 1):
            print(f"{Fore.CYAN}Test {i}: {phrase}{Style.RESET_ALL}")
            
            # Vary voice for tests
            if i == 2:
                self.set_voice_gender(VoiceGender.FEMALE)
            elif i == 3:
                self.set_voice_style(VoiceStyle.PROFESSIONAL)
            
            self.speak(phrase, wait=True)
            time.sleep(0.5)
        
        # Reset to default
        self.current_config = VoiceConfig()
        
        print(f"{Fore.GREEN}✅ Audio system test complete{Style.RESET_ALL}")
        return True
    
    def adjust_system_volume(self, direction: str = "up", amount: int = 10):
        """
        Adjust macOS system volume
        
        Args:
            direction: "up", "down", "mute", "unmute", "max"
            amount: Amount to change by
        """
        try:
            if direction == "up":
                os.system(f"osascript -e 'set volume output volume (output volume of (get volume settings) + {amount})'")
                new_volume = self.get_system_volume()
                self.speak(f"System volume increased to {new_volume} percent")
            
            elif direction == "down":
                os.system(f"osascript -e 'set volume output volume (output volume of (get volume settings) - {amount})'")
                new_volume = self.get_system_volume()
                self.speak(f"System volume decreased to {new_volume} percent")
            
            elif direction == "mute":
                os.system("osascript -e 'set volume output muted true'")
                self.speak("System audio muted")
            
            elif direction == "unmute":
                os.system("osascript -e 'set volume output muted false'")
                self.speak("System audio unmuted")
            
            elif direction == "max":
                os.system("osascript -e 'set volume output volume 100'")
                self.speak("System volume set to maximum")
                
            elif direction == "set":
                os.system(f"osascript -e 'set volume output volume {amount}'")
                new_volume = self.get_system_volume()
            
        except Exception as e:
            logger.error(f"System volume adjustment failed: {e}")
            self.speak("Sorry, I couldn't adjust the system volume")
    
    def get_system_volume(self) -> int:
        """Get current macOS system volume"""
        try:
            result = subprocess.run(
                ["osascript", "-e", "output volume of (get volume settings)"],
                capture_output=True,
                text=True
            )
            return int(result.stdout.strip())
        except:
            return 50
    
    def get_status(self) -> Dict[str, Any]:
        """Get current audio system status"""
        return {
            "is_speaking": self.is_speaking,
            "is_paused": self.is_paused,
            "queue_size": self.audio_queue.qsize(),
            "current_config": {
                "provider": self.current_config.provider.value,
                "voice": self.current_config.voice_name,
                "rate": self.current_config.rate,
                "volume": self.current_config.volume,
                "style": self.current_config.style.value
            },
            "volume_level": self.volume_level,
            "speech_rate": self.speech_rate,
            "available_providers": [
                p.value for p, e in self.engines.items() if e["available"]
            ],
            "default_output": self.default_output.name if self.default_output else None,
            "cache_enabled": self.cache_enabled,
            "system_volume": self.get_system_volume()
        }
    
    def cleanup(self):
        """Clean up resources"""
        # Stop queue processor
        self.audio_queue.put((0, None))
        if self.queue_thread:
            self.queue_thread.join(timeout=5)
        
        # Stop any playing audio
        self.stop_speech()
        
        # Clean up temp files
        if not self.cache_enabled:
            shutil.rmtree(self.audio_cache_dir, ignore_errors=True)
        
        logger.info("Audio system cleaned up")


# CLI interface for testing
if __name__ == "__main__":
    import sys
    
    audio = AudioSystem()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "speak" and len(sys.argv) > 2:
            text = " ".join(sys.argv[2:])
            audio.speak(text, wait=True)
        
        elif command == "test":
            audio.test_speakers()
        
        elif command == "volume" and len(sys.argv) > 2:
            level = int(sys.argv[2])
            audio.set_volume(level)
        
        elif command == "rate" and len(sys.argv) > 2:
            rate = int(sys.argv[2])
            audio.set_rate(rate)
        
        elif command == "voices":
            voices = audio.get_available_voices()
            for v in voices[:10]:  # Show first 10
                print(f"  {v.get('name', v.get('id'))} - {v.get('locale', '')}")
        
        elif command == "devices":
            devices = audio.get_audio_devices()
            for d in devices:
                print(f"  {d['id']}: {d['name']} ({d['type']})")
        
        elif command == "status":
            status = audio.get_status()
            for k, v in status.items():
                print(f"  {k}: {v}")
        
        else:
            print("Usage: audio_system.py [speak|test|volume|rate|voices|devices|status] [args]")
    else:
        # Demo mode
        print("Audio System Demo")
        print("-" * 50)
        
        # Get status
        status = audio.get_status()
        print(f"\nStatus: Speaking={status['is_speaking']}, Queue={status['queue_size']}")
        
        # Test beeps
        print("\nTesting beeps...")
        audio.play_beep("response")
        time.sleep(0.3)
        audio.play_beep("listening")
        time.sleep(0.3)
        audio.play_beep("success")
        
        # Test speech
        print("\nTesting speech...")
        audio.speak("Hello, I am Jarvis, your AI assistant.", wait=True)
        audio.speak("I can speak with different voices and styles.", 
                   config=VoiceConfig(style=VoiceStyle.PROFESSIONAL), wait=True)
        audio.speak("The audio system is fully operational.", 
                   config=VoiceConfig(gender=VoiceGender.FEMALE), wait=True)
        
        # Test queue
        print("\nTesting queue...")
        audio.speak("This is a high priority message.", priority=0)
        audio.speak("This is a low priority message.", priority=10)
        audio.speak("This is a medium priority message.", priority=5)
        
        # Wait for queue
        time.sleep(5)
        
        # Show final status
        print("\nFinal Status:")
        status = audio.get_status()
        print(f"  Queue size: {status['queue_size']}")
        print(f"  Current voice: {status['current_config']['voice']}")