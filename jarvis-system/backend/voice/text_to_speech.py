import logging
import asyncio
import os
import tempfile
import uuid
from typing import Optional, Dict, Any, List, Union
from enum import Enum
from dataclasses import dataclass
import hashlib
import json

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    pyttsx3 = None

# Advanced TTS libraries
try:
    import elevenlabs
    from elevenlabs import generate, play, save, set_api_key, Voice, VoiceSettings
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False

try:
    import edge_tts
    from edge_tts import Communicate, VoicesManager
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

try:
    import gtts
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    from pydub import AudioSegment
    from pydub.effects import normalize, speedup
    from pydub.playback import play as pydub_play
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

logger = logging.getLogger("TextToSpeech")

class TTSEngine(Enum):
    """Available TTS engines"""
    PYTTSX3 = "pyttsx3"          # Offline, basic
    ELEVENLABS = "elevenlabs"    # Online, high quality, emotional
    EDGE_TTS = "edge_tts"         # Online, Microsoft Edge, good quality
    GTTS = "gtts"                 # Online, Google, simple
    AUTO = "auto"                 # Automatically select best available

class Emotion(Enum):
    """Emotional states for speech"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    EXCITED = "excited"
    CALM = "calm"
    WHISPER = "whisper"
    SCARED = "scared"
    SARCASTIC = "sarcastic"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"

class VoiceGender(Enum):
    """Voice gender preferences"""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"

@dataclass
class VoiceProfile:
    """Voice profile configuration"""
    name: str
    engine: TTSEngine
    voice_id: Optional[str] = None
    gender: VoiceGender = VoiceGender.NEUTRAL
    language: str = "en"
    accent: str = "us"
    age_group: str = "adult"  # child, young, adult, elderly
    pitch: float = 1.0  # 0.5-2.0
    speed: float = 1.0  # 0.5-2.0
    volume: float = 1.0  # 0.0-1.0
    emotion_available: bool = False
    custom_settings: Dict[str, Any] = None

@dataclass
class SpeechOptions:
    """Options for speech synthesis"""
    text: str
    emotion: Emotion = Emotion.NEUTRAL
    voice_profile: Optional[VoiceProfile] = None
    engine: Optional[TTSEngine] = None
    language: Optional[str] = None
    speed: Optional[float] = None
    pitch: Optional[float] = None
    volume: Optional[float] = None
    save_to_file: Optional[str] = None
    play_audio: bool = True
    add_emphasis: bool = False
    add_pauses: bool = True
    prosody: Optional[Dict[str, float]] = None  # rhythm, intonation

class TextToSpeech:
    """
    Enhanced Text-to-Speech with human-like emotional expression
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize TTS with configuration
        
        Args:
            config: Configuration dictionary with:
                - primary_engine: TTSEngine to use primarily
                - backup_engines: List of backup engines
                - default_voice_profile: Default voice to use
                - elevenlabs_api_key: API key for ElevenLabs
                - cache_enabled: Cache generated audio (default: True)
                - cache_dir: Directory for audio cache
                - auto_detect_language: Auto-detect text language
                - emotion_mapping: Custom emotion to voice mapping
        """
        self.config = {
            'primary_engine': TTSEngine.AUTO,
            'backup_engines': [TTSEngine.EDGE_TTS, TTSEngine.PYTTSX3, TTSEngine.GTTS],
            'default_voice_profile': None,
            'elevenlabs_api_key': os.environ.get('ELEVENLABS_API_KEY'),
            'elevenlabs_voice_id': os.environ.get('ELEVENLABS_VOICE_ID', 'gfRt6Z3Z8aTbpLfexQ7N'),
            'cache_enabled': True,
            'cache_dir': os.path.join(tempfile.gettempdir(), 'jarvis_tts_cache'),
            'auto_detect_language': True,
            'emotion_mapping': {
                Emotion.HAPPY: {'speed': 1.2, 'pitch': 1.1},
                Emotion.SAD: {'speed': 0.8, 'pitch': 0.9},
                Emotion.ANGRY: {'speed': 1.1, 'pitch': 1.2, 'volume': 1.2},
                Emotion.EXCITED: {'speed': 1.3, 'pitch': 1.2},
                Emotion.CALM: {'speed': 0.9, 'pitch': 0.95},
                Emotion.WHISPER: {'volume': 0.3, 'speed': 0.9},
                Emotion.SCARED: {'speed': 1.1, 'pitch': 1.15, 'volume': 0.8},
                Emotion.SARCASTIC: {'speed': 0.9, 'pitch': 1.1},
                Emotion.PROFESSIONAL: {'speed': 1.0, 'pitch': 1.0},
                Emotion.FRIENDLY: {'speed': 1.1, 'pitch': 1.05}
            },
            'voice_profiles': {},
            'default_language': 'en',
            'default_gender': VoiceGender.NEUTRAL,
            'max_retries': 3,
            'timeout': 10,  # seconds
        }
        
        if config:
            self.config.update(config)
            
        # Initialize engines
        self._init_engines()
        
        # Initialize cache
        if self.config['cache_enabled']:
            os.makedirs(self.config['cache_dir'], exist_ok=True)
            
        # Load default voice profiles
        self._load_default_profiles()
        
        # Initialize pygame for audio playback
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
            except Exception as e:
                logger.warning(f"Failed to initialize pygame mixer: {e}")
    
    def _init_engines(self):
        """Initialize available TTS engines"""
        self.engines = {}
        
        # Initialize pyttsx3
        if PYTTSX3_AVAILABLE:
            try:
                self.engines[TTSEngine.PYTTSX3] = pyttsx3.init()
                logger.info("pyttsx3 initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize pyttsx3: {e}")
        
        # Initialize ElevenLabs
        if ELEVENLABS_AVAILABLE and self.config['elevenlabs_api_key']:
            try:
                elevenlabs.set_api_key(self.config['elevenlabs_api_key'])
                self.engines[TTSEngine.ELEVENLABS] = elevenlabs
                logger.info("ElevenLabs initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize ElevenLabs: {e}")
        
        # Edge TTS doesn't need initialization
        if EDGE_TTS_AVAILABLE:
            self.engines[TTSEngine.EDGE_TTS] = True
            logger.info("Edge TTS available")
        
        # gTTS doesn't need initialization
        if GTTS_AVAILABLE:
            self.engines[TTSEngine.GTTS] = True
            logger.info("gTTS available")
    
    def _load_default_profiles(self):
        """Load default voice profiles"""
        # Default pyttsx3 profile
        self.config['voice_profiles']['default_pyttsx3'] = VoiceProfile(
            name="Default pyttsx3",
            engine=TTSEngine.PYTTSX3,
            gender=VoiceGender.NEUTRAL,
            language="en",
            accent="us",
            speed=1.0,
            pitch=1.0
        )
        
        # Default Edge TTS profiles (will be populated when voices are fetched)
        if EDGE_TTS_AVAILABLE:
            self._load_edge_tts_profiles()
    
    def _load_edge_tts_profiles(self):
        """Load available Edge TTS voices"""
        try:
            async def fetch_voices():
                voices = await VoicesManager.create()
                return voices.voices
            
            # Run async function in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            voices = loop.run_until_complete(fetch_voices())
            loop.close()
            
            for voice in voices[:10]:  # Store first 10 voices
                profile = VoiceProfile(
                    name=voice['Name'],
                    engine=TTSEngine.EDGE_TTS,
                    voice_id=voice['ShortName'],
                    gender=VoiceGender.MALE if 'Male' in voice['Gender'] else VoiceGender.FEMALE,
                    language=voice['Locale'].split('-')[0],
                    accent=voice['Locale'].split('-')[1].lower() if '-' in voice['Locale'] else 'us',
                    emotion_available=True
                )
                self.config['voice_profiles'][voice['ShortName']] = profile
                
        except Exception as e:
            logger.warning(f"Failed to load Edge TTS profiles: {e}")
    
    async def speak(self, text: str, emotion: str = "neutral") -> None:
        """
        Simple speak method for backward compatibility
        
        Args:
            text: Text to speak
            emotion: Emotional tone
        """
        await self.speak_enhanced(
            text=text,
            emotion=Emotion(emotion) if emotion in Emotion.__members__.values() else Emotion.NEUTRAL
        )
    
    async def speak_enhanced(self, 
                           text: str, 
                           emotion: Union[Emotion, str] = Emotion.NEUTRAL,
                           voice_profile: Optional[Union[str, VoiceProfile]] = None,
                           engine: Optional[TTSEngine] = None,
                           **kwargs) -> Optional[str]:
        """
        Enhanced speech synthesis with emotional expression
        
        Args:
            text: Text to speak
            emotion: Emotional tone
            voice_profile: Voice profile name or VoiceProfile object
            engine: Specific engine to use
            **kwargs: Additional SpeechOptions parameters
            
        Returns:
            Path to saved audio file if save_to_file specified, else None
        """
        # Convert string emotion to Emotion enum
        if isinstance(emotion, str):
            try:
                emotion = Emotion(emotion.lower())
            except ValueError:
                emotion = Emotion.NEUTRAL
        
        # Get voice profile
        selected_profile = self._get_voice_profile(voice_profile, emotion)
        
        # Create speech options
        options = SpeechOptions(
            text=text,
            emotion=emotion,
            voice_profile=selected_profile,
            engine=engine or self.config['primary_engine'],
            language=kwargs.get('language', self.config['default_language']),
            speed=kwargs.get('speed'),
            pitch=kwargs.get('pitch'),
            volume=kwargs.get('volume'),
            save_to_file=kwargs.get('save_to_file'),
            play_audio=kwargs.get('play_audio', True),
            add_emphasis=kwargs.get('add_emphasis', False),
            add_pauses=kwargs.get('add_pauses', True),
            prosody=kwargs.get('prosody')
        )
        
        # Apply emotion-based modifications
        options = self._apply_emotion_modifiers(options)
        
        # Check cache
        cache_key = self._generate_cache_key(options)
        cached_file = self._check_cache(cache_key)
        
        if cached_file and options.play_audio:
            await self._play_audio(cached_file)
            return cached_file if options.save_to_file else None
        
        # Try primary engine
        result = await self._synthesize_with_engine(options)
        
        # If primary fails, try backup engines
        if not result and self.config['backup_engines']:
            for backup_engine in self.config['backup_engines']:
                if backup_engine != options.engine:
                    logger.info(f"Trying backup engine: {backup_engine.value}")
                    options.engine = backup_engine
                    result = await self._synthesize_with_engine(options)
                    if result:
                        break
        
        if result:
            # Cache the result
            if self.config['cache_enabled'] and result:
                self._cache_audio(cache_key, result)
            
            logger.info(f"Speech synthesized: {text[:50]}... (emotion: {emotion.value})")
            return result
        else:
            logger.error("All TTS engines failed")
            return None
    
    def _get_voice_profile(self, 
                          profile: Optional[Union[str, VoiceProfile]], 
                          emotion: Emotion) -> VoiceProfile:
        """Get appropriate voice profile based on emotion and preferences"""
        if isinstance(profile, VoiceProfile):
            return profile
        elif isinstance(profile, str) and profile in self.config['voice_profiles']:
            return self.config['voice_profiles'][profile]
        
        # Select default profile based on emotion
        # For now, return a basic profile
        return VoiceProfile(
            name="Default",
            engine=TTSEngine.AUTO,
            gender=self.config['default_gender'],
            language=self.config['default_language'],
            emotion_available=True
        )
    
    def _apply_emotion_modifiers(self, options: SpeechOptions) -> SpeechOptions:
        """Apply emotion-based modifications to speech parameters"""
        if options.emotion in self.config['emotion_mapping']:
            modifiers = self.config['emotion_mapping'][options.emotion]
            
            # Apply modifiers if not overridden
            if options.speed is None:
                options.speed = modifiers.get('speed', 1.0)
            if options.pitch is None:
                options.pitch = modifiers.get('pitch', 1.0)
            if options.volume is None:
                options.volume = modifiers.get('volume', 1.0)
        
        return options
    
    async def _synthesize_with_engine(self, options: SpeechOptions) -> Optional[str]:
        """Synthesize speech with specified engine"""
        engine = options.engine
        
        if engine == TTSEngine.AUTO:
            engine = self._select_best_engine(options)
        
        try:
            if engine == TTSEngine.PYTTSX3 and TTSEngine.PYTTSX3 in self.engines:
                return await self._synthesize_pyttsx3(options)
                
            elif engine == TTSEngine.ELEVENLABS and TTSEngine.ELEVENLABS in self.engines:
                return await self._synthesize_elevenlabs(options)
                
            elif engine == TTSEngine.EDGE_TTS and EDGE_TTS_AVAILABLE:
                return await self._synthesize_edge_tts(options)
                
            elif engine == TTSEngine.GTTS and GTTS_AVAILABLE:
                return await self._synthesize_gtts(options)
                
        except Exception as e:
            logger.error(f"Error with {engine.value}: {e}")
            
        return None
    
    def _select_best_engine(self, options: SpeechOptions) -> TTSEngine:
        """Select best engine based on requirements"""
        # If emotion required, prefer ElevenLabs
        if options.emotion != Emotion.NEUTRAL and ELEVENLABS_AVAILABLE:
            return TTSEngine.ELEVENLABS
        
        # If multiple languages, prefer Edge TTS
        if options.language != 'en' and EDGE_TTS_AVAILABLE:
            return TTSEngine.EDGE_TTS
        
        # Default to Edge TTS for quality
        if EDGE_TTS_AVAILABLE:
            return TTSEngine.EDGE_TTS
        
        # Fallback to pyttsx3
        if PYTTSX3_AVAILABLE:
            return TTSEngine.PYTTSX3
        
        # Last resort
        return TTSEngine.GTTS
    
    async def _synthesize_pyttsx3(self, options: SpeechOptions) -> Optional[str]:
        """Synthesize using pyttsx3"""
        engine = self.engines[TTSEngine.PYTTSX3]
        
        # Configure engine
        engine.setProperty('rate', int(150 * (options.speed or 1.0)))
        engine.setProperty('volume', options.volume or 1.0)
        
        # pyttsx3 doesn't support saving to file directly in all versions
        if options.save_to_file:
            engine.save_to_file(options.text, options.save_to_file)
            engine.runAndWait()
            return options.save_to_file
        elif options.play_audio:
            # Run in thread to avoid blocking
            await asyncio.to_thread(self._speak_pyttsx3_sync, engine, options.text)
            
        return None
    
    def _speak_pyttsx3_sync(self, engine, text: str):
        """Synchronous pyttsx3 speech"""
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            logger.error(f"pyttsx3 speech error: {e}")
    
    async def _synthesize_elevenlabs(self, options: SpeechOptions) -> Optional[str]:
        """Synthesize using ElevenLabs"""
        eleven = self.engines[TTSEngine.ELEVENLABS]
        
        # Map emotion to ElevenLabs stability/similarity settings
        stability = 0.5
        similarity = 0.75
        
        if options.emotion == Emotion.HAPPY:
            stability, similarity = 0.3, 0.8
        elif options.emotion == Emotion.SAD:
            stability, similarity = 0.7, 0.6
        elif options.emotion == Emotion.ANGRY:
            stability, similarity = 0.2, 0.9
        elif options.emotion == Emotion.EXCITED:
            stability, similarity = 0.1, 0.85
        elif options.emotion == Emotion.CALM:
            stability, similarity = 0.8, 0.7
        
        # Select voice
        voice_id = options.voice_profile.voice_id if options.voice_profile else self.config.get('elevenlabs_voice_id')
        
        try:
            # Generate audio
            audio = eleven.generate(
                text=options.text,
                voice=voice_id or self.config.get('elevenlabs_voice_id'),
                model="eleven_monolingual_v1",
                voice_settings=VoiceSettings(
                    stability=stability,
                    similarity_boost=similarity,
                    style=0.5,
                    use_speaker_boost=True
                )
            )
            
            # Save or play
            if options.save_to_file:
                eleven.save(audio, options.save_to_file)
                return options.save_to_file
            elif options.play_audio:
                eleven.play(audio)
                
        except Exception as e:
            logger.error(f"ElevenLabs error: {e}")
            
        return None
    
    async def _synthesize_edge_tts(self, options: SpeechOptions) -> Optional[str]:
        """Synthesize using Microsoft Edge TTS"""
        # Select voice based on language and gender
        voice = self._select_edge_voice(options)
        
        # Apply speed modifier
        rate = f"+{int((options.speed - 1.0) * 100)}%" if options.speed and options.speed > 1.0 else f"{int((options.speed - 1.0) * 100)}%"
        
        # Apply pitch modifier
        pitch = f"+{int((options.pitch - 1.0) * 50)}Hz" if options.pitch else "0Hz"
        
        communicate = Communicate(
            options.text,
            voice,
            rate=rate,
            pitch=pitch
        )
        
        if options.save_to_file:
            await communicate.save(options.save_to_file)
            return options.save_to_file
        elif options.play_audio:
            # Play using pygame or pydub
            temp_file = os.path.join(tempfile.gettempdir(), f"edge_tts_{uuid.uuid4()}.mp3")
            await communicate.save(temp_file)
            await self._play_audio(temp_file)
            os.unlink(temp_file)
            
        return None
    
    def _select_edge_voice(self, options: SpeechOptions) -> str:
        """Select appropriate Edge TTS voice"""
        # This would need to run async, but for simplicity, return a default
        if options.voice_profile and options.voice_profile.voice_id:
            return options.voice_profile.voice_id
        
        # Default voices based on gender
        if options.voice_profile and options.voice_profile.gender == VoiceGender.MALE:
            return "en-US-GuyNeural"
        elif options.voice_profile and options.voice_profile.gender == VoiceGender.FEMALE:
            return "en-US-JennyNeural"
        else:
            return "en-US-JennyNeural"  # Default
    
    async def _synthesize_gtts(self, options: SpeechOptions) -> Optional[str]:
        """Synthesize using Google TTS"""
        tts = gTTS(
            text=options.text,
            lang=options.language or 'en',
            slow=options.speed < 0.8 if options.speed else False
        )
        
        if options.save_to_file:
            tts.save(options.save_to_file)
            return options.save_to_file
        elif options.play_audio:
            temp_file = os.path.join(tempfile.gettempdir(), f"gtts_{uuid.uuid4()}.mp3")
            tts.save(temp_file)
            await self._play_audio(temp_file)
            os.unlink(temp_file)
            
        return None
    
    async def _play_audio(self, audio_file: str):
        """Play audio file using available player"""
        try:
            if PYGAME_AVAILABLE:
                # Use pygame
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
                    
            elif PYDUB_AVAILABLE:
                # Use pydub
                audio = AudioSegment.from_file(audio_file)
                pydub_play(audio)
                
            else:
                # Fallback to system player
                if os.name == 'nt':  # Windows
                    os.startfile(audio_file)
                else:  # Linux/Mac
                    os.system(f'ffplay -nodisp -autoexit "{audio_file}" 2>/dev/null || aplay "{audio_file}"')
                    
        except Exception as e:
            logger.error(f"Audio playback error: {e}")
    
    def _generate_cache_key(self, options: SpeechOptions) -> str:
        """Generate cache key from options"""
        key_data = {
            'text': options.text,
            'emotion': options.emotion.value,
            'voice_profile': options.voice_profile.name if options.voice_profile else None,
            'engine': options.engine.value if options.engine else None,
            'speed': options.speed,
            'pitch': options.pitch,
            'language': options.language
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _check_cache(self, cache_key: str) -> Optional[str]:
        """Check if cached audio exists"""
        if not self.config['cache_enabled']:
            return None
            
        cache_file = os.path.join(self.config['cache_dir'], f"{cache_key}.mp3")
        if os.path.exists(cache_file):
            logger.debug(f"Cache hit for {cache_key}")
            return cache_file
            
        return None
    
    def _cache_audio(self, cache_key: str, audio_file: str):
        """Cache audio file"""
        if not self.config['cache_enabled'] or not os.path.exists(audio_file):
            return
            
        cache_file = os.path.join(self.config['cache_dir'], f"{cache_key}.mp3")
        try:
            import shutil
            shutil.copy2(audio_file, cache_file)
            logger.debug(f"Cached audio to {cache_file}")
        except Exception as e:
            logger.error(f"Failed to cache audio: {e}")
    
    async def set_voice(self, voice_name: str):
        """Set active voice by name"""
        if voice_name in self.config['voice_profiles']:
            self.config['default_voice_profile'] = self.config['voice_profiles'][voice_name]
            logger.info(f"Voice set to {voice_name}")
        else:
            logger.warning(f"Voice {voice_name} not found")
    
    async def create_voice_clone(self, audio_samples: List[str], voice_name: str) -> bool:
        """
        Create a voice clone using ElevenLabs (requires API key)
        
        Args:
            audio_samples: List of paths to audio files for cloning
            voice_name: Name for the cloned voice
            
        Returns:
            True if successful, False otherwise
        """
        if not ELEVENLABS_AVAILABLE or TTSEngine.ELEVENLABS not in self.engines:
            logger.error("ElevenLabs not available for voice cloning")
            return False
            
        try:
            eleven = self.engines[TTSEngine.ELEVENLABS]
            
            # This would use ElevenLabs voice cloning API
            # For now, return a placeholder
            logger.info(f"Voice cloning requested for {voice_name} with {len(audio_samples)} samples")
            
            # Add to profiles
            profile = VoiceProfile(
                name=voice_name,
                engine=TTSEngine.ELEVENLABS,
                voice_id=voice_name,  # Would be actual ID
                emotion_available=True
            )
            self.config['voice_profiles'][voice_name] = profile
            
            return True
            
        except Exception as e:
            logger.error(f"Voice cloning failed: {e}")
            return False
    
    async def add_emphasis(self, text: str, words: List[str]) -> str:
        """Add emphasis markup to specific words"""
        for word in words:
            # Add SSML emphasis tags
            text = text.replace(word, f'<emphasis level="strong">{word}</emphasis>')
        return text
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices"""
        voices = []
        for name, profile in self.config['voice_profiles'].items():
            voices.append({
                'name': profile.name,
                'engine': profile.engine.value,
                'gender': profile.gender.value,
                'language': profile.language,
                'accent': profile.accent,
                'emotion_available': profile.emotion_available
            })
        return voices


class SpeechEmotionEngine:
    """Advanced emotion modeling for speech"""
    
    def __init__(self):
        self.emotion_params = {
            Emotion.HAPPY: {
                'pitch_range': (1.1, 1.3),
                'speed_range': (1.1, 1.4),
                'volume_range': (0.9, 1.1),
                'prosody': {'rhythm': 'bouncy', 'intonation': 'rising'}
            },
            Emotion.SAD: {
                'pitch_range': (0.7, 0.9),
                'speed_range': (0.6, 0.8),
                'volume_range': (0.6, 0.8),
                'prosody': {'rhythm': 'slow', 'intonation': 'falling'}
            },
            Emotion.ANGRY: {
                'pitch_range': (1.0, 1.4),
                'speed_range': (1.0, 1.3),
                'volume_range': (1.1, 1.4),
                'prosody': {'rhythm': 'sharp', 'intonation': 'fluctuating'}
            },
            Emotion.EXCITED: {
                'pitch_range': (1.2, 1.5),
                'speed_range': (1.2, 1.5),
                'volume_range': (1.0, 1.3),
                'prosody': {'rhythm': 'fast', 'intonation': 'rising'}
            },
            Emotion.CALM: {
                'pitch_range': (0.9, 1.1),
                'speed_range': (0.7, 0.9),
                'volume_range': (0.7, 0.9),
                'prosody': {'rhythm': 'smooth', 'intonation': 'steady'}
            },
            Emotion.WHISPER: {
                'pitch_range': (0.8, 1.0),
                'speed_range': (0.7, 0.9),
                'volume_range': (0.2, 0.4),
                'prosody': {'rhythm': 'breathy', 'intonation': 'soft'}
            }
        }
    
    def get_emotion_params(self, emotion: Emotion) -> Dict[str, Any]:
        """Get speech parameters for emotion"""
        return self.emotion_params.get(emotion, self.emotion_params[Emotion.NEUTRAL])


# Example usage
async def main():
    """Example usage of enhanced TTS"""
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create TTS instance
    tts = TextToSpeech({
        'primary_engine': TTSEngine.AUTO,
        'cache_enabled': True,
        'default_language': 'en'
    })
    
    print("Enhanced Text-to-Speech initialized")
    print(f"Available voices: {len(tts.get_available_voices())}")
    
    # Test different emotions
    test_phrases = [
        ("I'm so happy to see you today!", Emotion.HAPPY),
        ("I'm feeling a bit sad about that.", Emotion.SAD),
        ("That makes me very angry!", Emotion.ANGRY),
        ("This is so exciting!", Emotion.EXCITED),
        ("Everything is going to be okay.", Emotion.CALM),
        ("Psst, let me tell you a secret.", Emotion.WHISPER)
    ]
    
    for text, emotion in test_phrases:
        print(f"\nSpeaking with {emotion.value} emotion: {text}")
        await tts.speak_enhanced(text, emotion=emotion)
        await asyncio.sleep(1)
    
    # Test voice profiles
    voices = tts.get_available_voices()
    if voices:
        print(f"\nUsing first available voice: {voices[0]['name']}")
        await tts.set_voice(voices[0]['name'])
        await tts.speak_enhanced("This is my new voice!", emotion=Emotion.PROFESSIONAL)
    
    # Save to file example
    print("\nSaving speech to file...")
    saved_file = await tts.speak_enhanced(
        "This will be saved to a file.",
        emotion=Emotion.PROFESSIONAL,
        save_to_file="output.mp3",
        play_audio=False
    )
    if saved_file:
        print(f"Saved to {saved_file}")
    
    print("\nTTS demonstration complete!")


if __name__ == "__main__":
    asyncio.run(main())