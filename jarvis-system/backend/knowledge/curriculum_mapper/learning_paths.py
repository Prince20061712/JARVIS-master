"""
Advanced learning path generation with personalization and adaptive sequencing
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import networkx as nx
from collections import defaultdict, deque
import heapq
from sklearn.cluster import KMeans
import logging
import hashlib

class LearningStyle(Enum):
    """Different learning styles for path personalization"""
    VISUAL = "visual"
    AUDITORY = "auditory"
    READING = "reading"
    KINESTHETIC = "kinesthetic"
    ANALYTICAL = "analytical"
    HOLISTIC = "holistic"
    SEQUENTIAL = "sequential"
    GLOBAL = "global"

class Difficulty(Enum):
    """Difficulty levels"""
    BEGINNER = "beginner"
    EASY = "easy"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

@dataclass
class LearningObjective:
    """Learning objective for a path node"""
    id: str
    description: str
    bloom_level: str  # remember, understand, apply, analyze, evaluate, create
    estimated_time: int  # minutes
    mastery_criteria: Dict[str, Any] = field(default_factory=dict)
    prerequisites: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    assessment_methods: List[str] = field(default_factory=list)

@dataclass
class PathNode:
    """Node in learning path"""
    id: str
    title: str
    topic: str
    objectives: List[LearningObjective] = field(default_factory=list)
    difficulty: float = 0.5
    estimated_time: int = 60  # minutes
    prerequisites: List[str] = field(default_factory=list)
    resources: List[Dict[str, Any]] = field(default_factory=list)
    assessments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Learning style adaptations
    visual_content: Optional[str] = None
    auditory_content: Optional[str] = None
    reading_content: Optional[str] = None
    kinesthetic_content: Optional[str] = None

@dataclass
class LearningPath:
    """Personalized learning path"""
    id: str
    user_id: str
    subject: str
    goal: str
    nodes: List[PathNode] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    estimated_total_time: int = 0
    current_node_index: int = 0
    completed_nodes: Set[str] = field(default_factory=set)
    progress: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Personalization
    learning_style: LearningStyle = LearningStyle.READING
    difficulty_preference: float = 0.5
    pace_preference: str = "moderate"  # slow, moderate, fast
    
    def __post_init__(self):
        self.estimated_total_time = sum(node.estimated_time for node in self.nodes)
        self._update_progress()
    
    def _update_progress(self):
        """Update progress percentage"""
        if self.nodes:
            self.progress = len(self.completed_nodes) / len(self.nodes)
    
    def get_next_node(self) -> Optional[PathNode]:
        """Get next uncompleted node"""
        for i, node in enumerate(self.nodes[self.current_node_index:], self.current_node_index):
            if node.id not in self.completed_nodes:
                self.current_node_index = i
                return node
        return None
    
    def mark_completed(self, node_id: str, score: Optional[float] = None):
        """Mark a node as completed"""
        self.completed_nodes.add(node_id)
        if score is not None:
            self.metadata[f"score_{node_id}"] = score
        self._update_progress()
        self.updated_at = datetime.now()
    
    def get_completion_percentage(self) -> float:
        """Get completion percentage"""
        return self.progress * 100
    
    def get_remaining_time(self) -> int:
        """Get estimated remaining time in minutes"""
        remaining_nodes = [n for n in self.nodes if n.id not in self.completed_nodes]
        return sum(n.estimated_time for n in remaining_nodes)

class LearningPaths:
    """
    Advanced learning path generator with personalization and adaptation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize learning paths generator
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Storage for learning paths
        self.paths: Dict[str, LearningPath] = {}
        
        # User profiles
        self.user_profiles: Dict[str, Dict[str, Any]] = {}
        
        # Knowledge graph reference (will be set by main system)
        self.knowledge_graph = None
        self.subject_hierarchy = None
        
        # Path generation algorithms
        self.algorithms = {
            'prerequisite_first': self._generate_prerequisite_first_path,
            'difficulty_progressive': self._generate_difficulty_progressive_path,
            'interest_based': self._generate_interest_based_path,
            'balanced': self._generate_balanced_path
        }
        
        # Learning style adaptations
        self.style_adaptations = self._load_style_adaptations()
        
        self.logger = logging.getLogger(__name__)
    
    async def generate_path(
        self,
        user_id: str,
        subject: str,
        goal: str,
        learning_style: Optional[LearningStyle] = None,
        difficulty_preference: float = 0.5,
        pace_preference: str = "moderate",
        algorithm: str = "balanced",
        **kwargs
    ) -> LearningPath:
        """
        Generate personalized learning path
        
        Args:
            user_id: User identifier
            subject: Subject to learn
            goal: Learning goal
            learning_style: Preferred learning style
            difficulty_preference: Preferred difficulty (0-1)
            pace_preference: Learning pace
            algorithm: Path generation algorithm
            **kwargs: Additional arguments
            
        Returns:
            Personalized LearningPath
        """
        # Get or create user profile
        user_profile = await self._get_user_profile(user_id)
        
        # Use provided preferences or infer from profile
        if not learning_style:
            learning_style = user_profile.get('learning_style', LearningStyle.READING)
        
        # Get subject hierarchy and prerequisites
        if not self.subject_hierarchy:
            raise ValueError("Subject hierarchy not initialized")
        
        # Get topics for subject
        topics = await self._get_topics_for_subject(subject, goal)
        
        if not topics:
            raise ValueError(f"No topics found for subject: {subject}")
        
        # Build prerequisite graph for topics
        prereq_graph = await self._build_prerequisite_graph(topics)
        
        # Generate path using specified algorithm
        generator = self.algorithms.get(algorithm, self._generate_balanced_path)
        nodes = await generator(
            topics=topics,
            prereq_graph=prereq_graph,
            user_profile=user_profile,
            learning_style=learning_style,
            difficulty_preference=difficulty_preference,
            **kwargs
        )
        
        # Apply learning style adaptations
        nodes = await self._apply_style_adaptations(nodes, learning_style)
        
        # Create path
        path_id = self._generate_path_id(user_id, subject, goal)
        path = LearningPath(
            id=path_id,
            user_id=user_id,
            subject=subject,
            goal=goal,
            nodes=nodes,
            learning_style=learning_style,
            difficulty_preference=difficulty_preference,
            pace_preference=pace_preference,
            metadata={
                'algorithm': algorithm,
                'num_topics': len(topics),
                'generated_at': datetime.now().isoformat()
            }
        )
        
        # Store path
        self.paths[path_id] = path
        
        # Update user profile
        await self._update_user_profile(user_id, path)
        
        self.logger.info(f"Generated learning path {path_id} for user {user_id}")
        return path
    
    async def adapt_path(
        self,
        path_id: str,
        user_performance: Dict[str, Any]
    ) -> Optional[LearningPath]:
        """
        Adapt learning path based on user performance
        
        Args:
            path_id: Path identifier
            user_performance: Performance metrics
            
        Returns:
            Adapted LearningPath or None
        """
        if path_id not in self.paths:
            return None
        
        path = self.paths[path_id]
        
        # Analyze performance
        struggling_nodes = []
        mastered_nodes = []
        
        for node in path.nodes:
            score_key = f"score_{node.id}"
            if score_key in user_performance:
                score = user_performance[score_key]
                if score < 0.6:  # Struggling threshold
                    struggling_nodes.append(node)
                elif score > 0.9:  # Mastered threshold
                    mastered_nodes.append(node)
        
        # Adapt based on performance
        if struggling_nodes:
            # Add remedial content
            path = await self._add_remedial_content(path, struggling_nodes)
        
        if mastered_nodes:
            # Accelerate through mastered content
            path = await self._accelerate_path(path, mastered_nodes)
        
        # Adjust difficulty if needed
        if user_performance.get('avg_score', 0.5) < 0.6:
            # Too difficult, reduce difficulty
            path.difficulty_preference = max(0.2, path.difficulty_preference - 0.1)
        elif user_performance.get('avg_score', 0.5) > 0.9:
            # Too easy, increase difficulty
            path.difficulty_preference = min(0.9, path.difficulty_preference + 0.1)
        
        path.updated_at = datetime.now()
        self.paths[path_id] = path
        
        return path
    
    async def get_path_progress(
        self,
        path_id: str
    ) -> Dict[str, Any]:
        """Get detailed progress for a learning path"""
        if path_id not in self.paths:
            return {}
        
        path = self.paths[path_id]
        
        return {
            'path_id': path.id,
            'subject': path.subject,
            'goal': path.goal,
            'progress': path.get_completion_percentage(),
            'completed_nodes': len(path.completed_nodes),
            'total_nodes': len(path.nodes),
            'remaining_time': path.get_remaining_time(),
            'estimated_completion': (datetime.now() + timedelta(minutes=path.get_remaining_time())).isoformat(),
            'current_node': path.get_next_node().title if path.get_next_node() else None,
            'learning_style': path.learning_style.value,
            'difficulty_preference': path.difficulty_preference
        }
    
    async def recommend_next_paths(
        self,
        user_id: str,
        completed_path_id: str
    ) -> List[Dict[str, Any]]:
        """Recommend next learning paths after completion"""
        if completed_path_id not in self.paths:
            return []
        
        completed_path = self.paths[completed_path_id]
        user_profile = await self._get_user_profile(user_id)
        
        recommendations = []
        
        # Get related subjects
        if self.subject_hierarchy:
            related = self.subject_hierarchy.get_related_subjects(completed_path.subject)
            
            for subject, relevance in related[:5]:
                # Generate path for related subject
                path = await self.generate_path(
                    user_id=user_id,
                    subject=subject,
                    goal=f"Continue learning {subject}",
                    learning_style=completed_path.learning_style,
                    difficulty_preference=completed_path.difficulty_preference,
                    algorithm=completed_path.metadata.get('algorithm', 'balanced')
                )
                
                recommendations.append({
                    'subject': subject,
                    'relevance': relevance,
                    'estimated_time': path.estimated_total_time,
                    'difficulty': path.difficulty_preference
                })
        
        return recommendations
    
    async def _generate_prerequisite_first_path(
        self,
        topics: List[Dict[str, Any]],
        prereq_graph: nx.DiGraph,
        user_profile: Dict[str, Any],
        **kwargs
    ) -> List[PathNode]:
        """Generate path prioritizing prerequisites"""
        nodes = []
        visited = set()
        
        # Topological sort based on prerequisites
        try:
            sorted_topics = list(nx.topological_sort(prereq_graph))
        except nx.NetworkXUnfeasible:
            # Cycle detected, use heuristic
            sorted_topics = self._heuristic_sort(prereq_graph)
        
        for topic_name in sorted_topics:
            if topic_name in [t['name'] for t in topics]:
                topic_data = next(t for t in topics if t['name'] == topic_name)
                node = self._create_node(topic_data, user_profile)
                nodes.append(node)
        
        return nodes
    
    async def _generate_difficulty_progressive_path(
        self,
        topics: List[Dict[str, Any]],
        prereq_graph: nx.DiGraph,
        user_profile: Dict[str, Any],
        **kwargs
    ) -> List[PathNode]:
        """Generate path increasing in difficulty"""
        nodes = []
        
        # Group topics by difficulty
        difficulty_groups = defaultdict(list)
        for topic in topics:
            difficulty = topic.get('difficulty', 0.5)
            group = int(difficulty * 5)  # 0-4 groups
            difficulty_groups[group].append(topic)
        
        # Sort each group by prerequisites
        for group in sorted(difficulty_groups.keys()):
            group_topics = difficulty_groups[group]
            
            # Filter by prerequisites already covered
            available = []
            for topic in group_topics:
                prereqs = self._get_prerequisites(topic['name'], prereq_graph)
                if all(p in [n.topic for n in nodes] for p in prereqs):
                    available.append(topic)
            
            # Add to path
            for topic in available:
                node = self._create_node(topic, user_profile)
                nodes.append(node)
        
        return nodes
    
    async def _generate_interest_based_path(
        self,
        topics: List[Dict[str, Any]],
        prereq_graph: nx.DiGraph,
        user_profile: Dict[str, Any],
        **kwargs
    ) -> List[PathNode]:
        """Generate path based on user interests"""
        nodes = []
        
        # Get user interests from profile
        interests = user_profile.get('interests', [])
        
        # Score topics by interest
        topic_scores = []
        for topic in topics:
            score = 0
            for interest in interests:
                if interest.lower() in topic['name'].lower():
                    score += 1
                if interest.lower() in topic.get('keywords', []):
                    score += 0.5
            topic_scores.append((score, topic))
        
        # Sort by interest score
        topic_scores.sort(reverse=True)
        
        # Add to path respecting prerequisites
        added = set()
        for score, topic in topic_scores:
            prereqs = self._get_prerequisites(topic['name'], prereq_graph)
            if all(p in added for p in prereqs):
                node = self._create_node(topic, user_profile)
                nodes.append(node)
                added.add(topic['name'])
        
        return nodes
    
    async def _generate_balanced_path(
        self,
        topics: List[Dict[str, Any]],
        prereq_graph: nx.DiGraph,
        user_profile: Dict[str, Any],
        **kwargs
    ) -> List[PathNode]:
        """Generate balanced path considering multiple factors"""
        nodes = []
        
        # Calculate node scores based on multiple criteria
        node_scores = []
        for topic in topics:
            score = 0
            
            # Prerequisite importance
            out_degree = prereq_graph.out_degree(topic['name']) if topic['name'] in prereq_graph else 0
            score += out_degree * 0.3  # Topics with many dependents are important
            
            # Difficulty alignment with user preference
            user_diff = user_profile.get('difficulty_preference', 0.5)
            diff_alignment = 1 - abs(topic.get('difficulty', 0.5) - user_diff)
            score += diff_alignment * 0.2
            
            # Interest alignment
            interests = user_profile.get('interests', [])
            interest_match = sum(1 for i in interests if i.lower() in topic['name'].lower())
            score += interest_match * 0.1
            
            # Topic importance in syllabus
            importance = topic.get('importance', 0.5)
            score += importance * 0.2
            
            node_scores.append((score, topic))
        
        # Sort by score
        node_scores.sort(reverse=True)
        
        # Add to path respecting prerequisites
        added = set()
        for score, topic in node_scores:
            prereqs = self._get_prerequisites(topic['name'], prereq_graph)
            if all(p in added for p in prereqs):
                node = self._create_node(topic, user_profile)
                nodes.append(node)
                added.add(topic['name'])
        
        return nodes
    
    async def _get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get or create user profile"""
        if user_id not in self.user_profiles:
            # Create default profile
            self.user_profiles[user_id] = {
                'user_id': user_id,
                'learning_style': LearningStyle.READING,
                'difficulty_preference': 0.5,
                'pace_preference': 'moderate',
                'interests': [],
                'strengths': [],
                'weaknesses': [],
                'completed_paths': [],
                'avg_performance': 0.7,
                'learning_history': []
            }
        
        return self.user_profiles[user_id]
    
    async def _update_user_profile(self, user_id: str, path: LearningPath):
        """Update user profile with new path"""
        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            profile['completed_paths'].append(path.id)
            profile['learning_history'].append({
                'path_id': path.id,
                'subject': path.subject,
                'goal': path.goal,
                'timestamp': datetime.now().isoformat()
            })
    
    async def _get_topics_for_subject(
        self,
        subject: str,
        goal: str
    ) -> List[Dict[str, Any]]:
        """Get topics for a subject based on goal"""
        if not self.subject_hierarchy:
            return []
        
        # Get subject node
        subject_node = self.subject_hierarchy.get_subject(subject)
        if not subject_node:
            return []
        
        # Extract topics from subject hierarchy
        topics = []
        
        def extract_topics(node):
            topics.append({
                'name': node.name,
                'difficulty': node.difficulty,
                'importance': node.importance,
                'keywords': node.keywords,
                'estimated_time': node.estimated_hours * 60,  # Convert to minutes
                'prerequisites': node.prerequisites
            })
            for child in node.children:
                extract_topics(child)
        
        extract_topics(subject_node)
        
        # Filter based on goal if needed
        if goal and goal != f"Learn {subject}":
            # Use goal to filter/prioritize topics
            goal_keywords = set(goal.lower().split())
            filtered_topics = []
            for topic in topics:
                topic_keywords = set(topic['keywords'] + [topic['name'].lower()])
                if topic_keywords & goal_keywords:
                    filtered_topics.append(topic)
            topics = filtered_topics if filtered_topics else topics
        
        return topics
    
    async def _build_prerequisite_graph(
        self,
        topics: List[Dict[str, Any]]
    ) -> nx.DiGraph:
        """Build prerequisite graph for topics"""
        graph = nx.DiGraph()
        
        # Add nodes
        for topic in topics:
            graph.add_node(topic['name'], **topic)
        
        # Add edges for prerequisites
        for topic in topics:
            prereqs = topic.get('prerequisites', [])
            for prereq in prereqs:
                if prereq in graph:
                    graph.add_edge(prereq, topic['name'])
        
        return graph
    
    def _get_prerequisites(
        self,
        topic_name: str,
        graph: nx.DiGraph
    ) -> List[str]:
        """Get prerequisites for a topic"""
        if topic_name not in graph:
            return []
        
        return list(graph.predecessors(topic_name))
    
    def _create_node(
        self,
        topic_data: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> PathNode:
        """Create a path node from topic data"""
        # Generate learning objectives
        objectives = self._generate_objectives(topic_data)
        
        # Estimate time based on difficulty and user pace
        base_time = topic_data.get('estimated_time', 60)
        pace_factor = {
            'slow': 1.5,
            'moderate': 1.0,
            'fast': 0.7
        }.get(user_profile.get('pace_preference', 'moderate'), 1.0)
        
        estimated_time = int(base_time * pace_factor)
        
        return PathNode(
            id=self._generate_node_id(topic_data['name']),
            title=topic_data['name'],
            topic=topic_data['name'],
            objectives=objectives,
            difficulty=topic_data.get('difficulty', 0.5),
            estimated_time=estimated_time,
            prerequisites=topic_data.get('prerequisites', []),
            metadata={
                'importance': topic_data.get('importance', 0.5),
                'keywords': topic_data.get('keywords', [])
            }
        )
    
    def _generate_objectives(
        self,
        topic_data: Dict[str, Any]
    ) -> List[LearningObjective]:
        """Generate learning objectives for a topic"""
        objectives = []
        
        # Basic understanding objective
        objectives.append(LearningObjective(
            id=f"{topic_data['name']}_understand",
            description=f"Understand the fundamental concepts of {topic_data['name']}",
            bloom_level="understand",
            estimated_time=topic_data.get('estimated_time', 60) // 3
        ))
        
        # Application objective for intermediate difficulty
        if topic_data.get('difficulty', 0.5) > 0.3:
            objectives.append(LearningObjective(
                id=f"{topic_data['name']}_apply",
                description=f"Apply {topic_data['name']} concepts to solve problems",
                bloom_level="apply",
                estimated_time=topic_data.get('estimated_time', 60) // 3
            ))
        
        # Analysis objective for higher difficulty
        if topic_data.get('difficulty', 0.5) > 0.6:
            objectives.append(LearningObjective(
                id=f"{topic_data['name']}_analyze",
                description=f"Analyze complex scenarios involving {topic_data['name']}",
                bloom_level="analyze",
                estimated_time=topic_data.get('estimated_time', 60) // 3
            ))
        
        return objectives
    
    async def _apply_style_adaptations(
        self,
        nodes: List[PathNode],
        learning_style: LearningStyle
    ) -> List[PathNode]:
        """Apply learning style adaptations to nodes"""
        adaptations = self.style_adaptations.get(learning_style, {})
        
        for node in nodes:
            # Add style-specific content
            if 'visual' in adaptations:
                node.visual_content = f"Visual content for {node.title}"
            if 'auditory' in adaptations:
                node.auditory_content = f"Audio content for {node.title}"
            if 'kinesthetic' in adaptations:
                node.kinesthetic_content = f"Interactive content for {node.title}"
            
            # Adjust node based on style
            node.metadata['learning_style'] = learning_style.value
        
        return nodes
    
    async def _add_remedial_content(
        self,
        path: LearningPath,
        struggling_nodes: List[PathNode]
    ) -> LearningPath:
        """Add remedial content for struggling nodes"""
        for node in struggling_nodes:
            # Add simpler explanations
            simplified_node = PathNode(
                id=f"{node.id}_remedial",
                title=f"Simplified: {node.title}",
                topic=node.topic,
                objectives=[
                    LearningObjective(
                        id=f"{node.id}_remedial_obj",
                        description=f"Basic understanding of {node.topic}",
                        bloom_level="remember",
                        estimated_time=node.estimated_time // 2
                    )
                ],
                difficulty=max(0.2, node.difficulty - 0.2),
                estimated_time=node.estimated_time // 2,
                prerequisites=node.prerequisites
            )
            
            # Insert before the struggling node
            idx = path.nodes.index(node)
            path.nodes.insert(idx, simplified_node)
        
        return path
    
    async def _accelerate_path(
        self,
        path: LearningPath,
        mastered_nodes: List[PathNode]
    ) -> LearningPath:
        """Accelerate through mastered content"""
        # Mark mastered nodes as completed
        for node in mastered_nodes:
            if node.id not in path.completed_nodes:
                path.mark_completed(node.id, score=0.95)
        
        # Skip or compress related content
        mastered_topics = {node.topic for node in mastered_nodes}
        path.nodes = [
            node for node in path.nodes
            if node.topic not in mastered_topics or node in mastered_nodes
        ]
        
        return path
    
    def _generate_path_id(self, user_id: str, subject: str, goal: str) -> str:
        """Generate unique path ID"""
        content = f"{user_id}{subject}{goal}{datetime.now()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _generate_node_id(self, topic_name: str) -> str:
        """Generate unique node ID"""
        content = f"{topic_name}{datetime.now()}"
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    def _heuristic_sort(self, graph: nx.DiGraph) -> List[str]:
        """Heuristic topological sort for graphs with cycles"""
        # Kahn's algorithm with cycle handling
        in_degree = {node: graph.in_degree(node) for node in graph.nodes()}
        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            for neighbor in graph.successors(node):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Add remaining nodes (those in cycles)
        remaining = [node for node in graph.nodes() if node not in result]
        result.extend(remaining)
        
        return result
    
    def _load_style_adaptations(self) -> Dict[LearningStyle, Dict[str, Any]]:
        """Load learning style adaptations"""
        return {
            LearningStyle.VISUAL: {
                'visual': True,
                'content_type': 'diagrams, charts, videos',
                'preferred_formats': ['image', 'video', 'infographic']
            },
            LearningStyle.AUDITORY: {
                'auditory': True,
                'content_type': 'lectures, discussions, audio',
                'preferred_formats': ['audio', 'podcast', 'lecture']
            },
            LearningStyle.READING: {
                'reading': True,
                'content_type': 'text, articles, books',
                'preferred_formats': ['text', 'document', 'ebook']
            },
            LearningStyle.KINESTHETIC: {
                'kinesthetic': True,
                'content_type': 'interactive, hands-on, exercises',
                'preferred_formats': ['interactive', 'simulation', 'lab']
            },
            LearningStyle.ANALYTICAL: {
                'analytical': True,
                'content_type': 'logical, structured, detailed',
                'preferred_formats': ['analysis', 'problem_set', 'case_study']
            },
            LearningStyle.HOLISTIC: {
                'holistic': True,
                'content_type': 'overview, connections, big picture',
                'preferred_formats': ['overview', 'mindmap', 'summary']
            }
        }