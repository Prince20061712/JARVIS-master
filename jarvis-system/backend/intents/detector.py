from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
import re
import logging
from difflib import SequenceMatcher
from collections import defaultdict
from utils.logger import logger

@dataclass
class Intent:
    type: str 
    name: str 
    confidence: float
    entities: Dict[str, Any]
    suggested_handler: str

class IntentDetector:
    def __init__(self):
        # Common misspellings and slang variations
        self.slang_dict = {
            'plz': 'please', 'pls': 'please', 'thx': 'thanks',
            'u': 'you', 'r': 'are', 'yr': 'your', 'btw': 'by the way',
            'wanna': 'want to', 'gonna': 'going to', 'gotta': 'got to',
            'lemme': 'let me', 'imma': 'i am going to', 'ain\'t': 'am not',
            'ya': 'you', 'yea': 'yes', 'nah': 'no', 'dunno': 'don\'t know',
            'kinda': 'kind of', 'sorta': 'sort of', 'wha': 'what',
            'playin': 'playing', 'watchin': 'watching', 'listenin': 'listening'
        }
        
        # Expanded patterns with variations for different English levels
        self.system_patterns = [
            # Open/Launch commands
            (r'(open|launch|start|run|boot up|fire up|load|get)\s+(?:the\s+)?(?:app\s+)?(.*)', 
             "open_app", "system"),
            (r'(go to|take me to|show me|bring up)\s+(?:the\s+)?(.*)', 
             "open_app", "system"),
            (r'(app|application)\s+(?:called\s+)?(.*)', 
             "open_app", "system"),
            
            # Search commands
            (r'(search|look up|find|google|check|browse)\s+(?:for\s+)?(?:info\s+about\s+)?(.*)', 
             "web_search", "system"),
            (r'(what|who|where|when|why|how)\s+(?:is|are|was|were)\s+(.*)', 
             "web_search", "system"),
            (r'(i need|i want|show me|tell me)\s+(?:info\s+)?(?:about\s+)?(.*)', 
             "web_search", "system"),
            
            # Media control - Play
            (r'(play|start|stream|put on|turn on)\s+(?:some\s+)?(?:music\s+)?(?:video\s+)?(?:of\s+)?(.*)', 
             "play_media", "system"),
            (r'(i want to|can you|please)\s+(?:play|listen to|watch)\s+(.*)', 
             "play_media", "system"),
            (r'(play me|show me|let\'s watch|let\'s listen to)\s+(.*)', 
             "play_media", "system"),
            
            # Media control - Pause/Stop
            (r'(pause|stop|halt|freeze|hold on|wait)', 
             "pause_media", "system"),
            (r'(stop the|pause the|halt the)\s+(?:music|video|media)', 
             "pause_media", "system"),
            
            # System control - Shutdown
            (r'(shutdown|shut down|turn off|power off|close down|exit)', 
             "shutdown_system", "system"),
            (r'(quit|end|terminate|stop)\s+(?:the\s+)?(?:system|computer|program)', 
             "shutdown_system", "system"),
            
            # System control - Restart
            (r'(restart|reboot|reset|start over|begin again)', 
             "restart_system", "system"),
            (r'(start|boot)\s+(?:over|again|from beginning)', 
             "restart_system", "system"),
            
            # System info
            (r'(system info|computer info|specs|specifications|details)', 
             "system_info", "system"),
            (r'(what is|tell me|show me)\s+(?:my\s+)?(?:computer|system|device)\s+(?:info|details|specs)', 
             "system_info", "system"),
            (r'(how much|what is)\s+(?:my\s+)?(?:ram|cpu|memory|storage|space)\s+(?:left|available|usage)', 
             "system_info", "system"),
        ]
        
        self.knowledge_patterns = [
            # Definitions
            (r'(what is|what\'s|define|definition of|meaning of|what does)\s+(?:the\s+)?(?:word\s+)?(.*)', 
             "definition", "knowledge"),
            (r'(explain|describe|tell about)\s+(?:the\s+)?(?:concept\s+of\s+)?(.*)', 
             "definition", "knowledge"),
            
            # Biography
            (r'(who is|who\'s|tell me about|biography of|info about)\s+(.*)', 
             "biography", "knowledge"),
            (r'(what do you know about|can you tell me about)\s+(.*)', 
             "biography", "knowledge"),
            
            # How-to instructions
            (r'(how to|how do i|how can i|steps to|way to|method to)\s+(.*)', 
             "howto", "knowledge"),
            (r'(i need to know how|teach me how|show me how)\s+(?:to\s+)?(.*)', 
             "howto", "knowledge"),
            
            # Explanations
            (r'(explain|elaborate on|break down|clarify)\s+(?:the\s+)?(.*)', 
             "explanation", "knowledge"),
            (r'(why is|why does|why do|how come|reason for)\s+(.*)', 
             "explanation", "knowledge"),
        ]
        
        # Common informal phrases and their formal equivalents
        self.informal_phrases = {
            'gimme': 'give me',
            'wanna': 'want to',
            'gonna': 'going to',
            'lemme': 'let me',
            'imma': 'i am going to',
            'dunno': 'don\'t know',
            'kinda': 'kind of',
            'sorta': 'sort of',
            'alot': 'a lot',
            'ur': 'your',
            'plz': 'please',
            'thx': 'thanks'
        }
        
        # Keyword-based intent mapping for simple commands
        self.keyword_intents = {
            'open': 'open_app',
            'launch': 'open_app',
            'start': 'open_app',
            'play': 'play_media',
            'search': 'web_search',
            'find': 'web_search',
            'what': 'web_search',
            'who': 'web_search',
            'how': 'howto',
            'explain': 'explanation',
            'define': 'definition',
            'shutdown': 'shutdown_system',
            'restart': 'restart_system',
            'pause': 'pause_media',
            'stop': 'pause_media'
        }
        
        # Partial word matching for typos
        self.word_variations = {
            'play': ['play', 'pla', 'pley', 'plai', 'paly'],
            'open': ['open', 'opn', 'opne', 'oppen'],
            'search': ['search', 'serch', 'seach', 'serach'],
            'what': ['what', 'wat', 'wht', 'whut'],
            'music': ['music', 'muzik', 'musik', 'muisc']
        }

    def normalize_text(self, text: str) -> str:
        """Normalize text by handling slang, abbreviations, and common mistakes"""
        text = text.lower().strip()
        
        # Replace common slang and abbreviations
        for slang, formal in self.slang_dict.items():
            text = re.sub(r'\b' + re.escape(slang) + r'\b', formal, text)
        
        # Handle common contractions
        text = re.sub(r"won\'t", "will not", text)
        text = re.sub(r"can\'t", "cannot", text)
        text = re.sub(r"n\'t", " not", text)
        text = re.sub(r"\'re", " are", text)
        text = re.sub(r"\'s", " is", text)
        text = re.sub(r"\'d", " would", text)
        text = re.sub(r"\'ll", " will", text)
        text = re.sub(r"\'ve", " have", text)
        text = re.sub(r"\'m", " am", text)
        
        # Remove filler words that don't affect meaning
        filler_words = ['like', 'um', 'uh', 'you know', 'i mean', 'actually', 'basically']
        for word in filler_words:
            text = re.sub(r'\b' + word + r'\b', '', text)
        
        # Fix common misspellings
        text = re.sub(r'\balot\b', 'a lot', text)
        text = re.sub(r'\bcould of\b', 'could have', text)
        text = re.sub(r'\bshould of\b', 'should have', text)
        text = re.sub(r'\bwould of\b', 'would have', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text

    def fuzzy_match(self, word: str, target_list: List[str], threshold: float = 0.7) -> Optional[str]:
        """Fuzzy matching for misspelled words"""
        for target in target_list:
            similarity = SequenceMatcher(None, word, target).ratio()
            if similarity >= threshold:
                return target
        return None

    def extract_entities_robust(self, text: str, pattern: str) -> Dict[str, Any]:
        """Extract entities even with imperfect grammar"""
        try:
            match = re.search(pattern, text)
            if match and match.groups():
                # Get the captured group (the entity)
                entity_text = match.group(len(match.groups()))
                
                # Clean up the entity text
                entity_text = entity_text.strip()
                
                # Remove common trailing phrases
                trailing_phrases = ['please', 'thanks', 'thank you', 'ok', 'okay', 'now']
                for phrase in trailing_phrases:
                    if entity_text.endswith(' ' + phrase):
                        entity_text = entity_text[:-len(phrase)].strip()
                
                return {"target": entity_text}
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
        
        return {}

    def detect_with_keywords(self, text: str) -> Optional[Intent]:
        """Fallback detection using keyword matching"""
        words = text.split()
        
        for word in words:
            # Check for direct keyword matches
            if word in self.keyword_intents:
                # Determine intent type based on keyword
                if word in ['open', 'launch', 'start']:
                    intent_type = 'system'
                    handler = 'system'
                elif word in ['play', 'pause', 'stop']:
                    intent_type = 'system'
                    handler = 'system'
                elif word in ['search', 'find']:
                    intent_type = 'system'
                    handler = 'system'
                elif word in ['what', 'who']:
                    intent_type = 'knowledge'
                    handler = 'knowledge'
                elif word in ['how', 'explain', 'define']:
                    intent_type = 'knowledge'
                    handler = 'knowledge'
                else:
                    intent_type = 'system'
                    handler = 'system'
                
                return Intent(
                    type=intent_type,
                    name=self.keyword_intents[word],
                    confidence=0.6,  # Lower confidence for keyword-only match
                    entities={"text": text},
                    suggested_handler=handler
                )
        
        return None

    def detect(self, text: str) -> Intent:
        """Enhanced intent detection with support for various English levels"""
        original_text = text
        text = self.normalize_text(text)
        
        logger.info(f"Processing: '{original_text}' -> Normalized: '{text}'")
        
        # 1. Try pattern matching with normalized text
        for pattern, intent_name, handler in self.system_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities = self.extract_entities_robust(text, pattern)
                confidence = 0.9 if len(entities) > 0 else 0.7
                
                return Intent(
                    type="system",
                    name=intent_name,
                    confidence=confidence,
                    entities=entities,
                    suggested_handler=handler
                )
        
        # 2. Try knowledge patterns
        for pattern, intent_name, handler in self.knowledge_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities = self.extract_entities_robust(text, pattern)
                
                return Intent(
                    type="knowledge",
                    name=intent_name,
                    confidence=0.85,
                    entities=entities,
                    suggested_handler=handler
                )
        
        # 3. Try keyword-based detection
        keyword_intent = self.detect_with_keywords(text)
        if keyword_intent:
            return keyword_intent
        
        # 4. Handle very short or informal commands
        short_commands = {
            'open': ('open_app', 'system'),
            'play': ('play_media', 'system'),
            'search': ('web_search', 'system'),
            'find': ('web_search', 'system'),
            'what': ('web_search', 'system'),
            'who': ('biography', 'knowledge'),
            'how': ('howto', 'knowledge'),
            'explain': ('explanation', 'knowledge'),
        }
        
        for cmd, (intent_name, handler) in short_commands.items():
            if text.startswith(cmd + ' ') or text == cmd:
                # Extract what comes after the command
                parts = text.split(' ', 1)
                entities = {"target": parts[1]} if len(parts) > 1 else {}
                
                return Intent(
                    type="system" if handler == "system" else "knowledge",
                    name=intent_name,
                    confidence=0.65,
                    entities=entities,
                    suggested_handler=handler
                )
        
        # 5. Check for question words (fallback for very informal queries)
        question_words = ['what', 'who', 'where', 'when', 'why', 'how']
        if any(text.startswith(word) for word in question_words):
            return Intent(
                type="knowledge",
                name="general_query",
                confidence=0.5,
                entities={"query": text},
                suggested_handler="knowledge"
            )
        
        # 6. Check for imperative commands without clear intent
        if text.endswith('please') or any(word in text for word in ['can you', 'could you', 'would you']):
            return Intent(
                type="chat",
                name="polite_command",
                confidence=0.4,
                entities={"text": text, "original": original_text},
                suggested_handler="chat"
            )
        
        # 7. Ultimate fallback to Chat
        return Intent(
            type="chat",
            name="conversation",
            confidence=0.3,
            entities={
                "text": text,
                "original_text": original_text,
                "normalized": text
            },
            suggested_handler="chat"
        )

# Example usage and test cases
def test_intent_detector():
    detector = IntentDetector()
    
    test_cases = [
        # Formal English
        "Could you please open the Chrome browser for me?",
        "I would like to search for information about artificial intelligence",
        
        # Informal English
        "open chrome plz",
        "play some music",
        "search for cats",
        
        # Very informal / low-level English
        "gimme chrome",
        "wanna listen to music",
        "search cats",
        "play song",
        "open app",
        
        # With slang and abbreviations
        "plz open youtube",
        "thx play music",
        "wanna watch video",
        
        # Short commands
        "open",
        "play",
        "search",
        
        # With typos
        "opne chrome",
        "pla music",
        "serch internet",
        
        # Mixed grammar
        "me want open chrome",
        "chrome open please",
        "music play now",
        
        # Question forms
        "what is ai",
        "how to cook",
        "who is elon musk",
    ]
    
    print("Testing Enhanced Intent Detector:")
    print("=" * 50)
    
    for test in test_cases:
        intent = detector.detect(test)
        print(f"\nInput: '{test}'")
        print(f"Intent: {intent.name} (Type: {intent.type})")
        print(f"Confidence: {intent.confidence:.2f}")
        print(f"Entities: {intent.entities}")
        print(f"Handler: {intent.suggested_handler}")

if __name__ == "__main__":
    test_intent_detector()