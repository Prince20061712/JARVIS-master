"""Helper functions for common operations."""

import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Any, List, Dict
import logging

logger = logging.getLogger(__name__)


def generate_id() -> str:
    """
    Generate a unique ID.
    
    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime object to string.
    
    Args:
        dt: Datetime object
        format_str: Format string
    
    Returns:
        Formatted datetime string
    """
    return dt.strftime(format_str)


def parse_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """
    Parse datetime string to datetime object.
    
    Args:
        date_str: Date string
        format_str: Format string
    
    Returns:
        Datetime object
    """
    return datetime.strptime(date_str, format_str)


def calculate_interval(current_interval: int, ease_factor: float, repetitions: int) -> int:
    """
    Calculate next review interval using SM-2 algorithm.
    
    Args:
        current_interval: Current interval in days
        ease_factor: Ease factor (1.3-2.5)
        repetitions: Number of repetitions
    
    Returns:
        Next interval in days
    """
    if repetitions == 0:
        return 1
    elif repetitions == 1:
        return 3
    else:
        return round(current_interval * ease_factor)


def calculate_ease_factor(
    ease_factor: float,
    quality_response: int
) -> float:
    """
    Calculate new ease factor using SM-2 algorithm.
    
    Args:
        ease_factor: Current ease factor
        quality_response: Quality rating (0-5)
    
    Returns:
        New ease factor
    """
    new_factor = ease_factor + (0.1 - (5 - quality_response) * (0.08 + (5 - quality_response) * 0.02))
    return max(1.3, new_factor)  # Ensure minimum factor of 1.3


def hash_string(s: str) -> str:
    """
    Generate SHA256 hash of a string.
    
    Args:
        s: String to hash
    
    Returns:
        Hex digest
    """
    return hashlib.sha256(s.encode()).hexdigest()


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk
        overlap: Overlap between chunks
    
    Returns:
        List of text chunks
    """
    tokens = text.split()
    chunks = []
    start = 0
    
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk = ' '.join(tokens[start:end])
        chunks.append(chunk)
        start = end - overlap
    
    return chunks


def merge_dicts(*dicts: Dict) -> Dict:
    """
    Merge multiple dictionaries.
    
    Args:
        *dicts: Variable number of dictionaries
    
    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


def get_nested(obj: Dict, path: str, default: Any = None) -> Any:
    """
    Get nested dictionary value using dot notation.
    
    Args:
        obj: Dictionary object
        path: Dot-separated path (e.g., "metadata.author")
        default: Default value if not found
    
    Returns:
        Value at path or default
    """
    keys = path.split('.')
    current = obj
    
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
            if current is None:
                return default
        else:
            return default
    
    return current
