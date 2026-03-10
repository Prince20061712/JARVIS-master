"""
Viva (oral exam) API controller handling session management, adaptive questioning,
and real-time communication via WebSockets.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from enum import Enum

from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    Query,
    Path as PathParam,
    WebSocket,
    WebSocketDisconnect,
    BackgroundTasks
)
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, field_validator
import numpy as np

from ..viva_engine.viva_session import (
    VivaSession,
    VivaMode,
    Question,
    Answer,
    VivaState,
    SessionConfig
)
from ..viva_engine.adaptive_questioner import AdaptiveQuestioner, QuestionDifficulty
from ..analytics.learning_patterns import LearningPatterns
from ..scanner import SubjectScanner

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/viva", tags=["viva"])

# Global instances
_active_sessions: Dict[str, VivaSession] = {}
_websocket_connections: Dict[str, Set[WebSocket]] = {}
_adaptive_questioner: Optional[AdaptiveQuestioner] = None
_learning_patterns: Optional[LearningPatterns] = None


# Dependency injection
async def get_adaptive_questioner() -> AdaptiveQuestioner:
    """Dependency to get adaptive questioner instance."""
    global _adaptive_questioner
    if _adaptive_questioner is None:
        _adaptive_questioner = AdaptiveQuestioner()
    return _adaptive_questioner


async def get_learning_patterns() -> LearningPatterns:
    """Dependency to get learning patterns instance."""
    global _learning_patterns
    if _learning_patterns is None:
        project_root = Path(__file__).parent.parent.parent
        data_dir = project_root / "data" / "analytics"
        _learning_patterns = LearningPatterns(data_dir=data_dir)
    return _learning_patterns


# Pydantic models

class VivaModeEnum(str, Enum):
    """Viva modes for API."""
    PRACTICE = "practice"
    TIMED = "timed"
    ADAPTIVE = "adaptive"
    MOCK = "mock"
    RESEARCH = "research"


class QuestionDifficultyEnum(str, Enum):
    """Question difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class CreateVivaSessionRequest(BaseModel):
    """Request model for creating a viva session."""
    user_id: str = Field(..., min_length=1, max_length=100)
    topic: str = Field(..., min_length=1, max_length=200)
    subtopics: List[str] = Field(default_factory=list)
    mode: VivaModeEnum = VivaModeEnum.PRACTICE
    duration_minutes: Optional[int] = Field(None, ge=5, le=180)
    total_questions: Optional[int] = Field(None, ge=1, le=100)
    difficulty: QuestionDifficultyEnum = QuestionDifficultyEnum.MEDIUM
    include_diagrams: bool = False
    allow_skip: bool = True
    enable_emotion_tracking: bool = True
    config: Optional[Dict[str, Any]] = None
    
    @field_validator('duration_minutes')
    def validate_duration(cls, v, values):
        if values.get('mode') == VivaModeEnum.TIMED and v is None:
            raise ValueError('Timed mode requires duration_minutes')
        return v
    
    @field_validator('total_questions')
    def validate_questions(cls, v, values):
        if values.get('mode') == VivaModeEnum.MOCK and v is None:
            raise ValueError('Mock mode requires total_questions')
        return v


class StartSubjectVivaRequest(BaseModel):
    """Request model for starting viva from subject folder."""
    user_id: str = Field(..., min_length=1, max_length=100)
    subject_name: str = Field(..., min_length=1, max_length=100)
    mode: VivaModeEnum = VivaModeEnum.ADAPTIVE
    total_questions: int = Field(10, ge=1, le=50)
    difficulty: QuestionDifficultyEnum = QuestionDifficultyEnum.MEDIUM


class SubmitAnswerRequest(BaseModel):
    """Request model for submitting an answer."""
    session_id: str = Field(..., min_length=1)
    question_id: str = Field(..., min_length=1)
    answer_text: str = Field(..., min_length=1)
    response_time: float = Field(..., gt=0, le=3600)
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    emotional_state: Optional[Dict[str, Any]] = None
    attachments: Optional[List[str]] = None


class SessionActionRequest(BaseModel):
    """Request model for session actions."""
    session_id: str = Field(..., min_length=1)
    action: str = Field(..., pattern="^(pause|resume|skip|end)$")


class SessionResponse(BaseModel):
    """Response model for session details."""
    session_id: str
    user_id: str
    topic: str
    mode: str
    status: str
    start_time: str
    end_time: Optional[str]
    questions_asked: int
    questions_answered: int
    correct_answers: int
    current_score: float
    current_difficulty: str
    estimated_progress: float
    time_remaining: Optional[int]
    questions_remaining: Optional[int]


# API Endpoints

@router.post("/sessions", response_model=SessionResponse)
async def create_viva_session(
    request: CreateVivaSessionRequest,
    background_tasks: BackgroundTasks,
    questioner: AdaptiveQuestioner = Depends(get_adaptive_questioner),
    patterns: LearningPatterns = Depends(get_learning_patterns)
) -> Dict[str, Any]:
    """
    Create a new viva session.
    
    Args:
        request: Session creation request
        background_tasks: FastAPI background tasks
        questioner: Adaptive questioner instance
        patterns: Learning patterns instance
        
    Returns:
        Created session details
    """
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create session config
        config = SessionConfig(
            mode=VivaMode(request.mode.value),
            duration_minutes=request.duration_minutes,
            total_questions=request.total_questions,
            initial_difficulty=QuestionDifficulty(request.difficulty.value),
            include_diagrams=request.include_diagrams,
            allow_skip=request.allow_skip,
            enable_emotion_tracking=request.enable_emotion_tracking,
            custom_config=request.config or {}
        )
        
        # Get user's weak topics for adaptive mode
        weak_topics = []
        if request.mode == VivaModeEnum.ADAPTIVE:
            weaknesses = patterns.analyze_weaknesses(request.user_id)
            weak_topics = [t for t, _ in weaknesses.weak_topics[:5]]
        
        # Create session
        session = VivaSession(
            session_id=session_id,
            user_id=request.user_id,
            topic=request.topic,
            subtopics=request.subtopics or weak_topics,
            config=config,
            questioner=questioner
        )
        
        # Store session
        _active_sessions[session_id] = session
        
        # Preload questions in background
        background_tasks.add_task(
            preload_questions_background,
            session_id,
            questioner
        )
        
        logger.info(f"Created viva session {session_id} for user {request.user_id}")
        
        return SessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            topic=session.topic,
            mode=session.config.mode.value,
            status=session.state.status.value,
            start_time=session.state.start_time.isoformat(),
            end_time=session.state.end_time.isoformat() if session.state.end_time else None,
            questions_asked=session.state.questions_asked,
            questions_answered=session.state.questions_answered,
            correct_answers=session.state.correct_answers,
            current_score=session.state.current_score,
            current_difficulty=session.state.current_difficulty.value,
            estimated_progress=session.get_progress(),
            time_remaining=session.get_time_remaining(),
            questions_remaining=session.get_questions_remaining()
        )
        
    except Exception as e:
        logger.error(f"Error creating viva session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/from-subject", response_model=SessionResponse)
async def create_subject_viva_session(
    request: StartSubjectVivaRequest,
    background_tasks: BackgroundTasks,
    questioner: AdaptiveQuestioner = Depends(get_adaptive_questioner),
    patterns: LearningPatterns = Depends(get_learning_patterns)
) -> Dict[str, Any]:
    """
    Start a viva session from a subject folder.
    
    Args:
        request: Subject viva creation request
        background_tasks: FastAPI background tasks
        questioner: Adaptive questioner instance
        patterns: Learning patterns instance
        
    Returns:
        Created session details
    """
    try:
        # Check if subject exists
        scanner = SubjectScanner()
        subjects = scanner.scan_all_subjects()
        
        if request.subject_name not in subjects:
            raise HTTPException(status_code=404, detail=f"Subject folder '{request.subject_name}' not found")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create config
        config = SessionConfig(
            mode=VivaMode(request.mode.value),
            total_questions=request.total_questions,
            initial_difficulty=QuestionDifficulty(request.difficulty.value),
            adaptive_difficulty=True
        )
        
        # Create session
        session = VivaSession(
            session_id=session_id,
            user_id=request.user_id,
            topic=request.subject_name,
            subtopics=[],
            config=config,
            questioner=questioner
        )
        
        # Store session
        _active_sessions[session_id] = session
        
        # Process subject in background and generate dynamic questions
        background_tasks.add_task(
            generate_subject_viva_background,
            session_id,
            request.subject_name,
            request.total_questions,
            questioner
        )
        
        logger.info(f"Created subject-based viva session {session_id} for user {request.user_id}")
        
        return SessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            topic=session.topic,
            mode=session.config.mode.value,
            status=session.state.status.value,
            start_time=session.state.start_time.isoformat(),
            end_time=None,
            questions_asked=0,
            questions_answered=0,
            correct_answers=0,
            current_score=0.0,
            current_difficulty=session.state.current_difficulty.value,
            estimated_progress=0.0,
            time_remaining=None,
            questions_remaining=request.total_questions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating subject viva session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/from-subject", response_model=SessionResponse)
async def create_subject_viva_session(
    request: StartSubjectVivaRequest,
    background_tasks: BackgroundTasks,
    questioner: AdaptiveQuestioner = Depends(get_adaptive_questioner),
    patterns: LearningPatterns = Depends(get_learning_patterns)
) -> Dict[str, Any]:
    """
    Start a viva session from a subject folder.
    
    Args:
        request: Subject viva creation request
        background_tasks: FastAPI background tasks
        questioner: Adaptive questioner instance
        patterns: Learning patterns instance
        
    Returns:
        Created session details
    """
    try:
        # Check if subject exists
        scanner = SubjectScanner()
        subjects = scanner.scan_all_subjects()
        
        if request.subject_name not in subjects:
            raise HTTPException(status_code=404, detail=f"Subject folder '{request.subject_name}' not found")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create config
        config = SessionConfig(
            mode=VivaMode(request.mode.value),
            total_questions=request.total_questions,
            initial_difficulty=QuestionDifficulty(request.difficulty.value),
            adaptive_difficulty=True
        )
        
        # Create session
        session = VivaSession(
            session_id=session_id,
            user_id=request.user_id,
            topic=request.subject_name,
            subtopics=[],
            config=config,
            questioner=questioner
        )
        
        # Store session
        _active_sessions[session_id] = session
        
        # Process subject in background and generate dynamic questions
        background_tasks.add_task(
            generate_subject_viva_background,
            session_id,
            request.subject_name,
            request.total_questions,
            questioner
        )
        
        logger.info(f"Created subject-based viva session {session_id} for user {request.user_id}")
        
        return SessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            topic=session.topic,
            mode=session.config.mode.value,
            status=session.state.status.value,
            start_time=session.state.start_time.isoformat(),
            end_time=None,
            questions_asked=0,
            questions_answered=0,
            correct_answers=0,
            current_score=0.0,
            current_difficulty=session.state.current_difficulty.value,
            estimated_progress=0.0,
            time_remaining=None,
            questions_remaining=request.total_questions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating subject viva session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str = PathParam(..., min_length=1)
) -> Dict[str, Any]:
    """
    Get session details.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session details
    """
    session = _active_sessions.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        session_id=session.session_id,
        user_id=session.user_id,
        topic=session.topic,
        mode=session.config.mode.value,
        status=session.state.status.value,
        start_time=session.state.start_time.isoformat(),
        end_time=session.state.end_time.isoformat() if session.state.end_time else None,
        questions_asked=session.state.questions_asked,
        questions_answered=session.state.questions_answered,
        correct_answers=session.state.correct_answers,
        current_score=session.state.current_score,
        current_difficulty=session.state.current_difficulty.value,
        estimated_progress=session.get_progress(),
        time_remaining=session.get_time_remaining(),
        questions_remaining=session.get_questions_remaining()
    )


@router.get("/sessions")
async def list_sessions(
    user_id: str = Query(..., min_length=1),
    active_only: bool = Query(False)
) -> List[Dict[str, Any]]:
    """
    List sessions for a user.
    
    Args:
        user_id: User identifier
        active_only: Only return active sessions
        
    Returns:
        List of sessions
    """
    sessions = []
    
    for session in _active_sessions.values():
        if session.user_id == user_id:
            if active_only and session.state.status != VivaState.ACTIVE:
                continue
                
            sessions.append({
                "session_id": session.session_id,
                "topic": session.topic,
                "mode": session.config.mode.value,
                "status": session.state.status.value,
                "start_time": session.state.start_time.isoformat(),
                "progress": session.get_progress(),
                "score": session.state.current_score
            })
    
    return sessions


@router.post("/sessions/{session_id}/start")
async def start_session(
    session_id: str = PathParam(..., min_length=1)
) -> Dict[str, Any]:
    """
    Start a viva session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        First question
    """
    session = _active_sessions.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        question = await session.start()
        
        return {
            "status": "started",
            "session_id": session_id,
            "first_question": question.model_dump() if question else None,
            "total_questions": session.config.total_questions,
            "duration_minutes": session.config.duration_minutes
        }
        
    except Exception as e:
        logger.error(f"Error starting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/answer")
async def submit_answer(
    session_id: str = PathParam(..., min_length=1),
    request: SubmitAnswerRequest = None
) -> Dict[str, Any]:
    """
    Submit an answer for a question.
    
    Args:
        session_id: Session identifier
        request: Answer submission request
        
    Returns:
        Feedback and next question
    """
    session = _active_sessions.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        # Create answer object
        answer = Answer(
            question_id=request.question_id,
            answer_text=request.answer_text,
            response_time=request.response_time,
            confidence=request.confidence,
            emotional_state=request.emotional_state,
            attachments=request.attachments
        )
        
        # Submit answer
        feedback, next_question = await session.answer_question(answer)
        
        # Notify WebSocket clients
        await notify_session_update(session_id, {
            "type": "answer_processed",
            "question_id": request.question_id,
            "feedback": feedback.model_dump() if feedback else None,
            "next_question_available": next_question is not None
        })
        
        response = {
            "status": "success",
            "feedback": feedback.model_dump() if feedback else None,
            "current_score": session.state.current_score,
            "questions_remaining": session.get_questions_remaining(),
            "time_remaining": session.get_time_remaining()
        }
        
        if next_question:
            response["next_question"] = next_question.model_dump()
        
        return response
        
    except Exception as e:
        logger.error(f"Error submitting answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/action")
async def session_action(
    session_id: str = PathParam(..., min_length=1),
    request: SessionActionRequest = None
) -> Dict[str, Any]:
    """
    Perform an action on a session.
    
    Args:
        session_id: Session identifier
        request: Action request
        
    Returns:
        Action result
    """
    session = _active_sessions.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        if request.action == "pause":
            session.pause()
            message = "Session paused"
        elif request.action == "resume":
            session.resume()
            message = "Session resumed"
        elif request.action == "skip":
            await session.skip_question()
            message = "Question skipped"
        elif request.action == "end":
            summary = await session.end()
            
            # Notify WebSocket clients
            await notify_session_update(session_id, {
                "type": "session_ended",
                "summary": summary
            })
            
            # Clean up session after delay
            asyncio.create_task(cleanup_session(session_id, delay=300))
            
            return {
                "status": "ended",
                "message": "Session ended",
                "summary": summary
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")
        
        # Notify WebSocket clients
        await notify_session_update(session_id, {
            "type": "session_action",
            "action": request.action,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "status": "success",
            "message": message,
            "session_state": session.state.status.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/history")
async def get_session_history(
    session_id: str = PathParam(..., min_length=1)
) -> List[Dict[str, Any]]:
    """
    Get question/answer history for a session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session history
    """
    session = _active_sessions.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    history = []
    for q in session.state.question_history:
        history.append({
            "question": q.question.model_dump() if q.question else None,
            "answer": q.answer.model_dump() if q.answer else None,
            "feedback": q.feedback.model_dump() if q.feedback else None,
            "timestamp": q.timestamp.isoformat()
        })
    
    return history


@router.get("/sessions/{session_id}/summary")
async def get_session_summary(
    session_id: str = PathParam(..., min_length=1)
) -> Dict[str, Any]:
    """
    Get comprehensive session summary.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session summary with analytics
    """
    session = _active_sessions.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    summary = await session.get_summary()
    return summary


@router.post("/sessions/{session_id}/feedback")
async def submit_session_feedback(
    session_id: str = PathParam(..., min_length=1),
    rating: int = Query(..., ge=1, le=5),
    comments: Optional[str] = Query(None),
    patterns: LearningPatterns = Depends(get_learning_patterns)
) -> Dict[str, str]:
    """
    Submit feedback for a completed session.
    
    Args:
        session_id: Session identifier
        rating: Session rating (1-5)
        comments: Optional comments
        patterns: Learning patterns instance
        
    Returns:
        Feedback confirmation
    """
    session = _active_sessions.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        # Store feedback in analytics
        # This would be implemented in LearningPatterns
        
        logger.info(f"Received feedback for session {session_id}: rating={rating}")
        
        return {
            "status": "success",
            "message": "Feedback recorded"
        }
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time communication

@router.websocket("/ws/{session_id}")
async def viva_websocket(
    websocket: WebSocket,
    session_id: str,
    user_id: str = Query(...)
):
    """
    WebSocket endpoint for real-time viva session communication.
    
    Args:
        websocket: WebSocket connection
        session_id: Session identifier
        user_id: User identifier
    """
    await websocket.accept()
    
    # Add to connections
    if session_id not in _websocket_connections:
        _websocket_connections[session_id] = set()
    _websocket_connections[session_id].add(websocket)
    
    logger.info(f"WebSocket connected for session {session_id}, user {user_id}")
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # Handle incoming messages
        while True:
            data = await websocket.receive_json()
            command = data.get('command')
            
            if command == 'get_status':
                # Get session status
                session = _active_sessions.get(session_id)
                if session:
                    await websocket.send_json({
                        "type": "status",
                        "data": {
                            "status": session.state.status.value,
                            "questions_asked": session.state.questions_asked,
                            "questions_answered": session.state.questions_answered,
                            "current_score": session.state.current_score,
                            "time_remaining": session.get_time_remaining(),
                            "progress": session.get_progress()
                        }
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Session not found"
                    })
                    
            elif command == 'heartbeat':
                # Respond to heartbeat
                await websocket.send_json({
                    "type": "heartbeat_ack",
                    "timestamp": datetime.now().isoformat()
                })
                
            elif command == 'emotion_update':
                # Update emotional state
                emotion_data = data.get('emotion', {})
                session = _active_sessions.get(session_id)
                if session:
                    session.update_emotional_state(emotion_data)
                    
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown command: {command}"
                })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    finally:
        # Remove from connections
        if session_id in _websocket_connections:
            _websocket_connections[session_id].discard(websocket)
            if not _websocket_connections[session_id]:
                del _websocket_connections[session_id]
        await websocket.close()


# Streaming endpoint for question generation

@router.get("/sessions/{session_id}/stream")
async def stream_questions(
    session_id: str = PathParam(..., min_length=1)
):
    """
    Stream questions as they are generated.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Streaming response with questions
    """
    session = _active_sessions.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    async def generate():
        try:
            while session.state.status == VivaState.ACTIVE:
                # Get next question
                question = await session.get_next_question()
                
                if question:
                    yield f"data: {json.dumps(question.model_dump())}\n\n"
                
                # Wait before next question
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# Analytics endpoints

@router.get("/analytics/topics/{topic}")
async def get_topic_analytics(
    topic: str = PathParam(..., min_length=1),
    user_id: str = Query(..., min_length=1),
    patterns: LearningPatterns = Depends(get_learning_patterns)
) -> Dict[str, Any]:
    """
    Get analytics for a specific topic.
    
    Args:
        topic: Topic name
        user_id: User identifier
        patterns: Learning patterns instance
        
    Returns:
        Topic analytics
    """
    try:
        # Get retention curve
        curve = patterns.generate_retention_curve(user_id, topic)
        
        # Get performance data
        heatmap = patterns.generate_performance_heatmap(user_id, 'month')
        topic_data = next(
            (t for t in heatmap.get('topics', []) if t['topic'] == topic),
            None
        )
        
        return {
            "topic": topic,
            "retention_curve": {
                "forgetting_rate": curve.forgetting_rate,
                "predicted_forget_date": curve.predicted_forget_date.isoformat() if curve.predicted_forget_date else None,
                "days_until_50": curve.days_until_forget(50)
            },
            "performance": topic_data,
            "recommendations": patterns.get_study_recommendations(user_id, limit=3)
        }
        
    except Exception as e:
        logger.error(f"Error getting topic analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/recommendations")
async def get_recommendations(
    user_id: str = Query(..., min_length=1),
    patterns: LearningPatterns = Depends(get_learning_patterns)
) -> Dict[str, Any]:
    """
    Get study recommendations based on viva performance.
    
    Args:
        user_id: User identifier
        patterns: Learning patterns instance
        
    Returns:
        Study recommendations
    """
    try:
        recommendations = patterns.get_study_recommendations(user_id)
        weaknesses = patterns.analyze_weaknesses(user_id)
        
        return {
            "recommendations": recommendations,
            "weak_topics": [t for t, _ in weaknesses.weak_topics[:5]],
            "strong_topics": [t for t, _ in weaknesses.strong_topics[:3]],
            "improvement_pace": weaknesses.improvement_pace,
            "critical_gaps": weaknesses.critical_gaps
        }
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Background tasks

async def preload_questions_background(
    session_id: str,
    questioner: AdaptiveQuestioner
):
    """
    Preload questions for a session in the background.
    
    Args:
        session_id: Session identifier
        questioner: Adaptive questioner instance
    """
    try:
        session = _active_sessions.get(session_id)
        if session:
            await session.preload_questions(questioner)
            logger.info(f"Preloaded questions for session {session_id}")
            
    except Exception as e:
        logger.error(f"Error preloading questions for session {session_id}: {e}")


async def notify_session_update(session_id: str, data: Dict[str, Any]):
    """
    Notify all WebSocket clients about session updates.
    
    Args:
        session_id: Session identifier
        data: Update data
    """
    if session_id in _websocket_connections:
        dead_connections = set()
        
        for websocket in _websocket_connections[session_id]:
            try:
                await websocket.send_json(data)
            except Exception:
                dead_connections.add(websocket)
        
        # Remove dead connections
        _websocket_connections[session_id] -= dead_connections


async def cleanup_session(session_id: str, delay: int = 300):
    """
    Clean up a session after delay.
    
    Args:
        session_id: Session identifier
        delay: Delay in seconds before cleanup
    """
    await asyncio.sleep(delay)
    
    if session_id in _active_sessions:
        del _active_sessions[session_id]
        logger.info(f"Cleaned up session {session_id}")


# Periodic cleanup task

@router.on_event("startup")
async def startup_event():
    """Startup event handler."""
    asyncio.create_task(periodic_cleanup())


async def periodic_cleanup():
    """Periodically clean up old sessions."""
    while True:
        try:
            now = datetime.now()
            expired_sessions = []
            
            for session_id, session in _active_sessions.items():
                # Clean up sessions older than 24 hours
                if (now - session.state.start_time) > timedelta(hours=24):
                    expired_sessions.append(session_id)
                    
                # Clean up ended sessions older than 1 hour
                elif session.state.status == VivaState.ENDED:
                    if session.state.end_time and (now - session.state.end_time) > timedelta(hours=1):
                        expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del _active_sessions[session_id]
                logger.info(f"Cleaned up expired session {session_id}")
                
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")
            
        await asyncio.sleep(3600)  # Run every hour


# Health check

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(_active_sessions),
        "websocket_connections": sum(len(conns) for conns in _websocket_connections.values()),
        "modules": {
            "viva_engine": "loaded",
            "adaptive_questioner": "loaded" if _adaptive_questioner else "not_initialized",
            "learning_patterns": "loaded" if _learning_patterns else "not_initialized"
        }
    }


async def generate_subject_viva_background(
    session_id: str,
    subject_name: str,
    num_questions: int,
    questioner: AdaptiveQuestioner
):
    """
    Background task to generate dynamic questions from subject content and 
    inject them into a viva session.
    """
    try:
        session = _active_sessions.get(session_id)
        if not session:
            return
            
        scanner = SubjectScanner()
        content = scanner.get_subject_content(subject_name)
        
        if not content:
            logger.warning(f"No content extracted for viva subject {subject_name}")
            return
            
        # Dynamically generate questions
        dynamic_questions = await questioner.generate_from_text(
            text=content,
            topic=subject_name,
            num_questions=num_questions
        )
        
        if dynamic_questions:
            await session.add_questions(dynamic_questions)
            logger.info(f"Injected {len(dynamic_questions)} dynamic questions into session {session_id}")
            
    except Exception as e:
        logger.error(f"Background viva generation error: {e}")