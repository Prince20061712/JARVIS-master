"""
Advanced prerequisite graph management with knowledge tracing and gap analysis
"""

import networkx as nx
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import logging
from datetime import datetime

class KnowledgeLevel(Enum):
    """Knowledge levels for nodes"""
    UNKNOWN = "unknown"
    LEARNING = "learning"
    FAMILIAR = "familiar"
    PROFICIENT = "proficient"
    MASTERED = "mastered"

class RelationType(Enum):
    """Types of relationships between concepts"""
    PREREQUISITE = "prerequisite"
    RELATED = "related"
    PART_OF = "part_of"
    EXAMPLE_OF = "example_of"
    CONTRASTS_WITH = "contrasts_with"
    EXTENDS = "extends"

@dataclass
class KnowledgeNode:
    """Node in knowledge graph"""
    id: str
    name: str
    description: str = ""
    knowledge_level: KnowledgeLevel = KnowledgeLevel.UNKNOWN
    confidence: float = 0.0
    last_reviewed: Optional[datetime] = None
    times_reviewed: int = 0
    avg_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class KnowledgeEdge:
    """Edge in knowledge graph"""
    source: str
    target: str
    relation_type: RelationType
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class KnowledgeGraph:
    """
    Knowledge graph for tracking concept relationships and user knowledge
    """
    
    def __init__(self):
        """Initialize knowledge graph"""
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: Dict[Tuple[str, str], KnowledgeEdge] = {}
        
    def add_node(self, node: KnowledgeNode):
        """Add node to graph"""
        self.nodes[node.id] = node
        self.graph.add_node(node.id, **node.__dict__)
    
    def add_edge(self, edge: KnowledgeEdge):
        """Add edge to graph"""
        self.edges[(edge.source, edge.target)] = edge
        self.graph.add_edge(
            edge.source,
            edge.target,
            relation=edge.relation_type.value,
            weight=edge.weight,
            **edge.metadata
        )
    
    def get_prerequisites(self, node_id: str) -> List[KnowledgeNode]:
        """Get all prerequisites for a node"""
        predecessors = list(self.graph.predecessors(node_id))
        return [self.nodes[p] for p in predecessors if p in self.nodes]
    
    def get_dependents(self, node_id: str) -> List[KnowledgeNode]:
        """Get all nodes that depend on this node"""
        successors = list(self.graph.successors(node_id))
        return [self.nodes[s] for s in successors if s in self.nodes]
    
    def get_knowledge_gaps(self, target_node: str) -> List[KnowledgeNode]:
        """Find knowledge gaps for reaching a target node"""
        gaps = []
        
        def find_gaps(node_id: str, visited: Set[str]):
            if node_id in visited:
                return
            visited.add(node_id)
            
            node = self.nodes.get(node_id)
            if node and node.knowledge_level == KnowledgeLevel.UNKNOWN:
                gaps.append(node)
            
            for prereq in self.graph.predecessors(node_id):
                find_gaps(prereq, visited)
        
        find_gaps(target_node, set())
        return gaps
    
    def get_learning_path(
        self,
        target_node: str,
        current_knowledge: Optional[Set[str]] = None
    ) -> List[str]:
        """Generate learning path to target node"""
        if current_knowledge is None:
            current_knowledge = {
                nid for nid, node in self.nodes.items()
                if node.knowledge_level in [KnowledgeLevel.FAMILIAR, KnowledgeLevel.PROFICIENT, KnowledgeLevel.MASTERED]
            }
        
        # BFS to find shortest path considering current knowledge
        path = []
        visited = set()
        queue = deque()
        
        # Start from nodes we know
        for known in current_knowledge:
            queue.append((known, [known]))
            visited.add(known)
        
        while queue:
            node, current_path = queue.popleft()
            
            if node == target_node:
                path = current_path
                break
            
            for neighbor in self.graph.successors(node):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, current_path + [neighbor]))
        
        return path
    
    def update_knowledge(
        self,
        node_id: str,
        level: KnowledgeLevel,
        score: Optional[float] = None
    ):
        """Update knowledge level for a node"""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.knowledge_level = level
            node.last_reviewed = datetime.now()
            node.times_reviewed += 1
            if score is not None:
                # Update running average
                total = node.avg_score * (node.times_reviewed - 1) + score
                node.avg_score = total / node.times_reviewed
                node.confidence = node.avg_score
    
    def get_mastery_level(self, topic: str) -> float:
        """Get mastery level for a topic (0-1)"""
        if topic not in self.nodes:
            return 0.0
        
        node = self.nodes[topic]
        level_weights = {
            KnowledgeLevel.UNKNOWN: 0.0,
            KnowledgeLevel.LEARNING: 0.3,
            KnowledgeLevel.FAMILIAR: 0.6,
            KnowledgeLevel.PROFICIENT: 0.8,
            KnowledgeLevel.MASTERED: 1.0
        }
        
        base_level = level_weights[node.knowledge_level]
        confidence_factor = node.confidence
        
        return base_level * confidence_factor

class PrerequisiteGraph:
    """
    Advanced prerequisite graph management with analytics and optimization
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize prerequisite graph
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.knowledge_graph = KnowledgeGraph()
        
        # Analytics
        self.learning_paths: Dict[str, List[str]] = {}
        self.difficulty_cache: Dict[str, float] = {}
        
        self.logger = logging.getLogger(__name__)
    
    def build_from_syllabus(self, syllabus_data: Dict[str, Any]):
        """
        Build prerequisite graph from syllabus data
        
        Args:
            syllabus_data: Syllabus dictionary with topics and relationships
        """
        # Add topics as nodes
        for topic in syllabus_data.get('topics', []):
            node = KnowledgeNode(
                id=topic['id'],
                name=topic['name'],
                description=topic.get('description', ''),
                metadata={
                    'difficulty': topic.get('difficulty', 0.5),
                    'importance': topic.get('importance', 0.5),
                    'estimated_hours': topic.get('hours', 1.0)
                }
            )
            self.knowledge_graph.add_node(node)
        
        # Add prerequisite relationships
        for topic in syllabus_data.get('topics', []):
            for prereq_id in topic.get('prerequisites', []):
                edge = KnowledgeEdge(
                    source=prereq_id,
                    target=topic['id'],
                    relation_type=RelationType.PREREQUISITE,
                    weight=1.0
                )
                self.knowledge_graph.add_edge(edge)
        
        # Add other relationships
        for rel in syllabus_data.get('relationships', []):
            edge = KnowledgeEdge(
                source=rel['source'],
                target=rel['target'],
                relation_type=RelationType(rel['type']),
                weight=rel.get('weight', 1.0)
            )
            self.knowledge_graph.add_edge(edge)
        
        self.logger.info(f"Built prerequisite graph with {len(self.knowledge_graph.nodes)} nodes")
    
    def get_learning_path(
        self,
        target_topic: str,
        current_knowledge: Optional[List[str]] = None,
        optimize_for: str = 'time'  # 'time', 'difficulty', 'retention'
    ) -> List[Dict[str, Any]]:
        """
        Get optimal learning path to target topic
        
        Args:
            target_topic: Target topic ID
            current_knowledge: List of known topic IDs
            optimize_for: Optimization criterion
            
        Returns:
            List of path steps with metadata
        """
        if target_topic not in self.knowledge_graph.nodes:
            return []
        
        # Get base path
        path_ids = self.knowledge_graph.get_learning_path(
            target_topic,
            set(current_knowledge) if current_knowledge else None
        )
        
        # Enhance path with metadata
        path = []
        for i, topic_id in enumerate(path_ids):
            node = self.knowledge_graph.nodes[topic_id]
            
            # Calculate estimated time
            base_time = node.metadata.get('estimated_hours', 1.0) * 60
            if i > 0:
                # Adjust based on prerequisites mastered
                prereqs = self.knowledge_graph.get_prerequisites(topic_id)
                mastered_prereqs = sum(
                    1 for p in prereqs
                    if p.knowledge_level in [KnowledgeLevel.PROFICIENT, KnowledgeLevel.MASTERED]
                )
                prereq_factor = 1.0 - (mastered_prereqs / len(prereqs)) * 0.3 if prereqs else 1.0
                base_time *= prereq_factor
            
            path.append({
                'id': topic_id,
                'name': node.name,
                'description': node.description,
                'difficulty': node.metadata.get('difficulty', 0.5),
                'estimated_minutes': int(base_time),
                'prerequisites': [p.name for p in self.knowledge_graph.get_prerequisites(topic_id)],
                'position': i,
                'progress': node.knowledge_level.value if node.knowledge_level else 'unknown',
                'confidence': node.confidence
            })
        
        # Store for analytics
        self.learning_paths[target_topic] = path_ids
        
        return path
    
    def identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """
        Identify bottleneck topics that block many others
        
        Returns:
            List of bottleneck topics with metrics
        """
        bottlenecks = []
        
        for node_id in self.knowledge_graph.graph.nodes():
            # Calculate out-degree (number of dependents)
            out_degree = self.knowledge_graph.graph.out_degree(node_id)
            
            if out_degree > 2:  # Potential bottleneck
                node = self.knowledge_graph.nodes[node_id]
                
                # Calculate impact factor
                dependents = self.knowledge_graph.get_dependents(node_id)
                impact = len(dependents)
                
                # Calculate how many would be blocked if this is missing
                blocked = set()
                for dep in dependents:
                    blocked.update(
                        self.knowledge_graph.get_dependents(dep.id)
                    )
                
                bottlenecks.append({
                    'id': node_id,
                    'name': node.name,
                    'impact': impact,
                    'blocked_count': len(blocked),
                    'difficulty': node.metadata.get('difficulty', 0.5),
                    'importance': impact * len(blocked)
                })
        
        # Sort by importance
        bottlenecks.sort(key=lambda x: x['importance'], reverse=True)
        return bottlenecks[:10]  # Top 10 bottlenecks
    
    def analyze_prerequisite_strength(self) -> Dict[str, Any]:
        """
        Analyze strength of prerequisite relationships
        
        Returns:
            Analysis metrics
        """
        metrics = {
            'total_prerequisites': 0,
            'avg_depth': 0,
            'max_depth': 0,
            'cycles': [],
            'weak_links': [],
            'strong_links': []
        }
        
        # Count prerequisites
        for u, v in self.knowledge_graph.graph.edges():
            if self.knowledge_graph.edges[(u, v)].relation_type == RelationType.PREREQUISITE:
                metrics['total_prerequisites'] += 1
        
        # Calculate depth for each node
        depths = []
        for node in self.knowledge_graph.graph.nodes():
            try:
                depth = nx.shortest_path_length(
                    self.knowledge_graph.graph,
                    source=node,
                    target=None
                )
                depths.append(max(depth.values()))
            except:
                pass
        
        if depths:
            metrics['avg_depth'] = np.mean(depths)
            metrics['max_depth'] = max(depths)
        
        # Find cycles
        try:
            cycles = list(nx.simple_cycles(self.knowledge_graph.graph))
            metrics['cycles'] = [
                [self.knowledge_graph.nodes[n].name for n in cycle]
                for cycle in cycles[:5]  # Top 5 cycles
            ]
        except:
            pass
        
        return metrics
    
    def suggest_remediation(
        self,
        user_knowledge: Dict[str, KnowledgeLevel],
        target_topic: str
    ) -> List[Dict[str, Any]]:
        """
        Suggest remediation steps based on knowledge gaps
        
        Args:
            user_knowledge: Current user knowledge levels
            target_topic: Target topic
            
        Returns:
            List of remediation suggestions
        """
        # Update knowledge graph with user knowledge
        for topic_id, level in user_knowledge.items():
            if topic_id in self.knowledge_graph.nodes:
                self.knowledge_graph.update_knowledge(topic_id, level)
        
        # Find knowledge gaps
        gaps = self.knowledge_graph.get_knowledge_gaps(target_topic)
        
        # Prioritize gaps
        prioritized = []
        for gap in gaps:
            # Calculate priority score
            priority = 0.0
            
            # More prerequisites increase priority
            prereqs = self.knowledge_graph.get_prerequisites(gap.id)
            priority += len(prereqs) * 0.1
            
            # Higher difficulty decreases priority (start with easier ones)
            difficulty = gap.metadata.get('difficulty', 0.5)
            priority += (1 - difficulty) * 0.3
            
            # More dependents increase priority
            dependents = self.knowledge_graph.get_dependents(gap.id)
            priority += len(dependents) * 0.2
            
            prioritized.append({
                'topic_id': gap.id,
                'topic_name': gap.name,
                'priority': priority,
                'difficulty': difficulty,
                'estimated_time': gap.metadata.get('estimated_hours', 1.0) * 60,
                'prerequisites': [p.name for p in prereqs]
            })
        
        # Sort by priority
        prioritized.sort(key=lambda x: x['priority'], reverse=True)
        
        return prioritized
    
    def calculate_topic_difficulty(self, topic_id: str) -> float:
        """
        Calculate effective difficulty considering prerequisites
        
        Args:
            topic_id: Topic ID
            
        Returns:
            Effective difficulty (0-1)
        """
        if topic_id in self.difficulty_cache:
            return self.difficulty_cache[topic_id]
        
        if topic_id not in self.knowledge_graph.nodes:
            return 0.5
        
        node = self.knowledge_graph.nodes[topic_id]
        base_difficulty = node.metadata.get('difficulty', 0.5)
        
        # Adjust based on prerequisites
        prereqs = self.knowledge_graph.get_prerequisites(topic_id)
        if prereqs:
            prereq_difficulties = [
                self.calculate_topic_difficulty(p.id)
                for p in prereqs
            ]
            avg_prereq_difficulty = np.mean(prereq_difficulties)
            
            # Combined difficulty: own difficulty + prerequisite influence
            effective = base_difficulty * 0.6 + avg_prereq_difficulty * 0.4
        else:
            effective = base_difficulty
        
        self.difficulty_cache[topic_id] = effective
        return effective
    
    def find_alternative_paths(
        self,
        start_topic: str,
        end_topic: str,
        max_paths: int = 5
    ) -> List[List[Dict[str, Any]]]:
        """
        Find alternative learning paths between topics
        
        Args:
            start_topic: Starting topic
            end_topic: Target topic
            max_paths: Maximum number of paths
            
        Returns:
            List of alternative paths
        """
        try:
            # Find all simple paths
            paths = list(nx.all_simple_paths(
                self.knowledge_graph.graph,
                start_topic,
                end_topic,
                cutoff=10
            ))
            
            # Score and sort paths
            scored_paths = []
            for path in paths[:max_paths * 2]:  # Limit search
                score = self._score_path(path)
                scored_paths.append((score, path))
            
            scored_paths.sort(reverse=True)
            
            # Convert to detailed paths
            detailed_paths = []
            for score, path in scored_paths[:max_paths]:
                detailed = []
                for topic_id in path:
                    node = self.knowledge_graph.nodes[topic_id]
                    detailed.append({
                        'id': topic_id,
                        'name': node.name,
                        'difficulty': node.metadata.get('difficulty', 0.5)
                    })
                detailed_paths.append({
                    'path': detailed,
                    'score': score,
                    'length': len(detailed)
                })
            
            return detailed_paths
            
        except nx.NetworkXNoPath:
            return []
    
    def get_mastery_timeline(
        self,
        target_topic: str,
        study_hours_per_week: float = 5.0
    ) -> Dict[str, Any]:
        """
        Estimate timeline to achieve mastery
        
        Args:
            target_topic: Target topic
            study_hours_per_week: Hours available per week
            
        Returns:
            Timeline estimate
        """
        # Get learning path
        path = self.get_learning_path(target_topic)
        
        if not path:
            return {}
        
        total_minutes = sum(step['estimated_minutes'] for step in path)
        total_hours = total_minutes / 60
        
        # Calculate weeks needed
        weeks_needed = total_hours / study_hours_per_week
        
        # Break down by difficulty
        easy_topics = [s for s in path if s['difficulty'] < 0.3]
        medium_topics = [s for s in path if 0.3 <= s['difficulty'] < 0.7]
        hard_topics = [s for s in path if s['difficulty'] >= 0.7]
        
        return {
            'target_topic': target_topic,
            'total_topics': len(path),
            'total_hours': round(total_hours, 1),
            'weeks_needed': round(weeks_needed, 1),
            'easy_topics': len(easy_topics),
            'medium_topics': len(medium_topics),
            'hard_topics': len(hard_topics),
            'estimated_completion': (
                datetime.now() + timedelta(weeks=weeks_needed)
            ).isoformat(),
            'weekly_breakdown': [
                {
                    'week': i + 1,
                    'topics': path[i*7:(i+1)*7] if i*7 < len(path) else []
                }
                for i in range(int(weeks_needed) + 1)
            ]
        }
    
    def _score_path(self, path: List[str]) -> float:
        """Score a learning path"""
        score = 0.0
        
        # Shorter paths are better
        score += 10.0 / len(path)
        
        # Prefer paths with easier topics first
        for i, topic_id in enumerate(path):
            difficulty = self.calculate_topic_difficulty(topic_id)
            # Earlier topics should be easier
            score += (1 - difficulty) * (1.0 - i / len(path))
        
        return score
    
    def export_graph(self) -> Dict[str, Any]:
        """Export graph for visualization"""
        nodes = []
        for node_id, node in self.knowledge_graph.nodes.items():
            nodes.append({
                'id': node_id,
                'name': node.name,
                'level': node.knowledge_level.value,
                'difficulty': node.metadata.get('difficulty', 0.5)
            })
        
        edges = []
        for (source, target), edge in self.knowledge_graph.edges.items():
            edges.append({
                'source': source,
                'target': target,
                'type': edge.relation_type.value,
                'weight': edge.weight
            })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'stats': self.analyze_prerequisite_strength()
        }