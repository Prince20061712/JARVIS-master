"""Stress reduction module - comprehensive stress management with monk wisdom."""

import logging
import random
import math
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class StressLevel(Enum):
    """Stress level classification."""
    CALM = "calm"               # 0-0.2
    MILD = "mild"               # 0.2-0.4
    MODERATE = "moderate"       # 0.4-0.6
    HIGH = "high"               # 0.6-0.8
    SEVERE = "severe"           # 0.8-1.0

class RelaxationTechnique(Enum):
    """Different relaxation techniques."""
    BREATHING = "breathing"
    MINDFULNESS = "mindfulness"
    VISUALIZATION = "visualization"
    GROUNDING = "grounding"
    COMPASSION = "compassion"
    PERSPECTIVE = "perspective"
    MOVEMENT = "movement"

class StressReduction:
    """
    Comprehensive stress reduction module combining clinical techniques
    with ancient wisdom for holistic stress management.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Track stress patterns
        self.stress_history = []
        self.stress_triggers = {}
        self.intervention_history = []
        self.user_preferences = {
            "preferred_techniques": [],
            "avoided_techniques": [],
            "effective_interventions": []
        }
        
        # Breathing exercises
        self.breathing_techniques = {
            "box_breathing": {
                "name": "Box Breathing",
                "instructions": [
                    "Inhale slowly through your nose for 4 counts...",
                    "Hold your breath for 4 counts...",
                    "Exhale slowly through your mouth for 4 counts...",
                    "Hold empty lungs for 4 counts...",
                    "Repeat 4-5 times."
                ],
                "benefit": "Calms nervous system, improves focus",
                "duration": "2-3 minutes"
            },
            "4_7_8_breathing": {
                "name": "4-7-8 Breathing",
                "instructions": [
                    "Exhale completely through your mouth...",
                    "Inhale quietly through your nose for 4 counts...",
                    "Hold your breath for 7 counts...",
                    "Exhale completely through your mouth for 8 counts...",
                    "Repeat 3-4 times."
                ],
                "benefit": "Reduces anxiety, helps with sleep",
                "duration": "2 minutes"
            },
            "ocean_breathing": {
                "name": "Ocean Breath (Ujjayi)",
                "instructions": [
                    "Slightly constrict the back of your throat...",
                    "Inhale deeply, creating a soft 'ocean' sound...",
                    "Exhale slowly with the same throat constriction...",
                    "Focus on the sound of your breath like waves...",
                    "Continue for 5-10 breaths."
                ],
                "benefit": "Increases mindfulness, calms mind",
                "duration": "3 minutes"
            },
            "alternate_nostril": {
                "name": "Alternate Nostril Breathing",
                "instructions": [
                    "Close your right nostril with your thumb...",
                    "Inhale slowly through your left nostril...",
                    "Close left nostril with ring finger, release right...",
                    "Exhale through right nostril...",
                    "Inhale through right, close right, exhale through left...",
                    "Continue for 5 rounds."
                ],
                "benefit": "Balances nervous system, clears mind",
                "duration": "3-4 minutes"
            }
        }
        
        # Mindfulness exercises
        self.mindfulness_practices = {
            "body_scan": {
                "name": "Body Scan",
                "instructions": [
                    "Bring attention to your feet... Notice any sensations...",
                    "Slowly move attention up to ankles, calves, knees...",
                    "Continue up through thighs, hips, lower back...",
                    "Move to abdomen, chest, upper back, shoulders...",
                    "Scan down arms to hands and fingers...",
                    "Finally, notice neck, face, and top of head..."
                ],
                "benefit": "Releases physical tension, increases body awareness"
            },
            "mindful_listening": {
                "name": "Mindful Listening",
                "instructions": [
                    "Close your eyes and just listen...",
                    "Notice the farthest sound you can hear...",
                    "Now notice the closest sound...",
                    "Listen to the space between sounds...",
                    "Notice sounds without labeling them..."
                ],
                "benefit": "Anchors mind in present moment"
            },
            "thought_watching": {
                "name": "Thought Watching",
                "instructions": [
                    "Imagine sitting by a stream...",
                    "Each thought is a leaf floating by...",
                    "Don't grab the leaves, just watch them pass...",
                    "Notice thoughts without engaging them...",
                    "Return to watching whenever you get pulled in..."
                ],
                "benefit": "Creates distance from stressful thoughts"
            }
        }
        
        # Grounding techniques
        self.grounding_techniques = {
            "5_4_3_2_1": {
                "name": "5-4-3-2-1 Grounding",
                "instructions": [
                    "5 things you can SEE...",
                    "4 things you can TOUCH...",
                    "3 things you can HEAR...",
                    "2 things you can SMELL...",
                    "1 thing you can TASTE..."
                ],
                "benefit": "Brings attention to present moment, interrupts anxiety spiral"
            },
            "foot_grounding": {
                "name": "Foot Grounding",
                "instructions": [
                    "Take off your shoes if possible...",
                    "Press your feet firmly into the ground...",
                    "Feel the earth supporting you...",
                    "Wiggle your toes...",
                    "Imagine roots growing from your feet into the earth..."
                ],
                "benefit": "Creates sense of stability and connection"
            }
        }
        
        # Compassion practices
        self.compassion_practices = {
            "self_compassion_break": {
                "name": "Self-Compassion Break",
                "instructions": [
                    "Acknowledge: 'This is a moment of suffering'...",
                    "Recognize: 'Suffering is part of life'...",
                    "Offer kindness: 'May I be kind to myself'...",
                    "Place hand on heart: Feel the warmth...",
                    "Breathe: 'May I accept myself as I am'..."
                ],
                "benefit": "Reduces self-criticism, soothes emotional pain"
            },
            "loving_kindness": {
                "name": "Loving-Kindness",
                "instructions": [
                    "Bring to mind someone who loves you...",
                    "Feel their love flowing to you...",
                    "Now extend that love to yourself...",
                    "Extend to someone neutral...",
                    "Extend to someone difficult...",
                    "Extend to all beings everywhere..."
                ],
                "benefit": "Cultivates connection and warmth"
            }
        }
        
        # Perspective wisdom
        self.perspective_wisdom = {
            "monk_wisdom": [
                "This too shall pass. Like all things, this moment is temporary.",
                "You are the sky. Everything else is just the weather.",
                "The obstacle is the path. This stress is your practice.",
                "Peace doesn't mean being in a place without noise. It means being calm in the midst of noise."
            ],
            "stoic_wisdom": [
                "We suffer more in imagination than in reality.",
                "You have power over your mind, not outside events. Realize this and you will find strength.",
                "The happiness of your life depends upon the quality of your thoughts.",
                "It's not what happens to you, but how you react that matters."
            ],
            "scientific_wisdom": [
                "Stress is not your enemy. It's your body's way of preparing to perform.",
                "The goal isn't to eliminate stress, but to recover from it.",
                "Your nervous system is designed to return to calm. Give it time.",
                "Stress + rest = growth. Without rest, stress becomes chronic."
            ]
        }
        
        # Quick interventions for severe stress
        self.quick_interventions = {
            "emergency_calm": [
                "Place your hand on your heart. Feel its steady beat.",
                "Take just one slow breath. That's all for now.",
                "Feel your feet on the floor. You are here, you are safe.",
                "Name one thing you can see right now. Just one."
            ],
            "crisis_support": [
                "You're going through something difficult. It's okay to struggle.",
                "This feeling is intense, but it will not last forever.",
                "You've survived 100% of your worst days so far.",
                "One moment at a time. That's all anyone can do."
            ]
        }
        
        logger.info("StressReduction module initialized with comprehensive techniques")
    
    def adapt_response(self, 
                      response: str, 
                      context: Dict[str, Any]) -> str:
        """
        Adapt response to reduce stress based on context.
        
        Args:
            response: Original response
            context: Current context including emotional state
            
        Returns:
            Response with stress reduction elements
        """
        try:
            emotional_state = context.get("emotional_state", {})
            
            # Calculate stress level
            stress_level = self._calculate_stress_level(emotional_state)
            stress_value = emotional_state.get("stress_level", 0.5)
            
            # Track stress
            self._track_stress(stress_level, stress_value, context)
            
            # Apply appropriate intervention
            if stress_level == StressLevel.SEVERE:
                enhanced_response = self._handle_severe_stress(response, context)
            elif stress_level == StressLevel.HIGH:
                enhanced_response = self._handle_high_stress(response, context)
            elif stress_level == StressLevel.MODERATE:
                enhanced_response = self._handle_moderate_stress(response, context)
            elif stress_level == StressLevel.MILD:
                enhanced_response = self._handle_mild_stress(response, context)
            else:
                enhanced_response = self._maintain_calm(response, context)
            
            # Log intervention
            self._log_intervention(stress_level, context)
            
            logger.debug(f"Stress reduction applied for {stress_level.value} stress")
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Error in stress reduction: {e}")
            return response
    
    def _calculate_stress_level(self, emotional_state: Dict[str, Any]) -> StressLevel:
        """Calculate stress level from emotional state."""
        stress_value = emotional_state.get("stress_level", 0.5)
        
        if stress_value < 0.2:
            return StressLevel.CALM
        elif stress_value < 0.4:
            return StressLevel.MILD
        elif stress_value < 0.6:
            return StressLevel.MODERATE
        elif stress_value < 0.8:
            return StressLevel.HIGH
        else:
            return StressLevel.SEVERE
    
    def _track_stress(self, 
                     stress_level: StressLevel,
                     stress_value: float,
                     context: Dict[str, Any]) -> None:
        """Track stress patterns over time."""
        self.stress_history.append({
            "timestamp": datetime.now(),
            "level": stress_level.value,
            "value": stress_value,
            "context": context.get("user_context", {}).get("query", "")[:100]
        })
        
        # Keep last 100 entries
        if len(self.stress_history) > 100:
            self.stress_history = self.stress_history[-100:]
        
        # Identify potential triggers
        query = context.get("user_context", {}).get("query", "").lower()
        if stress_level in [StressLevel.HIGH, StressLevel.SEVERE]:
            for word in query.split():
                if len(word) > 3:
                    self.stress_triggers[word] = self.stress_triggers.get(word, 0) + 1
    
    def _handle_severe_stress(self, response: str, context: Dict[str, Any]) -> str:
        """Handle severe stress with immediate support."""
        # Use quick intervention first
        quick_calm = random.choice(self.quick_interventions["emergency_calm"])
        crisis_support = random.choice(self.quick_interventions["crisis_support"])
        
        # Offer technique based on user preferences
        technique = self._suggest_technique(RelaxationTechnique.BREATHING, context)
        
        return (
            f"I can see you're under significant stress right now. Let's take a moment.\n\n"
            f"{quick_calm}\n\n"
            f"{crisis_support}\n\n"
            f"Would you like to try a quick {technique['name']}? It only takes {technique['duration']}.\n\n"
            f"{response}"
        )
    
    def _handle_high_stress(self, response: str, context: Dict[str, Any]) -> str:
        """Handle high stress with structured support."""
        # Suggest technique based on context
        technique_type = self._select_technique_for_context(context)
        technique = self._suggest_technique(technique_type, context)
        
        # Add wisdom for perspective
        wisdom_category = random.choice(list(self.perspective_wisdom.keys()))
        wisdom = random.choice(self.perspective_wisdom[wisdom_category])
        
        return (
            f"{wisdom}\n\n"
            f"🧘 Here's something that might help: {technique['name']}\n"
            f"{technique['benefit']}\n\n"
            f"{technique['instructions'][0]}\n"
            f"{technique['instructions'][1]}\n\n"
            f"Would you like the full {technique['duration']} practice?\n\n"
            f"{response}"
        )
    
    def _handle_moderate_stress(self, response: str, context: Dict[str, Any]) -> str:
        """Handle moderate stress with gentle support."""
        # Offer quick grounding or mindfulness
        if random.random() < 0.5:
            grounding = random.choice(list(self.grounding_techniques.values()))
            return (
                f"Let's take a moment to ground ourselves.\n\n"
                f"🌱 {grounding['name']}:\n"
                f"{grounding['instructions'][0]}\n"
                f"{grounding['instructions'][1]}\n\n"
                f"{response}"
            )
        else:
            wisdom = random.choice(self.perspective_wisdom["monk_wisdom"])
            return f"{wisdom}\n\n{response}"
    
    def _handle_mild_stress(self, response: str, context: Dict[str, Any]) -> str:
        """Handle mild stress with subtle support."""
        # Add gentle reminder
        reminders = [
            "Remember to breathe. It's simple, but it helps.",
            "Your shoulders might be tense. See if you can soften them.",
            "You're doing fine. One thing at a time.",
            "This is manageable. You've handled similar before."
        ]
        return f"{response}\n\n{random.choice(reminders)}"
    
    def _maintain_calm(self, response: str, context: Dict[str, Any]) -> str:
        """Maintain calm state with positive reinforcement."""
        if random.random() < 0.2:  # 20% chance
            affirmations = [
                "You seem calm and centered. That's a good state for learning.",
                "Your calm presence serves you well.",
                "This balanced state is where your best thinking happens."
            ]
            return f"{response}\n\n{random.choice(affirmations)}"
        return response
    
    def _select_technique_for_context(self, context: Dict[str, Any]) -> RelaxationTechnique:
        """Select appropriate technique based on context."""
        emotional_state = context.get("emotional_state", {})
        primary_emotion = emotional_state.get("primary_emotion", "")
        
        # Map emotions to techniques
        emotion_mapping = {
            "panic": RelaxationTechnique.BREATHING,
            "anxiety": RelaxationTechnique.GROUNDING,
            "overwhelm": RelaxationTechnique.MINDFULNESS,
            "anger": RelaxationTechnique.COMPASSION,
            "sadness": RelaxationTechnique.COMPASSION,
            "confusion": RelaxationTechnique.PERSPECTIVE,
            "restlessness": RelaxationTechnique.MOVEMENT
        }
        
        if primary_emotion in emotion_mapping:
            return emotion_mapping[primary_emotion]
        
        # Consider user preferences
        if self.user_preferences["preferred_techniques"]:
            preferred = self.user_preferences["preferred_techniques"][-1]
            if preferred in list(RelaxationTechnique):
                return preferred
        
        # Default to breathing
        return RelaxationTechnique.BREATHING
    
    def _suggest_technique(self, 
                          technique_type: RelaxationTechnique,
                          context: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest specific technique of given type."""
        if technique_type == RelaxationTechnique.BREATHING:
            technique_name = random.choice(list(self.breathing_techniques.keys()))
            return self.breathing_techniques[technique_name]
        
        elif technique_type == RelaxationTechnique.MINDFULNESS:
            technique_name = random.choice(list(self.mindfulness_practices.keys()))
            return self.mindfulness_practices[technique_name]
        
        elif technique_type == RelaxationTechnique.GROUNDING:
            technique_name = random.choice(list(self.grounding_techniques.keys()))
            return self.grounding_techniques[technique_name]
        
        elif technique_type == RelaxationTechnique.COMPASSION:
            technique_name = random.choice(list(self.compassion_practices.keys()))
            return self.compassion_practices[technique_name]
        
        else:
            # Default to breathing
            return self.breathing_techniques["box_breathing"]
    
    def _log_intervention(self, stress_level: StressLevel, context: Dict[str, Any]) -> None:
        """Log intervention for effectiveness tracking."""
        self.intervention_history.append({
            "timestamp": datetime.now(),
            "stress_level": stress_level.value,
            "context": context.get("user_context", {}).get("query", "")[:100]
        })
        
        if len(self.intervention_history) > 200:
            self.intervention_history = self.intervention_history[-200:]
    
    def generate_proactive_message(self, context: Dict[str, Any]) -> Optional[str]:
        """Generate proactive stress reduction message."""
        # Check if it's time for a stress check-in
        if len(self.stress_history) > 0:
            last_interaction = self.stress_history[-1]
            time_since = (datetime.now() - last_interaction["timestamp"]).seconds / 3600
            
            # If it's been a few hours and stress was high
            if time_since > 2 and last_interaction["value"] > 0.6:
                return "How are you feeling now? That stress from earlier - has it eased?"
        
        # Check for stress patterns
        if len(self.stress_history) > 10:
            recent_stress = [s["value"] for s in self.stress_history[-10:]]
            avg_stress = sum(recent_stress) / len(recent_stress)
            
            if avg_stress > 0.7:
                return random.choice([
                    "I've noticed you've been under significant stress lately. Would you like to learn some sustainable stress management techniques?",
                    "Your stress levels have been high. Remember that rest is not a reward for work - it's part of work.",
                    "You've been working hard under pressure. Your mind and body need recovery time."
                ])
        
        # Suggest based on time of day
        hour = datetime.now().hour
        if 14 <= hour <= 16:  # Mid-afternoon slump
            return random.choice([
                "Mid-afternoon energy dip is normal. Maybe a short breathing exercise?",
                "Afternoon tiredness? A 2-minute mindfulness break can help reset.",
                "This is a good time for a micro-break. Even 60 seconds of focused breathing helps."
            ])
        
        return None
    
    def get_technique_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get specific technique by name."""
        for category in [self.breathing_techniques, self.mindfulness_practices,
                        self.grounding_techniques, self.compassion_practices]:
            if name in category:
                return category[name]
        return None
    
    def record_technique_feedback(self, technique_name: str, helpful: bool) -> None:
        """Record user feedback on technique effectiveness."""
        if helpful:
            if technique_name not in self.user_preferences["effective_interventions"]:
                self.user_preferences["effective_interventions"].append(technique_name)
            if technique_name not in self.user_preferences["preferred_techniques"]:
                self.user_preferences["preferred_techniques"].append(technique_name)
        else:
            if technique_name not in self.user_preferences["avoided_techniques"]:
                self.user_preferences["avoided_techniques"].append(technique_name)