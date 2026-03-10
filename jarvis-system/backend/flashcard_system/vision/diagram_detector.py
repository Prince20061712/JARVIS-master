"""Diagram detection and analysis for visual content."""

import logging
from typing import Optional, List, Dict, Tuple

logger = logging.getLogger(__name__)


class DiagramAnalyzer:
    """
    Analyzes mathematical and educational diagrams.
    Provides methods for extracting information from visual representations.
    """
    
    def __init__(self):
        """Initialize diagram analyzer."""
        self.diagram_types = [
            'flowchart', 'graph', 'circuit', 
            'venn_diagram', 'coordinate_plane', 'tree'
        ]
    
    def analyze_coordinate_plane(self, points: List[Tuple[float, float]]) -> Optional[Dict]:
        """
        Analyze points on a coordinate plane.
        
        Args:
            points: List of (x, y) coordinate tuples
        
        Returns:
            Analysis results dictionary or None
        """
        try:
            import numpy as np
            
            if not points or len(points) < 2:
                logger.warning("Not enough points to analyze")
                return None
            
            points_array = np.array(points)
            
            # Calculate basic statistics
            x_coords = points_array[:, 0]
            y_coords = points_array[:, 1]
            
            # Fit a line to the points
            z = np.polyfit(x_coords, y_coords, 1)
            slope = z[0]
            intercept = z[1]
            
            # Calculate R-squared
            y_fit = np.polyval(z, x_coords)
            ss_res = np.sum((y_coords - y_fit) ** 2)
            ss_tot = np.sum((y_coords - np.mean(y_coords)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            return {
                "point_count": len(points),
                "x_range": (float(np.min(x_coords)), float(np.max(x_coords))),
                "y_range": (float(np.min(y_coords)), float(np.max(y_coords))),
                "slope": float(slope),
                "intercept": float(intercept),
                "r_squared": float(r_squared),
                "equation": f"y = {slope:.2f}x + {intercept:.2f}"
            }
        except Exception as e:
            logger.error(f"Error analyzing coordinate plane: {str(e)}")
            return None
    
    def detect_equation_structure(self, text: str) -> Optional[Dict]:
        """
        Detect and parse mathematical equation structure.
        
        Args:
            text: Equation text
        
        Returns:
            Parsed equation information or None
        """
        try:
            import re
            
            # Basic equation detection patterns
            patterns = {
                'linear': r'^y\s*=\s*(.+)x\s*([+-])\s*(.+)$',
                'quadratic': r'^y\s*=\s*(.+)x\^2\s*([+-])\s*(.+)x\s*([+-])\s*(.+)$',
                'polynomial': r'^(.+)\s*=\s*0$',
                'fraction': r'^(.+)/(.+)$',
            }
            
            equation_type = None
            components = {}
            
            for eq_type, pattern in patterns.items():
                if re.match(pattern, text.replace(' ', '')):
                    equation_type = eq_type
                    break
            
            return {
                "equation": text,
                "type": equation_type,
                "components": components,
                "complexity": len(text.split())
            }
        except Exception as e:
            logger.error(f"Error detecting equation structure: {str(e)}")
            return None
    
    def extract_graph_data(self, nodes: List[Dict], edges: List[Tuple]) -> Optional[Dict]:
        """
        Extract and analyze graph/network structure.
        
        Args:
            nodes: List of node dictionaries
            edges: List of edge tuples (source, target)
        
        Returns:
            Graph analysis results or None
        """
        try:
            node_count = len(nodes)
            edge_count = len(edges)
            
            # Calculate degree for each node
            degree_map = {node['id']: 0 for node in nodes}
            for source, target in edges:
                if source in degree_map:
                    degree_map[source] += 1
                if target in degree_map:
                    degree_map[target] += 1
            
            # Find central nodes
            max_degree = max(degree_map.values()) if degree_map else 0
            central_nodes = [node for node, degree in degree_map.items() if degree == max_degree]
            
            return {
                "node_count": node_count,
                "edge_count": edge_count,
                "average_degree": sum(degree_map.values()) / node_count if node_count > 0 else 0,
                "max_degree": max_degree,
                "central_nodes": central_nodes,
                "is_connected": self._is_graph_connected(nodes, edges)
            }
        except Exception as e:
            logger.error(f"Error extracting graph data: {str(e)}")
            return None
    
    def _is_graph_connected(self, nodes: List[Dict], edges: List[Tuple]) -> bool:
        """
        Check if graph is connected.
        
        Args:
            nodes: List of node dictionaries
            edges: List of edge tuples
        
        Returns:
            True if connected, False otherwise
        """
        if not nodes:
            return False
        
        # Build adjacency list
        adj = {node['id']: [] for node in nodes}
        for source, target in edges:
            if source in adj and target in adj:
                adj[source].append(target)
                adj[target].append(source)
        
        # BFS to check connectivity
        start_node = nodes[0]['id']
        visited = {start_node}
        queue = [start_node]
        
        while queue:
            node = queue.pop(0)
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return len(visited) == len(nodes)
