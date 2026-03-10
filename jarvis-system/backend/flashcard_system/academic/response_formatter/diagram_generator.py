import matplotlib.pyplot as plt
import io
import base64
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from utils.logger import logger

class DiagramType(str, Enum):
    CIRCUIT = 'circuit'
    GRAPH = 'graph'
    FLOWCHART = 'flowchart'
    BLOCK = 'block'
    CUSTOM = 'custom'

class Diagram(BaseModel):
    type: DiagramType
    content: str
    title: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DiagramGenerator:
    """
    Generates ASCII and graphical diagrams for engineering subjects.
    Supports circuits, graphs, flowcharts, and block diagrams.
    """
    def __init__(self):
        pass

    def generate_circuit(self, components: List[Dict[str, Any]]) -> str:
        """Generates a simplified ASCII representation of an electronic circuit."""
        # Extremely simplified ASCII circuit for demonstration
        ascii_art = "[V] --- [R] --- [L] --- |\n"
        ascii_art += " |                      |\n"
        ascii_art += " ------------------------"
        return ascii_art

    def plot_graph(self, x_data: List[float], y_data: List[float], title: str = "Plot", xlabel: str = "x", ylabel: str = "y") -> str:
        """Plots a graph using matplotlib and returns a base64 encoded string or ASCII."""
        try:
            plt.figure(figsize=(6, 4))
            plt.plot(x_data, y_data)
            plt.title(title)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.grid(True)
            
            # Save to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
            return f"IMAGE_DATA:{img_str}"
        except Exception as e:
            logger.error(f"Failed to plot graph: {e}")
            return "Unable to generate graphical plot."

    def draw_flowchart(self, nodes: List[str], connections: List[tuple]) -> str:
        """Generates an ASCII flowchart."""
        flow = ""
        for i, node in enumerate(nodes):
            flow += f"[ {node} ]"
            if i < len(nodes) - 1:
                flow += " --> "
        return flow

    def generate_ascii_block_diagram(self, blocks: List[str]) -> str:
        """Simple ASCII block diagram."""
        diagram = ""
        for b in blocks:
            diagram += f"+----------+\n| {b:^8} |\n+----------+\n     |      \n     v      \n"
        return diagram.rstrip("\n     |      \n     v      \n")
