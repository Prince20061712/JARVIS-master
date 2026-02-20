import json
import os
from typing import List, Dict, Any, Optional

try:
    import networkx as nx
except ImportError:
    nx = None
    print("⚠️ NetworkX module not found. KnowledgeGraph will be disabled.")

from utils.logger import logger

class KnowledgeGraph:
    """
    Maintains a graph of concepts, documents, and their relationships
    (e.g., prerequisite, related_to, part_of).
    """
    def __init__(self, persist_path: str = "data/user_data/learning_history/knowledge_graph.json"):
        self.persist_path = persist_path
        self.graph = nx.DiGraph() if nx else None
        self.load_graph()

    def add_entity(self, entity_id: str, entity_type: str, properties: Optional[Dict] = None) -> bool:
        """Adds a concept or document node."""
        if self.graph is None: return False
        
        props = properties or {}
        props["type"] = entity_type
        
        self.graph.add_node(entity_id, **props)
        logger.debug(f"Added entity node: {entity_id} ({entity_type})")
        return True

    def add_relationship(self, source_id: str, target_id: str, relation_type: str, weight: float = 1.0) -> bool:
        """Adds an edge between two entities."""
        if self.graph is None: return False
        
        # Ensure nodes exist
        if not self.graph.has_node(source_id):
            logger.warning(f"Source node {source_id} does not exist.")
            return False
        if not self.graph.has_node(target_id):
            logger.warning(f"Target node {target_id} does not exist.")
            return False
            
        self.graph.add_edge(source_id, target_id, relation=relation_type, weight=weight)
        logger.debug(f"Added relationship: {source_id} -[{relation_type}]-> {target_id}")
        return True

    def find_path(self, source_id: str, target_id: str) -> List[str]:
        """Finds the shortest path between concepts."""
        if self.graph is None: return []
        
        try:
            path = nx.shortest_path(self.graph, source=source_id, target=target_id)
            return path
        except nx.NetworkXNoPath:
            return []
        except nx.NodeNotFound:
            return []

    def get_prerequisites(self, concept_id: str) -> List[str]:
        """Returns nodes that point TO the concept with a 'prerequisite' relationship."""
        if self.graph is None or not self.graph.has_node(concept_id): return []
        
        prereqs = []
        for src, dest, data in self.graph.in_edges(concept_id, data=True):
            if data.get("relation") == "prerequisite":
                prereqs.append(src)
        return prereqs

    def find_related(self, entity_id: str, max_depth: int = 1) -> List[Dict]:
        """Finds neighbor entities up to a certain depth."""
        if self.graph is None or not self.graph.has_node(entity_id): return []
        
        related = []
        try:
            # Using single source shortest path length to get neighbors within depth
            lengths = nx.single_source_shortest_path_length(self.graph, entity_id, cutoff=max_depth)
            for node, depth in lengths.items():
                if node != entity_id:
                    node_data = self.graph.nodes[node]
                    related.append({"id": node, "depth": depth, "data": node_data})
        except Exception as e:
            logger.error(f"Error finding related nodes for {entity_id}: {e}")
            
        return related

    def export_graph(self) -> bool:
        """Exports graph to JSON."""
        if self.graph is None: return False
        
        try:
            os.makedirs(os.path.dirname(self.persist_path), exist_ok=True)
            data = nx.node_link_data(self.graph)
            with open(self.persist_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Graph exported to {self.persist_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export graph: {e}")
            return False

    def load_graph(self) -> bool:
        """Loads graph from JSON."""
        if self.graph is None: return False
        if not os.path.exists(self.persist_path):
            logger.info("No existing graph found. Starting fresh.")
            return True
            
        try:
            with open(self.persist_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.graph = nx.node_link_graph(data)
            logger.info(f"Graph loaded successfully from {self.persist_path} with {self.graph.number_of_nodes()} nodes.")
            return True
        except Exception as e:
            logger.error(f"Failed to load graph: {e}")
            # Reset to empty on failure
            self.graph = nx.DiGraph()
            return False
