"""
Advanced topic extraction with multiple algorithms and educational focus
"""

import re
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import Counter, defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import networkx as nx
from rake_nltk import Rake
import yake
from keybert import KeyBERT
import spacy
from textblob import TextBlob
from dataclasses import dataclass, field
import logging
from heapq import nlargest

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    nlp = None

@dataclass
class ExtractedTopic:
    """Represents an extracted topic with metadata"""
    name: str
    confidence: float
    source: str  # Extraction method
    related_terms: List[str] = field(default_factory=list)
    importance: float = 0.5
    subtopics: List[str] = field(default_factory=list)
    embeddings: Optional[np.ndarray] = None

class TopicExtractor:
    """
    Advanced topic extractor with multiple algorithms for educational content
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize topic extractor
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Initialize extractors
        self.rake = Rake(
            min_length=1,
            max_length=4,
            include_repeated_phrases=False
        )
        
        self.yake = yake.KeywordExtractor(
            lan="en",
            n=3,
            dedupLim=0.9,
            top=20
        )
        
        try:
            self.keybert = KeyBERT()
            self.use_keybert = True
        except:
            self.use_keybert = False
        
        # TF-IDF Vectorizer
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 3)
        )
        
        # LDA for topic modeling
        self.lda = LatentDirichletAllocation(
            n_components=self.config.get('num_topics', 10),
            random_state=42,
            learning_method='online'
        )
        
        # Educational domain knowledge
        self.educational_terms = self._load_educational_terms()
        self.subject_specific_terms = self._load_subject_terms()
        
        # Stop words for filtering
        self.stop_words = set([
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'were',
            'has', 'have', 'had', 'been', 'being', 'be', 'are', 'am'
        ])
        
        self.logger = logging.getLogger(__name__)
    
    def extract_topics(
        self,
        text: str,
        method: str = 'hybrid',
        num_topics: int = 20,
        **kwargs
    ) -> List[ExtractedTopic]:
        """
        Extract topics from text using specified method
        
        Args:
            text: Input text
            method: Extraction method (tfidf, lda, rake, yake, keybert, hybrid)
            num_topics: Number of topics to extract
            **kwargs: Additional arguments
            
        Returns:
            List of extracted topics
        """
        if not text:
            return []
        
        # Clean text
        text = self._clean_text(text)
        
        # Select extraction method
        if method == 'tfidf':
            topics = self._extract_tfidf_topics(text, num_topics)
        elif method == 'lda':
            topics = self._extract_lda_topics(text, num_topics)
        elif method == 'rake':
            topics = self._extract_rake_topics(text, num_topics)
        elif method == 'yake':
            topics = self._extract_yake_topics(text, num_topics)
        elif method == 'keybert' and self.use_keybert:
            topics = self._extract_keybert_topics(text, num_topics)
        else:  # hybrid
            topics = self._extract_hybrid_topics(text, num_topics)
        
        # Enhance with educational context
        topics = self._enhance_topics(topics, text)
        
        return topics[:num_topics]
    
    def extract_hierarchical_topics(
        self,
        text: str,
        max_depth: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extract hierarchical topic structure
        
        Args:
            text: Input text
            max_depth: Maximum hierarchy depth
            **kwargs: Additional arguments
            
        Returns:
            Hierarchical topic structure
        """
        # First, extract main topics
        main_topics = self.extract_topics(text, num_topics=10, **kwargs)
        
        hierarchy = {}
        
        for topic in main_topics:
            # Find sentences containing the topic
            topic_sentences = self._extract_sentences_with_topic(text, topic.name)
            
            if topic_sentences:
                # Extract subtopics from these sentences
                subtopics = self.extract_topics(
                    ' '.join(topic_sentences),
                    num_topics=5,
                    **kwargs
                )
                
                hierarchy[topic.name] = {
                    'topic': topic,
                    'subtopics': [st.name for st in subtopics],
                    'confidence': topic.confidence
                }
        
        return hierarchy
    
    def extract_relationships(
        self,
        topics: List[str],
        text: str,
        window_size: int = 100
    ) -> nx.Graph:
        """
        Extract relationships between topics
        
        Args:
            topics: List of topics
            text: Input text
            window_size: Context window size
            
        Returns:
            NetworkX graph of topic relationships
        """
        graph = nx.Graph()
        
        # Add nodes
        for topic in topics:
            graph.add_node(topic, weight=0)
        
        # Calculate co-occurrence
        words = text.split()
        
        for i, topic in enumerate(topics):
            topic_words = topic.lower().split()
            
            for j, other_topic in enumerate(topics[i+1:], i+1):
                other_words = other_topic.lower().split()
                
                # Count co-occurrences within window
                co_occurrences = 0
                
                for idx, word in enumerate(words):
                    if any(tw == word for tw in topic_words):
                        # Look for other topic within window
                        window = words[idx:idx + window_size]
                        if any(ow in window for ow in other_words):
                            co_occurrences += 1
                
                if co_occurrences > 0:
                    graph.add_edge(topic, other_topic, weight=co_occurrences)
        
        return graph
    
    def _extract_tfidf_topics(
        self,
        text: str,
        num_topics: int
    ) -> List[ExtractedTopic]:
        """Extract topics using TF-IDF"""
        # Split into sentences
        sentences = self._split_into_sentences(text)
        
        if len(sentences) < 2:
            return []
        
        # Create TF-IDF matrix
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(sentences)
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            
            # Get top terms across all sentences
            avg_tfidf = np.asarray(tfidf_matrix.mean(axis=0)).flatten()
            top_indices = avg_tfidf.argsort()[-num_topics:][::-1]
            
            topics = []
            for idx in top_indices:
                if avg_tfidf[idx] > 0:
                    topic = ExtractedTopic(
                        name=feature_names[idx],
                        confidence=float(avg_tfidf[idx]),
                        source='tfidf'
                    )
                    topics.append(topic)
            
            return topics
            
        except Exception as e:
            self.logger.error(f"TF-IDF extraction failed: {e}")
            return []
    
    def _extract_lda_topics(
        self,
        text: str,
        num_topics: int
    ) -> List[ExtractedTopic]:
        """Extract topics using LDA"""
        # Split into sentences
        sentences = self._split_into_sentences(text)
        
        if len(sentences) < 5:
            return []
        
        try:
            # Create document-term matrix
            dtm = self.tfidf_vectorizer.fit_transform(sentences)
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            
            # Fit LDA
            self.lda.fit(dtm)
            
            # Get top terms for each topic
            topics = []
            for topic_idx, topic in enumerate(self.lda.components_):
                top_term_indices = topic.argsort()[-10:][::-1]
                
                for idx in top_term_indices[:num_topics // 5]:
                    term = feature_names[idx]
                    weight = topic[idx]
                    
                    if weight > 0:
                        extracted_topic = ExtractedTopic(
                            name=term,
                            confidence=float(weight),
                            source='lda'
                        )
                        topics.append(extracted_topic)
            
            return topics
            
        except Exception as e:
            self.logger.error(f"LDA extraction failed: {e}")
            return []
    
    def _extract_rake_topics(
        self,
        text: str,
        num_topics: int
    ) -> List[ExtractedTopic]:
        """Extract topics using RAKE"""
        self.rake.extract_keywords_from_text(text)
        rake_keywords = self.rake.get_ranked_phrases_with_scores()
        
        topics = []
        for score, phrase in rake_keywords[:num_topics]:
            if len(phrase.split()) <= 3:  # Keep phrases short
                topic = ExtractedTopic(
                    name=phrase,
                    confidence=float(score),
                    source='rake'
                )
                topics.append(topic)
        
        return topics
    
    def _extract_yake_topics(
        self,
        text: str,
        num_topics: int
    ) -> List[ExtractedTopic]:
        """Extract topics using YAKE"""
        yake_keywords = self.yake.extract_keywords(text)
        
        topics = []
        for phrase, score in yake_keywords[:num_topics]:
            # YAKE gives lower scores for better keywords, so invert
            confidence = 1.0 / (1.0 + score)
            
            topic = ExtractedTopic(
                name=phrase,
                confidence=confidence,
                source='yake'
            )
            topics.append(topic)
        
        return topics
    
    def _extract_keybert_topics(
        self,
        text: str,
        num_topics: int
    ) -> List[ExtractedTopic]:
        """Extract topics using KeyBERT"""
        if not self.use_keybert:
            return []
        
        try:
            keybert_keywords = self.keybert.extract_keywords(
                text,
                keyphrase_ngram_range=(1, 3),
                stop_words='english',
                top_n=num_topics
            )
            
            topics = []
            for phrase, score in keybert_keywords:
                topic = ExtractedTopic(
                    name=phrase,
                    confidence=float(score),
                    source='keybert'
                )
                topics.append(topic)
            
            return topics
            
        except Exception as e:
            self.logger.error(f"KeyBERT extraction failed: {e}")
            return []
    
    def _extract_hybrid_topics(
        self,
        text: str,
        num_topics: int
    ) -> List[ExtractedTopic]:
        """
        Hybrid topic extraction combining multiple methods
        """
        all_topics = []
        
        # Get topics from all methods
        methods = [
            self._extract_tfidf_topics(text, num_topics * 2),
            self._extract_rake_topics(text, num_topics * 2),
            self._extract_yake_topics(text, num_topics * 2)
        ]
        
        if self.use_keybert:
            methods.append(self._extract_keybert_topics(text, num_topics * 2))
        
        # Combine and weight
        topic_scores = defaultdict(float)
        topic_sources = defaultdict(list)
        
        for method_topics in methods:
            for topic in method_topics:
                # Normalize confidence
                confidence = min(1.0, topic.confidence)
                topic_scores[topic.name] += confidence
                topic_sources[topic.name].append(topic.source)
        
        # Create final topics
        topics = []
        for name, score in sorted(
            topic_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:num_topics]:
            # Average confidence
            avg_confidence = score / len(topic_sources[name])
            
            topic = ExtractedTopic(
                name=name,
                confidence=avg_confidence,
                source='hybrid',
                related_terms=[],  # Will be filled in _enhance_topics
                importance=avg_confidence
            )
            topics.append(topic)
        
        return topics
    
    def _enhance_topics(
        self,
        topics: List[ExtractedTopic],
        text: str
    ) -> List[ExtractedTopic]:
        """
        Enhance topics with additional information
        """
        # Calculate importance based on position
        sentences = self._split_into_sentences(text)
        first_para = ' '.join(sentences[:5]) if sentences else ''
        last_para = ' '.join(sentences[-5:]) if sentences else ''
        
        for topic in topics:
            # Boost confidence if topic appears in important sections
            if topic.name.lower() in first_para.lower():
                topic.confidence *= 1.2
                topic.importance *= 1.2
            
            if topic.name.lower() in last_para.lower():
                topic.confidence *= 1.1
                topic.importance *= 1.1
            
            # Find related terms
            topic.related_terms = self._find_related_terms(topic.name, text)
            
            # Cap confidence at 1.0
            topic.confidence = min(1.0, topic.confidence)
            topic.importance = min(1.0, topic.importance)
        
        return sorted(topics, key=lambda x: x.confidence, reverse=True)
    
    def _find_related_terms(
        self,
        topic: str,
        text: str,
        num_terms: int = 5
    ) -> List[str]:
        """
        Find terms related to a topic using co-occurrence
        """
        if nlp is None:
            return []
        
        # Find sentences containing the topic
        topic_sentences = self._extract_sentences_with_topic(text, topic)
        
        if not topic_sentences:
            return []
        
        # Extract noun phrases from these sentences
        related = Counter()
        
        for sentence in topic_sentences:
            doc = nlp(sentence)
            
            # Extract noun chunks
            for chunk in doc.noun_chunks:
                chunk_text = chunk.text.lower()
                if (chunk_text != topic.lower() and
                    chunk_text not in self.stop_words and
                    len(chunk_text.split()) <= 3):
                    related[chunk.text] += 1
        
        # Return most frequent related terms
        return [term for term, _ in related.most_common(num_terms)]
    
    def _extract_sentences_with_topic(
        self,
        text: str,
        topic: str
    ) -> List[str]:
        """Extract sentences containing the topic"""
        sentences = self._split_into_sentences(text)
        topic_lower = topic.lower()
        
        topic_sentences = []
        for sent in sentences:
            if topic_lower in sent.lower():
                topic_sentences.append(sent)
        
        return topic_sentences
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep important punctuation
        text = re.sub(r'[^\w\s.,;:!?-]', '', text)
        
        return text.strip()
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        if nlp:
            doc = nlp(text)
            return [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        else:
            # Simple sentence splitting
            sentences = re.split(r'[.!?]+', text)
            return [s.strip() for s in sentences if s.strip()]
    
    def _load_educational_terms(self) -> Set[str]:
        """Load common educational terms"""
        return {
            'concept', 'principle', 'theory', 'law', 'theorem',
            'formula', 'equation', 'method', 'technique', 'approach',
            'analysis', 'synthesis', 'evaluation', 'application',
            'understanding', 'knowledge', 'skill', 'competency',
            'objective', 'outcome', 'goal', 'aim', 'purpose',
            'definition', 'example', 'illustration', 'demonstration',
            'practice', 'exercise', 'problem', 'solution', 'calculation'
        }
    
    def _load_subject_terms(self) -> Dict[str, Set[str]]:
        """Load subject-specific terminology"""
        return {
            'mathematics': {
                'algebra', 'calculus', 'geometry', 'trigonometry',
                'equation', 'function', 'derivative', 'integral',
                'matrix', 'vector', 'probability', 'statistics'
            },
            'physics': {
                'force', 'energy', 'motion', 'velocity', 'acceleration',
                'quantum', 'relativity', 'thermodynamics', 'electromagnetism',
                'wave', 'particle', 'field', 'radiation', 'gravity'
            },
            'chemistry': {
                'element', 'compound', 'molecule', 'atom', 'bond',
                'reaction', 'acid', 'base', 'salt', 'solution',
                'concentration', 'pH', 'oxidation', 'reduction'
            },
            'biology': {
                'cell', 'tissue', 'organ', 'system', 'organism',
                'DNA', 'RNA', 'protein', 'enzyme', 'gene',
                'evolution', 'ecosystem', 'population', 'species'
            },
            'computer_science': {
                'algorithm', 'data', 'structure', 'programming',
                'software', 'hardware', 'network', 'database',
                'security', 'encryption', 'artificial', 'intelligence'
            }
        }