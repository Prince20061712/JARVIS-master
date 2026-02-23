"""
Enhanced Voice Typing Manager for macOS
Handles voice-to-text dictation, text input automation, and advanced typing features
"""

import pyautogui
import pyperclip
import speech_recognition as sr
import time
import threading
import queue
import re
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import difflib
import keyboard
import pynput
from pynput.keyboard import Key, Controller
import pygetwindow as gw
import applescript
import Quartz
import AppKit
import accessibility
import rpa as tagui
import autohotkey
from unidecode import unidecode
import Levenshtein
from rapidfuzz import fuzz, process

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TypingMode(Enum):
    """Typing modes"""
    STANDARD = "standard"  # Normal typing
    DICTATION = "dictation"  # Continuous dictation
    COMMAND = "command"  # Voice commands
    CORRECTION = "correction"  # Correction mode
    FORMATTING = "formatting"  # Text formatting
    CODE = "code"  # Code input
    SECURE = "secure"  # Secure input (no echo)
    BATCH = "batch"  # Batch text input


class InputMethod(Enum):
    """Input methods"""
    KEYBOARD = "keyboard"  # Direct keyboard input
    CLIPBOARD = "clipboard"  # Paste from clipboard
    PASTEBOARD = "pasteboard"  # macOS pasteboard
    DRAG_DROP = "drag_drop"  # Drag and drop text
    APPLE_EVENTS = "apple_events"  # Apple Events
    UI_ELEMENTS = "ui_elements"  # Direct UI element input
    JAVASCRIPT = "javascript"  # JavaScript injection (browser)


class DictationLanguage(Enum):
    """Supported dictation languages"""
    ENGLISH_US = "en-US"
    ENGLISH_UK = "en-GB"
    ENGLISH_AU = "en-AU"
    ENGLISH_IN = "en-IN"
    HINDI = "hi-IN"
    SPANISH = "es-ES"
    FRENCH = "fr-FR"
    GERMAN = "de-DE"
    ITALIAN = "it-IT"
    JAPANESE = "ja-JP"
    KOREAN = "ko-KR"
    CHINESE = "zh-CN"
    RUSSIAN = "ru-RU"
    ARABIC = "ar-SA"
    PORTUGUESE = "pt-PT"


class CorrectionStrategy(Enum):
    """Text correction strategies"""
    AUTO_CORRECT = "auto_correct"  # Automatic correction
    SUGGEST = "suggest"  # Suggest corrections
    CONFIDENCE_BASED = "confidence"  # Based on confidence score
    MANUAL = "manual"  # Manual selection
    HYBRID = "hybrid"  # Combined approach


class FormattingStyle(Enum):
    """Text formatting styles"""
    PLAIN = "plain"  # Plain text
    TITLE_CASE = "title_case"  # Title Case
    UPPER_CASE = "upper_case"  # UPPER CASE
    LOWER_CASE = "lower_case"  # lower case
    SENTENCE_CASE = "sentence_case"  # Sentence case
    CAMEL_CASE = "camelCase"  # camelCase
    PASCAL_CASE = "PascalCase"  # PascalCase
    SNAKE_CASE = "snake_case"  # snake_case
    KEBAB_CASE = "kebab-case"  # kebab-case
    MARKDOWN = "markdown"  # Markdown
    HTML = "html"  # HTML


@dataclass
class TypingContext:
    """Context information for typing"""
    app_name: Optional[str] = None
    window_title: Optional[str] = None
    input_type: Optional[str] = None  # text, password, search, etc.
    cursor_position: Tuple[int, int] = (0, 0)
    selected_text: Optional[str] = None
    surrounding_text: Optional[str] = None
    field_id: Optional[str] = None
    is_editable: bool = True
    is_focused: bool = False


@dataclass
class DictationResult:
    """Result of dictation"""
    text: str
    confidence: float
    alternatives: List[str] = field(default_factory=list)
    words: List[Dict] = field(default_factory=list)  # Word-level details
    language: DictationLanguage = DictationLanguage.ENGLISH_US
    duration: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class VoiceTypingError(Exception):
    """Custom exception for voice typing errors"""
    pass


class VoiceTypingManager:
    """
    Enhanced Voice Typing Manager with comprehensive features:
    - Multi-language dictation
    - Real-time transcription
    - Text correction and suggestions
    - Formatting options
    - Context-aware typing
    - Secure input mode
    - Batch processing
    - Text post-processing
    - Keyboard shortcuts
    - Accessibility integration
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the Voice Typing Manager
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or Path.home() / ".config" / "voice_typing.json"
        
        # Core components
        self.recognizer = sr.Recognizer()
        self.keyboard_controller = Controller()
        self.microphone = sr.Microphone()
        
        # Typing state
        self.current_mode = TypingMode.STANDARD
        self.is_typing = False
        self.is_paused = False
        self.typing_queue: queue.Queue = queue.Queue()
        self.typing_thread: Optional[threading.Thread] = None
        
        # Configuration
        self.default_language = DictationLanguage.ENGLISH_US
        self.default_method = InputMethod.KEYBOARD
        self.typing_speed = 0.05  # Delay between keystrokes
        self.auto_correct = True
        self.correction_strategy = CorrectionStrategy.CONFIDENCE_BASED
        self.confidence_threshold = 0.8
        self.min_word_confidence = 0.6
        self.max_alternatives = 3
        
        # Text processing
        self.custom_vocabulary: Dict[str, List[str]] = {}  # Custom words and alternatives
        self.auto_replacements: Dict[str, str] = {}  # Auto-replace patterns
        self.formatting_rules: Dict[str, Callable] = {}  # Custom formatting rules
        
        # Context tracking
        self.current_context = TypingContext()
        self.context_history: List[TypingContext] = []
        self.max_context_history = 10
        
        # Performance metrics
        self.metrics: Dict[str, Any] = {
            "total_dictations": 0,
            "total_words": 0,
            "total_characters": 0,
            "correction_rate": 0.0,
            "average_confidence": 0.0,
            "typing_speed": 0.0,  # characters per second
            "errors": []
        }
        
        # Keyboard shortcuts
        self.shortcuts: Dict[str, str] = {
            "start_dictation": "cmd+shift+d",
            "stop_dictation": "cmd+shift+s",
            "pause_typing": "cmd+shift+p",
            "clear_text": "cmd+shift+x",
            "format_text": "cmd+shift+f",
            "correct_text": "cmd+shift+c"
        }
        
        # Load configuration
        self.load_config()
        
        # Initialize keyboard listeners
        self.setup_keyboard_listeners()
        
        # Start background threads
        self.start_background_tasks()
        
        logger.info("Voice Typing Manager initialized")
    
    def load_config(self) -> None:
        """Load configuration from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    
                # Update configuration
                self.default_language = DictationLanguage(config.get("default_language", "en-US"))
                self.default_method = InputMethod(config.get("default_method", "keyboard"))
                self.typing_speed = config.get("typing_speed", 0.05)
                self.auto_correct = config.get("auto_correct", True)
                self.confidence_threshold = config.get("confidence_threshold", 0.8)
                self.min_word_confidence = config.get("min_word_confidence", 0.6)
                self.max_alternatives = config.get("max_alternatives", 3)
                self.custom_vocabulary = config.get("custom_vocabulary", {})
                self.auto_replacements = config.get("auto_replacements", {})
                self.shortcuts.update(config.get("shortcuts", {}))
                
                logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
    
    def save_config(self) -> None:
        """Save configuration to file"""
        try:
            config = {
                "default_language": self.default_language.value,
                "default_method": self.default_method.value,
                "typing_speed": self.typing_speed,
                "auto_correct": self.auto_correct,
                "confidence_threshold": self.confidence_threshold,
                "min_word_confidence": self.min_word_confidence,
                "max_alternatives": self.max_alternatives,
                "custom_vocabulary": self.custom_vocabulary,
                "auto_replacements": self.auto_replacements,
                "shortcuts": self.shortcuts
            }
            
            # Create directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def setup_keyboard_listeners(self) -> None:
        """Setup global keyboard shortcuts"""
        try:
            # Register keyboard shortcuts
            for action, shortcut in self.shortcuts.items():
                try:
                    keyboard.add_hotkey(shortcut, lambda a=action: self.handle_shortcut(a))
                    logger.info(f"Registered shortcut {shortcut} for {action}")
                except Exception as e:
                    logger.error(f"Failed to register shortcut {shortcut}: {e}")
        except Exception as e:
            logger.error(f"Failed to setup keyboard listeners: {e}")
    
    def handle_shortcut(self, action: str) -> None:
        """Handle keyboard shortcut actions"""
        try:
            if action == "start_dictation":
                self.start_dictation()
            elif action == "stop_dictation":
                self.stop_dictation()
            elif action == "pause_typing":
                self.toggle_pause()
            elif action == "clear_text":
                self.clear_text()
            elif action == "format_text":
                self.format_selected_text()
            elif action == "correct_text":
                self.correct_selected_text()
        except Exception as e:
            logger.error(f"Failed to handle shortcut {action}: {e}")
    
    def start_background_tasks(self) -> None:
        """Start background tasks"""
        # Start typing queue processor
        self.typing_thread = threading.Thread(target=self.process_typing_queue, daemon=True)
        self.typing_thread.start()
        
        # Start context monitor
        context_thread = threading.Thread(target=self.monitor_context, daemon=True)
        context_thread.start()
        
        logger.info("Background tasks started")
    
    def process_typing_queue(self) -> None:
        """Process typing queue in background"""
        while True:
            try:
                if not self.is_paused and not self.typing_queue.empty():
                    text = self.typing_queue.get(timeout=1)
                    self._type_text_with_context(text)
                time.sleep(0.1)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing typing queue: {e}")
    
    def monitor_context(self) -> None:
        """Monitor typing context in background"""
        while True:
            try:
                self.update_context()
                time.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Error monitoring context: {e}")
    
    def update_context(self) -> None:
        """Update current typing context"""
        try:
            # Get active window
            active_window = gw.getActiveWindow()
            if active_window:
                self.current_context.app_name = active_window.title
                self.current_context.window_title = active_window.title
            
            # Get cursor position
            self.current_context.cursor_position = pyautogui.position()
            
            # Try to get selected text
            try:
                with pyautogui.hold('cmd'):
                    pyautogui.press('c')
                    time.sleep(0.1)
                    selected = pyperclip.paste()
                    if selected:
                        self.current_context.selected_text = selected
            except:
                pass
            
            # Store in history
            self.context_history.append(self.current_context)
            if len(self.context_history) > self.max_context_history:
                self.context_history.pop(0)
                
        except Exception as e:
            logger.error(f"Failed to update context: {e}")
    
    def start_dictation(self, language: Optional[DictationLanguage] = None) -> None:
        """
        Start continuous dictation
        
        Args:
            language: Language for dictation
        """
        try:
            if self.is_typing:
                logger.warning("Dictation already in progress")
                return
            
            lang = language or self.default_language
            self.is_typing = True
            
            # Start dictation thread
            dictation_thread = threading.Thread(
                target=self._dictation_loop,
                args=(lang,),
                daemon=True
            )
            dictation_thread.start()
            
            logger.info(f"Started dictation in {lang.value}")
            
        except Exception as e:
            logger.error(f"Failed to start dictation: {e}")
            self.is_typing = False
    
    def _dictation_loop(self, language: DictationLanguage) -> None:
        """Main dictation loop"""
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            while self.is_typing:
                try:
                    # Listen for audio
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    
                    # Recognize speech
                    result = self.recognize_speech(audio, language)
                    
                    if result.text:
                        # Process and type text
                        self.process_and_type(result)
                        
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    logger.debug("Could not understand audio")
                except Exception as e:
                    logger.error(f"Error in dictation loop: {e}")
    
    def recognize_speech(self, audio, language: DictationLanguage) -> DictationResult:
        """
        Recognize speech from audio
        
        Args:
            audio: Audio data
            language: Language for recognition
            
        Returns:
            DictationResult object
        """
        try:
            start_time = time.time()
            
            # Get recognition results
            results = self.recognizer.recognize_google(
                audio,
                language=language.value,
                show_all=True
            )
            
            if not results:
                return DictationResult("", 0.0)
            
            # Parse results
            alternatives = []
            words = []
            
            if 'alternative' in results:
                alternatives = [alt['transcript'] for alt in results['alternative']]
                
                # Get confidence if available
                confidence = results['alternative'][0].get('confidence', 0.0)
                
                # Get word-level details if available
                if 'words' in results:
                    words = results['words']
            else:
                # Simple result
                text = results
                confidence = 1.0
                alternatives = [text]
            
            main_text = alternatives[0] if alternatives else ""
            
            duration = time.time() - start_time
            
            return DictationResult(
                text=main_text,
                confidence=confidence,
                alternatives=alternatives[1:self.max_alternatives],
                words=words,
                language=language,
                duration=duration
            )
            
        except Exception as e:
            logger.error(f"Speech recognition failed: {e}")
            return DictationResult("", 0.0)
    
    def process_and_type(self, result: DictationResult) -> None:
        """
        Process dictation result and add to typing queue
        
        Args:
            result: Dictation result to process
        """
        try:
            text = result.text
            
            # Apply auto-correction
            if self.auto_correct:
                text = self.correct_text(text, result.confidence)
            
            # Apply custom replacements
            text = self.apply_replacements(text)
            
            # Apply formatting
            text = self.apply_formatting(text)
            
            # Add to typing queue
            self.typing_queue.put(text)
            
            # Update metrics
            self.update_metrics(result)
            
        except Exception as e:
            logger.error(f"Failed to process dictation result: {e}")
    
    def correct_text(self, text: str, confidence: float) -> str:
        """
        Apply text correction
        
        Args:
            text: Text to correct
            confidence: Confidence score
            
        Returns:
            Corrected text
        """
        try:
            if confidence < self.confidence_threshold:
                # Use different correction strategies based on confidence
                if self.correction_strategy == CorrectionStrategy.AUTO_CORRECT:
                    return self.auto_correct_text(text)
                elif self.correction_strategy == CorrectionStrategy.SUGGEST:
                    suggestions = self.get_corrections(text)
                    if suggestions:
                        # Auto-apply best suggestion if confidence is very low
                        return suggestions[0]
                elif self.correction_strategy == CorrectionStrategy.CONFIDENCE_BASED:
                    return self.confidence_based_correction(text, confidence)
                elif self.correction_strategy == CorrectionStrategy.HYBRID:
                    return self.hybrid_correction(text, confidence)
            
            return text
            
        except Exception as e:
            logger.error(f"Text correction failed: {e}")
            return text
    
    def auto_correct_text(self, text: str) -> str:
        """Apply automatic text correction"""
        try:
            words = text.split()
            corrected_words = []
            
            for word in words:
                # Check custom vocabulary
                if word.lower() in self.custom_vocabulary:
                    corrected_words.append(self.custom_vocabulary[word.lower()][0])
                    continue
                
                # Check common corrections
                corrected = self.spell_correction(word)
                corrected_words.append(corrected)
            
            return ' '.join(corrected_words)
            
        except Exception as e:
            logger.error(f"Auto-correction failed: {e}")
            return text
    
    def get_corrections(self, text: str) -> List[str]:
        """Get correction suggestions"""
        try:
            suggestions = []
            
            # Get word-level corrections
            words = text.split()
            for i, word in enumerate(words):
                word_suggestions = self.get_word_corrections(word)
                for suggestion in word_suggestions:
                    new_text = words.copy()
                    new_text[i] = suggestion
                    suggestions.append(' '.join(new_text))
            
            return suggestions[:self.max_alternatives]
            
        except Exception as e:
            logger.error(f"Failed to get corrections: {e}")
            return []
    
    def get_word_corrections(self, word: str) -> List[str]:
        """Get corrections for a single word"""
        try:
            # Use fuzzy matching
            corrections = []
            
            # Check custom vocabulary
            if word.lower() in self.custom_vocabulary:
                corrections.extend(self.custom_vocabulary[word.lower()])
            
            # Use Levenshtein distance for spelling correction
            # This is a simplified version - in practice you'd use a dictionary
            common_words = ["the", "be", "to", "of", "and", "a", "in", "that", "have", "i"]
            for common in common_words:
                if Levenshtein.distance(word.lower(), common) <= 2:
                    corrections.append(common)
            
            return list(set(corrections))[:self.max_alternatives]
            
        except Exception as e:
            logger.error(f"Failed to get word corrections: {e}")
            return []
    
    def confidence_based_correction(self, text: str, confidence: float) -> str:
        """Apply correction based on confidence score"""
        try:
            words = text.split()
            
            # Adjust correction threshold based on overall confidence
            word_threshold = self.min_word_confidence * (confidence / self.confidence_threshold)
            
            corrected_words = []
            for word in words:
                # In practice, you'd have word-level confidence
                # For now, apply correction if word confidence is below threshold
                if confidence < word_threshold:
                    corrected = self.auto_correct_text(word)
                    corrected_words.append(corrected)
                else:
                    corrected_words.append(word)
            
            return ' '.join(corrected_words)
            
        except Exception as e:
            logger.error(f"Confidence-based correction failed: {e}")
            return text
    
    def hybrid_correction(self, text: str, confidence: float) -> str:
        """Apply hybrid correction approach"""
        try:
            # Try multiple strategies and pick best result
            corrections = []
            
            # Auto-correct
            auto_corrected = self.auto_correct_text(text)
            corrections.append(auto_corrected)
            
            # Get suggestions
            suggestions = self.get_corrections(text)
            corrections.extend(suggestions)
            
            # Use fuzzy matching to find best correction
            best = process.extractOne(text, corrections, scorer=fuzz.ratio)
            return best[0] if best else text
            
        except Exception as e:
            logger.error(f"Hybrid correction failed: {e}")
            return text
    
    def spell_correction(self, word: str) -> str:
        """Basic spell correction"""
        try:
            # Simple spell correction using common patterns
            # In practice, use a proper spell checker like enchant or textblob
            common_mistakes = {
                "teh": "the",
                "recieve": "receive",
                "seperate": "separate",
                "occured": "occurred",
                "accomodate": "accommodate"
            }
            
            return common_mistakes.get(word.lower(), word)
            
        except Exception as e:
            logger.error(f"Spell correction failed: {e}")
            return word
    
    def apply_replacements(self, text: str) -> str:
        """Apply custom text replacements"""
        try:
            for pattern, replacement in self.auto_replacements.items():
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
            return text
        except Exception as e:
            logger.error(f"Failed to apply replacements: {e}")
            return text
    
    def apply_formatting(self, text: str) -> str:
        """Apply text formatting"""
        try:
            # Apply formatting based on current mode or context
            if self.current_mode == TypingMode.FORMATTING:
                # Use detected formatting
                pass
            return text
        except Exception as e:
            logger.error(f"Failed to apply formatting: {e}")
            return text
    
    def _type_text_with_context(self, text: str) -> None:
        """
        Type text with context awareness
        
        Args:
            text: Text to type
        """
        try:
            # Check if current field is editable
            if not self.current_context.is_editable:
                logger.warning("Current field is not editable")
                return
            
            # Choose input method based on context
            method = self.select_input_method()
            
            # Type using selected method
            if method == InputMethod.KEYBOARD:
                self.type_with_keyboard(text)
            elif method == InputMethod.CLIPBOARD:
                self.type_with_clipboard(text)
            elif method == InputMethod.PASTEBOARD:
                self.type_with_pasteboard(text)
            elif method == InputMethod.UI_ELEMENTS:
                self.type_with_ui_element(text)
            else:
                # Fallback to keyboard
                self.type_with_keyboard(text)
            
            # Update metrics
            self.metrics["total_characters"] += len(text)
            self.metrics["total_words"] += len(text.split())
            
        except Exception as e:
            logger.error(f"Failed to type text: {e}")
            self.metrics["errors"].append(str(e))
    
    def select_input_method(self) -> InputMethod:
        """Select best input method for current context"""
        try:
            # Check for secure input
            if self.current_mode == TypingMode.SECURE:
                return InputMethod.KEYBOARD
            
            # Check for browser
            if self.current_context.app_name and "browser" in self.current_context.app_name.lower():
                return InputMethod.JAVASCRIPT
            
            # Default to clipboard for long texts
            if self.metrics.get("current_text_length", 0) > 1000:
                return InputMethod.CLIPBOARD
            
            return self.default_method
            
        except Exception as e:
            logger.error(f"Failed to select input method: {e}")
            return InputMethod.KEYBOARD
    
    def type_with_keyboard(self, text: str) -> None:
        """
        Type text using keyboard simulation
        
        Args:
            text: Text to type
        """
        try:
            # Split into chunks for better control
            chunks = self.split_text_chunks(text)
            
            for chunk in chunks:
                if self.is_paused:
                    break
                
                # Type the chunk
                for char in chunk:
                    if self.is_paused:
                        break
                    self.keyboard_controller.type(char)
                    time.sleep(self.typing_speed)
                
                # Small pause between chunks
                time.sleep(self.typing_speed * 5)
                
        except Exception as e:
            logger.error(f"Keyboard typing failed: {e}")
            raise
    
    def type_with_clipboard(self, text: str) -> None:
        """
        Type text using clipboard paste
        
        Args:
            text: Text to type
        """
        try:
            # Save current clipboard
            original = pyperclip.paste()
            
            # Copy new text
            pyperclip.copy(text)
            time.sleep(0.1)
            
            # Paste
            with self.keyboard_controller.pressed(Key.cmd):
                self.keyboard_controller.press('v')
                self.keyboard_controller.release('v')
            
            # Restore original clipboard
            time.sleep(0.1)
            pyperclip.copy(original)
            
        except Exception as e:
            logger.error(f"Clipboard typing failed: {e}")
            raise
    
    def type_with_pasteboard(self, text: str) -> None:
        """
        Type text using macOS pasteboard
        
        Args:
            text: Text to type
        """
        try:
            # Use AppleScript for pasteboard
            script = f'''
            set the clipboard to "{text}"
            tell application "System Events"
                keystroke "v" using command down
            end tell
            '''
            
            applescript.run(script)
            
        except Exception as e:
            logger.error(f"Pasteboard typing failed: {e}")
            raise
    
    def type_with_ui_element(self, text: str) -> None:
        """
        Type text directly into UI element
        
        Args:
            text: Text to type
        """
        try:
            # Use accessibility APIs
            # This is platform-specific and complex
            # Simplified version:
            script = f'''
            tell application "System Events"
                tell process "TargetApp"
                    set value of text field 1 to "{text}"
                end tell
            end tell
            '''
            
            applescript.run(script)
            
        except Exception as e:
            logger.error(f"UI element typing failed: {e}")
            raise
    
    def split_text_chunks(self, text: str, chunk_size: int = 50) -> List[str]:
        """
        Split text into manageable chunks
        
        Args:
            text: Text to split
            chunk_size: Maximum chunk size
            
        Returns:
            List of text chunks
        """
        chunks = []
        words = text.split()
        
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            
            if current_length + word_length > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def stop_dictation(self) -> None:
        """Stop current dictation session"""
        try:
            self.is_typing = False
            logger.info("Dictation stopped")
        except Exception as e:
            logger.error(f"Failed to stop dictation: {e}")
    
    def toggle_pause(self) -> None:
        """Toggle typing pause"""
        self.is_paused = not self.is_paused
        status = "paused" if self.is_paused else "resumed"
        logger.info(f"Typing {status}")
    
    def clear_text(self) -> None:
        """Clear current text field"""
        try:
            # Select all and delete
            with self.keyboard_controller.pressed(Key.cmd):
                self.keyboard_controller.press('a')
                self.keyboard_controller.release('a')
            
            time.sleep(0.1)
            self.keyboard_controller.press(Key.backspace)
            self.keyboard_controller.release(Key.backspace)
            
            logger.info("Text cleared")
            
        except Exception as e:
            logger.error(f"Failed to clear text: {e}")
    
    def format_selected_text(self, style: Optional[FormattingStyle] = None) -> None:
        """
        Format selected text
        
        Args:
            style: Formatting style to apply
        """
        try:
            if not self.current_context.selected_text:
                logger.warning("No text selected")
                return
            
            text = self.current_context.selected_text
            style = style or FormattingStyle.PLAIN
            
            # Apply formatting
            if style == FormattingStyle.TITLE_CASE:
                formatted = text.title()
            elif style == FormattingStyle.UPPER_CASE:
                formatted = text.upper()
            elif style == FormattingStyle.LOWER_CASE:
                formatted = text.lower()
            elif style == FormattingStyle.SENTENCE_CASE:
                formatted = text.capitalize()
            elif style == FormattingStyle.CAMEL_CASE:
                words = text.split()
                formatted = words[0].lower() + ''.join(w.title() for w in words[1:])
            elif style == FormattingStyle.PASCAL_CASE:
                formatted = ''.join(w.title() for w in text.split())
            elif style == FormattingStyle.SNAKE_CASE:
                formatted = '_'.join(text.lower().split())
            elif style == FormattingStyle.KEBAB_CASE:
                formatted = '-'.join(text.lower().split())
            else:
                formatted = text
            
            # Replace selected text
            self.type_with_keyboard(formatted)
            
            logger.info(f"Text formatted with {style.value}")
            
        except Exception as e:
            logger.error(f"Failed to format text: {e}")
    
    def correct_selected_text(self) -> None:
        """Correct selected text"""
        try:
            if not self.current_context.selected_text:
                logger.warning("No text selected")
                return
            
            text = self.current_context.selected_text
            corrected = self.auto_correct_text(text)
            
            # Replace with corrected text
            if corrected != text:
                # Delete selected text
                self.keyboard_controller.press(Key.backspace)
                self.keyboard_controller.release(Key.backspace)
                
                # Type corrected text
                self.type_with_keyboard(corrected)
                
                logger.info(f"Corrected text: {corrected}")
            else:
                logger.info("No corrections needed")
                
        except Exception as e:
            logger.error(f"Failed to correct text: {e}")
    
    def add_to_vocabulary(self, word: str, corrections: List[str]) -> None:
        """
        Add word to custom vocabulary
        
        Args:
            word: Word to add
            corrections: List of correct forms
        """
        try:
            self.custom_vocabulary[word.lower()] = corrections
            self.save_config()
            logger.info(f"Added '{word}' to vocabulary")
        except Exception as e:
            logger.error(f"Failed to add to vocabulary: {e}")
    
    def add_replacement(self, pattern: str, replacement: str) -> None:
        """
        Add auto-replacement rule
        
        Args:
            pattern: Pattern to match
            replacement: Replacement text
        """
        try:
            self.auto_replacements[pattern] = replacement
            self.save_config()
            logger.info(f"Added replacement: '{pattern}' -> '{replacement}'")
        except Exception as e:
            logger.error(f"Failed to add replacement: {e}")
    
    def update_metrics(self, result: DictationResult) -> None:
        """Update performance metrics"""
        try:
            self.metrics["total_dictations"] += 1
            self.metrics["total_characters"] += len(result.text)
            self.metrics["total_words"] += len(result.text.split())
            
            # Update average confidence
            total = self.metrics["average_confidence"] * (self.metrics["total_dictations"] - 1)
            total += result.confidence
            self.metrics["average_confidence"] = total / self.metrics["total_dictations"]
            
            # Update correction rate
            if result.confidence < self.confidence_threshold:
                corrections = self.metrics.get("corrections", 0) + 1
                self.metrics["correction_rate"] = corrections / self.metrics["total_dictations"]
            
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.metrics.copy()
    
    def get_context(self) -> TypingContext:
        """Get current typing context"""
        return self.current_context
    
    def set_typing_mode(self, mode: TypingMode) -> None:
        """
        Set typing mode
        
        Args:
            mode: Typing mode to set
        """
        self.current_mode = mode
        logger.info(f"Typing mode set to {mode.value}")
    
    def set_input_method(self, method: InputMethod) -> None:
        """
        Set default input method
        
        Args:
            method: Input method to set
        """
        self.default_method = method
        logger.info(f"Input method set to {method.value}")
    
    def set_language(self, language: DictationLanguage) -> None:
        """
        Set default dictation language
        
        Args:
            language: Language to set
        """
        self.default_language = language
        logger.info(f"Language set to {language.value}")
    
    def cleanup(self) -> None:
        """Cleanup resources"""
        try:
            self.is_typing = False
            self.is_paused = False
            
            # Clear queue
            while not self.typing_queue.empty():
                try:
                    self.typing_queue.get_nowait()
                except queue.Empty:
                    break
            
            # Save configuration
            self.save_config()
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Failed to cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()


# Example usage
if __name__ == "__main__":
    # Create voice typing manager
    manager = VoiceTypingManager()
    
    try:
        # Start dictation
        manager.start_dictation(DictationLanguage.ENGLISH_US)
        
        # Add custom vocabulary
        manager.add_to_vocabulary("pyautogui", ["pyautogui", "py-auto-gui"])
        
        # Add auto-replacement
        manager.add_replacement(r"\bpy\b", "Python")
        
        # Keep running
        time.sleep(60)
        
    except KeyboardInterrupt:
        print("\nStopping voice typing...")
    finally:
        # Cleanup
        manager.cleanup()