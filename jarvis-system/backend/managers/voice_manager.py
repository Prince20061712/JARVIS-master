import pyautogui
import pyperclip
import speech_recognition as sr

class VoiceTypingManager:
    """Manages voice typing and text input"""
    
    def type_text(self, text):
        """Type text using keyboard"""
        try:
            pyautogui.write(text, interval=0.05)
            return f"Typed: {text[:50]}..." if len(text) > 50 else f"Typed: {text}"
        except:
            return "Could not type text"
    
    def type_from_clipboard(self):
        """Type text from clipboard"""
        try:
            text = pyperclip.paste()
            if text:
                pyautogui.write(text, interval=0.05)
                return f"Typed from clipboard: {text[:50]}..."
            else:
                return "Clipboard is empty"
        except:
            return "Could not type from clipboard"
    
    def voice_to_text(self, audio_system, recognizer):
        """Convert voice to text and type it"""
        try:
            with sr.Microphone() as source:
                audio_system.speak("Speak now, I'm listening...")
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=30)
                text = recognizer.recognize_google(audio)
                
                pyautogui.write(text, interval=0.05)
                return f"Voice typed: {text[:100]}..."
        except Exception as e:
            return f"Voice typing failed: {str(e)}"
