"""
Study Controller for Handling Engineering Tutor RAG Setup and Engine Pipeline
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
from engine.engine import JarvisFiveLayerEngine
from brain.ai_brain import FullFledgedAIBrain

router = APIRouter()

# Global instances for the backend server
# We instantiate them lazily using a dependency or function to avoid asyncio loop issues on import
_engine_instance = None
_ai_brain_instance = None

def get_engine():
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = JarvisFiveLayerEngine()
    return _engine_instance

def get_ai_brain():
    global _ai_brain_instance
    if _ai_brain_instance is None:
        _ai_brain_instance = FullFledgedAIBrain(user_name="Prince")
    return _ai_brain_instance

class ContextRequest(BaseModel):
    query: str
    subject: Optional[str] = None

class ContextResponse(BaseModel):
    context: str

class QueryRequest(BaseModel):
    query: str
    marks: Optional[int] = None
    subject: Optional[str] = None
    topic: Optional[str] = None
    university: Optional[str] = None
    semester: Optional[int] = None

class QueryResponse(BaseModel):
    response: str
    sources: List[str]
    confidence: float
    suggested_topics: List[str]
    emotion_adapted: bool
    detected_emotion: str

@router.get("/session")
async def get_study_session():
    """
    Get current active study session parameters.
    """
    # Placeholder for study session status
    # Future integration: tie this to ai_brain.study manager
    return {"active": True, "duration_mins": 45, "current_topic": "General Engineering"}

@router.post("/context", response_model=ContextResponse)
async def get_context(request: ContextRequest):
    """
    Retrieve academic context using the Engineering Tutor RAG Setup.
    """
    try:
        brain = get_ai_brain()
        if not hasattr(brain, 'rag_engine') or not brain.rag_engine:
            raise HTTPException(status_code=500, detail="RAG Engine is not available.")
        
        context = brain.rag_engine.retrieve_context(request.query, subject=request.subject)
        return ContextResponse(context=context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a student query with the Enhanced 5-Layer Pipeline
    """
    try:
        eng = get_engine()
        # Process query asynchronously via the 5-layer engine
        result = await eng.process_student_query_async(
            query=request.query,
            subject=request.subject
        )
        
        proactive = result.get('proactive_suggestions', [])
        
        return QueryResponse(
            response=result.get('final_response', ""),
            sources=[], # Future: Extract sources from layer_metadata.cognitive
            confidence=result.get('confidence', 1.0),
            suggested_topics=proactive,
            emotion_adapted=True,
            detected_emotion=result.get('detected_emotion', 'neutral')
        )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))