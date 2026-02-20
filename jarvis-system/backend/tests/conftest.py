"""
Pytest Configuration and Fixtures
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import yaml
import os

@pytest.fixture
def sample_syllabus():
    """Create sample syllabus for testing"""
    return {
        "university": "MU",
        "semester": 3,
        "subjects": [
            {
                "name": "Data Structures",
                "topics": [
                    {"name": "Arrays", "weightage": 15},
                    {"name": "Linked Lists", "weightage": 20},
                    {"name": "Trees", "weightage": 25}
                ]
            }
        ]
    }

@pytest.fixture
def temp_data_dir():
    """Create temporary directory for test data"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
async def rag_engine(temp_data_dir, sample_syllabus):
    """Create RAG engine instance for testing"""
    from knowledge.rag_engine.syllabus_aware_rag import SyllabusAwareRAG
    
    # Setup directory structure for test
    syllabus_dir = temp_data_dir / "data" / "syllabus"
    os.makedirs(syllabus_dir, exist_ok=True)
    
    syllabus_path = syllabus_dir / "MU_computer_engineering_sem3.json"
    import json
    with open(syllabus_path, 'w') as f:
        json.dump(sample_syllabus, f)
    
    # Mocking some parts might be needed depending on depth
    engine = SyllabusAwareRAG(
        university_code="MU",
        semester=3,
        branch="computer_engineering"
    )
    
    yield engine
    
    # Cleanup (assuming engine has a close or similar)
    if hasattr(engine, 'close'):
        await engine.close()

@pytest.fixture
def sample_query():
    """Sample student query"""
    return "Explain array operations with examples"

@pytest.fixture
def sample_document():
    """Sample textbook content"""
    return """
    Arrays are fundamental data structures that store elements in contiguous memory locations.
    
    Common operations:
    1. Insertion: Adding an element at a specific position
    2. Deletion: Removing an element from a specific position
    3. Traversal: Accessing each element sequentially
    4. Searching: Finding an element's position
    
    Time Complexity:
    - Access: O(1)
    - Search: O(n)
    - Insertion: O(n)
    - Deletion: O(n)
    """
