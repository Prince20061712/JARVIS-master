import logging
import asyncio
import os
try:
    import speech_recognition as sr
except ImportError:
    sr = None

logger = logging.getLogger("SpeechToText")

class SpeechToText:
    def __init__(self):
        if sr:
             self.recognizer = sr.Recognizer()
        else:
            self.recognizer = None
            logger.warning("speech_recognition not installed.")
            
    async def listen(self, timeout: int = 5) -> str:
        """
        Listens for audio and returns transcribed text.
        """
        if not self.recognizer:
            return ""

        # Run blocking IO in executor
        return await asyncio.to_thread(self._listen_sync, timeout)

    def _listen_sync(self, timeout):
        try:
            with sr.Microphone() as source:
                logger.info("Listening...")
                # self.recognizer.adjust_for_ambient_noise(source)
                try:
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                except sr.WaitTimeoutError:
                    return ""
                
                logger.info("Recognizing...")
                # Default to Google for prototype (free, no API key needed for basic)
                # For offline, use sphinx or whisper locally if configured
                text = self.recognizer.recognize_google(audio)
                return text
        except sr.UnknownValueError:
            logger.debug("Could not understand audio")
            return ""
        except sr.RequestError as e:
            logger.error(f"Could not request results; {e}")
            return ""
        except Exception as e:
             # Often happens if no microphone, etc.
             logger.error(f"Microphone error: {e}")
             return ""
