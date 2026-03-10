"""
Hand drawing recognition module for analyzing sketches, diagrams, and handwritten content.
Integrates with OCR engines and shape recognition for educational context.
"""

import asyncio
import base64
import hashlib
import json
import logging
import math
import os
import re
import tempfile
import uuid
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, Set, Union
import numpy as np
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import threading

import cv2
from PIL import Image, ImageDraw, ImageFont
import pytesseract
from pdf2image import convert_from_path
import requests
from io import BytesIO

# For shape recognition
from shapely.geometry import Polygon, Point, LineString
from shapely import affinity

# For machine learning based recognition
try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ShapeType(Enum):
    """Types of shapes that can be recognized."""
    UNKNOWN = "unknown"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"
    SQUARE = "square"
    RECTANGLE = "rectangle"
    TRIANGLE = "triangle"
    LINE = "line"
    ARROW = "arrow"
    CURVE = "curve"
    CLOUD = "cloud"
    STAR = "star"
    HEXAGON = "hexagon"
    PENTAGON = "pentagon"
    DIAMOND = "diamond"
    PARALLELOGRAM = "parallelogram"
    TRAPEZOID = "trapezoid"
    TEXT = "text"
    FLOWCHART_NODE = "flowchart_node"
    FLOWCHART_DECISION = "flowchart_decision"
    FLOWCHART_TERMINAL = "flowchart_terminal"
    FLOWCHART_PROCESS = "flowchart_process"
    FLOWCHART_DATA = "flowchart_data"
    UML_CLASS = "uml_class"
    UML_ACTOR = "uml_actor"
    UML_USE_CASE = "uml_use_case"
    MATH_SYMBOL = "math_symbol"
    CHEMICAL_STRUCTURE = "chemical_structure"


class DrawingMedium(Enum):
    """Medium used for drawing."""
    DIGITAL = "digital"
    PAPER = "paper"
    WHITEBOARD = "whiteboard"
    BLACKBOARD = "blackboard"
    SCREENSHOT = "screenshot"
    SCANNED = "scanned"


class RecognitionConfidence(Enum):
    """Confidence levels for recognition."""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"
    UNCERTAIN = "uncertain"


@dataclass
class RecognitionOptions:
    """Options for drawing recognition."""
    language: str = "eng"
    ocr_enabled: bool = True
    shape_recognition: bool = True
    diagram_recognition: bool = True
    handwritten_text: bool = True
    detect_arrows: bool = True
    detect_connections: bool = True
    extract_relationships: bool = True
    min_confidence: float = 0.5
    preprocessing: bool = True
    denoise: bool = True
    threshold: bool = True
    deskew: bool = True
    enhance_contrast: bool = True
    dpi: int = 300
    page_segmentation_mode: int = 6  # PSM for Tesseract
    character_whitelist: Optional[str] = None
    timeout_seconds: int = 30
    use_tensorflow: bool = False  # Use TF if available
    model_path: Optional[Path] = None
    save_debug_images: bool = False
    debug_dir: Optional[Path] = None


@dataclass
class Point:
    """2D point with coordinates."""
    x: float
    y: float
    
    def distance_to(self, other: 'Point') -> float:
        """Calculate Euclidean distance to another point."""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
    
    def as_tuple(self) -> Tuple[float, float]:
        """Return as tuple."""
        return (self.x, self.y)


@dataclass
class BoundingBox:
    """Bounding box for detected elements."""
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    
    @property
    def width(self) -> float:
        return self.x_max - self.x_min
    
    @property
    def height(self) -> float:
        return self.y_max - self.y_min
    
    @property
    def center(self) -> Point:
        return Point(
            (self.x_min + self.x_max) / 2,
            (self.y_min + self.y_max) / 2
        )
    
    @property
    def area(self) -> float:
        return self.width * self.height
    
    def contains(self, point: Point) -> bool:
        """Check if point is inside bounding box."""
        return (self.x_min <= point.x <= self.x_max and 
                self.y_min <= point.y <= self.y_max)
    
    def intersection(self, other: 'BoundingBox') -> Optional['BoundingBox']:
        """Get intersection with another bounding box."""
        x_min = max(self.x_min, other.x_min)
        y_min = max(self.y_min, other.y_min)
        x_max = min(self.x_max, other.x_max)
        y_max = min(self.y_max, other.y_max)
        
        if x_min < x_max and y_min < y_max:
            return BoundingBox(x_min, y_min, x_max, y_max)
        return None
    
    def union(self, other: 'BoundingBox') -> 'BoundingBox':
        """Get union with another bounding box."""
        return BoundingBox(
            min(self.x_min, other.x_min),
            min(self.y_min, other.y_min),
            max(self.x_max, other.x_max),
            max(self.y_max, other.y_max)
        )
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            'x_min': self.x_min,
            'y_min': self.y_min,
            'x_max': self.x_max,
            'y_max': self.y_max,
            'width': self.width,
            'height': self.height
        }


@dataclass
class DiagramElement:
    """A single element in a diagram."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    shape_type: ShapeType
    bounding_box: BoundingBox
    points: List[Point] = field(default_factory=list)
    text: Optional[str] = None
    confidence: float = 0.0
    color: Optional[Tuple[int, int, int]] = None
    thickness: Optional[int] = None
    filled: bool = False
    connections: List[str] = field(default_factory=list)  # IDs of connected elements
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'shape_type': self.shape_type.value,
            'bounding_box': self.bounding_box.to_dict(),
            'points': [(p.x, p.y) for p in self.points],
            'text': self.text,
            'confidence': self.confidence,
            'color': self.color,
            'thickness': self.thickness,
            'filled': self.filled,
            'connections': self.connections,
            'metadata': self.metadata
        }


@dataclass
class Diagram:
    """Complete diagram with multiple elements."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    elements: List[DiagramElement] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    title: Optional[str] = None
    description: Optional[str] = None
    diagram_type: Optional[str] = None  # flowchart, UML, mindmap, etc.
    created_at: datetime = field(default_factory=datetime.now)
    image_path: Optional[Path] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_element(self, element: DiagramElement):
        """Add an element to the diagram."""
        self.elements.append(element)
    
    def get_element(self, element_id: str) -> Optional[DiagramElement]:
        """Get element by ID."""
        for element in self.elements:
            if element.id == element_id:
                return element
        return None
    
    def find_connected_components(self, element_id: str) -> List[str]:
        """Find all elements connected to the given element."""
        visited = set()
        to_visit = [element_id]
        
        while to_visit:
            current = to_visit.pop(0)
            if current in visited:
                continue
            
            visited.add(current)
            element = self.get_element(current)
            if element:
                for conn in element.connections:
                    if conn not in visited:
                        to_visit.append(conn)
        
        return list(visited)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'elements': [e.to_dict() for e in self.elements],
            'relationships': self.relationships,
            'title': self.title,
            'description': self.description,
            'diagram_type': self.diagram_type,
            'created_at': self.created_at.isoformat(),
            'element_count': len(self.elements),
            'metadata': self.metadata
        }


@dataclass
class OCRResult:
    """Result of OCR text recognition."""
    text: str
    confidence: float
    bounding_box: BoundingBox
    language: str
    page_number: Optional[int] = None
    line_number: Optional[int] = None
    word_boxes: List[Dict[str, Any]] = field(default_factory=list)
    is_handwritten: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'text': self.text,
            'confidence': self.confidence,
            'bounding_box': self.bounding_box.to_dict(),
            'language': self.language,
            'page_number': self.page_number,
            'line_number': self.line_number,
            'word_boxes': self.word_boxes,
            'is_handwritten': self.is_handwritten,
            'metadata': self.metadata
        }


@dataclass
class DrawingAnalysis:
    """Complete analysis of a drawing."""
    diagram: Diagram
    ocr_results: List[OCRResult] = field(default_factory=list)
    shapes: List[DiagramElement] = field(default_factory=list)
    text_elements: List[OCRResult] = field(default_factory=list)
    confidence: RecognitionConfidence = RecognitionConfidence.MEDIUM
    processing_time_ms: float = 0.0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'diagram': self.diagram.to_dict(),
            'ocr_results': [r.to_dict() for r in self.ocr_results],
            'shapes': [s.to_dict() for s in self.shapes],
            'text_elements': [t.to_dict() for t in self.text_elements],
            'confidence': self.confidence.value,
            'processing_time_ms': self.processing_time_ms,
            'warnings': self.warnings,
            'errors': self.errors
        }


@dataclass
class Sketch:
    """A single sketch/drawing from a session."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    image_data: Optional[bytes] = None
    image_path: Optional[Path] = None
    timestamp: datetime = field(default_factory=datetime.now)
    analysis: Optional[DrawingAnalysis] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    @property
    def has_image(self) -> bool:
        """Check if sketch has image data."""
        return self.image_data is not None or (self.image_path and self.image_path.exists())
    
    def get_image(self) -> Optional[Image.Image]:
        """Get PIL Image of the sketch."""
        if self.image_data:
            return Image.open(BytesIO(self.image_data))
        elif self.image_path and self.image_path.exists():
            return Image.open(self.image_path)
        return None


@dataclass
class DrawingSession:
    """A session containing multiple sketches/drawings."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    topic: Optional[str] = None
    sketches: List[Sketch] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_sketch(self, sketch: Sketch):
        """Add a sketch to the session."""
        sketch.session_id = self.id
        self.sketches.append(sketch)
    
    def complete(self):
        """Mark session as completed."""
        self.end_time = datetime.now()
    
    def get_duration(self) -> float:
        """Get session duration in seconds."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        total_sketches = len(self.sketches)
        analyzed = sum(1 for s in self.sketches if s.analysis is not None)
        
        return {
            'total_sketches': total_sketches,
            'analyzed_sketches': analyzed,
            'duration_seconds': self.get_duration(),
            'topic': self.topic,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None
        }


class ImagePreprocessor:
    """Preprocess images for better recognition."""
    
    @staticmethod
    def preprocess(
        image: Image.Image,
        options: RecognitionOptions
    ) -> Image.Image:
        """
        Preprocess image for recognition.
        
        Args:
            image: PIL Image
            options: Recognition options
            
        Returns:
            Preprocessed image
        """
        # Convert to numpy array for OpenCV
        img_array = np.array(image)
        
        # Convert to grayscale if needed
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Denoise
        if options.denoise:
            gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Enhance contrast
        if options.enhance_contrast:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
        
        # Threshold
        if options.threshold:
            gray = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
        
        # Deskew
        if options.deskew:
            gray = ImagePreprocessor._deskew(gray)
        
        # Convert back to PIL
        return Image.fromarray(gray)
    
    @staticmethod
    def _deskew(image: np.ndarray) -> np.ndarray:
        """Deskew image."""
        coords = np.column_stack(np.where(image > 0))
        if len(coords) < 2:
            return image
        
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        
        if abs(angle) < 0.5:
            return image
        
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        
        return rotated


class ShapeRecognizer:
    """Recognize shapes in drawings."""
    
    def __init__(self):
        """Initialize shape recognizer."""
        self._init_shape_templates()
    
    def _init_shape_templates(self):
        """Initialize shape templates for matching."""
        self.templates = {
            ShapeType.CIRCLE: self._is_circle,
            ShapeType.SQUARE: self._is_square,
            ShapeType.RECTANGLE: self._is_rectangle,
            ShapeType.TRIANGLE: self._is_triangle,
            ShapeType.LINE: self._is_line,
            ShapeType.ARROW: self._is_arrow,
            ShapeType.DIAMOND: self._is_diamond,
            ShapeType.PARALLELOGRAM: self._is_parallelogram,
            ShapeType.TRAPEZOID: self._is_trapezoid
        }
    
    def recognize(
        self,
        contour: np.ndarray,
        options: RecognitionOptions
    ) -> Tuple[ShapeType, float]:
        """
        Recognize shape from contour.
        
        Args:
            contour: OpenCV contour
            options: Recognition options
            
        Returns:
            Tuple of (shape_type, confidence)
        """
        if not options.shape_recognition:
            return ShapeType.UNKNOWN, 0.0
        
        # Approximate contour
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        num_vertices = len(approx)
        
        # Basic shape classification
        if num_vertices == 2:
            return self._recognize_line(contour, options)
        elif num_vertices == 3:
            return ShapeType.TRIANGLE, self._calculate_triangle_confidence(contour)
        elif num_vertices == 4:
            return self._recognize_quadrilateral(contour)
        elif num_vertices > 4:
            return self._recognize_polygon(contour, num_vertices)
        
        return ShapeType.UNKNOWN, 0.0
    
    def _recognize_line(
        self,
        contour: np.ndarray,
        options: RecognitionOptions
    ) -> Tuple[ShapeType, float]:
        """Recognize line or arrow."""
        if options.detect_arrows and self._is_arrow(contour):
            return ShapeType.ARROW, 0.8
        
        # Check if it's a straight line
        if self._is_line(contour):
            return ShapeType.LINE, 0.9
        
        # Check if it's a curve
        if self._is_curve(contour):
            return ShapeType.CURVE, 0.7
        
        return ShapeType.UNKNOWN, 0.3
    
    def _recognize_quadrilateral(self, contour: np.ndarray) -> Tuple[ShapeType, float]:
        """Recognize quadrilateral shapes."""
        # Calculate shape properties
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        if perimeter == 0:
            return ShapeType.UNKNOWN, 0.0
        
        # Get bounding rectangle
        rect = cv2.minAreaRect(contour)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        
        # Calculate aspect ratio
        width = rect[1][0]
        height = rect[1][1]
        if width == 0 or height == 0:
            return ShapeType.UNKNOWN, 0.0
        
        aspect_ratio = max(width, height) / min(width, height)
        
        # Calculate rectangularity
        rect_area = width * height
        rectangularity = area / rect_area if rect_area > 0 else 0
        
        # Check for square
        if abs(aspect_ratio - 1.0) < 0.2 and rectangularity > 0.8:
            return ShapeType.SQUARE, rectangularity
        
        # Check for rectangle
        if rectangularity > 0.7:
            return ShapeType.RECTANGLE, rectangularity
        
        # Check for diamond (rotated square)
        if self._is_diamond(contour):
            return ShapeType.DIAMOND, 0.7
        
        # Check for parallelogram
        if self._is_parallelogram(contour):
            return ShapeType.PARALLELOGRAM, 0.6
        
        # Check for trapezoid
        if self._is_trapezoid(contour):
            return ShapeType.TRAPEZOID, 0.6
        
        return ShapeType.UNKNOWN, rectangularity
    
    def _recognize_polygon(
        self,
        contour: np.ndarray,
        num_vertices: int
    ) -> Tuple[ShapeType, float]:
        """Recognize polygon shapes."""
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        if perimeter == 0:
            return ShapeType.UNKNOWN, 0.0
        
        # Calculate circularity
        circularity = 4 * math.pi * area / (perimeter * perimeter)
        
        if circularity > 0.8:
            return ShapeType.CIRCLE, circularity
        elif circularity > 0.6:
            return ShapeType.ELLIPSE, circularity
        
        # Check for specific polygons
        if num_vertices == 5:
            return ShapeType.PENTAGON, 0.7
        elif num_vertices == 6:
            if self._is_hexagon(contour):
                return ShapeType.HEXAGON, 0.7
        
        return ShapeType.UNKNOWN, circularity
    
    def _is_circle(self, contour: np.ndarray) -> bool:
        """Check if contour is a circle."""
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        if perimeter == 0:
            return False
        
        circularity = 4 * math.pi * area / (perimeter * perimeter)
        return circularity > 0.8
    
    def _is_square(self, contour: np.ndarray) -> bool:
        """Check if contour is a square."""
        rect = cv2.minAreaRect(contour)
        width, height = rect[1]
        
        if width == 0 or height == 0:
            return False
        
        aspect_ratio = max(width, height) / min(width, height)
        return abs(aspect_ratio - 1.0) < 0.2
    
    def _is_rectangle(self, contour: np.ndarray) -> bool:
        """Check if contour is a rectangle."""
        rect = cv2.minAreaRect(contour)
        area = cv2.contourArea(contour)
        rect_area = rect[1][0] * rect[1][1]
        
        if rect_area == 0:
            return False
        
        rectangularity = area / rect_area
        return rectangularity > 0.7
    
    def _is_triangle(self, contour: np.ndarray) -> bool:
        """Check if contour is a triangle."""
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        return len(approx) == 3
    
    def _is_line(self, contour: np.ndarray) -> bool:
        """Check if contour is a line."""
        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(contour)
        
        # Calculate aspect ratio
        if min(w, h) == 0:
            return False
        
        aspect_ratio = max(w, h) / min(w, h)
        
        # Calculate area/perimeter ratio (should be small for lines)
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        if perimeter == 0:
            return False
        
        area_perimeter_ratio = area / perimeter
        
        return aspect_ratio > 5 and area_perimeter_ratio < 2
    
    def _is_arrow(self, contour: np.ndarray) -> bool:
        """Check if contour is an arrow."""
        # Simplified arrow detection
        hull = cv2.convexHull(contour)
        
        if len(hull) < 5:
            return False
        
        # Check for triangular head
        epsilon = 0.02 * cv2.arcLength(hull, True)
        approx = cv2.approxPolyDP(hull, epsilon, True)
        
        return len(approx) >= 5 and len(approx) <= 8
    
    def _is_curve(self, contour: np.ndarray) -> bool:
        """Check if contour is a curve."""
        # Calculate curvature
        if len(contour) < 5:
            return False
        
        # Fit a line
        [vx, vy, x, y] = cv2.fitLine(contour, cv2.DIST_L2, 0, 0.01, 0.01)
        
        # Calculate distances from line
        line = LineString([(x - 100*vx, y - 100*vy), (x + 100*vx, y + 100*vy)])
        
        total_distance = 0
        for point in contour:
            p = Point(point[0][0], point[0][1])
            total_distance += line.distance(p)
        
        avg_distance = total_distance / len(contour)
        
        return avg_distance > 5
    
    def _is_diamond(self, contour: np.ndarray) -> bool:
        """Check if contour is a diamond."""
        rect = cv2.minAreaRect(contour)
        width, height = rect[1]
        
        if width == 0 or height == 0:
            return False
        
        # Check if it's roughly square
        if abs(width - height) / max(width, height) > 0.3:
            return False
        
        # Check rotation
        angle = abs(rect[2])
        
        return 35 < angle < 55 or 125 < angle < 145
    
    def _is_parallelogram(self, contour: np.ndarray) -> bool:
        """Check if contour is a parallelogram."""
        # Approximate to 4 points
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        if len(approx) != 4:
            return False
        
        # Calculate angles
        points = approx.reshape(-1, 2)
        
        def angle(p1, p2, p3):
            v1 = p1 - p2
            v2 = p3 - p2
            cos = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
            return np.arccos(np.clip(cos, -1, 1))
        
        angles = [
            angle(points[i], points[(i+1)%4], points[(i+2)%4])
            for i in range(4)
        ]
        
        # Opposite angles should be equal
        return abs(angles[0] - angles[2]) < 0.3 and abs(angles[1] - angles[3]) < 0.3
    
    def _is_trapezoid(self, contour: np.ndarray) -> bool:
        """Check if contour is a trapezoid."""
        # Approximate to 4 points
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        if len(approx) != 4:
            return False
        
        # Check for one pair of parallel sides
        points = approx.reshape(-1, 2)
        
        def is_parallel(p1, p2, p3, p4):
            v1 = p2 - p1
            v2 = p4 - p3
            if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
                return False
            cos = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
            return abs(abs(cos) - 1) < 0.1
        
        parallel_pairs = [
            is_parallel(points[0], points[1], points[2], points[3]),
            is_parallel(points[1], points[2], points[3], points[0])
        ]
        
        return any(parallel_pairs)
    
    def _is_hexagon(self, contour: np.ndarray) -> bool:
        """Check if contour is a hexagon."""
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        if len(approx) != 6:
            return False
        
        # Check for symmetry
        hull = cv2.convexHull(contour)
        return len(hull) == 6
    
    def _calculate_triangle_confidence(self, contour: np.ndarray) -> float:
        """Calculate confidence for triangle detection."""
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        if perimeter == 0:
            return 0.0
        
        # Calculate how well it fits in its bounding triangle
        rect = cv2.boundingRect(contour)
        rect_area = rect[2] * rect[3]
        
        area_ratio = area / rect_area if rect_area > 0 else 0
        
        return area_ratio


class HandDrawingRecognizer:
    """
    Main class for recognizing hand drawings, diagrams, and handwritten text.
    """
    
    def __init__(
        self,
        tesseract_cmd: Optional[str] = None,
        data_dir: Optional[Path] = None,
        use_gpu: bool = False
    ):
        """
        Initialize hand drawing recognizer.
        
        Args:
            tesseract_cmd: Path to tesseract executable
            data_dir: Directory for storing data
            use_gpu: Whether to use GPU for TensorFlow
        """
        # Set tesseract path if provided
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        self.data_dir = data_dir or Path.home() / '.jarvis' / 'vision'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.preprocessor = ImagePreprocessor()
        self.shape_recognizer = ShapeRecognizer()
        
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._lock = threading.Lock()
        
        # TensorFlow setup
        self.tf_model = None
        if use_gpu and TF_AVAILABLE:
            self._setup_tensorflow()
        
        # Active sessions
        self._active_sessions: Dict[str, DrawingSession] = {}
        
        logger.info(f"HandDrawingRecognizer initialized with data dir: {self.data_dir}")
    
    def _setup_tensorflow(self):
        """Setup TensorFlow model for advanced recognition."""
        try:
            # This would load a pre-trained model for sketch recognition
            # For now, just note that TF is available
            logger.info("TensorFlow is available for sketch recognition")
            
            # Example: Load a MobileNet for feature extraction
            # self.tf_model = tf.keras.applications.MobileNetV2(weights='imagenet')
            
        except Exception as e:
            logger.warning(f"Failed to setup TensorFlow: {e}")
            self.tf_model = None
    
    async def recognize_drawing(
        self,
        image: Union[str, Path, bytes, Image.Image],
        options: Optional[RecognitionOptions] = None,
        session_id: Optional[str] = None
    ) -> DrawingAnalysis:
        """
        Recognize elements in a drawing.
        
        Args:
            image: Input image (path, bytes, or PIL Image)
            options: Recognition options
            session_id: Optional session ID
            
        Returns:
            DrawingAnalysis with recognized elements
        """
        start_time = datetime.now()
        options = options or RecognitionOptions()
        
        try:
            # Load image
            pil_image = await self._load_image(image)
            
            # Preprocess
            if options.preprocessing:
                pil_image = self.preprocessor.preprocess(pil_image, options)
            
            # Save debug image if requested
            if options.save_debug_images and options.debug_dir:
                debug_path = options.debug_dir / f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                pil_image.save(debug_path)
            
            # Convert to OpenCV format
            img_array = np.array(pil_image)
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Perform OCR
            ocr_results = []
            if options.ocr_enabled:
                ocr_results = await self._perform_ocr(pil_image, options)
            
            # Perform shape recognition
            shapes = []
            diagram_elements = []
            
            if options.shape_recognition or options.diagram_recognition:
                shapes, diagram_elements = await self._recognize_shapes(
                    gray, options
                )
            
            # Detect relationships between elements
            relationships = []
            if options.extract_relationships:
                relationships = self._detect_relationships(
                    diagram_elements, ocr_results
                )
            
            # Create diagram
            diagram = Diagram(
                elements=diagram_elements,
                relationships=relationships,
                diagram_type=self._determine_diagram_type(diagram_elements, relationships)
            )
            
            # Calculate overall confidence
            confidences = []
            if ocr_results:
                confidences.extend([r.confidence for r in ocr_results])
            if shapes:
                confidences.extend([s.confidence for s in shapes])
            
            overall_confidence = np.mean(confidences) if confidences else 0.5
            confidence_level = self._confidence_to_level(overall_confidence)
            
            # Create analysis
            analysis = DrawingAnalysis(
                diagram=diagram,
                ocr_results=ocr_results,
                shapes=shapes,
                text_elements=ocr_results,
                confidence=confidence_level,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
            # Save to session if provided
            if session_id and session_id in self._active_sessions:
                sketch = Sketch(
                    image_data=await self._image_to_bytes(pil_image) if isinstance(image, (str, Path)) else None,
                    image_path=Path(image) if isinstance(image, (str, Path)) else None,
                    analysis=analysis,
                    user_id=self._active_sessions[session_id].user_id,
                    session_id=session_id
                )
                self._active_sessions[session_id].add_sketch(sketch)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Drawing recognition failed: {e}")
            return DrawingAnalysis(
                diagram=Diagram(),
                errors=[str(e)],
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    async def _load_image(
        self,
        image: Union[str, Path, bytes, Image.Image]
    ) -> Image.Image:
        """Load image from various sources."""
        try:
            if isinstance(image, (str, Path)):
                return Image.open(image)
            elif isinstance(image, bytes):
                return Image.open(BytesIO(image))
            elif isinstance(image, Image.Image):
                return image
            else:
                raise ValueError(f"Unsupported image type: {type(image)}")
        except Exception as e:
            raise ValueError(f"Failed to load image: {e}")
    
    async def _image_to_bytes(self, image: Image.Image, format: str = 'PNG') -> bytes:
        """Convert PIL Image to bytes."""
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format=format)
        return img_byte_arr.getvalue()
    
    async def _perform_ocr(
        self,
        image: Image.Image,
        options: RecognitionOptions
    ) -> List[OCRResult]:
        """
        Perform OCR on image.
        
        Args:
            image: PIL Image
            options: Recognition options
            
        Returns:
            List of OCR results
        """
        results = []
        
        try:
            # Configure Tesseract
            config = f"--psm {options.page_segmentation_mode} -l {options.language}"
            if options.character_whitelist:
                config += f" -c tessedit_char_whitelist={options.character_whitelist}"
            
            # Run OCR in thread pool
            loop = asyncio.get_event_loop()
            
            # Get data with bounding boxes
            ocr_data = await loop.run_in_executor(
                self.executor,
                lambda: pytesseract.image_to_data(
                    image,
                    config=config,
                    output_type=pytesseract.Output.DICT
                )
            )
            
            # Parse results
            n_boxes = len(ocr_data['text'])
            for i in range(n_boxes):
                if int(ocr_data['conf'][i]) > 0:  # Filter low confidence
                    text = ocr_data['text'][i].strip()
                    if text:  # Only add non-empty text
                        conf = float(ocr_data['conf'][i]) / 100.0
                        
                        # Only include if confidence meets minimum
                        if conf >= options.min_confidence:
                            box = BoundingBox(
                                x_min=ocr_data['left'][i],
                                y_min=ocr_data['top'][i],
                                x_max=ocr_data['left'][i] + ocr_data['width'][i],
                                y_max=ocr_data['top'][i] + ocr_data['height'][i]
                            )
                            
                            results.append(OCRResult(
                                text=text,
                                confidence=conf,
                                bounding_box=box,
                                language=options.language,
                                line_number=ocr_data['line_num'][i],
                                word_boxes=[{
                                    'text': text,
                                    'conf': conf,
                                    'bbox': box.to_dict()
                                }]
                            ))
            
            logger.info(f"OCR found {len(results)} text elements")
            
        except Exception as e:
            logger.error(f"OCR failed: {e}")
        
        return results
    
    async def _recognize_shapes(
        self,
        image: np.ndarray,
        options: RecognitionOptions
    ) -> Tuple[List[DiagramElement], List[DiagramElement]]:
        """
        Recognize shapes in image.
        
        Args:
            image: Grayscale image array
            options: Recognition options
            
        Returns:
            Tuple of (shapes_list, diagram_elements)
        """
        shapes = []
        diagram_elements = []
        
        try:
            # Find contours
            contours, _ = cv2.findContours(
                image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            loop = asyncio.get_event_loop()
            
            for contour in contours:
                # Filter small contours
                area = cv2.contourArea(contour)
                if area < 100:  # Ignore very small artifacts
                    continue
                
                # Recognize shape
                shape_type, confidence = await loop.run_in_executor(
                    self.executor,
                    lambda: self.shape_recognizer.recognize(contour, options)
                )
                
                if confidence >= options.min_confidence:
                    # Create bounding box
                    x, y, w, h = cv2.boundingRect(contour)
                    bbox = BoundingBox(x, y, x + w, y + h)
                    
                    # Extract points
                    points = [
                        Point(float(p[0][0]), float(p[0][1]))
                        for p in contour
                    ]
                    
                    # Create element
                    element = DiagramElement(
                        shape_type=shape_type,
                        bounding_box=bbox,
                        points=points,
                        confidence=confidence
                    )
                    
                    shapes.append(element)
                    
                    if options.diagram_recognition:
                        diagram_elements.append(element)
            
            logger.info(f"Shape recognition found {len(shapes)} shapes")
            
        except Exception as e:
            logger.error(f"Shape recognition failed: {e}")
        
        return shapes, diagram_elements
    
    def _detect_relationships(
        self,
        elements: List[DiagramElement],
        text_elements: List[OCRResult]
    ) -> List[Dict[str, Any]]:
        """
        Detect relationships between diagram elements.
        
        Args:
            elements: List of diagram elements
            text_elements: List of OCR results
            
        Returns:
            List of relationships
        """
        relationships = []
        
        # Check for proximity-based relationships
        for i, elem1 in enumerate(elements):
            for j, elem2 in enumerate(elements[i+1:], i+1):
                # Calculate distance between centers
                center1 = elem1.bounding_box.center
                center2 = elem2.bounding_box.center
                
                distance = center1.distance_to(center2)
                
                # Check if they're close enough to be related
                avg_size = (elem1.bounding_box.width + elem2.bounding_box.width) / 2
                
                if distance < avg_size * 1.5:
                    relationships.append({
                        'type': 'proximity',
                        'from_id': elem1.id,
                        'to_id': elem2.id,
                        'confidence': 1.0 - (distance / (avg_size * 2))
                    })
        
        # Check for arrow-based relationships
        arrows = [e for e in elements if e.shape_type == ShapeType.ARROW]
        
        for arrow in arrows:
            # Find elements near arrow ends
            arrow_points = arrow.points
            if len(arrow_points) >= 2:
                start = arrow_points[0]
                end = arrow_points[-1]
                
                # Find nearest elements
                nearest_to_start = self._find_nearest_element(start, elements)
                nearest_to_end = self._find_nearest_element(end, elements)
                
                if nearest_to_start and nearest_to_end:
                    relationships.append({
                        'type': 'arrow',
                        'from_id': nearest_to_start.id,
                        'to_id': nearest_to_end.id,
                        'arrow_id': arrow.id,
                        'confidence': 0.8
                    })
        
        # Associate text with shapes
        for text in text_elements:
            text_center = text.bounding_box.center
            
            # Find closest shape
            nearest = self._find_nearest_element(text_center, elements)
            if nearest:
                # Check if text is inside shape
                if nearest.bounding_box.contains(text_center):
                    nearest.text = text.text
                    relationships.append({
                        'type': 'label',
                        'element_id': nearest.id,
                        'text': text.text,
                        'confidence': 0.9
                    })
        
        return relationships
    
    def _find_nearest_element(
        self,
        point: Point,
        elements: List[DiagramElement]
    ) -> Optional[DiagramElement]:
        """Find the nearest element to a point."""
        if not elements:
            return None
        
        nearest = None
        min_distance = float('inf')
        
        for elem in elements:
            center = elem.bounding_box.center
            distance = point.distance_to(center)
            
            if distance < min_distance:
                min_distance = distance
                nearest = elem
        
        return nearest
    
    def _determine_diagram_type(
        self,
        elements: List[DiagramElement],
        relationships: List[Dict[str, Any]]
    ) -> str:
        """Determine the type of diagram."""
        shape_types = [e.shape_type for e in elements]
        
        # Check for flowchart
        flowchart_shapes = [
            ShapeType.FLOWCHART_NODE,
            ShapeType.FLOWCHART_DECISION,
            ShapeType.FLOWCHART_PROCESS,
            ShapeType.FLOWCHART_TERMINAL,
            ShapeType.FLOWCHART_DATA
        ]
        
        if any(s in flowchart_shapes for s in shape_types):
            return "flowchart"
        
        # Check for UML
        uml_shapes = [
            ShapeType.UML_CLASS,
            ShapeType.UML_ACTOR,
            ShapeType.UML_USE_CASE
        ]
        
        if any(s in uml_shapes for s in shape_types):
            return "uml"
        
        # Check for mind map (lots of circles with connections)
        circles = sum(1 for s in shape_types if s == ShapeType.CIRCLE)
        if circles >= 3 and len(relationships) >= circles - 1:
            return "mind_map"
        
        # Check for mathematical diagram
        if ShapeType.MATH_SYMBOL in shape_types:
            return "mathematical"
        
        # Default
        return "general_diagram"
    
    def _confidence_to_level(self, confidence: float) -> RecognitionConfidence:
        """Convert confidence score to level."""
        if confidence >= 0.9:
            return RecognitionConfidence.VERY_HIGH
        elif confidence >= 0.8:
            return RecognitionConfidence.HIGH
        elif confidence >= 0.6:
            return RecognitionConfidence.MEDIUM
        elif confidence >= 0.4:
            return RecognitionConfidence.LOW
        elif confidence >= 0.2:
            return RecognitionConfidence.VERY_LOW
        else:
            return RecognitionConfidence.UNCERTAIN
    
    async def create_session(
        self,
        user_id: str,
        topic: Optional[str] = None
    ) -> DrawingSession:
        """
        Create a new drawing session.
        
        Args:
            user_id: User identifier
            topic: Session topic
            
        Returns:
            Created DrawingSession
        """
        session = DrawingSession(
            user_id=user_id,
            topic=topic
        )
        
        self._active_sessions[session.id] = session
        logger.info(f"Created drawing session {session.id} for user {user_id}")
        
        return session
    
    def get_session(self, session_id: str) -> Optional[DrawingSession]:
        """Get a drawing session by ID."""
        return self._active_sessions.get(session_id)
    
    def end_session(self, session_id: str) -> Optional[DrawingSession]:
        """End a drawing session."""
        session = self._active_sessions.get(session_id)
        if session:
            session.complete()
            # Optionally save to disk
            self._save_session(session)
            del self._active_sessions[session_id]
            logger.info(f"Ended drawing session {session_id}")
        
        return session
    
    def _save_session(self, session: DrawingSession):
        """Save session to disk."""
        try:
            session_file = self.data_dir / f"session_{session.id}.json"
            
            # Convert to serializable format
            session_data = {
                'id': session.id,
                'user_id': session.user_id,
                'topic': session.topic,
                'start_time': session.start_time.isoformat(),
                'end_time': session.end_time.isoformat() if session.end_time else None,
                'sketch_count': len(session.sketches),
                'metadata': session.metadata
            }
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            # Save individual sketches
            sketches_dir = self.data_dir / 'sketches' / session.id
            sketches_dir.mkdir(parents=True, exist_ok=True)
            
            for i, sketch in enumerate(session.sketches):
                if sketch.image_data:
                    sketch_path = sketches_dir / f"sketch_{i}_{sketch.id}.png"
                    with open(sketch_path, 'wb') as f:
                        f.write(sketch.image_data)
                    
                    if sketch.analysis:
                        analysis_path = sketches_dir / f"analysis_{i}_{sketch.id}.json"
                        with open(analysis_path, 'w') as f:
                            json.dump(sketch.analysis.to_dict(), f, indent=2)
            
            logger.info(f"Saved session {session.id} to disk")
            
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
    
    async def compare_drawings(
        self,
        drawing1: Union[str, Path, bytes, Image.Image],
        drawing2: Union[str, Path, bytes, Image.Image],
        options: Optional[RecognitionOptions] = None
    ) -> Dict[str, Any]:
        """
        Compare two drawings and find similarities/differences.
        
        Args:
            drawing1: First drawing
            drawing2: Second drawing
            options: Recognition options
            
        Returns:
            Comparison results
        """
        # Analyze both drawings
        analysis1 = await self.recognize_drawing(drawing1, options)
        analysis2 = await self.recognize_drawing(drawing2, options)
        
        # Compare elements
        elements1 = {e.id: e for e in analysis1.diagram.elements}
        elements2 = {e.id: e for e in analysis2.diagram.elements}
        
        # Find matching elements based on shape and position
        matches = []
        differences = []
        
        for id1, elem1 in elements1.items():
            best_match = None
            best_score = 0
            
            for id2, elem2 in elements2.items():
                if elem1.shape_type == elem2.shape_type:
                    # Calculate position similarity
                    center1 = elem1.bounding_box.center
                    center2 = elem2.bounding_box.center
                    
                    distance = center1.distance_to(center2)
                    size_diff = abs(elem1.bounding_box.area - elem2.bounding_box.area)
                    
                    # Normalize scores
                    position_score = 1.0 / (1.0 + distance / 100)
                    size_score = 1.0 / (1.0 + size_diff / 1000)
                    
                    combined_score = (position_score + size_score) / 2
                    
                    if combined_score > best_score:
                        best_score = combined_score
                        best_match = id2
            
            if best_score > 0.7:
                matches.append({
                    'element1_id': id1,
                    'element2_id': best_match,
                    'similarity': best_score
                })
            else:
                differences.append({
                    'element_id': id1,
                    'reason': 'No matching element found',
                    'confidence': best_score
                })
        
        # Compare text
        text1 = [r.text for r in analysis1.ocr_results]
        text2 = [r.text for r in analysis2.ocr_results]
        
        common_text = set(text1) & set(text2)
        unique_text1 = set(text1) - set(text2)
        unique_text2 = set(text2) - set(text1)
        
        return {
            'drawing1_analysis': analysis1.to_dict(),
            'drawing2_analysis': analysis2.to_dict(),
            'comparison': {
                'matching_elements': matches,
                'different_elements': differences,
                'common_text': list(common_text),
                'unique_text_drawing1': list(unique_text1),
                'unique_text_drawing2': list(unique_text2),
                'similarity_score': len(matches) / max(len(elements1), 1)
            }
        }
    
    async def extract_text_from_drawing(
        self,
        image: Union[str, Path, bytes, Image.Image],
        options: Optional[RecognitionOptions] = None
    ) -> str:
        """
        Extract all text from a drawing.
        
        Args:
            image: Input image
            options: Recognition options
            
        Returns:
            Extracted text
        """
        analysis = await self.recognize_drawing(image, options)
        
        # Combine all text
        texts = [r.text for r in analysis.ocr_results]
        return '\n'.join(texts)
    
    async def grade_drawing(
        self,
        student_drawing: Union[str, Path, bytes, Image.Image],
        expected_elements: List[Dict[str, Any]],
        options: Optional[RecognitionOptions] = None
    ) -> Dict[str, Any]:
        """
        Grade a student drawing against expected elements.
        
        Args:
            student_drawing: Student's drawing
            expected_elements: List of expected elements with descriptions
            options: Recognition options
            
        Returns:
            Grading results
        """
        # Analyze student drawing
        analysis = await self.recognize_drawing(student_drawing, options)
        
        found_elements = []
        missing_elements = []
        partial_elements = []
        
        for expected in expected_elements:
            expected_type = expected.get('type')
            expected_text = expected.get('text', '').lower()
            
            found = False
            best_confidence = 0
            
            for element in analysis.diagram.elements:
                # Check shape type
                if expected_type and element.shape_type.value == expected_type:
                    found = True
                    best_confidence = max(best_confidence, element.confidence)
                    
                    # Check text if expected
                    if expected_text and element.text:
                        if expected_text in element.text.lower():
                            found_elements.append({
                                'element': element.to_dict(),
                                'expected': expected,
                                'confidence': element.confidence
                            })
                        else:
                            partial_elements.append({
                                'element': element.to_dict(),
                                'expected': expected,
                                'reason': 'Wrong text',
                                'confidence': element.confidence * 0.5
                            })
                    else:
                        found_elements.append({
                            'element': element.to_dict(),
                            'expected': expected,
                            'confidence': element.confidence
                        })
            
            if not found:
                missing_elements.append(expected)
        
        # Calculate score
        total_elements = len(expected_elements)
        found_count = len(found_elements)
        partial_count = len(partial_elements)
        
        if total_elements > 0:
            score = (found_count + partial_count * 0.5) / total_elements * 100
        else:
            score = 0
        
        return {
            'score': round(score, 2),
            'found_elements': found_elements,
            'missing_elements': missing_elements,
            'partial_elements': partial_elements,
            'total_expected': total_elements,
            'found_count': found_count,
            'partial_count': partial_count,
            'analysis': analysis.to_dict()
        }
    
    async def detect_handwriting(
        self,
        image: Union[str, Path, bytes, Image.Image],
        options: Optional[RecognitionOptions] = None
    ) -> bool:
        """
        Detect if text in image is handwritten.
        
        Args:
            image: Input image
            options: Recognition options
            
        Returns:
            True if handwriting detected
        """
        analysis = await self.recognize_drawing(image, options)
        
        # Simple heuristic: handwritten text often has
        # - Lower confidence from OCR
        # - More variation in character spacing
        # - Non-horizontal baselines
        
        if not analysis.ocr_results:
            return False
        
        avg_confidence = np.mean([r.confidence for r in analysis.ocr_results])
        
        # Check for baseline variation
        y_positions = [r.bounding_box.y_min for r in analysis.ocr_results]
        y_std = np.std(y_positions) if y_positions else 0
        
        # Handwriting indicators
        is_handwritten = (
            avg_confidence < 0.7 or  # Lower OCR confidence
            y_std > 10  # More vertical variation
        )
        
        return is_handwritten
    
    async def cleanup(self):
        """Clean up resources."""
        self.executor.shutdown(wait=False)
        
        # Save all active sessions
        for session_id in list(self._active_sessions.keys()):
            self.end_session(session_id)
        
        logger.info("Cleaned up HandDrawingRecognizer resources")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()