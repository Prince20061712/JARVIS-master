import logging
import asyncio
import os
from typing import Optional

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    from elevenlabs import generate, save
    # Note: older elevenlabs lib version might differ, adapting for generic usage
except ImportError:
    pass

logger = logging.getLogger("TextToSpeech")

class TextToSpeech:
    def __init__(self):
        self.engine = None
        if pyttsx3:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty('rate', 170)
            except Exception as e:
                logger.error(f"Failed to init pyttsx3: {e}")

    async def speak(self, text: str, emotion: str = "neutral"):
        """
        Synthesizes speech.
        """
        logger.info(f"Speaking: {text}")
        
        # Check for ElevenLabs API key TODO
        use_elevenlabs = False 
        
        if use_elevenlabs:
             # Logic for ElevenLabs
             pass
        elif self.engine:
            # Local fallback
            await asyncio.to_thread(self._speak_sync, text)
        else:
            logger.warning("No TTS engine available.")

    def _speak_sync(self, text):
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"TTS Error: {e}")
