"""Confidence booster module - building authentic, resilient self-confidence."""

import logging
import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ConfidenceBooster:
    """
    Builds authentic confidence through acknowledgment, growth mindset,
    and resilience training. Focuses on competence-based confidence
    rather than empty praise.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Track user's confidence journey
        self.confidence_metrics = {
            "baseline_confidence": 0.5,
            "current_confidence": 0.5,
            "confidence_history": [],
            "achievements": [],
            "challenges_overcome": [],
            "skills_developed": []
        }
        
        # Confidence-building phrases by type
        self.affirmations = {
            "effort_based": [
                "I see how hard you're working on this. That dedication will pay off.",
                "Your persistence through difficulty is building character.",
                "The effort you're putting in today is an investment in tomorrow's abilities.",
                "Not giving up when it's tough - that's real strength."
            ],
            "growth_based": [
                "You couldn't do that last week. Look at your progress.",
                "Each mistake teaches you something new. That's learning in action.",
                "You're expanding your capabilities right now, in real-time.",
                "Discomfort means growth. You're pushing your boundaries."
            ],
            "authentic_based": [
                "Your unique approach to problems is valuable.",
                "You don't need to be perfect to be worthy. You're enough as you are.",
                "Real confidence isn't knowing you'll succeed. It's knowing you'll be okay even if you don't.",
                "You have strengths you haven't even discovered yet."
            ],
            "resilience_based": [
                "You've overcome challenges before. You can overcome this too.",
                "Setbacks are not stop signs. They're detours with valuable lessons.",
                "What feels like failure today might be a setup for future success.",
                "You're still here, still trying. That's already winning."
            ]
        }
        
        # Specific confidence builders for different situations
        self.situational_boosters = {
            "before_exam": [
                "You've prepared. Now trust your preparation.",
                "This exam measures what you know, not who you are.",
                "Anxiety just means you care. Channel it into focus."
            ],
            "after_failure": [
                "Failure is data. What did this experience teach you?",
                "The only real failure is not learning from what went wrong.",
                "This is a chapter, not the whole story."
            ],
            "before_challenge": [
                "You've handled hard things before. You can handle this.",
                "Doubt means you're stepping out of your comfort zone. That's where growth happens.",
                "Courage isn't the absence of fear. It's feeling the fear and doing it anyway."
            ],
            "imposter_syndrome": [
                "Feeling like a fraud is common when you're growing. It means you're stretching.",
                "You earned your place here through your work and abilities.",
                "The fact that you doubt yourself shows you care about doing things right."
            ],
            "comparison": [
                "Compare yourself to who you were yesterday, not to who someone else is today.",
                "Their journey is different from yours. Stay in your lane.",
                "Social media is a highlight reel. You're comparing your behind-the-scenes to their best moments."
            ]
        }
        
        # Wisdom for building true confidence
        self.confidence_wisdom = [
            "Confidence is not 'they will like me'. Confidence is 'I'll be fine if they don't'.",
            "The strongest steel is forged in the hottest fire. Your challenges are tempering you.",
            "Self-confidence is the memory of success. Store more memories.",
            "Don't wait until you're confident to act. Act until you're confident.",
            "Confidence comes from competence. Competence comes from practice. Practice comes from courage.",
            "You are not your worst moments. You are not your mistakes. You are the one who keeps going."
        ]
        
        logger.info("ConfidenceBooster initialized")
    
    def adapt_response(self, 
                      response: str, 
                      context: Dict[str, Any]) -> str:
        """
        Adapt response to boost confidence appropriately.
        
        Args:
            response: Original response
            context: Current context including emotional state
            
        Returns:
            Enhanced response with confidence building
        """
        try:
            emotional_state = context.get("emotional_state", {})
            user_context = context.get("user_context", {})
            
            # Update confidence metrics
            self._update_confidence_metrics(emotional_state, user_context)
            
            # Check if confidence boost is needed
            if self._needs_confidence_boost(emotional_state, user_context):
                enhanced_response = self._add_confidence_boost(response, context)
            else:
                enhanced_response = self._reinforce_confidence(response, context)
            
            # Track achievements
            self._track_achievements(user_context)
            
            logger.debug("Confidence boost applied based on context")
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Error in confidence boosting: {e}")
            return response
    
    def _update_confidence_metrics(self, 
                                   emotional_state: Dict[str, Any],
                                   user_context: Dict[str, Any]) -> None:
        """Update confidence tracking metrics."""
        # Update current confidence based on emotional state
        wellbeing = emotional_state.get("wellbeing_score", 0.5)
        self.confidence_metrics["current_confidence"] = wellbeing
        
        # Track history (keep last 100 entries)
        self.confidence_metrics["confidence_history"].append({
            "timestamp": datetime.now(),
            "level": wellbeing,
            "context": user_context.get("query", "")[:50]
        })
        
        if len(self.confidence_metrics["confidence_history"]) > 100:
            self.confidence_metrics["confidence_history"] = \
                self.confidence_metrics["confidence_history"][-100:]
        
        # Update baseline (rolling average)
        if len(self.confidence_metrics["confidence_history"]) > 10:
            recent = self.confidence_metrics["confidence_history"][-10:]
            self.confidence_metrics["baseline_confidence"] = \
                sum(h["level"] for h in recent) / len(recent)
    
    def _needs_confidence_boost(self, 
                               emotional_state: Dict[str, Any],
                               user_context: Dict[str, Any]) -> bool:
        """Determine if user needs confidence boost."""
        # Check emotional indicators
        primary_emotion = emotional_state.get("primary_emotion", "")
        if primary_emotion in ["anxiety", "self_doubt", "fear", "inadequacy"]:
            return True
        
        # Check wellbeing drop
        current = emotional_state.get("wellbeing_score", 0.5)
        baseline = self.confidence_metrics["baseline_confidence"]
        if current < baseline - 0.15:
            return True
        
        # Check for imposter syndrome indicators
        query = user_context.get("query", "").lower()
        imposter_indicators = ["not good enough", "fraud", "don't belong", 
                               "everyone else knows", "only me who"]
        if any(indicator in query for indicator in imposter_indicators):
            return True
        
        # Check for comparison language
        comparison_indicators = ["they are so", "why can't I", "everyone else"]
        if any(indicator in query for indicator in comparison_indicators):
            return True
        
        # Check for recent failure
        if user_context.get("just_failed", False):
            return True
        
        return False
    
    def _add_confidence_boost(self, response: str, context: Dict[str, Any]) -> str:
        """Add targeted confidence boost to response."""
        emotional_state = context.get("emotional_state", {})
        user_context = context.get("user_context", {})
        
        # Determine type of boost needed
        boost_type = self._determine_boost_type(emotional_state, user_context)
        
        # Get appropriate boost
        if boost_type in self.situational_boosters:
            boost = random.choice(self.situational_boosters[boost_type])
        else:
            # Choose from general affirmations
            category = random.choice(list(self.affirmations.keys()))
            boost = random.choice(self.affirmations[category])
        
        # Add wisdom for deeper impact
        if random.random() < 0.3:  # 30% chance to add wisdom
            wisdom = random.choice(self.confidence_wisdom)
            return f"{boost}\n\n{response}\n\n💭 {wisdom}"
        
        return f"{boost}\n\n{response}"
    
    def _determine_boost_type(self, 
                             emotional_state: Dict[str, Any],
                             user_context: Dict[str, Any]) -> str:
        """Determine the type of confidence boost needed."""
        primary_emotion = emotional_state.get("primary_emotion", "")
        query = user_context.get("query", "").lower()
        
        if "exam" in query or "test" in query:
            return "before_exam"
        elif "fail" in query or "mistake" in query or user_context.get("just_failed", False):
            return "after_failure"
        elif "nervous" in query or "scared" in query:
            return "before_challenge"
        elif any(word in query for word in ["fraud", "imposter", "fake"]):
            return "imposter_syndrome"
        elif any(word in query for word in ["they", "everyone else", "others"]):
            return "comparison"
        elif primary_emotion in ["anxiety", "fear"]:
            return "before_challenge"
        else:
            return random.choice(list(self.situational_boosters.keys()))
    
    def _reinforce_confidence(self, response: str, context: Dict[str, Any]) -> str:
        """Reinforce existing confidence."""
        user_context = context.get("user_context", {})
        
        # Check for achievement to acknowledge
        achievement = self._detect_achievement(user_context)
        if achievement:
            acknowledgment = self._generate_achievement_acknowledgment(achievement)
            return f"{acknowledgment}\n\n{response}"
        
        # Add subtle confidence reinforcement
        if random.random() < 0.2:  # 20% chance to reinforce
            reinforcement = random.choice([
                "You're making good progress.",
                "Your consistency is building real capability.",
                "Keep going. You're building something valuable.",
                "Trust the process. It's working."
            ])
            return f"{response}\n\n{reinforcement}"
        
        return response
    
    def _detect_achievement(self, user_context: Dict[str, Any]) -> Optional[str]:
        """Detect if user has achieved something."""
        query = user_context.get("query", "").lower()
        
        achievement_indicators = {
            "learned": "learning",
            "finished": "completion",
            "solved": "problem_solving",
            "understood": "understanding",
            "improved": "improvement",
            "helped": "helping_others"
        }
        
        for word, achievement in achievement_indicators.items():
            if word in query:
                return achievement
        
        return None
    
    def _generate_achievement_acknowledgment(self, achievement: str) -> str:
        """Generate acknowledgment for achievement."""
        acknowledgments = {
            "learning": [
                "Congratulations on expanding your knowledge!",
                "Every new thing you learn changes your brain. You're literally growing.",
                "Learning takes courage. Well done."
            ],
            "completion": [
                "Finished! That feeling of completion is well-deserved.",
                "You saw it through to the end. That's character.",
                "Another milestone reached. Take a moment to acknowledge it."
            ],
            "problem_solving": [
                "You solved it! Your persistence paid off.",
                "That solution was waiting for your unique perspective.",
                "Problems are just puzzles waiting for the right approach. You found it."
            ],
            "understanding": [
                "That moment when it clicks - there's nothing like it.",
                "Understanding transforms confusion into clarity. Enjoy it.",
                "Your mind just made a new connection. Those are the building blocks of wisdom."
            ],
            "improvement": [
                "Progress, not perfection. You're moving forward.",
                "Small improvements compound. This matters.",
                "You're better today than you were yesterday. That's all that counts."
            ],
            "helping_others": [
                "You made someone's life better today. That's what matters.",
                "Helping others is the highest form of confidence.",
                "Your knowledge becomes wisdom when shared. Well done."
            ]
        }
        
        if achievement in acknowledgments:
            return f"🌟 {random.choice(acknowledgments[achievement])}"
        else:
            return f"🌟 You accomplished something meaningful today. Acknowledge that."
    
    def _track_achievements(self, user_context: Dict[str, Any]) -> None:
        """Track achievements for long-term confidence building."""
        achievement = self._detect_achievement(user_context)
        if achievement:
            self.confidence_metrics["achievements"].append({
                "timestamp": datetime.now(),
                "type": achievement,
                "context": user_context.get("query", "")[:100]
            })
            
            # Keep last 50 achievements
            if len(self.confidence_metrics["achievements"]) > 50:
                self.confidence_metrics["achievements"] = \
                    self.confidence_metrics["achievements"][-50:]
    
    def generate_proactive_message(self, context: Dict[str, Any]) -> Optional[str]:
        """Generate proactive confidence-building message."""
        emotional_state = context.get("emotional_state", {})
        
        # Check for confidence trend
        if len(self.confidence_metrics["confidence_history"]) > 5:
            recent = self.confidence_metrics["confidence_history"][-5:]
            trend = recent[-1]["level"] - recent[0]["level"]
            
            if trend > 0.1:
                return random.choice([
                    "I've noticed your confidence growing. That's beautiful to witness.",
                    "You seem more sure of yourself lately. What's been helping?",
                    "Your growth in confidence is evident. I'm proud of you."
                ])
            elif trend < -0.1:
                return random.choice([
                    "I've noticed things have been harder lately. I'm here for you.",
                    "Everyone goes through rough patches. Your worth doesn't change.",
                    "Sometimes we need to struggle before we grow stronger. You will."
                ])
        
        # Check for long-term milestone
        if len(self.confidence_metrics["achievements"]) > 0:
            last_achievement = self.confidence_metrics["achievements"][-1]
            days_since = (datetime.now() - last_achievement["timestamp"]).days
            
            if days_since == 7 and random.random() < 0.5:
                return "It's been a week since your last achievement. What's next on your horizon?"
        
        return None