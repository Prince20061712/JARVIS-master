"""
Advanced query enhancement with expansion, reformulation, and intent detection
"""

import re
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
import numpy as np
from collections import Counter
import spacy
from rake_nltk import Rake
import yake
from keybert import KeyBERT
import nltk
from nltk.corpus import wordnet
import logging

# Download required NLTK data
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

try:
    nlp = spacy.load("en_core_web_sm")
except:
    nlp = None

@dataclass
class EnhancedQuery:
    """Represents an enhanced query with multiple expansions"""
    original: str
    expanded: List[str] = field(default_factory=list)
    reformulated: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    entities: Dict[str, List[str]] = field(default_factory=dict)
    intent: str = "unknown"
    domain: str = "general"
    difficulty: float = 0.5
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class QueryIntent:
    """Query intent types"""
    FACTUAL = "factual"  # What is X?
    PROCEDURAL = "procedural"  # How to do X?
    COMPARATIVE = "comparative"  # Compare X and Y
    CAUSAL = "causal"  # Why does X happen?
    DEFINITIONAL = "definitional"  # Define X
    EXPLANATORY = "explanatory"  # Explain X
    LIST = "list"  # List examples of X
    PROBLEM_SOLVING = "problem_solving"  # Solve X
    UNKNOWN = "unknown"

class QueryDomain:
    """Query domain types"""
    MATHEMATICS = "mathematics"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    COMPUTER_SCIENCE = "computer_science"
    HISTORY = "history"
    LITERATURE = "literature"
    GENERAL = "general"

class QueryEnhancer:
    """
    Advanced query enhancement with multiple expansion strategies and intent detection
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize query enhancer
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Initialize keyword extractors
        self.rake = Rake(
            min_length=1,
            max_length=4,
            include_repeated_phrases=False
        )
        
        self.yake = yake.KeywordExtractor(
            lan="en",
            n=3,
            dedupLim=0.9,
            top=10
        )
        
        try:
            self.keybert = KeyBERT()
            self.use_keybert = True
        except:
            self.use_keybert = False
        
        # Academic vocabulary
        self.academic_terms = self._load_academic_terms()
        
        # Subject-specific terminology
        self.subject_terms = self._load_subject_terms()
        
        # Question patterns
        self.question_patterns = self._load_question_patterns()
        
        self.logger = logging.getLogger(__name__)
    
    def enhance_query(
        self,
        query: str,
        subject: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> EnhancedQuery:
        """
        Enhance query with multiple strategies
        
        Args:
            query: Original query string
            subject: Optional subject context
            context: Additional context
            **kwargs: Additional arguments
            
        Returns:
            EnhancedQuery object
        """
        enhanced = EnhancedQuery(original=query)
        
        # Extract intent
        enhanced.intent = self.detect_intent(query)
        
        # Extract domain
        if subject:
            enhanced.domain = self.map_subject_to_domain(subject)
        else:
            enhanced.domain = self.detect_domain(query)
        
        # Extract entities
        enhanced.entities = self.extract_entities(query)
        
        # Extract keywords
        enhanced.keywords = self.extract_keywords(query, top_n=10)
        
        # Generate expansions
        enhanced.expanded = self.expand_query(
            query,
            enhanced.keywords,
            enhanced.entities,
            enhanced.domain
        )
        
        # Generate reformulations
        enhanced.reformulated = self.reformulate_query(
            query,
            enhanced.intent,
            enhanced.domain
        )
        
        # Assess difficulty
        enhanced.difficulty = self.assess_difficulty(query, enhanced.domain)
        
        # Add metadata
        enhanced.metadata.update({
            'subject': subject,
            'context': context,
            'word_count': len(query.split()),
            'has_question': any(query.lower().startswith(q) for q in ['what', 'why', 'how', 'when', 'where', 'who', 'which']),
            'has_math': bool(re.search(r'[\+\-\*\/\^=]|\d+', query))
        })
        
        return enhanced
    
    def expand_query(
        self,
        query: str,
        keywords: List[str],
        entities: Dict[str, List[str]],
        domain: str
    ) -> List[str]:
        """
        Generate query expansions
        
        Args:
            query: Original query
            keywords: Extracted keywords
            entities: Extracted entities
            domain: Query domain
            
        Returns:
            List of expanded queries
        """
        expansions = []
        
        # 1. Synonym expansion
        synonym_expansions = self._expand_with_synonyms(query, keywords)
        expansions.extend(synonym_expansions)
        
        # 2. Hyponym/Hypernym expansion
        hierarchy_expansions = self._expand_with_hierarchy(query, keywords)
        expansions.extend(hierarchy_expansions)
        
        # 3. Domain-specific term expansion
        domain_expansions = self._expand_with_domain_terms(query, domain)
        expansions.extend(domain_expansions)
        
        # 4. Entity-based expansion
        entity_expansions = self._expand_with_entities(query, entities)
        expansions.extend(entity_expansions)
        
        # 5. Question pattern expansion
        pattern_expansions = self._expand_question_patterns(query)
        expansions.extend(pattern_expansions)
        
        # Remove duplicates and original
        expansions = list(set(expansions))
        if query in expansions:
            expansions.remove(query)
        
        return expansions[:10]  # Limit to top 10
    
    def reformulate_query(
        self,
        query: str,
        intent: str,
        domain: str
    ) -> List[str]:
        """
        Generate query reformulations
        
        Args:
            query: Original query
            intent: Query intent
            domain: Query domain
            
        Returns:
            List of reformulated queries
        """
        reformulations = []
        
        # 1. Convert to declarative form
        declarative = self._to_declarative(query, intent)
        if declarative and declarative != query:
            reformulations.append(declarative)
        
        # 2. Convert to question form
        question = self._to_question(query, intent)
        if question and question != query:
            reformulations.append(question)
        
        # 3. Simplify complex queries
        simplified = self._simplify_query(query)
        if simplified and simplified != query:
            reformulations.append(simplified)
        
        # 4. Domain-specific reformulations
        domain_reform = self._domain_specific_reformulation(query, domain)
        if domain_reform and domain_reform != query:
            reformulations.append(domain_reform)
        
        return list(set(reformulations))[:5]  # Limit to top 5
    
    def detect_intent(self, query: str) -> str:
        """
        Detect query intent
        
        Args:
            query: Query string
            
        Returns:
            Intent type
        """
        query_lower = query.lower().strip()
        
        # Check patterns
        for intent, patterns in self.question_patterns.items():
            for pattern in patterns:
                if pattern.search(query_lower):
                    return intent
        
        # Default intent detection based on structure
        words = query_lower.split()
        
        if any(q in words[:3] for q in ['what', 'define', 'meaning']):
            return QueryIntent.DEFINITIONAL
        elif any(q in words[:3] for q in ['how', 'way', 'method', 'steps']):
            return QueryIntent.PROCEDURAL
        elif any(q in words[:3] for q in ['why', 'reason', 'cause']):
            return QueryIntent.CAUSAL
        elif any(q in words[:3] for q in ['compare', 'difference', 'versus', 'vs']):
            return QueryIntent.COMPARATIVE
        elif any(q in words[:3] for q in ['explain', 'describe']):
            return QueryIntent.EXPLANATORY
        elif any(q in words[:3] for q in ['list', 'examples', 'types']):
            return QueryIntent.LIST
        elif any(q in words[:3] for q in ['solve', 'calculate', 'find']):
            return QueryIntent.PROBLEM_SOLVING
        
        return QueryIntent.FACTUAL
    
    def detect_domain(self, query: str) -> str:
        """
        Detect query domain/subject
        
        Args:
            query: Query string
            
        Returns:
            Domain type
        """
        query_lower = query.lower()
        
        # Check domain-specific terms
        for domain, terms in self.subject_terms.items():
            for term in terms:
                if term in query_lower:
                    return domain
        
        # Use spaCy for entity-based detection
        if nlp:
            doc = nlp(query)
            for ent in doc.ents:
                if ent.label_ in ['SCIENCE', 'LAW', 'ORG']:
                    # Map entity types to domains
                    if any(subj in ent.text.lower() for subj in ['math', 'algebra', 'calculus']):
                        return QueryDomain.MATHEMATICS
                    elif any(subj in ent.text.lower() for subj in ['physic', 'quantum', 'mechanics']):
                        return QueryDomain.PHYSICS
                    elif any(subj in ent.text.lower() for subj in ['chem', 'molecule', 'reaction']):
                        return QueryDomain.CHEMISTRY
                    elif any(subj in ent.text.lower() for subj in ['bio', 'cell', 'organism']):
                        return QueryDomain.BIOLOGY
        
        return QueryDomain.GENERAL
    
    def extract_keywords(self, query: str, top_n: int = 10) -> List[str]:
        """
        Extract keywords from query using multiple methods
        
        Args:
            query: Query string
            top_n: Number of keywords to return
            
        Returns:
            List of keywords
        """
        all_keywords = []
        
        # 1. RAKE extraction
        self.rake.extract_keywords_from_text(query)
        rake_keywords = self.rake.get_ranked_phrases()[:5]
        all_keywords.extend(rake_keywords)
        
        # 2. YAKE extraction
        yake_keywords = self.yake.extract_keywords(query)
        yake_keywords = [kw[0] for kw in yake_keywords[:5]]
        all_keywords.extend(yake_keywords)
        
        # 3. KeyBERT extraction (if available)
        if self.use_keybert:
            try:
                keybert_keywords = self.keybert.extract_keywords(
                    query,
                    keyphrase_ngram_range=(1, 3),
                    stop_words='english',
                    top_n=5
                )
                keybert_keywords = [kw[0] for kw in keybert_keywords]
                all_keywords.extend(keybert_keywords)
            except:
                pass
        
        # 4. Academic term detection
        for term in self.academic_terms:
            if term in query.lower():
                all_keywords.append(term)
        
        # 5. Remove duplicates while preserving order
        seen = set()
        keywords = []
        for kw in all_keywords:
            if kw not in seen:
                seen.add(kw)
                keywords.append(kw)
        
        return keywords[:top_n]
    
    def extract_entities(self, query: str) -> Dict[str, List[str]]:
        """
        Extract named entities from query
        
        Args:
            query: Query string
            
        Returns:
            Dictionary of entity types and values
        """
        entities = {
            'PERSON': [],
            'ORG': [],
            'GPE': [],
            'DATE': [],
            'MONEY': [],
            'PERCENT': [],
            'LAW': [],
            'PRODUCT': [],
            'EVENT': [],
            'WORK_OF_ART': [],
            'SCIENTIFIC_TERM': []
        }
        
        if nlp is None:
            return entities
        
        doc = nlp(query)
        
        for ent in doc.ents:
            if ent.label_ in entities:
                entities[ent.label_].append(ent.text)
            elif ent.label_ in ['SCIENCE', 'TECH']:
                entities['SCIENTIFIC_TERM'].append(ent.text)
        
        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities
    
    def assess_difficulty(self, query: str, domain: str) -> float:
        """
        Assess query difficulty (0-1)
        
        Args:
            query: Query string
            domain: Query domain
            
        Returns:
            Difficulty score
        """
        score = 0.5  # Default medium difficulty
        
        # Factor 1: Vocabulary complexity
        words = query.split()
        avg_word_length = sum(len(w) for w in words) / len(words) if words else 0
        if avg_word_length > 8:
            score += 0.2
        elif avg_word_length > 6:
            score += 0.1
        
        # Factor 2: Academic term presence
        academic_term_count = sum(1 for term in self.academic_terms if term in query.lower())
        score += min(0.3, academic_term_count * 0.05)
        
        # Factor 3: Mathematical notation
        if re.search(r'[\+\-\*\/\^=∫∑√∞]|\$.*\$', query):
            score += 0.2
        
        # Factor 4: Multi-concept query
        if len(self.extract_keywords(query)) > 3:
            score += 0.1
        
        # Factor 5: Domain-specific adjustment
        domain_difficulty = {
            QueryDomain.MATHEMATICS: 0.1,
            QueryDomain.PHYSICS: 0.1,
            QueryDomain.CHEMISTRY: 0.1,
            QueryDomain.BIOLOGY: 0.05,
            QueryDomain.COMPUTER_SCIENCE: 0.1
        }
        score += domain_difficulty.get(domain, 0)
        
        return min(1.0, max(0.0, score))
    
    def map_subject_to_domain(self, subject: str) -> str:
        """Map subject to domain"""
        subject_lower = subject.lower()
        
        mapping = {
            'mathematics': QueryDomain.MATHEMATICS,
            'math': QueryDomain.MATHEMATICS,
            'algebra': QueryDomain.MATHEMATICS,
            'calculus': QueryDomain.MATHEMATICS,
            'physics': QueryDomain.PHYSICS,
            'chemistry': QueryDomain.CHEMISTRY,
            'biology': QueryDomain.BIOLOGY,
            'computer science': QueryDomain.COMPUTER_SCIENCE,
            'cs': QueryDomain.COMPUTER_SCIENCE,
            'programming': QueryDomain.COMPUTER_SCIENCE,
            'history': QueryDomain.HISTORY,
            'literature': QueryDomain.LITERATURE
        }
        
        for key, value in mapping.items():
            if key in subject_lower:
                return value
        
        return QueryDomain.GENERAL
    
    def _expand_with_synonyms(self, query: str, keywords: List[str]) -> List[str]:
        """Expand query using synonyms"""
        expansions = []
        
        for keyword in keywords[:3]:  # Limit to top 3 keywords
            synonyms = set()
            
            # Get WordNet synonyms
            for syn in wordnet.synsets(keyword):
                for lemma in syn.lemmas():
                    synonym = lemma.name().replace('_', ' ')
                    if synonym != keyword and len(synonym.split()) <= 2:
                        synonyms.add(synonym)
            
            # Create expansion
            for synonym in list(synonyms)[:2]:  # Limit to 2 synonyms per keyword
                expanded = query.replace(keyword, synonym)
                if expanded != query:
                    expansions.append(expanded)
        
        return expansions
    
    def _expand_with_hierarchy(self, query: str, keywords: List[str]) -> List[str]:
        """Expand using hypernyms and hyponyms"""
        expansions = []
        
        for keyword in keywords[:2]:
            # Get hypernyms (more general)
            for syn in wordnet.synsets(keyword):
                for hypernym in syn.hypernyms()[:2]:
                    for lemma in hypernym.lemmas():
                        hyper = lemma.name().replace('_', ' ')
                        expanded = query.replace(keyword, hyper)
                        if expanded != query:
                            expansions.append(expanded)
                
                # Get hyponyms (more specific)
                for hyponym in syn.hyponyms()[:2]:
                    for lemma in hyponym.lemmas():
                        hypo = lemma.name().replace('_', ' ')
                        expanded = query.replace(keyword, hypo)
                        if expanded != query:
                            expansions.append(expanded)
        
        return expansions
    
    def _expand_with_domain_terms(self, query: str, domain: str) -> List[str]:
        """Expand query with domain-specific terminology"""
        expansions = []
        
        domain_terms = self.subject_terms.get(domain, [])
        for term in domain_terms[:3]:
            if term not in query.lower():
                expansions.append(f"{query} related to {term}")
        
        return expansions
    
    def _expand_with_entities(self, query: str, entities: Dict[str, List[str]]) -> List[str]:
        """Expand query using extracted entities"""
        expansions = []
        
        for entity_type, entity_list in entities.items():
            for entity in entity_list[:2]:
                if entity not in query:
                    expansions.append(f"{query} about {entity}")
        
        return expansions
    
    def _expand_question_patterns(self, query: str) -> List[str]:
        """Expand by converting between question types"""
        expansions = []
        
        # Convert between question types
        if query.lower().startswith('what'):
            # What is X? -> Define X
            subject = query[4:].strip()
            expansions.append(f"define {subject}")
            expansions.append(f"explain {subject}")
        elif query.lower().startswith('how'):
            # How to do X? -> Steps to do X
            subject = query[3:].strip()
            expansions.append(f"steps to {subject}")
            expansions.append(f"method for {subject}")
        elif query.lower().startswith('why'):
            # Why X? -> Reasons for X
            subject = query[3:].strip()
            expansions.append(f"reasons for {subject}")
            expansions.append(f"causes of {subject}")
        
        return expansions
    
    def _to_declarative(self, query: str, intent: str) -> str:
        """Convert question to declarative form"""
        if intent == QueryIntent.DEFINITIONAL:
            # "What is X?" -> "X is"
            match = re.match(r'what\s+is\s+(.+)', query, re.IGNORECASE)
            if match:
                return f"{match.group(1)} is"
        
        elif intent == QueryIntent.PROCEDURAL:
            # "How to X?" -> "Steps to X"
            match = re.match(r'how\s+to\s+(.+)', query, re.IGNORECASE)
            if match:
                return f"steps to {match.group(1)}"
        
        elif intent == QueryIntent.CAUSAL:
            # "Why X?" -> "Reasons for X"
            match = re.match(r'why\s+(.+)', query, re.IGNORECASE)
            if match:
                return f"reasons for {match.group(1)}"
        
        return query
    
    def _to_question(self, query: str, intent: str) -> str:
        """Convert declarative to question form"""
        if intent == QueryIntent.FACTUAL and not query.endswith('?'):
            return f"What is {query}?"
        
        return query
    
    def _simplify_query(self, query: str) -> str:
        """Simplify complex queries"""
        # Remove unnecessary words
        stop_words = {'please', 'can', 'you', 'tell', 'me', 'about', 'the'}
        words = query.split()
        simplified = [w for w in words if w.lower() not in stop_words]
        
        return ' '.join(simplified)
    
    def _domain_specific_reformulation(self, query: str, domain: str) -> str:
        """Apply domain-specific reformulations"""
        if domain == QueryDomain.MATHEMATICS:
            # Add mathematical context
            if not any(term in query for term in ['equation', 'formula', 'theorem']):
                return f"mathematical {query}"
        
        elif domain == QueryDomain.PHYSICS:
            if not any(term in query for term in ['law', 'principle', 'theory']):
                return f"physics concept of {query}"
        
        elif domain == QueryDomain.CHEMISTRY:
            if not any(term in query for term in ['reaction', 'compound', 'element']):
                return f"chemical {query}"
        
        return query
    
    def _load_academic_terms(self) -> Set[str]:
        """Load academic vocabulary"""
        return {
            'theory', 'theorem', 'lemma', 'proof', 'hypothesis',
            'analysis', 'synthesis', 'evaluation', 'application',
            'methodology', 'paradigm', 'framework', 'model',
                        'concept', 'principle', 'doctrine', 'doctrine', 'axiom', 'postulate',
            'corollary', 'proposition', 'conjecture', 'algorithm', 'heuristic',
            'empirical', 'theoretical', 'quantitative', 'qualitative',
            'deductive', 'inductive', 'abductive', 'inference', 'premise',
            'conclusion', 'argument', 'fallacy', 'paradox', 'dilemma'
        }
    
    def _load_subject_terms(self) -> Dict[str, List[str]]:
        """Load subject-specific terminology"""
        return {
            QueryDomain.MATHEMATICS: [
                'algebra', 'calculus', 'geometry', 'trigonometry', 'statistics',
                'probability', 'equation', 'function', 'derivative', 'integral',
                'matrix', 'vector', 'theorem', 'proof', 'graph', 'algorithm'
            ],
            QueryDomain.PHYSICS: [
                'quantum', 'mechanics', 'thermodynamics', 'electromagnetism',
                'relativity', 'particle', 'wave', 'force', 'energy', 'momentum',
                'velocity', 'acceleration', 'gravity', 'field', 'radiation'
            ],
            QueryDomain.CHEMISTRY: [
                'reaction', 'compound', 'element', 'molecule', 'atom',
                'bond', 'acid', 'base', 'salt', 'solution', 'concentration',
                'pH', 'oxidation', 'reduction', 'catalyst', 'polymer'
            ],
            QueryDomain.BIOLOGY: [
                'cell', 'DNA', 'protein', 'enzyme', 'organism', 'evolution',
                'genetics', 'ecosystem', 'species', 'population', 'habitat',
                'photosynthesis', 'respiration', 'reproduction', 'metabolism'
            ],
            QueryDomain.COMPUTER_SCIENCE: [
                'algorithm', 'data', 'structure', 'programming', 'software',
                'hardware', 'network', 'database', 'security', 'encryption',
                'artificial', 'intelligence', 'machine', 'learning', 'cloud'
            ],
            QueryDomain.HISTORY: [
                'ancient', 'medieval', 'modern', 'war', 'revolution',
                'empire', 'civilization', 'dynasty', 'kingdom', 'republic',
                'treaty', 'battle', 'movement', 'reform', 'renaissance'
            ],
            QueryDomain.LITERATURE: [
                'novel', 'poetry', 'drama', 'prose', 'fiction', 'nonfiction',
                'genre', 'theme', 'character', 'plot', 'setting', 'symbolism',
                'metaphor', 'allegory', 'narrative', 'protagonist'
            ]
        }
    
    def _load_question_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Load regex patterns for question intent detection"""
        return {
            QueryIntent.DEFINITIONAL: [
                re.compile(r'^what\s+is'),
                re.compile(r'^define'),
                re.compile(r'^give\s+the\s+meaning'),
                re.compile(r'^what\s+does\s+.+\s+mean')
            ],
            QueryIntent.PROCEDURAL: [
                re.compile(r'^how\s+to'),
                re.compile(r'^how\s+do\s+I'),
                re.compile(r'^what\s+are\s+the\s+steps'),
                re.compile(r'^what\s+is\s+the\s+process')
            ],
            QueryIntent.CAUSAL: [
                re.compile(r'^why'),
                re.compile(r'^what\s+causes'),
                re.compile(r'^what\s+is\s+the\s+reason'),
                re.compile(r'^how\s+does\s+.+\s+cause')
            ],
            QueryIntent.COMPARATIVE: [
                re.compile(r'^compare'),
                re.compile(r'^what\s+is\s+the\s+difference'),
                re.compile(r'^how\s+is\s+.+\s+different'),
                re.compile(r'^similarities?\s+between')
            ],
            QueryIntent.EXPLANATORY: [
                re.compile(r'^explain'),
                re.compile(r'^describe'),
                re.compile(r'^elaborate'),
                re.compile(r'^clarify')
            ],
            QueryIntent.LIST: [
                re.compile(r'^list'),
                re.compile(r'^what\s+are\s+the\s+types'),
                re.compile(r'^give\s+examples'),
                re.compile(r'^name\s+some')
            ],
            QueryIntent.PROBLEM_SOLVING: [
                re.compile(r'^solve'),
                re.compile(r'^calculate'),
                re.compile(r'^find'),
                re.compile(r'^determine'),
                re.compile(r'^evaluate'),
                re.compile(r'^simplify')
            ]
        }