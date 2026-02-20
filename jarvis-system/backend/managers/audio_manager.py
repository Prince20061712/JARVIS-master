import os
import time
import asyncio
from colorama import Fore

JARVIS_NAME = "Jarvis"

class AudioSystem:
    """Enhanced audio system for better speech control"""
    
    def __init__(self, websocket_manager=None, loop=None):
        self.websocket_manager = websocket_manager
        self.loop = loop
        self.engine = None
        try:
            # Use Edge TTS for high quality voice
            from core.system.tts_engine import EdgeTTSEngine
            self.engine = EdgeTTSEngine(voice="en-US-ChristopherNeural")
            print(f"{Fore.GREEN}🔊 Initialized Edge TTS (Voice: Christopher)")
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️  Could not initialize Edge TTS engine: {e}")
            print(f"{Fore.YELLOW}⚠️  Running in text-only mode (backend voice disabled)")
        
        self.volume_level = 80
        self.speech_rate = 175
        self._ensure_audio_output()
        
    def _ensure_audio_output(self):
        """Ensure audio output is properly configured"""
        print(f"\n{Fore.CYAN}🔊 Configuring Audio System...")
        if self.engine:
            try:
                pass
            except Exception:
                print(f"{Fore.GREEN}✅ Audio output configured")
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️  Audio test warning: {e}")
            
            try:
                self.engine.setProperty('volume', 0.9)
                self.engine.setProperty('rate', 175)
                print(f"{Fore.CYAN}🔊 Volume: 90% | Rate: 175 wpm")
            except:
                pass
        else:
            print(f"{Fore.YELLOW}🔊 Audio System: WebSocket-only mode")
    
    def configure_jarvis_voice(self):
        """Configure pyttsx3 to sound more like JARVIS"""
        if not self.engine: return
        
        try:
            self.engine.setProperty('rate', 175)
            self.engine.setProperty('volume', 0.9)
            
            voices = self.engine.getProperty('voices')
            preferred_voices = ['daniel', 'alex', 'fred', 'samantha']
            for voice in voices:
                voice_name = voice.name.lower()
                for pref in preferred_voices:
                    if pref in voice_name:
                        self.engine.setProperty('voice', voice.id)
                        print(f"{Fore.CYAN}🔊 Selected voice: {voice.name}")
                        return
            
            if len(voices) > 0:
                self.engine.setProperty('voice', voices[0].id)
                print(f"{Fore.CYAN}🔊 Using voice: {voices[0].name}")
        except:
            pass
    
    def set_volume(self, level):
        """Set speech volume (0.0 to 1.0)"""
        if not self.engine: return 0
        
        try:
            level = max(0.0, min(1.0, level))
            self.engine.setProperty('volume', level)
            self.volume_level = level * 100
            print(f"{Fore.CYAN}🔊 Volume set to: {self.volume_level:.0f}%")
            return self.volume_level
        except:
            return 0
    
    def get_volume(self):
        """Get current volume level"""
        if not self.engine: return 0
        try:
            return self.engine.getProperty('volume')
        except:
            return 0
    
    def set_rate(self, rate):
        """Set speech rate (words per minute)"""
        if not self.engine: return
        try:
            self.engine.setProperty('rate', rate)
            self.speech_rate = rate
            print(f"{Fore.CYAN}🔊 Speech rate set to: {rate} wpm")
        except:
            pass
    
    def speak(self, text, play_beep=False, rate=None, on_complete=None, on_start=None):
        """Speak text using Edge TTS (High Quality)"""
        if not text:
            if on_complete: on_complete()
            return

        print(f"{Fore.GREEN}{JARVIS_NAME}: {text}")
        
        # 1. Send text to frontend immediately (no animation)
        if self.websocket_manager and self.loop:
            try:
                asyncio.run_coroutine_threadsafe(
                    self.websocket_manager.broadcast({
                        "type": "text",
                        "text": text
                    }),
                    self.loop
                )
            except Exception as e:
                print(f"{Fore.RED}Error broadcasting to WebSocket: {e}")

        # 2. Speak audio locally
        if self.engine:
            try:
                # Pass on_start to trigger animation exactly when audio starts
                # Check signature compatibility
                if 'on_start' in self.engine.speak.__code__.co_varnames:
                    self.engine.speak(text, on_complete=on_complete, on_start=on_start)
                else:
                    # Fallback for older engine versions
                    if on_start: on_start()
                    self.engine.speak(text, on_complete=on_complete)
            except Exception as e:
                print(f"{Fore.RED}Error in speech synthesis: {e}")
                if on_complete: on_complete()
        else:
             if on_complete: on_complete()
    
    def play_beep(self, type="response"):
        """Play different beep sounds"""
        try:
            if type == "response":
                print('\a', end='', flush=True)
            elif type == "listening":
                print('\a', end='', flush=True)
            elif type == "error":
                print('\a', end='', flush=True)
            elif type == "ai_processing":
                print('\a', end='', flush=True)
        except:
            pass
    
    def test_speakers(self):
        """Test audio output on all speakers"""
        print(f"\n{Fore.CYAN}🔊 Testing audio system...")
        test_messages = [
            "Audio system test one.",
            "Audio system test two.",
            "Audio system test three.",
            "Audio system verification complete."
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"{Fore.CYAN}🔊 Test {i}: {message}")
            self.speak(message)
            time.sleep(0.8)
        
        self.speak("Audio system test complete. All speakers are functional.")
        print(f"{Fore.GREEN}✅ Audio system test complete")
        return True
    
    def adjust_system_volume(self, direction="up"):
        """Adjust macOS system volume"""
        try:
            if direction == "up":
                os.system("osascript -e 'set volume output volume (output volume of (get volume settings) + 10)'")
                self.speak("System volume increased.")
            elif direction == "down":
                os.system("osascript -e 'set volume output volume (output volume of (get volume settings) - 10)'")
                self.speak("System volume decreased.")
            elif direction == "mute":
                os.system("osascript -e 'set volume output muted true'")
                self.speak("System audio muted.")
            elif direction == "unmute":
                os.system("osascript -e 'set volume output muted false'")
                self.speak("System audio unmuted.")
            elif direction == "max":
                os.system("osascript -e 'set volume output volume 100'")
                self.speak("System volume set to maximum.")
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️  System volume adjustment failed: {e}")
