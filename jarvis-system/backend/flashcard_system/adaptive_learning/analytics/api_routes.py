"""
REST API routes for the analytics module.
Provides endpoints for accessing learning analytics, retention curves, and performance metrics.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json

from fastapi import APIRouter, HTTPException, Depends, Query, Path as PathParam
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, field_validator

from .learning_patterns import LearningPatterns, RetentionCurve, WeaknessAnalysis

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Initialize analytics engine (singleton)
_analytics_engine: Optional[LearningPatterns] = None


def get_analytics_engine() -> LearningPatterns:
    """Dependency to get analytics engine instance."""
    global _analytics_engine
    if _analytics_engine is None:
        project_root = Path(__file__).parent.parent.parent.parent
        data_dir = project_root / "data" / "analytics"
        _analytics_engine = LearningPatterns(data_dir=data_dir)
    return _analytics_engine


# Pydantic models for request/response validation

class FlashcardReviewRequest(BaseModel):
    """Request model for recording flashcard review."""
    user_id: str = Field(..., min_length=1, max_length=100)
    topic: str = Field(..., min_length=1, max_length=200)
    difficulty_rating: int = Field(..., ge=0, le=5)
    response_time: float = Field(..., gt=0, le=3600)
    emotional_state: Optional[str] = Field(None, max_length=50)


class VivaResponseRequest(BaseModel):
    """Request model for recording viva response."""
    user_id: str = Field(..., min_length=1, max_length=100)
    session_id: str = Field(..., min_length=1, max_length=100)
    question: Dict[str, Any]
    answer: Dict[str, Any]
    emotional_state: Dict[str, Any]


class TimeRangeRequest(BaseModel):
    """Request model for time range queries."""
    user_id: str = Field(..., min_length=1, max_length=100)
    time_period: str = Field("week", pattern="^(day|week|month|year)$")
    
    @field_validator('time_period')
    def validate_time_period(cls, v):
        if v not in ['day', 'week', 'month', 'year']:
            raise ValueError('time_period must be day, week, month, or year')
        return v


class ExportRequest(BaseModel):
    """Request model for data export."""
    user_id: str = Field(..., min_length=1, max_length=100)
    format: str = Field("json", pattern="^(json|csv|report)$")
    
    @field_validator('format')
    def validate_format(cls, v):
        if v not in ['json', 'csv', 'report']:
            raise ValueError('format must be json, csv, or report')
        return v


# API Endpoints

@router.post("/flashcard/review")
async def record_flashcard_review(
    request: FlashcardReviewRequest,
    engine: LearningPatterns = Depends(get_analytics_engine)
) -> Dict[str, Any]:
    """
    Record a flashcard review session.
    
    Args:
        request: Flashcard review data
        
    Returns:
        Confirmation message
    """
    try:
        engine.record_flashcard_review(
            user_id=request.user_id,
            topic=request.topic,
            difficulty_rating=request.difficulty_rating,
            response_time=request.response_time,
            emotional_state=request.emotional_state
        )
        
        return {
            "status": "success",
            "message": "Flashcard review recorded",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error recording flashcard review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/viva/response")
async def record_viva_response(
    request: VivaResponseRequest,
    engine: LearningPatterns = Depends(get_analytics_engine)
) -> Dict[str, Any]:
    """
    Record a viva response for analysis.
    
    Args:
        request: Viva response data
        
    Returns:
        Confirmation message
    """
    try:
        engine.record_viva_response(
            user_id=request.user_id,
            session_id=request.session_id,
            question=request.question,
            answer=request.answer,
            emotional_state=request.emotional_state
        )
        
        return {
            "status": "success",
            "message": "Viva response recorded",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error recording viva response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retention/{user_id}/{topic}")
async def get_retention_curve(
    user_id: str = PathParam(..., min_length=1, max_length=100),
    topic: str = PathParam(..., min_length=1, max_length=200),
    days_ahead: int = Query(30, ge=1, le=365),
    engine: LearningPatterns = Depends(get_analytics_engine)
) -> Dict[str, Any]:
    """
    Get Ebbinghaus retention curve for a specific topic.
    
    Args:
        user_id: User identifier
        topic: Topic to analyze
        days_ahead: Number of days to predict ahead
        
    Returns:
        Retention curve data
    """
    try:
        curve = engine.generate_retention_curve(user_id, topic, days_ahead)
        
        # Generate prediction points for visualization
        predictions = []
        for day in range(0, days_ahead + 1, max(1, days_ahead // 30)):
            predictions.append({
                "day": day,
                "retention": curve.predict_retention(day)
            })
        
        return {
            "topic": curve.topic,
            "forgetting_rate": curve.forgetting_rate,
            "initial_retention": curve.initial_retention,
            "model_type": curve.model_type.value,
            "r_squared": curve.r_squared,
            "predicted_forget_date": curve.predicted_forget_date.isoformat() if curve.predicted_forget_date else None,
            "days_until_50_percent": curve.days_until_forget(50),
            "days_until_30_percent": curve.days_until_forget(30),
            "data_points": [
                {"date": ts.isoformat(), "retention": ret}
                for ts, ret in curve.data_points
            ],
            "predictions": predictions,
            "confidence_interval": {
                "lower": curve.confidence_interval[0],
                "upper": curve.confidence_interval[1]
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating retention curve: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/heatmap")
async def get_performance_heatmap(
    request: TimeRangeRequest,
    engine: LearningPatterns = Depends(get_analytics_engine)
) -> Dict[str, Any]:
    """
    Generate performance heatmap for a user.
    
    Args:
        request: Time range request
        
    Returns:
        Performance heatmap data
    """
    try:
        heatmap = engine.generate_performance_heatmap(
            user_id=request.user_id,
            time_period=request.time_period
        )
        
        return heatmap
        
    except Exception as e:
        logger.error(f"Error generating heatmap: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weaknesses/{user_id}")
async def analyze_weaknesses(
    user_id: str = PathParam(..., min_length=1, max_length=100),
    engine: LearningPatterns = Depends(get_analytics_engine)
) -> Dict[str, Any]:
    """
    Perform deep analysis of learning weaknesses.
    
    Args:
        user_id: User identifier
        
    Returns:
        Weakness analysis data
    """
    try:
        weaknesses = engine.analyze_weaknesses(user_id)
        
        return {
            "weak_topics": [
                {"topic": topic, "weakness_score": score}
                for topic, score in weaknesses.weak_topics
            ],
            "strong_topics": [
                {"topic": topic, "strength_score": score}
                for topic, score in weaknesses.strong_topics
            ],
            "improvement_pace": weaknesses.improvement_pace,
            "recommended_focus": weaknesses.recommended_focus,
            "critical_gaps": weaknesses.critical_gaps,
            "topic_correlations": weaknesses.topic_correlations,
            "priority_topics": weaknesses.get_priority_topics(5)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing weaknesses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/{user_id}")
async def get_study_recommendations(
    user_id: str = PathParam(..., min_length=1, max_length=100),
    limit: int = Query(5, ge=1, le=20),
    engine: LearningPatterns = Depends(get_analytics_engine)
) -> Dict[str, Any]:
    """
    Get personalized study recommendations.
    
    Args:
        user_id: User identifier
        limit: Maximum number of recommendations
        
    Returns:
        Study recommendations
    """
    try:
        recommendations = engine.get_study_recommendations(user_id, limit)
        
        return {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "recommendations": recommendations,
            "total_recommendations": len(recommendations)
        }
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/{user_id}")
async def get_learning_insights(
    user_id: str = PathParam(..., min_length=1, max_length=100),
    engine: LearningPatterns = Depends(get_analytics_engine)
) -> Dict[str, Any]:
    """
    Get comprehensive learning insights.
    
    Args:
        user_id: User identifier
        
    Returns:
        Learning insights data
    """
    try:
        insights = engine.get_learning_insights(user_id)
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{user_id}/{session_id}")
async def get_session_metrics(
    user_id: str = PathParam(..., min_length=1, max_length=100),
    session_id: str = PathParam(..., min_length=1, max_length=100),
    engine: LearningPatterns = Depends(get_analytics_engine)
) -> Dict[str, Any]:
    """
    Get metrics for a specific study session.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        
    Returns:
        Session metrics
    """
    try:
        session = engine.track_study_session(user_id, session_id)
        
        return {
            "session_id": session.session_id,
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "duration_minutes": session.duration_minutes,
            "flashcards_reviewed": session.flashcards_reviewed,
            "viva_questions_answered": session.viva_questions_answered,
            "avg_difficulty": session.avg_difficulty,
            "avg_performance": session.avg_performance,
            "learning_efficiency": session.learning_efficiency,
            "topics_studied": session.topics_studied,
            "performance_scores": session.performance_scores,
            "emotional_progression": [
                {
                    "timestamp": ts.isoformat(),
                    "state": state,
                    "intensity": intensity
                }
                for ts, state, intensity in session.emotional_progression
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting session metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_analytics(
    request: ExportRequest,
    engine: LearningPatterns = Depends(get_analytics_engine)
) -> Response:
    """
    Export analytics data in various formats.
    
    Args:
        request: Export request parameters
        
    Returns:
        Exported data with appropriate content type
    """
    try:
        data = engine.export_analytics(
            user_id=request.user_id,
            format=request.format
        )
        
        if request.format == 'json':
            return JSONResponse(content=data)
        elif request.format == 'report':
            return Response(
                content=data,
                media_type="text/plain",
                headers={
                    "Content-Disposition": f"attachment; filename=analytics_report_{request.user_id}.txt"
                }
            )
        else:
            # CSV format
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            
            # Write CSV header and data
            if isinstance(data, dict):
                # Flatten dictionary for CSV
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        writer.writerow([key, json.dumps(value)])
                    else:
                        writer.writerow([key, value])
            
            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=analytics_export_{request.user_id}.csv"
                }
            )
        
    except Exception as e:
        logger.error(f"Error exporting analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/user/{user_id}")
async def clear_user_data(
    user_id: str = PathParam(..., min_length=1, max_length=100),
    engine: LearningPatterns = Depends(get_analytics_engine)
) -> Dict[str, Any]:
    """
    Clear all analytics data for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        Confirmation message
    """
    try:
        success = engine.clear_user_data(user_id)
        
        if success:
            return {
                "status": "success",
                "message": f"All analytics data cleared for user {user_id}",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear user data")
        
    except Exception as e:
        logger.error(f"Error clearing user data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check(
    engine: LearningPatterns = Depends(get_analytics_engine)
) -> Dict[str, Any]:
    """
    Health check endpoint for analytics module.
    
    Returns:
        Health status
    """
    try:
        # Perform basic health check
        return {
            "status": "healthy",
            "module": "analytics",
            "timestamp": datetime.now().isoformat(),
            "data_dir": str(engine.data_dir),
            "data_loaded": True
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "module": "analytics",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# WebSocket event handlers (if using WebSockets for real-time analytics)
async def handle_analytics_websocket(websocket, user_id: str):
    """
    Handle WebSocket connections for real-time analytics updates.
    
    Args:
        websocket: WebSocket connection
        user_id: User identifier
    """
    try:
        await websocket.accept()
        
        engine = get_analytics_engine()
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            command = data.get('command')
            
            if command == 'get_insights':
                insights = engine.get_learning_insights(user_id)
                await websocket.send_json({
                    'type': 'insights',
                    'data': insights
                })
                
            elif command == 'get_heatmap':
                time_period = data.get('time_period', 'week')
                heatmap = engine.generate_performance_heatmap(user_id, time_period)
                await websocket.send_json({
                    'type': 'heatmap',
                    'data': heatmap
                })
                
            elif command == 'get_recommendations':
                recommendations = engine.get_study_recommendations(user_id)
                await websocket.send_json({
                    'type': 'recommendations',
                    'data': recommendations
                })
                
            elif command == 'ping':
                await websocket.send_json({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                })
                
            else:
                await websocket.send_json({
                    'type': 'error',
                    'message': f'Unknown command: {command}'
                })
                
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        await websocket.close()


# Note: Middleware is not supported on APIRouter.
# Request logging is handled at the main FastAPI app level.