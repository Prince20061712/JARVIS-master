"""
Adapts JARVIS's responses based on emotional understanding
"""

from typing import Dict, Any, Optional, List
import random

class EmotionalResponseAdapter:
    """
    Adapts responses based on detected emotional state
    Provides emotionally intelligent communication
    """
    
    def __init__(self):
        self.response_templates = self._load_templates()
        self.emotional_memory = {}
        
    def _load_templates(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Load response templates for different emotional contexts
        """
        return {
            # Joy/happiness responses
            "joy": {
                "acknowledgment": [
                    "I'm glad to see you're enjoying this!",
                    "Your enthusiasm is wonderful!",
                    "It's great to see you so engaged!",
                    "Your excitement is contagious!"
                ],
                "encouragement": [
                    "Keep up this great momentum!",
                    "You're doing fantastic work!",
                    "This positive energy will help you learn even better!",
                    "You're making excellent progress!"
                ],
                "deepening": [
                    "Would you like to explore this topic further?",
                    "I have some fascinating related concepts to share!",
                    "There's an advanced aspect to this if you're interested.",
                    "This connects to several other interesting topics."
                ]
            },
            
            # Frustration responses
            "frustration": {
                "acknowledgment": [
                    "I understand this can be frustrating.",
                    "Many students find this challenging at first.",
                    "It's normal to feel stuck sometimes.",
                    "This is a tricky concept, but you can master it."
                ],
                "encouragement": [
                    "Let's take a step back and try a different approach.",
                    "You've mastered difficult concepts before - you can do this too.",
                    "Every expert was once a beginner who kept trying.",
                    "The breakthrough often comes right after the frustration."
                ],
                "strategy": [
                    "Would it help to see a simpler example?",
                    "Should we break this down into smaller steps?",
                    "Maybe we could try a visual explanation.",
                    "I could show you a different perspective on this."
                ]
            },
            
            # Anxiety/stress responses
            "anxiety": {
                "calming": [
                    "Take a deep breath. We'll work through this together.",
                    "There's no pressure - we can go at whatever pace works for you.",
                    "Remember that learning is a journey, not a race.",
                    "You're in a safe space to learn and make mistakes."
                ],
                "reassurance": [
                    "You've prepared well for this.",
                    "You have the foundation to understand this.",
                    "I'm here to help you every step of the way.",
                    "We'll make sure you're ready before any exam."
                ],
                "grounding": [
                    "Let's focus on just this one step right now.",
                    "What's one small thing we can tackle first?",
                    "We don't need to solve everything at once.",
                    "Let's start with what you already know."
                ]
            },
            
            # Curiosity responses
            "curiosity": {
                "encouragement": [
                    "That's an excellent question!",
                    "I love your curiosity!",
                    "Great observation!",
                    "You're thinking like a true engineer!"
                ],
                "exploration": [
                    "Let me show you something interesting about that...",
                    "This connects to several fascinating concepts...",
                    "There's a deeper layer to this if you're ready...",
                    "This actually relates to real-world applications like..."
                ],
                "resources": [
                    "Would you like to explore some additional resources on this?",
                    "I can suggest some related topics you might find interesting.",
                    "There are some great examples of this in action.",
                    "This principle appears in many engineering fields."
                ]
            },
            
            # Sadness/discouragement responses
            "sadness": {
                "comfort": [
                    "I understand. Learning isn't always easy.",
                    "It's okay to feel discouraged sometimes.",
                    "Your feelings are completely valid.",
                    "Everyone has challenging days."
                ],
                "perspective": [
                    "Remember how far you've already come.",
                    "Think about the concepts you've already mastered.",
                    "Every step forward, no matter how small, is progress.",
                    "You're building understanding that will last."
                ],
                "hope": [
                    "Tomorrow is a fresh opportunity to learn.",
                    "This challenge will make your understanding stronger.",
                    "The difficult parts often become our strongest knowledge.",
                    "You have the ability to overcome this."
                ]
            },
            
            # Burnout responses
            "burnout": {
                "validation": [
                    "You've been working really hard.",
                    "It's completely normal to feel exhausted.",
                    "Your dedication is impressive, but rest is important too.",
                    "Even the best engineers need breaks."
                ],
                "self_care": [
                    "How about taking a short break?",
                    "Maybe step away for 15 minutes and come back refreshed.",
                    "Your brain needs rest to consolidate learning.",
                    "Would you like to switch to something lighter?"
                ],
                "recovery": [
                    "When you're ready, we can pick up where you left off.",
                    "I'll be here whenever you're ready to continue.",
                    "Sometimes the best thing for learning is rest.",
                    "You'll come back stronger after a break."
                ]
            },
            
            # Breakthrough/excitement responses
            "breakthrough": {
                "celebration": [
                    "That's it! You've got it!",
                    "Brilliant! That's exactly right!",
                    "Excellent! You made the connection!",
                    "Perfect! That understanding will stick with you!"
                ],
                "reinforcement": [
                    "You've just mastered a key concept.",
                    "This understanding will help with many related topics.",
                    "You've built a strong foundation now.",
                    "This is a significant step in your learning."
                ],
                "momentum": [
                    "What would you like to explore next?",
                    "You're on a roll - shall we continue?",
                    "This momentum is perfect for tackling the next concept.",
                    "Your confidence is growing - let's build on it!"
                ]
            },
            
            # Confusion responses
            "confusion": {
                "normalizing": [
                    "This concept trips up many students at first.",
                    "It's completely normal to feel confused here.",
                    "The confusion means you're engaging deeply with the material.",
                    "Let's untangle this together."
                ],
                "clarifying": [
                    "Let me explain that differently.",
                    "Here's another way to think about it...",
                    "Maybe a concrete example would help.",
                    "What part is most confusing?"
                ],
                "checking": [
                    "Should we review the prerequisites for this?",
                    "Would it help to start with a simpler version?",
                    "Do you want me to break this down step by step?",
                    "Should we try a different teaching approach?"
                ]
            }
        }
    
    def adapt_response(self, 
                      base_response: str,
                      emotional_state: Dict[str, Any],
                      context: Dict[str, Any]) -> str:
        """
        Adapt the base response based on emotional state
        """
        emotion = emotional_state.get('primary_emotion', 'neutral')
        intensity = emotional_state.get('intensity', 0.0)
        
        # Don't adapt for neutral or low intensity
        if emotion == 'neutral' or intensity < 0.3:
            return base_response
        
        # Get templates for this emotion
        templates = self.response_templates.get(emotion, {})
        if not templates:
            return base_response
        
        # Build adapted response
        adapted_parts = []
        
        # Add acknowledgment based on emotion
        if intensity > 0.4 and 'acknowledgment' in templates:
            adapted_parts.append(random.choice(templates['acknowledgment']))
        
        # Add main response (slightly modified based on emotion)
        adapted_parts.append(self._modify_base_response(base_response, emotion))
        
        # Add emotional support based on intensity
        if intensity > 0.6:
            if emotion in ['frustration', 'anxiety', 'sadness']:
                if 'encouragement' in templates:
                    adapted_parts.append(random.choice(templates['encouragement']))
            elif emotion in ['curiosity', 'joy']:
                if 'exploration' in templates:
                    adapted_parts.append(random.choice(templates['exploration']))
        
        # Add strategy if relevant
        if emotion in ['frustration', 'confusion'] and 'strategy' in templates:
            if intensity > 0.5:
                adapted_parts.append(random.choice(templates['strategy']))
        
        # Add calming for high anxiety
        if emotion == 'anxiety' and intensity > 0.7:
            if 'calming' in templates:
                adapted_parts.insert(0, random.choice(templates['calming']))
        
        # Combine parts
        return ' '.join(adapted_parts)
    
    def _modify_base_response(self, response: str, emotion: str) -> str:
        """
        Slightly modify base response tone based on emotion
        """
        # Add emotional prefixes/suffixes
        emotional_modifiers = {
            'joy': ["! ", " 😊 ", " ✨ "],
            'frustration': [". I know this is tough. ", ". Let's work through it. "],
            'anxiety': [". Remember to breathe. ", ". Take your time. "],
            'curiosity': ["? That's interesting! ", ". Let's explore that! "],
            'sadness': [". It's okay. ", ". You're doing fine. "],
            'breakthrough': ["! You've got it! ", "! Excellent! "],
            'confusion': [". Let me clarify. ", ". Here's another way: "]
        }
        
        if emotion in emotional_modifiers:
            modifier = random.choice(emotional_modifiers[emotion])
            # Don't modify if response already has emotional tone
            if not any(m.strip() in response for m in emotional_modifiers[emotion]):
                response = response + modifier
        
        return response
    
    def generate_proactive_message(self, emotional_state: Dict[str, Any]) -> Optional[str]:
        """
        Generate proactive emotional support messages
        """
        emotion = emotional_state.get('primary_emotion', 'neutral')
        intensity = emotional_state.get('intensity', 0.0)
        trend = emotional_state.get('recent_trend', 'stable')
        
        # Proactive messages for sustained negative emotions
        if emotion in ['frustration', 'anxiety', 'sadness'] and intensity > 0.5:
            if trend == 'declining':
                # Getting worse - intervene
                templates = self.response_templates.get(emotion, {})
                if 'encouragement' in templates:
                    return random.choice(templates['encouragement'])
            
            elif trend == 'stable' and intensity > 0.6:
                # Sustained high negative emotion - suggest break
                return "You've been working through some challenging material. Would you like to take a short break or try a different approach?"
        
        # Celebrate sustained positive emotions
        elif emotion in ['joy', 'breakthrough'] and intensity > 0.6:
            if trend == 'improving':
                return "Your progress is amazing! Keep up this great momentum!"
        
        return None
