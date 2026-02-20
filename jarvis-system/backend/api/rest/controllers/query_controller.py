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
    from core.engine import JARVISCore
    return JARVISCore()

@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a student query with syllabus-aware RAG
    """
    try:
        engine = get_engine()
        
        # Process query
        result = await engine.process_query(
            query=request.query,
            marks=request.marks,
            subject=request.subject,
            topic=request.topic
        )
        
        return QueryResponse(
            response=result.get('response', ""),
            sources=result.get('sources', []),
            confidence=result.get('confidence', 0.0),
            suggested_topics=result.get('suggested_topics', []),
            emotion_adapted=result.get('emotion_adapted', False)
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
        async for token in engine.stream_query(request.query):
            yield f"data: {token}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
