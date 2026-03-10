"""Vision processing utilities for OCR and document analysis."""

import logging
from typing import Optional, Dict, List, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class OCRProcessor:
    """
    Optical Character Recognition processor for hand-drawn and printed text.
    Integrates with handwriting recognition and text extraction.
    """
    
    def __init__(self):
        """Initialize OCR processor."""
        self.supported_formats = ['png', 'jpg', 'jpeg', 'bmp', 'gif', 'pdf']
    
    def extract_text(self, image_path: str) -> Optional[str]:
        """
        Extract text from image using OCR.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Extracted text or None
        """
        try:
            import pytesseract
            from PIL import Image
            
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            logger.info(f"Extracted text from {image_path}: {len(text)} chars")
            return text
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            return None
    
    def extract_text_with_confidence(self, image_path: str) -> Optional[Dict]:
        """
        Extract text with confidence scores.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Dictionary with text and confidence scores or None
        """
        try:
            import pytesseract
            from PIL import Image
            
            image = Image.open(image_path)
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            confidence = np.array(data['conf']).astype(int)
            valid_confidence = confidence[confidence > 0]
            avg_confidence = np.mean(valid_confidence) if len(valid_confidence) > 0 else 0
            
            text = pytesseract.image_to_string(image)
            
            return {
                "text": text,
                "confidence": float(avg_confidence),
                "word_count": len(text.split()),
                "character_count": len(text)
            }
        except Exception as e:
            logger.error(f"Error extracting text with confidence: {str(e)}")
            return None
    
    def extract_structured_text(self, image_path: str) -> Optional[List[Dict]]:
        """
        Extract text with position information.
        
        Args:
            image_path: Path to image file
        
        Returns:
            List of text regions with positions or None
        """
        try:
            import pytesseract
            from PIL import Image
            
            image = Image.open(image_path)
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            regions = []
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 0:
                    region = {
                        "text": data['text'][i],
                        "x": int(data['left'][i]),
                        "y": int(data['top'][i]),
                        "width": int(data['width'][i]),
                        "height": int(data['height'][i]),
                        "confidence": int(data['conf'][i])
                    }
                    regions.append(region)
            
            logger.info(f"Extracted {len(regions)} text regions from {image_path}")
            return regions
        except Exception as e:
            logger.error(f"Error extracting structured text: {str(e)}")
            return None


class DiagramDetector:
    """
    Detects and analyzes geometric shapes and diagrams in images.
    Used for identifying visual learning content.
    """
    
    def __init__(self):
        """Initialize diagram detector."""
        self.shape_types = ['circle', 'rectangle', 'triangle', 'line', 'polygon']
    
    def detect_shapes(self, image_path: str) -> Optional[List[Dict]]:
        """
        Detect geometric shapes in image.
        
        Args:
            image_path: Path to image file
        
        Returns:
            List of detected shapes or None
        """
        try:
            import cv2
            
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Could not read image: {image_path}")
                return None
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            shapes = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < 100:  # Filter small noise
                    continue
                
                perimeter = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
                
                shape_type = self._classify_shape(approx)
                x, y, w, h = cv2.boundingRect(contour)
                
                shapes.append({
                    "type": shape_type,
                    "x": int(x),
                    "y": int(y),
                    "width": int(w),
                    "height": int(h),
                    "area": float(area),
                    "vertices": len(approx)
                })
            
            logger.info(f"Detected {len(shapes)} shapes in {image_path}")
            return shapes
        except Exception as e:
            logger.error(f"Error detecting shapes: {str(e)}")
            return None
    
    def _classify_shape(self, approx) -> str:
        """
        Classify shape based on vertices.
        
        Args:
            approx: Approximated contour
        
        Returns:
            Shape type string
        """
        vertices = len(approx)
        
        if vertices == 3:
            return "triangle"
        elif vertices == 4:
            return "rectangle"
        elif vertices > 4:
            return "polygon"
        else:
            return "unknown"
    
    def detect_lines(self, image_path: str) -> Optional[List[Tuple]]:
        """
        Detect lines in image using Hough Line Transform.
        
        Args:
            image_path: Path to image file
        
        Returns:
            List of detected lines or None
        """
        try:
            import cv2
            
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
            
            if lines is None:
                return []
            
            detected_lines = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                detected_lines.append((int(x1), int(y1), int(x2), int(y2)))
            
            logger.info(f"Detected {len(detected_lines)} lines in {image_path}")
            return detected_lines
        except Exception as e:
            logger.error(f"Error detecting lines: {str(e)}")
            return None
