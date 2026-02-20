"""
Advanced subject hierarchy management with cross-subject relationships
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import networkx as nx
from collections import defaultdict
import logging
import numpy as np

class AcademicLevel(Enum):
    """Academic levels"""
    PRIMARY = "primary"
    MIDDLE = "middle"
    HIGH = "high"
    UNDERGRADUATE = "undergraduate"
    GRADUATE = "graduate"
    PROFESSIONAL = "professional"

class SubjectType(Enum):
    """Subject types"""
    CORE = "core"
    ELECTIVE = "elective"
    VOCATIONAL = "vocational"
    FOUNDATION = "foundation"
    ADVANCED = "advanced"

@dataclass
class SubjectNode:
    """Node in subject hierarchy"""
    id: str
    name: str
    level: AcademicLevel
    subject_type: SubjectType
    description: str = ""
    parent: Optional[str] = None
    children: List[str] = field(default_factory=list)
    related_subjects: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    difficulty: float = 0.5
    importance: float = 0.5
    estimated_hours: float = 40.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class SubjectHierarchy:
    """
    Advanced subject hierarchy with cross-subject relationships and analytics
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize subject hierarchy
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Storage
        self.subjects: Dict[str, SubjectNode] = {}
        self.graph = nx.DiGraph()
        
        # Indices
        self.level_index: Dict[AcademicLevel, List[str]] = defaultdict(list)
        self.type_index: Dict[SubjectType, List[str]] = defaultdict(list)
        self.keyword_index: Dict[str, List[str]] = defaultdict(list)
        
        # Cross-subject relationships
        self.relatedness_matrix: Dict[Tuple[str, str], float] = {}
        
        # Prerequisite graph
        self.prerequisite_graph = nx.DiGraph()
        
        self.logger = logging.getLogger(__name__)
    
    def add_subject(self, subject: SubjectNode):
        """
        Add subject to hierarchy
        
        Args:
            subject: Subject node to add
        """
        self.subjects[subject.id] = subject
        self.graph.add_node(subject.id, **subject.__dict__)
        
        # Update indices
        self.level_index[subject.level].append(subject.id)
        self.type_index[subject.subject_type].append(subject.id)
        
        for keyword in subject.keywords:
            self.keyword_index[keyword.lower()].append(subject.id)
        
        # Add to prerequisite graph
        self.prerequisite_graph.add_node(subject.id)
        
        self.logger.info(f"Added subject: {subject.name} ({subject.id})")
    
    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str = "prerequisite",
        weight: float = 1.0
    ):
        """
        Add relationship between subjects
        
        Args:
            source_id: Source subject ID
            target_id: Target subject ID
            relationship_type: Type of relationship
            weight: Relationship weight
        """
        if source_id not in self.subjects or target_id not in self.subjects:
            self.logger.error(f"Invalid subject IDs: {source_id}, {target_id}")
            return
        
        # Add to main graph
        self.graph.add_edge(
            source_id,
            target_id,
            type=relationship_type,
            weight=weight
        )
        
        # Update subject objects
        if relationship_type == "prerequisite":
            self.subjects[target_id].prerequisites.append(source_id)
            self.prerequisite_graph.add_edge(source_id, target_id, weight=weight)
        elif relationship_type == "related":
            self.subjects[source_id].related_subjects.append(target_id)
            self.subjects[target_id].related_subjects.append(source_id)
            self.relatedness_matrix[(source_id, target_id)] = weight
            self.relatedness_matrix[(target_id, source_id)] = weight
        elif relationship_type == "parent":
            self.subjects[source_id].children.append(target_id)
            self.subjects[target_id].parent = source_id
    
    def build_hierarchy_from_dict(self, data: Dict[str, Any]):
        """
        Build hierarchy from dictionary structure
        
        Args:
            data: Dictionary with subject structure
        """
        def process_node(node_data: Dict[str, Any], parent_id: Optional[str] = None):
            # Create subject node
            subject = SubjectNode(
                id=node_data['id'],
                name=node_data['name'],
                level=AcademicLevel(node_data.get('level', 'high')),
                subject_type=SubjectType(node_data.get('type', 'core')),
                description=node_data.get('description', ''),
                parent=parent_id,
                keywords=node_data.get('keywords', []),
                topics=node_data.get('topics', []),
                difficulty=node_data.get('difficulty', 0.5),
                importance=node_data.get('importance', 0.5),
                estimated_hours=node_data.get('hours', 40.0)
            )
            
            self.add_subject(subject)
            
            # Add parent relationship
            if parent_id:
                self.add_relationship(parent_id, subject.id, "parent")
            
            # Process children
            for child in node_data.get('children', []):
                process_node(child, subject.id)
        
        process_node(data)
    
    def get_subject(self, subject_id: str) -> Optional[SubjectNode]:
        """Get subject by ID"""
        return self.subjects.get(subject_id)
    
    def search_subjects(
        self,
        query: str,
        level: Optional[AcademicLevel] = None,
        subject_type: Optional[SubjectType] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search subjects by name, keywords, or topics
        
        Args:
            query: Search query
            level: Filter by academic level
            subject_type: Filter by subject type
            max_results: Maximum results
            
        Returns:
            List of matching subjects with relevance scores
        """
        query_lower = query.lower()
        results = []
        
        for subject_id, subject in self.subjects.items():
            # Apply filters
            if level and subject.level != level:
                continue
            if subject_type and subject.subject_type != subject_type:
                continue
            
            # Calculate relevance
            relevance = 0.0
            
            # Name match
            if query_lower in subject.name.lower():
                relevance += 1.0
            
            # Keyword matches
            for keyword in subject.keywords:
                if query_lower in keyword.lower():
                    relevance += 0.5
            
            # Topic matches
            for topic in subject.topics:
                if query_lower in topic.lower():
                    relevance += 0.3
            
            if relevance > 0:
                results.append({
                    'id': subject_id,
                    'name': subject.name,
                    'level': subject.level.value,
                    'type': subject.subject_type.value,
                    'relevance': relevance,
                    'description': subject.description[:200] + '...' if len(subject.description) > 200 else subject.description
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:max_results]
    
    def get_prerequisites(
        self,
        subject_id: str,
        recursive: bool = False
    ) -> List[SubjectNode]:
        """
        Get prerequisites for a subject
        
        Args:
            subject_id: Subject ID
            recursive: Whether to include indirect prerequisites
            
        Returns:
            List of prerequisite subjects
        """
        if subject_id not in self.subjects:
            return []
        
        if recursive:
            # Get all ancestors in prerequisite graph
            if subject_id in self.prerequisite_graph:
                prereq_ids = nx.ancestors(self.prerequisite_graph, subject_id)
                return [self.subjects[pid] for pid in prereq_ids if pid in self.subjects]
        
        # Direct prerequisites only
        return [self.subjects[pid] for pid in self.subjects[subject_id].prerequisites if pid in self.subjects]
    
    def get_dependents(
        self,
        subject_id: str,
        recursive: bool = False
    ) -> List[SubjectNode]:
        """
        Get subjects that depend on this subject
        
        Args:
            subject_id: Subject ID
            recursive: Whether to include indirect dependents
            
        Returns:
            List of dependent subjects
        """
        if subject_id not in self.subjects:
            return []
        
        if recursive:
            # Get all descendants in prerequisite graph
            if subject_id in self.prerequisite_graph:
                dependent_ids = nx.descendants(self.prerequisite_graph, subject_id)
                return [self.subjects[did] for did in dependent_ids if did in self.subjects]
        
        # Direct dependents only
        dependents = []
        for subj in self.subjects.values():
            if subject_id in subj.prerequisites:
                dependents.append(subj)
        
        return dependents
    
    def get_related_subjects(
        self,
        subject_id: str,
        min_relevance: float = 0.3,
        max_results: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Get subjects related to given subject
        
        Args:
            subject_id: Subject ID
            min_relevance: Minimum relevance threshold
            max_results: Maximum results
            
        Returns:
            List of (subject_id, relevance_score)
        """
        if subject_id not in self.subjects:
            return []
        
        subject = self.subjects[subject_id]
        related = []
        
        for other_id, other in self.subjects.items():
            if other_id == subject_id:
                continue
            
            # Calculate relevance
            relevance = 0.0
            
            # Check stored relationships
            if (subject_id, other_id) in self.relatedness_matrix:
                relevance = self.relatedness_matrix[(subject_id, other_id)]
            else:
                # Calculate based on various factors
                
                # Same level
                if other.level == subject.level:
                    relevance += 0.2
                
                # Shared keywords
                shared_keywords = set(subject.keywords) & set(other.keywords)
                relevance += len(shared_keywords) * 0.1
                
                # Shared topics
                shared_topics = set(subject.topics) & set(other.topics)
                relevance += len(shared_topics) * 0.15
                
                # Parent-child relationship
                if other.parent == subject_id or subject.parent == other_id:
                    relevance += 0.3
                
                # Prerequisite relationship
                if subject_id in other.prerequisites or other_id in subject.prerequisites:
                    relevance += 0.25
            
            if relevance >= min_relevance:
                related.append((other_id, relevance))
        
        # Sort by relevance
        related.sort(key=lambda x: x[1], reverse=True)
        return related[:max_results]
    
    def get_learning_path(
        self,
        target_subject: str,
        current_knowledge: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate learning path to target subject
        
        Args:
            target_subject: Target subject ID
            current_knowledge: List of known subject IDs
            
        Returns:
            Learning path with subjects
        """
        if target_subject not in self.subjects:
            return []
        
        # Get all prerequisites
        all_prereqs = self.get_prerequisites(target_subject, recursive=True)
        prereq_ids = [p.id for p in all_prereqs]
        
        # Filter out known subjects
        if current_knowledge:
            prereq_ids = [pid for pid in prereq_ids if pid not in current_knowledge]
        
        # Sort by difficulty and dependencies
        # Create a subgraph of prerequisites
        subgraph = self.prerequisite_graph.subgraph(prereq_ids + [target_subject])
        
        # Topological sort
        try:
            sorted_prereqs = list(nx.topological_sort(subgraph))
        except:
            # If cycle, use heuristic
            sorted_prereqs = self._heuristic_sort(subgraph)
        
        # Remove target if it's in the list
        if target_subject in sorted_prereqs:
            sorted_prereqs.remove(target_subject)
        
        # Add target at the end
        sorted_prereqs.append(target_subject)
        
        # Build path with metadata
        path = []
        for i, subject_id in enumerate(sorted_prereqs):
            subject = self.subjects[subject_id]
            
            # Calculate estimated time
            base_time = subject.estimated_hours * 60
            if i < len(sorted_prereqs) - 1:
                # Adjust based on next subject
                next_subj = self.subjects[sorted_prereqs[i + 1]]
                if subject_id in next_subj.prerequisites:
                    base_time *= 1.2  # Extra time for foundational topics
            
            path.append({
                'id': subject_id,
                'name': subject.name,
                'level': subject.level.value,
                'type': subject.subject_type.value,
                'difficulty': subject.difficulty,
                'estimated_minutes': int(base_time),
                'position': i,
                'prerequisites': subject.prerequisites
            })
        
        return path
    
    def analyze_curriculum(self) -> Dict[str, Any]:
        """
        Analyze curriculum structure and provide insights
        
        Returns:
            Dictionary with curriculum analytics
        """
        analysis = {
            'total_subjects': len(self.subjects),
            'by_level': {},
            'by_type': {},
            'prerequisite_stats': {},
            'bottlenecks': [],
            'isolated_subjects': [],
            'depth': 0,
            'breadth': 0
        }
        
        # Count by level
        for level in AcademicLevel:
            count = len(self.level_index[level])
            if count > 0:
                analysis['by_level'][level.value] = count
        
        # Count by type
        for stype in SubjectType:
            count = len(self.type_index[stype])
            if count > 0:
                analysis['by_type'][stype.value] = count
        
        # Prerequisite statistics
        if self.prerequisite_graph.nodes():
            # Average prerequisites per subject
            prereq_counts = [len(self.get_prerequisites(sid)) for sid in self.subjects]
            analysis['prerequisite_stats']['avg_prerequisites'] = np.mean(prereq_counts)
            analysis['prerequisite_stats']['max_prerequisites'] = max(prereq_counts)
            
            # Identify bottlenecks (subjects with many dependents)
            for subject_id in self.subjects:
                dependents = self.get_dependents(subject_id, recursive=True)
                if len(dependents) > 3:
                    analysis['bottlenecks'].append({
                        'id': subject_id,
                        'name': self.subjects[subject_id].name,
                        'dependent_count': len(dependents)
                    })
            
            # Find isolated subjects (no prerequisites or dependents)
            for subject_id, subject in self.subjects.items():
                if not subject.prerequisites and not self.get_dependents(subject_id):
                    analysis['isolated_subjects'].append({
                        'id': subject_id,
                        'name': subject.name
                    })
            
            # Calculate depth and breadth
            try:
                # Longest path
                longest_path = nx.dag_longest_path(self.prerequisite_graph)
                analysis['depth'] = len(longest_path)
                
                # Max branching factor
                max_branch = max(self.prerequisite_graph.out_degree(node) for node in self.prerequisite_graph.nodes())
                analysis['breadth'] = max_branch
            except:
                pass
        
        # Sort bottlenecks
        analysis['bottlenecks'].sort(key=lambda x: x['dependent_count'], reverse=True)
        analysis['bottlenecks'] = analysis['bottlenecks'][:10]
        
        return analysis
    
    def find_cross_disciplinary_connections(
        self,
        subject_ids: List[str],
        max_connections: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find connections between different subjects
        
        Args:
            subject_ids: List of subject IDs to analyze
            max_connections: Maximum connections to return
            
        Returns:
            List of connections between subjects
        """
        connections = []
        
        for i, subj1_id in enumerate(subject_ids):
            if subj1_id not in self.subjects:
                continue
            
            subj1 = self.subjects[subj1_id]
            
            for j, subj2_id in enumerate(subject_ids[i+1:], i+1):
                if subj2_id not in self.subjects:
                    continue
                
                subj2 = self.subjects[subj2_id]
                
                # Calculate connection strength
                strength = 0.0
                connection_types = []
                
                # Direct relationship
                if subj2_id in subj1.related_subjects:
                    strength += 0.5
                    connection_types.append("direct_relation")
                
                # Shared keywords
                shared_keywords = set(subj1.keywords) & set(subj2.keywords)
                if shared_keywords:
                    strength += len(shared_keywords) * 0.1
                    connection_types.append(f"shared_keywords:{len(shared_keywords)}")
                
                # Shared topics
                shared_topics = set(subj1.topics) & set(subj2.topics)
                if shared_topics:
                    strength += len(shared_topics) * 0.15
                    connection_types.append(f"shared_topics:{len(shared_topics)}")
                
                # Prerequisite relationship
                if subj1_id in subj2.prerequisites:
                    strength += 0.3
                    connection_types.append("prerequisite_to")
                if subj2_id in subj1.prerequisites:
                    strength += 0.3
                    connection_types.append("prerequisite_from")
                
                # Same level
                if subj1.level == subj2.level:
                    strength += 0.2
                    connection_types.append("same_level")
                
                if strength > 0:
                    connections.append({
                        'subject1': {
                            'id': subj1_id,
                            'name': subj1.name
                        },
                        'subject2': {
                            'id': subj2_id,
                            'name': subj2.name
                        },
                        'strength': strength,
                        'types': connection_types
                    })
        
        # Sort by strength
        connections.sort(key=lambda x: x['strength'], reverse=True)
        return connections[:max_connections]
    
    def suggest_prerequisites(
        self,
        subject_id: str,
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Suggest possible missing prerequisites
        
        Args:
            subject_id: Subject ID
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of suggested prerequisites with confidence
        """
        if subject_id not in self.subjects:
            return []
        
        subject = self.subjects[subject_id]
        suggestions = []
        
        # Look at other subjects at lower levels
        level_order = list(AcademicLevel)
        subject_level_index = level_order.index(subject.level)
        
        for other_id, other in self.subjects.items():
            if other_id == subject_id:
                continue
            
            # Check if other is at lower level
            other_level_index = level_order.index(other.level)
            if other_level_index >= subject_level_index:
                continue
            
            # Check if not already a prerequisite
            if other_id in subject.prerequisites:
                continue
            
            # Calculate confidence
            confidence = 0.0
            
            # Shared keywords suggest relevance
            shared_keywords = set(subject.keywords) & set(other.keywords)
            confidence += len(shared_keywords) * 0.15
            
            # Shared topics
            shared_topics = set(subject.topics) & set(other.topics)
            confidence += len(shared_topics) * 0.2
            
            # If other is a prerequisite for related subjects
            related = self.get_related_subjects(subject_id, min_relevance=0.3)
            for rel_id, rel_score in related:
                if rel_id in other.prerequisites:
                    confidence += 0.25
            
            if confidence >= min_confidence:
                suggestions.append({
                    'id': other_id,
                    'name': other.name,
                    'level': other.level.value,
                    'confidence': confidence,
                    'reasons': [
                        f"Shares {len(shared_keywords)} keywords",
                        f"Shares {len(shared_topics)} topics"
                    ] if shared_keywords or shared_topics else ["General relevance"]
                })
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        return suggestions
    
    def export_hierarchy(self, format: str = 'json') -> Dict[str, Any]:
        """
        Export hierarchy for visualization
        
        Args:
            format: Export format
            
        Returns:
            Hierarchy data
        """
        nodes = []
        for subj_id, subject in self.subjects.items():
            nodes.append({
                'id': subj_id,
                'name': subject.name,
                'level': subject.level.value,
                'type': subject.subject_type.value,
                'difficulty': subject.difficulty,
                'importance': subject.importance,
                'estimated_hours': subject.estimated_hours
            })
        
        edges = []
        for u, v, data in self.graph.edges(data=True):
            edges.append({
                'source': u,
                'target': v,
                'type': data.get('type', 'unknown'),
                'weight': data.get('weight', 1.0)
            })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'stats': self.analyze_curriculum()
        }
    
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