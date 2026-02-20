import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

# --- Text Processing Utilities ---

def clean_text(text: str) -> str:
    """Removes extra whitespace and non-printable characters."""
    if not isinstance(text, str):
        return ""
    # Remove excessive newlines and spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_keywords(text: str, min_length: int = 4) -> List[str]:
    """Extracts simple unique words from text (naive approach)."""
    if not text:
        return []
    cleaned = re.sub(r'[^\w\s]', '', text.lower())
    words = cleaned.split()
    return list(set(word for word in words if len(word) >= min_length))


# --- File Operations ---

def safe_read(filepath: str) -> Optional[str]:
    """Reads a file safely, returning None if not found or corrupted."""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return None

def safe_write(filepath: str, content: str) -> bool:
    """Writes to a file safely, ensuring directory exists."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing to file {filepath}: {e}")
        return False

def get_file_extension(filename: str) -> str:
    """Returns lowercase file extension without dot."""
    ext = os.path.splitext(filename)[1]
    return ext.lower().lstrip('.')


# --- Time Utilities ---

def format_timestamp(dt: datetime = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Formats a datetime object to string."""
    if dt is None:
        dt = datetime.now()
    return dt.strftime(fmt)

def time_ago(dt: datetime) -> str:
    """Returns a string representing the time elapsed since dt."""
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        return f"{int(seconds // 60)} minutes ago"
    elif seconds < 86400:
        return f"{int(seconds // 3600)} hours ago"
    else:
        return f"{int(seconds // 86400)} days ago"


# --- Data Structure Helpers ---

def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """Recursively merges dict2 into dict1."""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result

def flatten_list(nested_list: List[Any]) -> List[Any]:
    """Flattens a list of lists."""
    flat = []
    for item in nested_list:
        if isinstance(item, list):
            flat.extend(flatten_list(item))
        else:
            flat.append(item)
    return flat
