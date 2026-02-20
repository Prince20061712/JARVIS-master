"""
Comprehensive Emotion Taxonomy for JARVIS
Defines the complete range of emotions the system can understand
"""

from enum import Enum
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

class EmotionCategory(Enum):
    """Primary emotion categories"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    COMPLEX = "complex"

@dataclass
class EmotionDefinition:
    """Definition of an emotion with its characteristics"""
    name: str
    category: EmotionCategory
    intensity_range: Tuple[float, float]  # min, max
    typical_causes: List[str]
    associated_needs: List[str]
    response_strategies: List[str]
    physiological_signs: List[str]
    vocal_signs: List[str]
    linguistic_patterns: List[str]

class EmotionTaxonomy:
    """
    Complete taxonomy of emotions JARVIS can understand
    Based on Plutchik's wheel of emotions and extended for academic context
    """
    
    # Primary emotions (basic, universal)
    PRIMARY_EMOTIONS = {
        # Positive primary
        "joy": EmotionDefinition(
            name="joy",
            category=EmotionCategory.POSITIVE,
            intensity_range=(0.3, 1.0),
            typical_causes=["understanding concept", "solving problem", "good grade", "praise"],
            associated_needs=["celebration", "acknowledgment", "sharing"],
            response_strategies=["reinforce", "encourage", "build_confidence"],
            physiological_signs=["smiling", "relaxed posture", "bright eyes"],
            vocal_signs=["higher pitch", "varied tone", "laughter"],
            linguistic_patterns=["I get it!", "Awesome!", "This is great"]
        ),
        "trust": EmotionDefinition(
            name="trust",
            category=EmotionCategory.POSITIVE,
            intensity_range=(0.2, 0.9),
            typical_causes=["consistent help", "accurate answers", "reliable system"],
            associated_needs=["reliability", "consistency", "honesty"],
            response_strategies=["maintain_consistency", "be_honest", "deliver_promises"],
            physiological_signs=["open posture", "relaxed", "calm breathing"],
            vocal_signs=["steady tone", "moderate pace"],
            linguistic_patterns=["I believe", "I trust", "You're right"]
        ),
        "fear": EmotionDefinition(
            name="fear",
            category=EmotionCategory.NEGATIVE,
            intensity_range=(0.4, 1.0),
            typical_causes=["exam anxiety", "difficult topic", "failure fear", "unknown"],
            associated_needs=["reassurance", "safety", "guidance", "preparation"],
            response_strategies=["reassure", "provide_structure", "build_confidence"],
            physiological_signs=["tense muscles", "rapid heartbeat", "sweating"],
            vocal_signs=["trembling", "high pitch", "fast speech"],
            linguistic_patterns=["I'm scared", "What if", "I can't"]
        ),
        "surprise": EmotionDefinition(
            name="surprise",
            category=EmotionCategory.NEUTRAL,
            intensity_range=(0.3, 0.8),
            typical_causes=["unexpected result", "new information", "sudden insight"],
            associated_needs=["explanation", "context", "understanding"],
            response_strategies=["explain", "provide_context", "encourage_curiosity"],
            physiological_signs=["raised eyebrows", "wide eyes", "open mouth"],
            vocal_signs=["sharp intake", "exclamation", "pause"],
            linguistic_patterns=["Wow!", "Really?", "I didn't know"]
        ),
        "sadness": EmotionDefinition(
            name="sadness",
            category=EmotionCategory.NEGATIVE,
            intensity_range=(0.2, 0.9),
            typical_causes=["poor performance", "confusion", "setback", "disappointment"],
            associated_needs=["comfort", "encouragement", "hope", "support"],
            response_strategies=["comfort", "encourage", "provide_hope", "break_down"],
            physiological_signs=["downcast eyes", "slumped posture", "slow movements"],
            vocal_signs=["low pitch", "slow speech", "monotone", "sighs"],
            linguistic_patterns=["I failed", "I don't understand", "It's too hard"]
        ),
        "anger": EmotionDefinition(
            name="anger",
            category=EmotionCategory.NEGATIVE,
            intensity_range=(0.5, 1.0),
            typical_causes=["frustration", "repeated failure", "system error", "injustice"],
            associated_needs=["validation", "problem_solving", "control", "fairness"],
            response_strategies=["calm", "validate", "problem_solve", "offer_control"],
            physiological_signs=["tense jaw", "clenched fists", "flushed face"],
            vocal_signs=["loud volume", "harsh tone", "fast speech", "sharp words"],
            linguistic_patterns=["This is stupid", "Why won't it", "I'm frustrated"]
        ),
        "anticipation": EmotionDefinition(
            name="anticipation",
            category=EmotionCategory.NEUTRAL,
            intensity_range=(0.2, 0.7),
            typical_causes=["upcoming exam", "new topic", "project deadline"],
            associated_needs=["preparation", "planning", "readiness"],
            response_strategies=["help_plan", "provide_preview", "set_expectations"],
            physiological_signs=["focused attention", "leaning forward"],
            vocal_signs=["eager tone", "questioning pitch"],
            linguistic_patterns=["What's next?", "I'm ready", "Let's start"]
        ),
        "disgust": EmotionDefinition(
            name="disgust",
            category=EmotionCategory.NEGATIVE,
            intensity_range=(0.3, 0.8),
            typical_causes=["boring topic", "uninteresting subject", "repetitive content"],
            associated_needs=["engagement", "variety", "relevance"],
            response_strategies=["make_engaging", "show_relevance", "change_approach"],
            physiological_signs=["nose wrinkle", "turned away", "distaste expression"],
            vocal_signs=["disinterested tone", "sighs", "drawn out words"],
            linguistic_patterns=["This is boring", "Do I have to", "Not again"]
        ),
    }
    
    # Secondary emotions (combinations of primary)
    SECONDARY_EMOTIONS = {
        "optimism": ("anticipation", "joy"),  # anticipation + joy
        "love": ("joy", "trust"),  # joy + trust
        "submission": ("trust", "fear"),  # trust + fear
        "awe": ("fear", "surprise"),  # fear + surprise
        "disapproval": ("surprise", "sadness"),  # surprise + sadness
        "remorse": ("sadness", "disgust"),  # sadness + disgust
        "contempt": ("disgust", "anger"),  # disgust + anger
        "aggressiveness": ("anger", "anticipation"),  # anger + anticipation
    }
    
    # Academic-specific emotional states
    ACADEMIC_EMOTIONS = {
        "curiosity": EmotionDefinition(
            name="curiosity",
            category=EmotionCategory.POSITIVE,
            intensity_range=(0.3, 0.9),
            typical_causes=["new topic", "interesting problem", "open question"],
            associated_needs=["exploration", "answers", "deeper knowledge"],
            response_strategies=["encourage_exploration", "provide_resources", "ask_questions"],
            physiological_signs=["leaning in", "focused gaze", "head tilt"],
            vocal_signs=["questioning tone", "eager pace", "rising intonation"],
            linguistic_patterns=["Why?", "How does", "Tell me more", "What if"]
        ),
        "frustration": EmotionDefinition(
            name="frustration",
            category=EmotionCategory.NEGATIVE,
            intensity_range=(0.4, 1.0),
            typical_causes=["stuck on problem", "unclear explanation", "repeated errors"],
            associated_needs=["clarification", "alternative approach", "break", "success"],
            response_strategies=["simplify", "try_different", "encourage", "suggest_break"],
            physiological_signs=["furrowed brow", "tapping", "sighing", "tense shoulders"],
            vocal_signs=["strained tone", "frustrated exhales", "repetitive questions"],
            linguistic_patterns=["I don't get it", "This doesn't make sense", "Still wrong"]
        ),
        "confidence": EmotionDefinition(
            name="confidence",
            category=EmotionCategory.POSITIVE,
            intensity_range=(0.3, 1.0),
            typical_causes=["mastery", "past success", "preparation"],
            associated_needs=["challenge", "recognition", "application"],
            response_strategies=["provide_challenge", "acknowledge", "encourage_teaching"],
            physiological_signs=["straight posture", "steady gaze", "relaxed demeanor"],
            vocal_signs=["clear voice", "steady pace", "assertive tone"],
            linguistic_patterns=["I know this", "Let me try", "I understand"]
        ),
        "overwhelmed": EmotionDefinition(
            name="overwhelmed",
            category=EmotionCategory.NEGATIVE,
            intensity_range=(0.6, 1.0),
            typical_causes=["too much information", "complex topic", "time pressure"],
            associated_needs=["simplification", "prioritization", "break", "support"],
            response_strategies=["break_down", "prioritize", "calm", "suggest_break"],
            physiological_signs=["wide eyes", "rapid breathing", "fidgeting", "confusion"],
            vocal_signs=["rapid speech", "stammering", "high pitch", "running words together"],
            linguistic_patterns=["Too much", "Can't keep up", "Slow down", "Wait"]
        ),
        "breakthrough": EmotionDefinition(
            name="breakthrough",
            category=EmotionCategory.POSITIVE,
            intensity_range=(0.7, 1.0),
            typical_causes=["sudden understanding", "solved problem", "connection made"],
            associated_needs=["celebration", "reinforcement", "application"],
            response_strategies=["celebrate", "reinforce", "encourage_application"],
            physiological_signs=["bright eyes", "smile", "alert posture", "gestures"],
            vocal_signs=["excited tone", "higher pitch", "faster speech", "laughter"],
            linguistic_patterns=["Aha!", "I get it now!", "That makes sense", "Eureka!"]
        ),
        "imposter_syndrome": EmotionDefinition(
            name="imposter_syndrome",
            category=EmotionCategory.NEGATIVE,
            intensity_range=(0.5, 0.9),
            typical_causes=["difficult topic", "comparison", "high expectations"],
            associated_needs=["validation", "reassurance", "evidence_of_ability"],
            response_strategies=["validate", "normalize", "show_progress", "build_evidence"],
            physiological_signs=["withdrawn", "avoidant", "tense", "self-soothing gestures"],
            vocal_signs=["quiet voice", "uncertain tone", "frequent pauses", "self-doubt words"],
            linguistic_patterns=["I'm not smart enough", "Others get it", "I don't belong"]
        ),
        "flow_state": EmotionDefinition(
            name="flow_state",
            category=EmotionCategory.POSITIVE,
            intensity_range=(0.4, 0.9),
            typical_causes=["engaging challenge", "perfect difficulty", "clear goals"],
            associated_needs=["continued_challenge", "minimal_interruption", "progress_tracking"],
            response_strategies=["maintain_flow", "track_progress", "subtle_guidance"],
            physiological_signs=["focused", "still", "minimal blinking", "engaged"],
            vocal_signs=["minimal speech", "short responses", "focused tone"],
            linguistic_patterns=["Working on it", "Almost there", "Let me finish"]
        ),
        "test_anxiety": EmotionDefinition(
            name="test_anxiety",
            category=EmotionCategory.NEGATIVE,
            intensity_range=(0.5, 1.0),
            typical_causes=["upcoming exam", "past failure", "pressure", "unprepared"],
            associated_needs=["preparation", "calming", "strategy", "confidence"],
            response_strategies=["provide_strategy", "calm", "build_confidence", "practice"],
            physiological_signs=["sweating", "trembling", "nausea", "restlessness"],
            vocal_signs=["trembling voice", "high pitch", "rapid then slow speech", "stuttering"],
            linguistic_patterns=["I'm going to fail", "Can't remember", "Blank out"]
        ),
        "burnout": EmotionDefinition(
            name="burnout",
            category=EmotionCategory.NEGATIVE,
            intensity_range=(0.6, 1.0),
            typical_causes=["prolonged stress", "no breaks", "excessive workload"],
            associated_needs=["rest", "perspective", "reduced_load", "support"],
            response_strategies=["recommend_break", "adjust_pace", "provide_support", "validate"],
            physiological_signs=["exhausted appearance", "slumped", "dark circles", "slow"],
            vocal_signs=["flat tone", "slow speech", "long pauses", "monotone"],
            linguistic_patterns=["Too tired", "Can't anymore", "No energy", "What's the point"]
        ),
    }

class ContextAwareness:
    """
    Adjusts emotion detection based on context
    """
    
    def __init__(self):
        self.context_rules = {
            "exam_period": {
                "anxiety": 1.3,  # Boost anxiety during exams
                "stress": 1.4,
                "frustration": 1.2
            },
            "difficult_topic": {
                "frustration": 1.5,
                "confusion": 1.6,
                "curiosity": 1.2
            },
            "late_night": {
                "fatigue": 1.5,
                "burnout": 1.3,
                "frustration": 1.2
            },
            "after_break": {
                "joy": 1.2,
                "curiosity": 1.3,
                "optimism": 1.2
            }
        }
    
    def adjust_for_context(self, emotion_result: Dict, context: Dict) -> Dict:
        """
        Adjust emotion interpretation based on context
        """
        adjusted_scores = emotion_result.get('emotion_scores', {}).copy()
        
        # Apply context multipliers
        for context_factor, factor_value in context.items():
            if context_factor in self.context_rules:
                rules = self.context_rules[context_factor]
                for emotion, multiplier in rules.items():
                    if emotion in adjusted_scores:
                        adjusted_scores[emotion] *= multiplier
        
        # Re-normalize
        if adjusted_scores:
            max_score = max(adjusted_scores.values())
            if max_score > 1.0:
                for emotion in adjusted_scores:
                    adjusted_scores[emotion] /= max_score
            
            # Update primary emotion if changed
            new_primary = max(adjusted_scores, key=adjusted_scores.get)
            if new_primary != emotion_result['primary_emotion']:
                emotion_result['context_adjusted'] = True
                emotion_result['original_emotion'] = emotion_result['primary_emotion']
                emotion_result['primary_emotion'] = new_primary
                emotion_result['intensity'] = adjusted_scores[new_primary]
        
        emotion_result['emotion_scores'] = adjusted_scores
        return emotion_result

class EmotionDetector:
    """
    Detects and interprets emotions from multiple modalities
    """
    
    def __init__(self):
        self.taxonomy = EmotionTaxonomy()
        self.context_awareness = ContextAwareness()
        
    async def detect_emotion(self, 
                            text: Optional[str] = None,
                            voice_features: Optional[Dict] = None,
                            facial_features: Optional[Dict] = None,
                            context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Detect emotion from available modalities
        """
        results = {}
        confidence_scores = {}
        
        # Text-based detection
        if text:
            text_result = self._analyze_text(text)
            results['text'] = text_result
            confidence_scores['text'] = text_result['confidence']
        
        # Voice-based detection
        if voice_features:
            voice_result = self._analyze_voice(voice_features)
            results['voice'] = voice_result
            confidence_scores['voice'] = voice_result['confidence']
        
        # Facial expression detection
        if facial_features:
            facial_result = self._analyze_facial(facial_features)
            results['facial'] = facial_result
            confidence_scores['facial'] = facial_result['confidence']
        
        # Fuse results
        fused_emotion = self._fuse_emotions(results, confidence_scores)
        
        # Apply context awareness
        if context:
            fused_emotion = self.context_awareness.adjust_for_context(
                fused_emotion, context
            )
        
        return fused_emotion
    
    def _analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze text for emotional content
        Uses linguistic patterns, keywords, and semantic analysis
        """
        text_lower = text.lower()
        
        # Check for emotion keywords
        emotion_scores = {}
        
        # Check primary emotions
        for emotion, definition in self.taxonomy.PRIMARY_EMOTIONS.items():
            score = 0
            for pattern in definition.linguistic_patterns:
                if pattern.lower() in text_lower:
                    score += 0.3
            if score > 0:
                emotion_scores[emotion] = min(score, 1.0)
        
        # Check academic emotions
        for emotion, definition in self.taxonomy.ACADEMIC_EMOTIONS.items():
            score = 0
            for pattern in definition.linguistic_patterns:
                if pattern.lower() in text_lower:
                    score += 0.3
            if score > 0:
                emotion_scores[emotion] = min(score, 1.0)
        
        # If no emotions detected, default to neutral
        if not emotion_scores:
            return {
                "primary_emotion": "neutral",
                "intensity": 0.0,
                "confidence": 0.5,
                "secondary_emotions": []
            }
        
        # Get highest scoring emotion
        primary = max(emotion_scores, key=emotion_scores.get)
        intensity = emotion_scores[primary]
        
        # Get secondary emotions (above threshold)
        secondary = [e for e, s in emotion_scores.items() 
                    if e != primary and s > 0.3]
        
        return {
            "primary_emotion": primary,
            "intensity": intensity,
            "confidence": min(0.9, 0.5 + intensity * 0.4),
            "secondary_emotions": secondary,
            "emotion_scores": emotion_scores
        }
    
    def _analyze_voice(self, features: Dict) -> Dict[str, Any]:
        """
        Analyze voice features for emotional content
        Features include: pitch, tone, rate, volume, pauses
        """
        emotion_scores = {}
        
        # Extract features
        pitch_mean = features.get('pitch_mean', 0)
        pitch_variance = features.get('pitch_variance', 0)
        speech_rate = features.get('speech_rate', 150)  # words per minute
        volume_mean = features.get('volume_mean', 0)
        pause_frequency = features.get('pause_frequency', 0)
        
        # Detect emotions based on voice patterns
        # High pitch + high variance + fast rate = excitement/joy
        if pitch_mean > 200 and pitch_variance > 100 and speech_rate > 180:
            emotion_scores['joy'] = 0.7
            emotion_scores['excitement'] = 0.8
        
        # Low pitch + slow rate + low volume = sadness/fatigue
        elif pitch_mean < 120 and speech_rate < 120 and volume_mean < 0.3:
            emotion_scores['sadness'] = 0.6
            emotion_scores['burnout'] = 0.5
        
        # High pitch + high rate + high volume = anger/frustration
        elif pitch_mean > 180 and speech_rate > 200 and volume_mean > 0.8:
            emotion_scores['anger'] = 0.7
            emotion_scores['frustration'] = 0.8
        
        # Many pauses + variable rate = anxiety/uncertainty
        elif pause_frequency > 10:
            emotion_scores['anxiety'] = 0.6
            emotion_scores['test_anxiety'] = 0.5
        
        # Monotone + low variance = boredom/disinterest
        elif pitch_variance < 30:
            emotion_scores['boredom'] = 0.7
            emotion_scores['disgust'] = 0.4
        
        # Default neutral
        else:
            return {
                "primary_emotion": "neutral",
                "intensity": 0.0,
                "confidence": 0.5,
                "secondary_emotions": []
            }
        
        # Get primary emotion
        primary = max(emotion_scores, key=emotion_scores.get)
        intensity = emotion_scores[primary]
        
        return {
            "primary_emotion": primary,
            "intensity": intensity,
            "confidence": 0.7,
            "secondary_emotions": [e for e in emotion_scores if e != primary]
        }
    
    def _analyze_facial(self, features: Dict) -> Dict[str, Any]:
        """
        Analyze facial expressions for emotional content
        """
        # This would integrate with a facial expression recognition model
        # For now, return placeholder
        return {
            "primary_emotion": "neutral",
            "intensity": 0.0,
            "confidence": 0.3
        }
    
    def _fuse_emotions(self, results: Dict, confidences: Dict) -> Dict[str, Any]:
        """
        Fuse emotion detection results from multiple modalities
        Uses weighted average based on confidence
        """
        if not results:
            return {
                "primary_emotion": "neutral",
                "intensity": 0.0,
                "confidence": 0.0,
                "secondary_emotions": []
            }
        
        # Calculate weighted emotion scores
        emotion_scores = {}
        total_weight = 0
        
        for modality, result in results.items():
            weight = confidences.get(modality, 0.5)
            total_weight += weight
            
            # Add primary emotion
            primary = result.get('primary_emotion')
            if primary:
                emotion_scores[primary] = emotion_scores.get(primary, 0) + weight
            
            # Add secondary emotions with lower weight
            for secondary in result.get('secondary_emotions', []):
                emotion_scores[secondary] = emotion_scores.get(secondary, 0) + weight * 0.3
        
        # Normalize scores
        if total_weight > 0:
            for emotion in emotion_scores:
                emotion_scores[emotion] /= total_weight
        
        # Get primary emotion
        primary = max(emotion_scores, key=emotion_scores.get)
        intensity = emotion_scores[primary]
        
        # Get secondary emotions
        secondary = [e for e, s in emotion_scores.items() 
                    if e != primary and s > 0.2]
        
        return {
            "primary_emotion": primary,
            "intensity": intensity,
            "confidence": min(0.95, total_weight / len(results)),
            "secondary_emotions": secondary,
            "emotion_scores": emotion_scores,
            "modalities_used": list(results.keys())
        }
