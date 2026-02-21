"""
Advanced difficulty mapping for educational content
"""

import re
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from textstat import textstat
from collections import Counter

# Load spaCy model
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except:
    nlp = None

class DifficultyLevel(Enum):
    """Difficulty levels"""
    BEGINNER = "beginner"
    EASY = "easy"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

@dataclass
class DifficultyMetrics:
    """Comprehensive difficulty metrics"""
    overall: float = 0.5
    level: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    
    # Text-based metrics
    readability_score: float = 0.5
    vocabulary_complexity: float = 0.5
    sentence_complexity: float = 0.5
    
    # Content-based metrics
    concept_density: float = 0.5
    abstraction_level: float = 0.5
    technical_depth: float = 0.5
    
    # Educational metrics
    prerequisite_count: int = 0
    formula_density: float = 0.0
    citation_density: float = 0.0
    
    # Metadata
    confidence: float = 0.5
    factors: Dict[str, float] = field(default_factory=dict)

class DifficultyMapper:
    """
    Advanced difficulty mapper for educational content
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize difficulty mapper
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Load complexity indicators
        self.complex_terms = self._load_complex_terms()
        self.abstract_terms = self._load_abstract_terms()
        self.technical_indicators = self._load_technical_indicators()
        
        # Formula patterns
        self.formula_patterns = self._compile_formula_patterns()
        
        # Readability thresholds
        self.readability_thresholds = {
            'beginner': (90, 100),
            'easy': (70, 89),
            'intermediate': (50, 69),
            'advanced': (30, 49),
            'expert': (0, 29)
        }
        
        self.logger = logging.getLogger(__name__)
    
    def estimate_difficulty(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> DifficultyMetrics:
        """
        Estimate difficulty of text
        
        Args:
            text: Input text
            context: Additional context (subject, topic, etc.)
            
        Returns:
            DifficultyMetrics object
        """
        metrics = DifficultyMetrics()
        
        # Calculate individual metrics
        metrics.readability_score = self._calculate_readability(text)
        metrics.vocabulary_complexity = self._calculate_vocabulary_complexity(text)
        metrics.sentence_complexity = self._calculate_sentence_complexity(text)
        metrics.concept_density = self._calculate_concept_density(text)
        metrics.abstraction_level = self._calculate_abstraction_level(text)
        metrics.technical_depth = self._calculate_technical_depth(text, context)
        
        # Count special elements
        metrics.formula_density = self._calculate_formula_density(text)
        metrics.citation_density = self._calculate_citation_density(text)
        
        # Calculate overall difficulty
        metrics.overall = self._calculate_overall_difficulty(metrics)
        
        # Determine difficulty level
        metrics.level = self._get_difficulty_level(metrics.overall)
        
        # Store individual factor scores
        metrics.factors = {
            'readability': metrics.readability_score,
            'vocabulary': metrics.vocabulary_complexity,
            'sentence': metrics.sentence_complexity,
            'concept_density': metrics.concept_density,
            'abstraction': metrics.abstraction_level,
            'technical_depth': metrics.technical_depth,
            'formula_density': metrics.formula_density,
            'citation_density': metrics.citation_density
        }
        
        # Calculate confidence based on text length
        word_count = len(text.split())
        metrics.confidence = min(1.0, word_count / 500)  # Max confidence at 500 words
        
        return metrics
    
    def get_level(self, difficulty_score: float) -> str:
        """Convert numeric difficulty to level"""
        if difficulty_score < 0.2:
            return DifficultyLevel.BEGINNER.value
        elif difficulty_score < 0.4:
            return DifficultyLevel.EASY.value
        elif difficulty_score < 0.6:
            return DifficultyLevel.INTERMEDIATE.value
        elif difficulty_score < 0.8:
            return DifficultyLevel.ADVANCED.value
        else:
            return DifficultyLevel.EXPERT.value
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate readability score (normalized 0-1, higher = easier)"""
        try:
            # Use multiple readability formulas
            flesch = textstat.flesch_reading_ease(text)
            fog = textstat.gunning_fog(text)
            coleman = textstat.coleman_liau_index(text)
            
            # Normalize scores (higher is easier)
            flesch_norm = flesch / 100  # Flesch is 0-100
            fog_norm = max(0, min(1, 1 - (fog - 6) / 12))  # Fog: 6=easy, 18=hard
            coleman_norm = max(0, min(1, 1 - (coleman - 5) / 15))  # Coleman: 5=easy, 20=hard
            
            # Average
            readability = np.mean([flesch_norm, fog_norm, coleman_norm])
            return float(readability)
            
        except:
            return 0.5
    
    def _calculate_vocabulary_complexity(self, text: str) -> float:
        """Calculate vocabulary complexity (0-1, higher = more complex)"""
        words = text.split()
        
        if len(words) < 10:
            return 0.5
        
        # Average word length
        avg_word_length = np.mean([len(w) for w in words])
        length_score = min(1.0, (avg_word_length - 4) / 6)  # 4 chars = simple, 10+ = complex
        
        # Unique word ratio (type-token ratio)
        unique_ratio = len(set(w.lower() for w in words)) / len(words)
        
        # Long word frequency (>6 characters)
        long_words = [w for w in words if len(w) > 6]
        long_word_ratio = len(long_words) / len(words)
        
        # Presence of complex terms
        complex_term_count = sum(1 for term in self.complex_terms if term in text.lower())
        complex_term_score = min(1.0, complex_term_count / 10)
        
        # Combine metrics
        complexity = np.mean([
            length_score * 0.3,
            unique_ratio * 0.2,
            long_word_ratio * 0.3,
            complex_term_score * 0.2
        ])
        
        return float(complexity)
    
    def _calculate_sentence_complexity(self, text: str) -> float:
        """Calculate sentence complexity (0-1, higher = more complex)"""
        if nlp is None:
            return 0.5
        
        doc = nlp(text)
        sentences = list(doc.sents)
        
        if len(sentences) < 2:
            return 0.5
        
        complexities = []
        
        for sent in sentences:
            sent_complexity = 0.0
            
            # Average words per sentence
            word_count = len([token for token in sent if not token.is_punct])
            if word_count > 30:
                sent_complexity += 0.3
            elif word_count > 20:
                sent_complexity += 0.2
            elif word_count > 10:
                sent_complexity += 0.1
            
            # Clause count (approximated by number of verbs)
            verb_count = len([token for token in sent if token.pos_ == "VERB"])
            if verb_count > 3:
                sent_complexity += 0.3
            elif verb_count > 2:
                sent_complexity += 0.2
            elif verb_count > 1:
                sent_complexity += 0.1
            
            # Subordinate clauses (approximated by subordinating conjunctions)
            subord_count = len([token for token in sent if token.dep_ == "mark"])
            if subord_count > 2:
                sent_complexity += 0.3
            elif subord_count > 1:
                sent_complexity += 0.2
            
            complexities.append(min(1.0, sent_complexity))
        
        return float(np.mean(complexities))
    
    def _calculate_concept_density(self, text: str) -> float:
        """Calculate concept density (0-1, higher = more dense)"""
        if nlp is None:
            return 0.5
        
        doc = nlp(text)
        
        # Count noun phrases (potential concepts)
        noun_phrases = list(doc.noun_chunks)
        
        # Count technical terms
        technical_terms = [token.text for token in doc 
                          if token.text.lower() in self.technical_indicators]
        
        # Normalize by text length
        word_count = len([token for token in doc if not token.is_punct])
        
        if word_count == 0:
            return 0.5
        
        concept_density = (len(noun_phrases) + len(technical_terms)) / word_count
        
        # Normalize to 0-1 (assuming max density around 0.5)
        return min(1.0, concept_density * 2)
    
    def _calculate_abstraction_level(self, text: str) -> float:
        """Calculate abstraction level (0-1, higher = more abstract)"""
        if nlp is None:
            return 0.5
        
        doc = nlp(text)
        
        # Count abstract terms
        abstract_count = 0
        total_words = 0
        
        for token in doc:
            if not token.is_punct and not token.is_stop:
                total_words += 1
                if token.text.lower() in self.abstract_terms:
                    abstract_count += 1
                # Check for abstract suffixes
                elif token.text.endswith(('ism', 'ity', 'tion', 'ness', 'ence', 'ance')):
                    abstract_count += 0.5
        
        if total_words == 0:
            return 0.5
        
        abstraction = abstract_count / total_words
        return min(1.0, abstraction * 3)  # Scale factor
    
    def _calculate_technical_depth(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate technical depth (0-1, higher = more technical)"""
        technical_score = 0.0
        
        # Check for technical indicators
        technical_count = 0
        for indicator, weight in self.technical_indicators.items():
            if indicator in text.lower():
                technical_count += weight
        
        technical_score += min(0.6, technical_count / 10)
        
        # Check for formulas
        formula_count = len(re.findall(self.formula_patterns['math'], text))
        if formula_count > 0:
            technical_score += min(0.3, formula_count * 0.05)
        
        # Check for citations
        citation_count = len(re.findall(r'\[\d+\]|\(\w+ et al\.', text))
        if citation_count > 0:
            technical_score += min(0.2, citation_count * 0.02)
        
        # Adjust for subject
        if context and 'subject' in context:
            subject = context['subject'].lower()
            if subject in ['mathematics', 'physics', 'chemistry']:
                technical_score += 0.1
        
        return min(1.0, technical_score)
    
    def _calculate_formula_density(self, text: str) -> float:
        """Calculate density of mathematical formulas"""
        # Count formula-like patterns
        formula_count = 0
        for pattern in self.formula_patterns.values():
            formula_count += len(re.findall(pattern, text))
        
        # Normalize by text length
        word_count = len(text.split())
        if word_count == 0:
            return 0.0
        
        density = formula_count / word_count
        return min(1.0, density * 5)  # Scale factor
    
    def _calculate_citation_density(self, text: str) -> float:
        """Calculate density of citations"""
        citation_patterns = [
            r'\[\d+\]',
            r'\(\w+ et al\.\s*\d{4}\)',
            r'\(\w+,\s*\d{4}\)',
            r'according to \w+'
        ]
        
        citation_count = 0
        for pattern in citation_patterns:
            citation_count += len(re.findall(pattern, text, re.IGNORECASE))
        
        # Normalize by text length
        word_count = len(text.split())
        if word_count == 0:
            return 0.0
        
        density = citation_count / word_count
        return min(1.0, density * 10)  # Scale factor
    
    def _calculate_overall_difficulty(self, metrics: DifficultyMetrics) -> float:
        """Calculate overall difficulty score"""
        weights = {
            'readability': 0.15,  # Note: readability is inverse (higher = easier)
            'vocabulary': 0.15,
            'sentence': 0.15,
            'concept_density': 0.15,
            'abstraction': 0.10,
            'technical_depth': 0.15,
            'formula_density': 0.10,
            'citation_density': 0.05
        }
        
        # Invert readability (lower readability = higher difficulty)
        readability_difficulty = 1.0 - metrics.readability_score
        
        difficulty = (
            readability_difficulty * weights['readability'] +
            metrics.vocabulary_complexity * weights['vocabulary'] +
            metrics.sentence_complexity * weights['sentence'] +
            metrics.concept_density * weights['concept_density'] +
            metrics.abstraction_level * weights['abstraction'] +
            metrics.technical_depth * weights['technical_depth'] +
            metrics.formula_density * weights['formula_density'] +
            metrics.citation_density * weights['citation_density']
        )
        
        return difficulty
    
    def _get_difficulty_level(self, score: float) -> DifficultyLevel:
        """Convert numeric score to difficulty level"""
        if score < 0.2:
            return DifficultyLevel.BEGINNER
        elif score < 0.4:
            return DifficultyLevel.EASY
        elif score < 0.6:
            return DifficultyLevel.INTERMEDIATE
        elif score < 0.8:
            return DifficultyLevel.ADVANCED
        else:
            return DifficultyLevel.EXPERT
    
    def _load_complex_terms(self) -> Set[str]:
        """Load vocabulary of complex terms"""
        return {
            'paradigm', 'heuristic', 'ontology', 'epistemology',
            'phenomenon', 'hypothesis', 'theorem', 'corollary',
            'algorithm', 'heterogeneous', 'homogeneous', 'anisotropic',
            'stochastic', 'deterministic', 'probabilistic', 'empirical',
            'theoretical', 'quantitative', 'qualitative', 'methodological'
        }
    
    def _load_abstract_terms(self) -> Set[str]:
        """Load vocabulary of abstract terms"""
        return {
            'concept', 'idea', 'notion', 'theory', 'principle',
            'abstraction', 'generalization', 'speculation', 'hypothesis',
            'paradigm', 'framework', 'model', 'approach', 'perspective',
            'philosophy', 'ideology', 'doctrine', 'dogma', 'belief'
        }
    
    def _load_technical_indicators(self) -> Dict[str, float]:
        """Load technical indicators with weights"""
        return {
            'theorem': 1.0,
            'proof': 0.8,
            'lemma': 0.9,
            'corollary': 0.9,
            'definition': 0.5,
            'equation': 0.7,
            'formula': 0.6,
            'algorithm': 0.8,
            'function': 0.4,
            'variable': 0.3,
            'parameter': 0.4,
            'coefficient': 0.6,
            'matrix': 0.7,
            'vector': 0.6,
            'derivative': 0.8,
            'integral': 0.8,
            'quantum': 0.9,
            'relativity': 0.9,
            'thermodynamics': 0.8
        }
    
    def _compile_formula_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for mathematical formulas"""
        return {
            'math': re.compile(r'[\+\-\*\/\^=∫∑√∞π]|\$.*?\$|\\\(.*?\\\)|\\\[.*?\\\]'),
            'equation': re.compile(r'[A-Za-z]\s*=\s*[^.!?]+'),
            'subscript': re.compile(r'[A-Za-z]_\d+'),
            'superscript': re.compile(r'[A-Za-z]\^\d+')
        }