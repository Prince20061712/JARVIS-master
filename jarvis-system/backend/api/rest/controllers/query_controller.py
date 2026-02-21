"""
Query Controller for Handling Student Questions
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio

router = APIRouter()

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

def get_engine():
    """Dependency to get engine instance. In a real app, this would be injected."""
    from engine import JarvisFiveLayerEngine
    return JarvisFiveLayerEngine()

@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a student query with syllabus-aware RAG
    """
    try:
        engine = get_engine()
        
        # Process query
        result = engine.process_student_query(
            query=request.query,
            subject=request.subject
        )
        
        proactive = result.get('proactive_interventions', [])
        if not proactive:
            proactive = []
            
        return QueryResponse(
            response=result.get('final_response', ""),
            sources=[],
            confidence=1.0,
            suggested_topics=proactive,
            emotion_adapted=True
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query/stream")
async def stream_query(request: QueryRequest):
    """
    Stream a query response token by token
    """
    engine = get_engine()
    
    async def generate():
        if hasattr(engine, 'stream_query'):
            async for token in engine.stream_query(request.query):
                yield f"data: {token}\n\n"
        else:
            result = engine.process_student_query(request.query, request.subject)
            yield f"data: {result.get('final_response', '')}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
