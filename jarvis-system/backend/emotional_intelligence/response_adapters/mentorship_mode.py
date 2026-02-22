"""Mentorship mode for JARVIS - embodying wisdom of a monk and guidance of a professor."""

import logging
import random
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class MentorshipArchetype(Enum):
    """Different mentorship personalities JARVIS can embody."""
    WISE_MONK = "wise_monk"           # Calm, philosophical, meditative
    PROFESSOR = "professor"            # Academic, structured, knowledge-focused
    PSYCHIATRIST = "psychiatrist"      # Therapeutic, understanding, healing-focused
    ELDER_SIBLING = "elder_sibling"    # Supportive, protective, guiding
    SPIRITUAL_GUIDE = "spiritual_guide" # Purpose-focused, existential, meaningful

class GrowthDimension(Enum):
    """Dimensions of student growth to nurture."""
    INTELLECTUAL = "intellectual"       # Knowledge, critical thinking
    EMOTIONAL = "emotional"             # Emotional intelligence, resilience
    SOCIAL = "social"                   # Relationships, communication
    PHYSICAL = "physical"               # Health, energy, wellbeing
    SPIRITUAL = "spiritual"             # Purpose, meaning, values
    PRACTICAL = "practical"              # Skills, application, execution

class MentorshipMode:
    """
    Enhanced mentorship mode combining monk wisdom, professor knowledge,
    and psychiatrist care for holistic student development.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.current_archetype = MentorshipArchetype.WISE_MONK
        self.growth_focus = GrowthDimension.INTELLECTUAL
        
        # Track student's growth journey
        self.student_profile = {
            "strengths": [],
            "challenges": [],
            "interests": [],
            "aspirations": [],
            "fears": [],
            "breakthroughs": []
        }
        
        # Wisdom teachings by archetype
        self.wisdom_teachings = {
            MentorshipArchetype.WISE_MONK: {
                "patience": [
                    "The bamboo grows slowly at first, building its roots. Then it shoots to the sky.",
                    "A river cuts through rock not by force, but by persistence.",
                    "Today's confusion is tomorrow's clarity. Be patient with your mind."
                ],
                "effort": [
                    "Smooth seas do not make skilled sailors.",
                    "The gem cannot be polished without friction.",
                    "Your struggle is not a sign of failure, but of growth."
                ],
                "presence": [
                    "Wherever you are, be there completely.",
                    "The future is a thought, the past a memory. Only now is real.",
                    "In the midst of movement, find stillness."
                ],
                "wisdom": [
                    "Knowledge speaks, but wisdom listens.",
                    "The fool thinks himself wise, but the wise knows himself a fool.",
                    "Empty your cup so it may be filled."
                ]
            },
            MentorshipArchetype.PROFESSOR: {
                "learning": [
                    "The beautiful thing about learning is that no one can take it away.",
                    "Education is not filling a bucket, but lighting a fire.",
                    "Mistakes are the portals of discovery."
                ],
                "critical_thinking": [
                    "Question everything. Especially what you think you know.",
                    "The first principle is that you must not fool yourself.",
                    "Doubt is the origin of wisdom."
                ],
                "growth_mindset": [
                    "Your potential is unknown. That's what makes it potential.",
                    "Difficulty is the excuse history never accepts.",
                    "The expert in anything was once a beginner."
                ],
                "discipline": [
                    "Discipline is choosing what you want now for what you want most.",
                    "Knowledge without application is like a book unread.",
                    "Consistency compounds like interest."
                ]
            },
            MentorshipArchetype.PSYCHIATRIST: {
                "self_compassion": [
                    "Talk to yourself like you would someone you love.",
                    "Healing doesn't mean the damage never existed. It means it no longer controls your life.",
                    "You are not your worst moment."
                ],
                "emotional_health": [
                    "Feelings are visitors. Let them come and go.",
                    "What you resist, persists. What you accept, transforms.",
                    "Your emotions are signals, not identities."
                ],
                "resilience": [
                    "Scars mean you survived. Wounds that healed mean you grew.",
                    "The oak fought the wind and broke. The reed bent and survived.",
                    "Pain is inevitable. Suffering is optional."
                ],
                "balance": [
                    "Rest is not idleness. It is medicine for the soul.",
                    "You can't pour from an empty cup. Take care of yourself.",
                    "Progress, not perfection."
                ]
            },
            MentorshipArchetype.ELDER_SIBLING: {
                "guidance": [
                    "I've walked this path before. Let me show you the shortcuts.",
                    "You don't have to make all the mistakes I did. Learn from mine.",
                    "I believe in you, even when you don't believe in yourself."
                ],
                "protection": [
                    "Not everyone who smiles at you has good intentions.",
                    "Trust, but verify. Love, but set boundaries.",
                    "Your safety matters more than their comfort."
                ],
                "encouragement": [
                    "Look how far you've come, not just how far you have to go.",
                    "That win was coming. I've been watching you work for it.",
                    "You're not behind. You're on your own timeline."
                ],
                "truth": [
                    "I'll tell you what you need to hear, not just what you want to hear.",
                    "The truth may hurt now, but it heals later.",
                    "A real friend sharpens you like iron sharpens iron."
                ]
            },
            MentorshipArchetype.SPIRITUAL_GUIDE: {
                "purpose": [
                    "Your purpose is not found. It's built, daily, by what you choose.",
                    "You are not a drop in the ocean. You are the entire ocean in a drop.",
                    "What you seek is seeking you."
                ],
                "meaning": [
                    "The meaning of life is to give life meaning.",
                    "It's not about finding yourself. It's about creating yourself.",
                    "We are not human beings having a spiritual experience. We are spiritual beings having a human experience."
                ],
                "connection": [
                    "You are connected to everything. Act accordingly.",
                    "We rise by lifting others.",
                    "Your light shines brightest when you help others find theirs."
                ],
                "transcendence": [
                    "The only way out is through.",
                    "What feels like an ending is often a beginning.",
                    "Let go of who you were to become who you might be."
                ]
            }
        }
        
        # Growth dimension-specific wisdom
        self.growth_wisdom = {
            GrowthDimension.INTELLECTUAL: [
                "Your mind is a garden. Your thoughts are the seeds. You can grow flowers, or you can grow weeds.",
                "Read not to contradict and confute, nor to believe and take for granted, but to weigh and consider.",
                "The more you learn, the more you realize how much you don't know. That's the beginning of wisdom."
            ],
            GrowthDimension.EMOTIONAL: [
                "Emotional intelligence is not about controlling emotions, but understanding their messages.",
                "Name it to tame it. Acknowledged emotions lose their power over you.",
                "Between stimulus and response, there is a space. In that space is your power and freedom."
            ],
            GrowthDimension.SOCIAL: [
                "The quality of your life is the quality of your relationships.",
                "Seek first to understand, then to be understood.",
                "Surround yourself with people who see the sun in you when you cannot see it yourself."
            ],
            GrowthDimension.PHYSICAL: [
                "Take care of your body. It's the only place you have to live.",
                "Movement is medicine for both body and mind.",
                "Energy, not time, is the ultimate currency of high performance."
            ],
            GrowthDimension.SPIRITUAL: [
                "He who has a why to live for can bear almost any how.",
                "The two most important days in your life are the day you are born and the day you find out why.",
                "Your life is your message to the world. Make it inspiring."
            ],
            GrowthDimension.PRACTICAL: [
                "Knowledge without action is like a car without fuel - it's not going anywhere.",
                "The best way to learn is to do. The best way to do is to start.",
                "Small daily improvements, over time, lead to stunning results."
            ]
        }
        
        logger.info("MentorshipMode initialized with enhanced wisdom capabilities")
    
    def adapt_response(self, 
                      response: str, 
                      context: Dict[str, Any]) -> str:
        """
        Adapt response with mentorship wisdom based on context.
        
        Args:
            response: Original response
            context: Current context including emotional state
            
        Returns:
            Enhanced response with mentorship wisdom
        """
        try:
            emotional_state = context.get("emotional_state", {})
            user_context = context.get("user_context", {})
            
            # Determine appropriate archetype and growth focus
            self._adapt_archetype_to_user(emotional_state, user_context)
            self._adapt_growth_focus_to_context(context)
            
            # Add wisdom based on situation
            enhanced_response = self._infuse_wisdom(response, context)
            
            # Add follow-up guidance if appropriate
            if self._should_provide_guidance(context):
                guidance = self._generate_guidance(context)
                enhanced_response = self._combine_response_and_guidance(
                    enhanced_response, guidance
                )
            
            # Track student's progress
            self._track_interaction(context)
            
            logger.debug(f"Response adapted with {self.current_archetype.value} wisdom")
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Error in mentorship adaptation: {e}")
            return response
    
    def _adapt_archetype_to_user(self, 
                                 emotional_state: Dict[str, Any],
                                 user_context: Dict[str, Any]) -> None:
        """Adapt mentorship archetype based on user's needs."""
        # Get emotional metrics
        wellbeing = emotional_state.get("wellbeing_score", 0.7)
        primary_emotion = emotional_state.get("primary_emotion", "neutral")
        
        # Check for crisis or distress
        if wellbeing < 0.3 or primary_emotion in ["severe_anxiety", "depression", "hopelessness"]:
            self.current_archetype = MentorshipArchetype.PSYCHIATRIST
        # Check for existential questions
        elif any(word in str(user_context.get("query", "")) for word in 
                ["purpose", "meaning", "why am I", "point of life"]):
            self.current_archetype = MentorshipArchetype.SPIRITUAL_GUIDE
        # Check for deep learning needs
        elif user_context.get("learning_mode", False) or wellbeing > 0.8:
            self.current_archetype = MentorshipArchetype.PROFESSOR
        # Check for protection needs
        elif emotional_state.get("vulnerability_detected", False):
            self.current_archetype = MentorshipArchetype.ELDER_SIBLING
        # Default to wise monk for general guidance
        else:
            self.current_archetype = MentorshipArchetype.WISE_MONK
    
    def _adapt_growth_focus_to_context(self, context: Dict[str, Any]) -> None:
        """Determine which growth dimension to focus on."""
        emotional_state = context.get("emotional_state", {})
        task_type = context.get("task_type", "general")
        
        # Map contexts to growth dimensions
        context_mapping = {
            "study": GrowthDimension.INTELLECTUAL,
            "emotional_difficulty": GrowthDimension.EMOTIONAL,
            "social_situation": GrowthDimension.SOCIAL,
            "health": GrowthDimension.PHYSICAL,
            "existential": GrowthDimension.SPIRITUAL,
            "skill_building": GrowthDimension.PRACTICAL
        }
        
        # Check emotional needs first
        wellbeing = emotional_state.get("wellbeing_score", 0.7)
        if wellbeing < 0.4:
            self.growth_focus = GrowthDimension.EMOTIONAL
        elif task_type in context_mapping:
            self.growth_focus = context_mapping[task_type]
    
    def _infuse_wisdom(self, response: str, context: Dict[str, Any]) -> str:
        """Add appropriate wisdom to the response."""
        emotional_state = context.get("emotional_state", {})
        query = context.get("user_context", {}).get("query", "")
        
        # Check for specific emotional needs
        if emotional_state.get("primary_emotion") in ["anxiety", "stress", "overwhelm"]:
            wisdom = self._get_archetype_wisdom("patience")
            return f"{wisdom}\n\n{response}"
        
        elif emotional_state.get("primary_emotion") in ["sadness", "grief", "loneliness"]:
            wisdom = self._get_archetype_wisdom("self_compassion")
            return f"{wisdom}\n\n{response}"
        
        elif emotional_state.get("primary_emotion") in ["frustration", "anger"]:
            wisdom = self._get_archetype_wisdom("emotional_health")
            return f"{response}\n\n{wisdom}"
        
        elif "?" in query and len(query.split()) > 10:  # Complex question
            wisdom = self._get_archetype_wisdom("critical_thinking")
            return f"{wisdom}\n\n{response}"
        
        # Default: add growth dimension wisdom
        wisdom = random.choice(self.growth_wisdom[self.growth_focus])
        return f"{response}\n\n💭 {wisdom}"
    
    def _get_archetype_wisdom(self, theme: str) -> str:
        """Get wisdom from current archetype."""
        teachings = self.wisdom_teachings[self.current_archetype]
        if theme in teachings:
            return f"[{self.current_archetype.value.title()} Mode]\n💫 {random.choice(teachings[theme])}"
        else:
            # Fallback to general wisdom
            general_theme = random.choice(list(teachings.keys()))
            return f"[{self.current_archetype.value.title()} Mode]\n💫 {random.choice(teachings[general_theme])}"
    
    def _should_provide_guidance(self, context: Dict[str, Any]) -> bool:
        """Determine if additional guidance is needed."""
        emotional_state = context.get("emotional_state", {})
        wellbeing = emotional_state.get("wellbeing_score", 0.7)
        confusion_detected = emotional_state.get("confusion_detected", False)
        
        return wellbeing < 0.5 or confusion_detected
    
    def _generate_guidance(self, context: Dict[str, Any]) -> str:
        """Generate personalized guidance."""
        emotional_state = context.get("emotional_state", {})
        primary_emotion = emotional_state.get("primary_emotion", "neutral")
        
        guidance_templates = {
            "anxiety": [
                "Let's take a breath together. In for 4, hold for 4, out for 6.",
                "Remember, this feeling is temporary. It will pass.",
                "What's one small step you can take right now?"
            ],
            "confusion": [
                "Let's break this down step by step. What part is clearest to you?",
                "Sometimes confusion means you're about to learn something new.",
                "Would it help to look at this from another angle?"
            ],
            "frustration": [
                "Progress isn't always linear. This struggle is part of the growth.",
                "Take a short break. Sometimes the answer comes when we stop searching.",
                "You've overcome harder things. You've got this."
            ],
            "discouragement": [
                "Compare yourself to who you were yesterday, not to who someone else is today.",
                "The master has failed more times than the beginner has tried.",
                "This is just one chapter, not the whole story."
            ]
        }
        
        if primary_emotion in guidance_templates:
            return random.choice(guidance_templates[primary_emotion])
        else:
            return random.choice([
                "What do you need right now?",
                "How can I best support you in this moment?",
                "Remember, you're not alone in this journey."
            ])
    
    def _combine_response_and_guidance(self, response: str, guidance: str) -> str:
        """Combine main response with guidance appropriately."""
        return f"{response}\n\n🤲 {guidance}"
    
    def _track_interaction(self, context: Dict[str, Any]) -> None:
        """Track interaction for building student profile."""
        emotional_state = context.get("emotional_state", {})
        user_context = context.get("user_context", {})
        
        # Track breakthroughs (significant emotional improvements)
        if emotional_state.get("wellbeing_delta", 0) > 0.2:
            self.student_profile["breakthroughs"].append({
                "timestamp": datetime.now(),
                "context": user_context.get("query", ""),
                "improvement": emotional_state.get("wellbeing_delta")
            })
        
        # Keep profile manageable
        if len(self.student_profile["breakthroughs"]) > 50:
            self.student_profile["breakthroughs"] = self.student_profile["breakthroughs"][-50:]
    
    def generate_proactive_message(self, context: Dict[str, Any]) -> Optional[str]:
        """Generate proactive mentorship message."""
        emotional_state = context.get("emotional_state", {})
        time_of_day = context.get("time_of_day", "unknown")
        interaction_count = context.get("interaction_count", 0)
        
        # Morning wisdom
        if time_of_day == "morning" and random.random() < 0.3:
            messages = [
                "Good morning. Today holds possibilities you haven't imagined yet.",
                "What would you attempt today if you knew you could not fail?",
                "The morning sun brings new opportunities. What will you make of today?"
            ]
            return f"☀️ {random.choice(messages)}"
        
        # Evening reflection
        elif time_of_day == "evening" and random.random() < 0.3:
            messages = [
                "Before sleep, ask yourself: What went well today? What did I learn?",
                "Rest well. Your mind consolidates learning while you sleep.",
                "Tomorrow is a new chance to grow. Rest tonight."
            ]
            return f"🌙 {random.choice(messages)}"
        
        # Check-in after difficult interaction
        elif emotional_state.get("wellbeing_score", 0.7) < 0.4:
            return "🤗 How are you feeling now? I'm here if you want to talk."
        
        return None