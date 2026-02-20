import os
import re
from typing import Any, Dict, Optional
from pydantic import BaseModel, EmailStr, validator, ValidationError

# --- Input Validation Functions ---

def validate_email(email: str) -> bool:
    """Basic email format validation."""
    if not isinstance(email, str):
        return False
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email))

def validate_file_path(filepath: str, allowed_extensions: list = None) -> bool:
    """
    Validates if a file path is safe and optionally checks its extension.
    Does not check if the file exists, only if the path is valid.
    """
    if not isinstance(filepath, str) or not filepath:
        return False
        
    # Prevent directory traversal attacks
    if ".." in filepath or filepath.startswith("/etc/"):
        return False
        
    if allowed_extensions:
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in allowed_extensions:
            return False
            
    return True


# --- Schema Validators for API Requests (Pydantic Base) ---

class BaseAPIRequest(BaseModel):
    """Base schema for API requests with common validation."""
    
    @validator('*', pre=True)
    def strip_strings(cls, v):
        """Strip whitespace from all string fields."""
        if isinstance(v, str):
            return v.strip()
        return v

class StudyQueryRequest(BaseAPIRequest):
    """Schema for a student asking a question."""
    query: str
    subject: Optional[str] = None
    
    @validator('query')
    def query_must_not_be_empty(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Query must contain at least 2 characters')
        return v

def validate_request_schema(schema_class: type[BaseModel], data: Dict[str, Any]) -> tuple[bool, Optional[BaseModel], Optional[str]]:
    """Validates data against a Pydantic schema class."""
    try:
        validated_data = schema_class(**data)
        return True, validated_data, None
    except ValidationError as e:
        return False, None, str(e)


# --- Data Type Converters ---

def to_int(value: Any, default: int = 0) -> int:
    """Safely converts a value to an integer."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def to_bool(value: Any) -> bool:
    """
    Converts a value to boolean.
    Handles 'true', '1', 'yes', 'on' strings.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 't', 'y', 'yes', 'on')
    return bool(value)


# --- Sanitization Functions ---

def sanitize_filename(filename: str) -> str:
    """
    Removes potentially dangerous characters from a filename.
    """
    if not isinstance(filename, str):
        return "unnamed_file"
    # Keep only alphanumeric, dash, underscore, and dot
    clean = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
    # Ensure it's not empty and no consecutive dots
    clean = re.sub(r'\.+', '.', clean).strip('_')
    return clean if clean else "unnamed_file"

def sanitize_html(text: str) -> str:
    """Basic HTML tag stripping to prevent XSS."""
    if not isinstance(text, str):
        return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)
