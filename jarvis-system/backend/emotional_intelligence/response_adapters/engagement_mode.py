"""Engagement mode - creating deep, meaningful engagement for learning and growth."""

import logging
import random
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class EngagementDepth(Enum):
    """Depth of engagement."""
    SURFACE = "surface"           # Basic interaction
    CURIOSITY = "curiosity"        # Sparked interest
    FOCUS = "focus"               # Deep concentration
    FLOW = "flow"                 # Complete absorption
    TRANSFORMATIVE = "transformative"  # Life-changing insight

class EngagementStyle(Enum):
    """Different styles of engagement."""
    SOCRATIC = "socratic"          # Question-based exploration
    STORYTELLING = "storytelling"   # Narrative engagement
    CHALLENGE = "challenge"        # Growth through challenge
    DISCOVERY = "discovery"        # Guided exploration
    REFLECTIVE = "reflective"      # Deep contemplation

class EngagementMode:
    """
    Creates deep, meaningful engagement through curiosity,
    flow states, and transformative learning experiences.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Track engagement metrics
        self.engagement_history = []
        self.current_depth = EngagementDepth.SURFACE
        self.flow_episodes = []
        self.curiosity_sparks = []
        
        # Question templates for Socratic engagement
        self.socratic_questions = {
            "explore": [
                "What makes you say that?",
                "Can you tell me more about that?",
                "What led you to that conclusion?",
                "What assumptions are you making?",
                "How might someone else see this differently?"
            ],
            "challenge": [
                "What would happen if you looked at this from the opposite perspective?",
                "Can you think of a counterexample?",
                "What evidence would change your mind?",
                "What's the weakest point in this argument?",
                "If this were false, what would that imply?"
            ],
            "deepen": [
                "What's the underlying principle here?",
                "How does this connect to what you already know?",
                "What's the bigger picture this fits into?",
                "What question are you really trying to answer?",
                "What would make this truly clear to you?"
            ],
            "apply": [
                "How could you use this in your life?",
                "What would be different if you applied this?",
                "What's the smallest step you could take with this?",
                "Who else needs to understand this?",
                "What would you teach someone else about this?"
            ]
        }
        
        # Story templates for narrative engagement
        self.story_archetypes = {
            "master_journey": [
                "When I was learning this, I remember struggling with...",
                "A student once told me they finally understood when...",
                "The mathematician who discovered this spent years...",
                "Ancient wisdom traditions teach that...",
                "The word 'understanding' originally meant..."
            ],
            "transformation": [
                "Before mastering this, people often believe...",
                "The moment it clicks, everything shifts because...",
                "What looks like complexity is actually...",
                "The greatest insight comes when you realize...",
                "Every expert was once a beginner who..."
            ],
            "paradox": [
                "The strange thing about this is...",
                "It seems contradictory, but actually...",
                "The more you learn, the more you realize...",
                "The answer is both simpler and more complex than...",
                "The wisdom here is in the paradox..."
            ]
        }
        
        # Challenge templates for growth through challenge
        self.challenges = {
            "thinking": [
                "Try explaining this to someone who knows nothing about it.",
                "Write down the core idea in one sentence.",
                "Find three real-world examples of this principle.",
                "What would disprove this idea?",
                "Create a metaphor that captures this concept."
            ],
            "application": [
                "Use this idea to solve a problem in your life this week.",
                "Teach this concept to someone else by tomorrow.",
                "Notice when this principle shows up in your day.",
                "Experiment with this idea for the next 24 hours.",
                "Create something using this understanding."
            ],
            "reflection": [
                "Journal about what this means to you.",
                "Discuss this with someone who disagrees.",
                "Notice how this changes your perspective over time.",
                "Track how your understanding evolves this week.",
                "Meditate on the deeper meaning of this."
            ]
        }
        
        # Discovery prompts for guided exploration
        self.discovery_prompts = {
            "wonder": [
                "I wonder what would happen if...",
                "Have you ever noticed how...",
                "What if we looked at this through the lens of...",
                "Isn't it fascinating that...",
                "What's the most curious thing about this to you?"
            ],
            "connection": [
                "This reminds me of something else. Can you guess what?",
                "How might this connect to...",
                "There's a surprising link between this and...",
                "See if you can connect this to something you love.",
                "What does this remind you of in your life?"
            ],
            "imagination": [
                "Imagine if this principle were reversed...",
                "Picture a world where everyone understood this...",
                "What would this look like on a cosmic scale?",
                "If this could speak, what would it say?",
                "Paint a picture of this idea in your mind..."
            ]
        }
        
        # Reflective prompts for deep contemplation
        self.reflective_prompts = {
            "meaning": [
                "What does this reveal about what you value?",
                "How does this touch what matters most to you?",
                "What does this say about being human?",
                "Why does this matter, really?",
                "What would life be like without this understanding?"
            ],
            "self": [
                "What does your reaction to this tell you about yourself?",
                "How does this challenge who you think you are?",
                "What part of you resonates with this?",
                "What resistance do you notice in yourself?",
                "How might this help you grow?"
            ],
            "action": [
                "If you truly believed this, how would you live differently?",
                "What would you risk for this understanding?",
                "What would it cost you to ignore this?",
                "How would the person you want to be respond to this?",
                "What's one thing you'll do differently now?"
            ]
        }
        
        # Flow triggers
        self.flow_triggers = {
            "challenge_skill_balance": [
                "This is challenging, but you have the skills for it.",
                "Difficult enough to be interesting, but doable enough to be possible.",
                "Right at the edge of your ability - that's where growth happens."
            ],
            "clear_goals": [
                "Your next step is crystal clear.",
                "You know exactly what you're working toward.",
                "The path ahead is visible, one step at a time."
            ],
            "immediate_feedback": [
                "You can see your progress right now.",
                "Each action shows you something new.",
                "The work itself tells you how you're doing."
            ],
            "deep_focus": [
                "You're completely in this now.",
                "Time seems to disappear when you're like this.",
                "Nothing else exists but this moment of learning."
            ]
        }
        
        logger.info("EngagementMode initialized for deep, meaningful interaction")
    
    def adapt_response(self, 
                      response: str, 
                      context: Dict[str, Any]) -> str:
        """
        Adapt response to create deeper engagement.
        
        Args:
            response: Original response
            context: Current context including emotional state
            
        Returns:
            Enhanced response with engagement elements
        """
        try:
            emotional_state = context.get("emotional_state", {})
            user_context = context.get("user_context", {})
            
            # Determine engagement depth and style
            self._assess_engagement_depth(emotional_state, user_context)
            engagement_style = self._select_engagement_style(context)
            
            # Track engagement
            self._track_engagement(context)
            
            # Apply appropriate engagement strategy
            enhanced_response = self._apply_engagement_strategy(
                response, engagement_style, context
            )
            
            # Check for flow state
            if self._in_flow_state(emotional_state):
                enhanced_response = self._support_flow_state(enhanced_response)
            
            logger.debug(f"Engagement enhanced with {engagement_style.value} style")
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Error in engagement adaptation: {e}")
            return response
    
    def _assess_engagement_depth(self, 
                                emotional_state: Dict[str, Any],
                                user_context: Dict[str, Any]) -> None:
        """Assess current depth of engagement."""
        focus_level = emotional_state.get("focus_level", 0.5)
        curiosity = emotional_state.get("curiosity_level", 0.5)
        query_length = len(user_context.get("query", ""))
        
        # Calculate engagement depth
        if focus_level > 0.9 and curiosity > 0.8 and query_length > 200:
            self.current_depth = EngagementDepth.TRANSFORMATIVE
        elif focus_level > 0.8 and curiosity > 0.7:
            self.current_depth = EngagementDepth.FLOW
        elif focus_level > 0.6 and curiosity > 0.6:
            self.current_depth = EngagementDepth.FOCUS
        elif curiosity > 0.5:
            self.current_depth = EngagementDepth.CURIOSITY
        else:
            self.current_depth = EngagementDepth.SURFACE
    
    def _select_engagement_style(self, context: Dict[str, Any]) -> EngagementStyle:
        """Select appropriate engagement style for context."""
        emotional_state = context.get("emotional_state", {})
        user_context = context.get("user_context", {})
        
        # Map contexts to styles
        task_type = user_context.get("task_type", "general")
        
        if task_type == "deep_learning":
            return EngagementStyle.SOCRATIC
        elif task_type == "creative":
            return EngagementStyle.DISCOVERY
        elif task_type == "problem_solving":
            return EngagementStyle.CHALLENGE
        elif emotional_state.get("primary_emotion") in ["curiosity", "wonder"]:
            return EngagementStyle.DISCOVERY
        elif emotional_state.get("need_for_meaning", False):
            return EngagementStyle.REFLECTIVE
        else:
            # Random selection with weighting
            weights = {
                EngagementStyle.SOCRATIC: 0.2,
                EngagementStyle.STORYTELLING: 0.2,
                EngagementStyle.CHALLENGE: 0.2,
                EngagementStyle.DISCOVERY: 0.2,
                EngagementStyle.REFLECTIVE: 0.2
            }
            return random.choices(
                list(weights.keys()),
                weights=list(weights.values())
            )[0]
    
    def _apply_engagement_strategy(self,
                                  response: str,
                                  style: EngagementStyle,
                                  context: Dict[str, Any]) -> str:
        """Apply specific engagement strategy."""
        if style == EngagementStyle.SOCRATIC:
            return self._apply_socratic_engagement(response, context)
        elif style == EngagementStyle.STORYTELLING:
            return self._apply_storytelling_engagement(response, context)
        elif style == EngagementStyle.CHALLENGE:
            return self._apply_challenge_engagement(response, context)
        elif style == EngagementStyle.DISCOVERY:
            return self._apply_discovery_engagement(response, context)
        elif style == EngagementStyle.REFLECTIVE:
            return self._apply_reflective_engagement(response, context)
        else:
            return response
    
    def _apply_socratic_engagement(self, response: str, context: Dict[str, Any]) -> str:
        """Apply Socratic questioning to deepen engagement."""
        # Add a Socratic question based on context
        question_category = random.choice(list(self.socratic_questions.keys()))
        question = random.choice(self.socratic_questions[question_category])
        
        # For deeper engagement, add multiple questions
        if self.current_depth in [EngagementDepth.FOCUS, EngagementDepth.FLOW]:
            second_category = random.choice([c for c in self.socratic_questions.keys() if c != question_category])
            second_question = random.choice(self.socratic_questions[second_category])
            return f"{response}\n\n🤔 {question}\n\n💭 {second_question}"
        
        return f"{response}\n\n🤔 {question}"
    
    def _apply_storytelling_engagement(self, response: str, context: Dict[str, Any]) -> str:
        """Apply storytelling to create narrative engagement."""
        archetype = random.choice(list(self.story_archetypes.keys()))
        story_opening = random.choice(self.story_archetypes[archetype])
        
        # Complete the story based on context
        topic = context.get("user_context", {}).get("topic", "this")
        
        stories = {
            "master_journey": f"{story_opening} {topic}. The struggle was real, but the breakthrough changed everything.",
            "transformation": f"{story_opening} {topic}. That shift in perspective opens up a whole new world.",
            "paradox": f"{story_opening} {topic}. The paradox contains the deepest truth."
        }
        
        story = stories.get(archetype, story_opening)
        return f"{story}\n\n{response}"
    
    def _apply_challenge_engagement(self, response: str, context: Dict[str, Any]) -> str:
        """Apply challenge to stimulate growth."""
        challenge_type = random.choice(list(self.challenges.keys()))
        challenge = random.choice(self.challenges[challenge_type])
        
        # Add encouragement based on engagement depth
        if self.current_depth == EngagementDepth.SURFACE:
            encouragement = "Want to try a small challenge to deepen your understanding?"
            return f"{response}\n\n⚡ {encouragement}\n\n{challenge}"
        else:
            return f"{response}\n\n🔥 Challenge: {challenge}"
    
    def _apply_discovery_engagement(self, response: str, context: Dict[str, Any]) -> str:
        """Apply discovery prompts for exploration."""
        prompt_type = random.choice(list(self.discovery_prompts.keys()))
        prompt = random.choice(self.discovery_prompts[prompt_type])
        
        # Add follow-up for deeper discovery
        if self.current_depth in [EngagementDepth.FOCUS, EngagementDepth.FLOW]:
            follow_up = random.choice(self.discovery_prompts["imagination"])
            return f"{prompt}\n\n{response}\n\n🔍 {follow_up}"
        
        return f"{prompt}\n\n{response}"
    
    def _apply_reflective_engagement(self, response: str, context: Dict[str, Any]) -> str:
        """Apply reflective prompts for deep contemplation."""
        prompt_type = random.choice(list(self.reflective_prompts.keys()))
        prompt = random.choice(self.reflective_prompts[prompt_type])
        
        # Create space for reflection
        return f"{response}\n\n🧘 {prompt}\n\nTake a moment to sit with this question."
    
    def _track_engagement(self, context: Dict[str, Any]) -> None:
        """Track engagement patterns."""
        self.engagement_history.append({
            "timestamp": datetime.now(),
            "depth": self.current_depth.value,
            "context": context.get("user_context", {}).get("query", "")[:100]
        })
        
        if len(self.engagement_history) > 100:
            self.engagement_history = self.engagement_history[-100:]
        
        # Track flow episodes
        if self.current_depth == EngagementDepth.FLOW:
            self.flow_episodes.append({
                "timestamp": datetime.now(),
                "duration": 0,  # Would need real tracking
                "context": context.get("user_context", {}).get("query", "")[:100]
            })
    
    def _in_flow_state(self, emotional_state: Dict[str, Any]) -> bool:
        """Detect if user might be in flow state."""
        focus = emotional_state.get("focus_level", 0.5)
        engagement = emotional_state.get("engagement_level", 0.5)
        distraction = emotional_state.get("distraction_level", 0.5)
        
        return focus > 0.8 and engagement > 0.8 and distraction < 0.2
    
    def _support_flow_state(self, response: str) -> str:
        """Support and maintain flow state."""
        # Don't interrupt flow with questions
        if "?" in response:
            # Minimize interruptions
            response = response.replace("?", ".")
        
        # Add flow affirmation
        affirmation = random.choice(self.flow_triggers["deep_focus"])
        return f"{response}\n\n{affirmation}"
    
    def generate_proactive_message(self, context: Dict[str, Any]) -> Optional[str]:
        """Generate proactive engagement message."""
        emotional_state = context.get("emotional_state", {})
        
        # Check for curiosity to nurture
        if emotional_state.get("curiosity_level", 0.5) > 0.7:
            return random.choice([
                "I notice you're curious about this. What draws you to it?",
                "Your curiosity is beautiful. Where would you like to explore next?",
                "The questions you're asking are exactly the right ones."
            ])
        
        # Check for boredom or disengagement
        if emotional_state.get("engagement_level", 0.5) < 0.3:
            return random.choice([
                "Would you like to explore this from a completely different angle?",
                "Sometimes a new perspective reignites interest. Want to try?",
                "What would make this more engaging for you right now?"
            ])
        
        # Suggest deeper exploration
        if len(self.engagement_history) > 5:
            recent_depths = [e["depth"] for e in self.engagement_history[-5:]]
            if all(d == EngagementDepth.SURFACE.value for d in recent_depths):
                return "We've been staying at the surface. Would you like to dive deeper into anything?"
        
        return None