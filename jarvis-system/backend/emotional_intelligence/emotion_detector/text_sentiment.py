"""
Text sentiment analysis with deep psychological and spiritual insights.
Analyzes not just what is said, but the deeper meaning beneath words.
"""

from typing import Dict, List, Tuple, Optional, Any
import re
from collections import defaultdict
import numpy as np

class SpiritualArchetype:
    """Spiritual and psychological archetypes in language"""
    
    ARCHETYPES = {
        'seeker': ['search', 'find', 'looking', 'purpose', 'meaning', 'why'],
        'wounded_healer': ['hurt', 'pain', 'suffering', 'help others', 'understand pain'],
        'warrior': ['fight', 'battle', 'struggle', 'overcome', 'strong'],
        'sage': ['wisdom', 'understand', 'know', 'truth', 'enlighten'],
        'innocent': ['trust', 'simple', 'pure', 'believe', 'hope'],
        'orphan': ['alone', 'abandoned', 'lost', 'belong', 'outsider'],
        'caregiver': ['care', 'help', 'support', 'nurture', 'protect'],
        'creator': ['create', 'make', 'build', 'express', 'manifest']
    }
    
    SHADOW_ARCHETYPES = {
        'seeker': ['lost', 'confused', 'directionless', 'aimless'],
        'wounded_healer': ['broken', 'unfixable', 'damaged', 'scarred'],
        'warrior': ['angry', 'aggressive', 'vengeful', 'bitter'],
        'sage': ['know-it-all', 'judgmental', 'critical', 'dismissive']
    }

class PsychologicalDefense:
    """Psychological defense mechanisms in language"""
    
    DEFENSES = {
        'denial': [r'not (that|true|real)', r'didn\'t happen', r'never said'],
        'projection': [r'they (always|never)', r'everyone (is|does)', r'you always'],
        'rationalization': [r'because', r'reason is', r'makes sense because'],
        'intellectualization': [r'logically', r'analysis', r'statistically'],
        'sublimation': [r'channel into', r'turn into', r'express through'],
        'humor': [r'funny', r'joke', r'laugh'],
        'suppression': [r'don\'t want to think', r'put aside', r'ignore']
    }

class TextSentimentAnalyzer:
    """
    Enhanced text sentiment analyzer with psychological and spiritual depth.
    Detects not just emotions, but archetypes, defense mechanisms, and spiritual seeking.
    """
    
    def __init__(self):
        # Basic emotion lexicons
        self.emotion_lexicon = self._build_emotion_lexicon()
        
        # Intensity modifiers
        self.intensifiers = {
            'very': 1.5,
            'extremely': 2.0,
            'absolutely': 2.0,
            'deeply': 1.8,
            'profoundly': 2.0,
            'terribly': 1.5,
            'horribly': 1.5,
            'incredibly': 1.5,
            'so': 1.3,
            'such': 1.3
        }
        
        # Spiritual seeking indicators
        self.spiritual_keywords = {
            'meaning': ['purpose', 'meaning', 'point', 'significance'],
            'transcendence': ['beyond', 'higher', 'transcend', 'awaken'],
            'connection': ['connected', 'one', 'unity', 'oneness', 'universe'],
            'presence': ['present', 'moment', 'now', 'here'],
            'surrender': ['let go', 'release', 'surrender', 'accept'],
            'gratitude': ['thank', 'grateful', 'appreciate', 'blessing']
        }
        
        # Psychological depth indicators
        self.depth_indicators = [
            r'I (feel|felt)',
            r'why (do|does|did) I',
            r'always (feel|think)',
            r'never (understand|know)',
            r'my (heart|soul|spirit)',
            r'deep (down|inside)'
        ]
        
        # Contextual modifiers
        self.context_weights = {
            'learning': {'curiosity': 1.3, 'frustration': 1.2},
            'work': {'stress': 1.4, 'anxiety': 1.3},
            'relationship': {'love': 1.5, 'hurt': 1.4},
            'health': {'fear': 1.4, 'hope': 1.3}
        }
        
    async def analyze(self, text: str, context: str = "") -> Dict[str, Any]:
        """
        Analyze text for emotional and spiritual content.
        Returns comprehensive analysis with deep insights.
        """
        # Preprocess text
        text_lower = text.lower()
        words = text_lower.split()
        
        # Basic sentiment analysis
        sentiment_scores = self._analyze_sentiment(text_lower, words)
        
        # Emotion detection
        primary_emotion, secondary_emotions = self._detect_emotions(text_lower, words)
        
        # Spiritual archetype detection
        archetypes = self._detect_archetypes(text_lower)
        
        # Defense mechanism detection
        defenses = self._detect_defense_mechanisms(text)
        
        # Psychological depth analysis
        depth_score, depth_indicators = self._analyze_psychological_depth(text)
        
        # Spiritual seeking detection
        spiritual_seeking = self._detect_spiritual_seeking(text_lower)
        
        # Contextual adjustment
        if context:
            primary_emotion, sentiment_scores = self._apply_context(
                primary_emotion, sentiment_scores, context
            )
        
        # Generate insights
        insights = self._generate_insights(
            primary_emotion, 
            archetypes, 
            spiritual_seeking,
            depth_score
        )
        
        return {
            'primary_emotion': {
                'emotion': primary_emotion['emotion'],
                'intensity': primary_emotion['intensity'],
                'confidence': primary_emotion.get('confidence', 0.7)
            },
            'secondary_emotions': secondary_emotions,
            'sentiment_scores': sentiment_scores,
            'archetypes': archetypes,
            'defense_mechanisms': defenses,
            'spiritual_seeking': spiritual_seeking,
            'psychological_depth': {
                'score': depth_score,
                'indicators': depth_indicators
            },
            'insights': insights,
            'confidence': self._calculate_confidence(text, primary_emotion),
            'needs_deeper_listening': depth_score > 0.6 or len(spiritual_seeking) > 0
        }
    
    def _build_emotion_lexicon(self) -> Dict[str, List[Tuple[str, float]]]:
        """Build enhanced emotion lexicon with spiritual emotions"""
        return {
            # Primary emotions
            'joy': [
                ('happy', 0.8), ('joy', 1.0), ('glad', 0.7), ('delighted', 0.9),
                ('pleased', 0.6), ('thrilled', 0.9), ('ecstatic', 1.0),
                ('blessed', 0.8), ('grateful', 0.7)
            ],
            'sadness': [
                ('sad', 0.8), ('unhappy', 0.7), ('depressed', 0.9), ('grief', 1.0),
                ('sorrow', 0.9), ('heartbroken', 1.0), ('down', 0.6),
                ('melancholy', 0.7), ('blue', 0.5)
            ],
            'anger': [
                ('angry', 0.9), ('mad', 0.7), ('furious', 1.0), ('irritated', 0.6),
                ('annoyed', 0.5), ('frustrated', 0.7), ('outraged', 1.0),
                ('bitter', 0.8), ('resentful', 0.8)
            ],
            'fear': [
                ('scared', 0.8), ('afraid', 0.8), ('terrified', 1.0), ('anxious', 0.7),
                ('worried', 0.6), ('nervous', 0.5), ('frightened', 0.8),
                ('dread', 0.9), ('panic', 0.9)
            ],
            'love': [
                ('love', 1.0), ('adore', 0.9), ('cherish', 0.9), ('care', 0.6),
                ('compassion', 0.8), ('kindness', 0.6), ('affection', 0.7)
            ],
            'peace': [
                ('peace', 1.0), ('calm', 0.8), ('serene', 0.9), ('tranquil', 0.8),
                ('centered', 0.7), ('balanced', 0.6), ('harmony', 0.8)
            ],
            'curiosity': [
                ('curious', 0.8), ('wonder', 0.7), ('interested', 0.6),
                ('intrigued', 0.7), ('fascinated', 0.8), ('explore', 0.5)
            ],
            'gratitude': [
                ('grateful', 1.0), ('thankful', 0.9), ('appreciate', 0.7),
                ('blessed', 0.8), ('fortunate', 0.7)
            ],
            'hope': [
                ('hope', 0.9), ('optimistic', 0.8), ('positive', 0.6),
                ('encouraged', 0.7), ('trust', 0.5), ('faith', 0.7)
            ],
            'awe': [
                ('awe', 1.0), ('wonder', 0.8), ('amazed', 0.7), ('astonished', 0.7),
                ('miraculous', 0.8), ('sacred', 0.9), ('divine', 0.9)
            ],
            'bittersweet': [
                ('bittersweet', 1.0), ('melancholy joy', 0.9), ('nostalgic', 0.8),
                ('wistful', 0.7), ('tender sorrow', 0.8)
            ],
            'longing': [
                ('long', 0.8), ('yearn', 0.9), ('ache', 0.7), ('miss', 0.6),
                ('homesick', 0.7), ('desire', 0.6)
            ]
        }
    
    def _analyze_sentiment(self, text: str, words: List[str]) -> Dict[str, float]:
        """Analyze basic sentiment with intensity weighting"""
        sentiment = {
            'positive': 0.0,
            'negative': 0.0,
            'neutral': 0.0,
            'compound': 0.0
        }
        
        # Count sentiment words
        positive_words = ['good', 'great', 'excellent', 'wonderful', 'amazing', 'beautiful']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'painful', 'difficult']
        
        for word in words:
            if word in positive_words:
                sentiment['positive'] += 1
            elif word in negative_words:
                sentiment['negative'] += 1
            else:
                sentiment['neutral'] += 0.5
        
        # Normalize
        total = sum(sentiment.values())
        if total > 0:
            for key in sentiment:
                sentiment[key] /= total
        
        # Calculate compound score (-1 to 1)
        sentiment['compound'] = sentiment['positive'] - sentiment['negative']
        
        return sentiment
    
    def _detect_emotions(self, text: str, words: List[str]) -> Tuple[Dict, List]:
        """Detect emotions with intensity and confidence"""
        emotion_scores = defaultdict(float)
        emotion_matches = defaultdict(list)
        
        # Check each word against emotion lexicon
        for word in words:
            for emotion, terms in self.emotion_lexicon.items():
                for term, base_intensity in terms:
                    if term in word or word in term.split():
                        # Check for intensifiers before this word
                        intensity = base_intensity
                        word_index = words.index(word)
                        if word_index > 0 and words[word_index - 1] in self.intensifiers:
                            intensity *= self.intensifiers[words[word_index - 1]]
                        
                        emotion_scores[emotion] += intensity
                        emotion_matches[emotion].append(word)
        
        # Check for phrases
        for emotion, terms in self.emotion_lexicon.items():
            for term, intensity in terms:
                if ' ' in term and term in text:
                    emotion_scores[emotion] += intensity
                    emotion_matches[emotion].append(term)
        
        # Normalize scores
        if emotion_scores:
            max_score = max(emotion_scores.values())
            if max_score > 0:
                for emotion in emotion_scores:
                    emotion_scores[emotion] /= max_score
        
        # Get primary emotion (highest score)
        primary = None
        if emotion_scores:
            primary_emotion = max(emotion_scores.items(), key=lambda x: x[1])
            primary = {
                'emotion': primary_emotion[0],
                'intensity': primary_emotion[1],
                'confidence': min(0.5 + primary_emotion[1] * 0.5, 0.95)
            }
        else:
            primary = {
                'emotion': 'neutral',
                'intensity': 0.5,
                'confidence': 0.5
            }
        
        # Get secondary emotions (top 3 excluding primary)
        secondary = sorted(
            [(e, s) for e, s in emotion_scores.items() if e != primary['emotion']],
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        return primary, secondary
    
    def _detect_archetypes(self, text: str) -> List[Dict]:
        """Detect spiritual and psychological archetypes"""
        detected = []
        text_lower = text.lower()
        
        # Check for light archetypes
        for archetype, keywords in SpiritualArchetype.ARCHETYPES.items():
            matches = [k for k in keywords if k in text_lower]
            if matches:
                # Check for shadow aspect
                shadow = SpiritualArchetype.SHADOW_ARCHETYPES.get(archetype, [])
                shadow_matches = [s for s in shadow if s in text_lower]
                
                detected.append({
                    'archetype': archetype,
                    'strength': len(matches) / len(keywords),
                    'is_shadow': len(shadow_matches) > 0,
                    'keywords': matches[:3]
                })
        
        return sorted(detected, key=lambda x: x['strength'], reverse=True)[:3]
    
    def _detect_defense_mechanisms(self, text: str) -> List[Dict]:
        """Detect psychological defense mechanisms"""
        detected = []
        
        for defense, patterns in PsychologicalDefense.DEFENSES.items():
            matches = []
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    matches.append(pattern)
            
            if matches:
                detected.append({
                    'defense': defense,
                    'strength': len(matches) / len(patterns),
                    'patterns': matches[:2]
                })
        
        return detected
    
    def _analyze_psychological_depth(self, text: str) -> Tuple[float, List]:
        """Analyze psychological depth of the text"""
        depth_indicators_found = []
        depth_score = 0.0
        
        for pattern in self.depth_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                depth_indicators_found.append(pattern)
                depth_score += 0.2
        
        # Cap at 1.0
        depth_score = min(1.0, depth_score)
        
        return depth_score, depth_indicators_found
    
    def _detect_spiritual_seeking(self, text: str) -> List[Dict]:
        """Detect spiritual seeking patterns"""
        seeking = []
        
        for category, keywords in self.spiritual_keywords.items():
            matches = [k for k in keywords if k in text]
            if matches:
                seeking.append({
                    'category': category,
                    'intensity': len(matches) / len(keywords),
                    'keywords': matches
                })
        
        return seeking
    
    def _apply_context(self, emotion: Dict, sentiment: Dict, context: str) -> Tuple[Dict, Dict]:
        """Apply contextual adjustments to emotion and sentiment"""
        context_lower = context.lower()
        
        for ctx, adjustments in self.context_weights.items():
            if ctx in context_lower:
                for emotion_type, multiplier in adjustments.items():
                    if emotion['emotion'] == emotion_type:
                        emotion['intensity'] *= multiplier
                        emotion['intensity'] = min(1.0, emotion['intensity'])
        
        return emotion, sentiment
    
    def _generate_insights(self, primary_emotion: Dict, archetypes: List, 
                          spiritual_seeking: List, depth_score: float) -> List[str]:
        """Generate deep psychological and spiritual insights"""
        insights = []
        
        # Emotion-based insights
        emotion = primary_emotion['emotion']
        intensity = primary_emotion['intensity']
        
        if intensity > 0.8:
            insights.append(f"This {emotion} runs deep. There's wisdom here worth exploring.")
        elif intensity < 0.3 and emotion != 'neutral':
            insights.append(f"A subtle whisper of {emotion}. Sometimes our deepest feelings start quietly.")
        
        # Archetype insights
        for arch in archetypes:
            if arch['strength'] > 0.5:
                if arch['is_shadow']:
                    insights.append(f"The {arch['archetype']} archetype is active but in shadow form. This often indicates unhealed aspects seeking attention.")
                else:
                    insights.append(f"The {arch['archetype']} archetype is emerging in your journey.")
        
        # Spiritual seeking insights
        for seeking in spiritual_seeking:
            if seeking['intensity'] > 0.5:
                insights.append(f"You're showing signs of spiritual {seeking['category']}. This is a sacred call.")
        
        # Depth insights
        if depth_score > 0.7:
            insights.append("You're speaking from a place of deep psychological insight. This is fertile ground for growth.")
        
        return insights[:3]  # Return top 3 insights
    
    def _calculate_confidence(self, text: str, primary_emotion: Dict) -> float:
        """Calculate overall confidence in analysis"""
        # More text = higher confidence (up to a point)
        text_length_confidence = min(1.0, len(text.split()) / 50)
        
        # Emotion intensity contributes to confidence
        emotion_confidence = primary_emotion.get('confidence', 0.5)
        
        # Combine
        confidence = (text_length_confidence * 0.3 + emotion_confidence * 0.7)
        
        return min(1.0, confidence)