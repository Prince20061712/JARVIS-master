"""
Screen Controller for ScreenCaptureManager
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
from pathlib import Path

# Try importing the manager
try:
    from managers.screen_manager import ScreenCaptureManager, CaptureMode, ImageFormat
except ImportError:
    # Fallback if structure is different
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent.parent))
    from managers.screen_manager import ScreenCaptureManager, CaptureMode, ImageFormat

router = APIRouter()

# Initialize manager
screen_manager = ScreenCaptureManager()

class ScreenshotRequest(BaseModel):
    mode: str = "full_screen" # full_screen, active_window, etc.
    quality: int = 95
    include_cursor: bool = True

class OCRRequest(BaseModel):
    mode: str = "full_screen"
    language: str = "eng"

@router.post("/screenshot")
async def take_screenshot(request: ScreenshotRequest):
    try:
        mode_enum = CaptureMode(request.mode) if request.mode else CaptureMode.FULL_SCREEN
        result = await screen_manager.take_screenshot_async(
            mode=mode_enum,
            quality=request.quality,
            include_cursor=request.include_cursor
        )
        if result.success:
            return {
                "success": True, 
                "file_path": str(result.file_path),
                "message": result.message
            }
        else:
            raise HTTPException(status_code=500, detail=result.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract-text")
async def extract_text_from_screen(request: OCRRequest):
    try:
        mode_enum = CaptureMode(request.mode) if request.mode else CaptureMode.FULL_SCREEN
        # First capture
        capture_result = await screen_manager.take_screenshot_async(mode=mode_enum)
        if not capture_result.success:
            raise HTTPException(status_code=500, detail="Failed to capture screen for OCR")
        
        # Then extract text
        ocr_result = screen_manager.extract_text(
            image_path=capture_result.file_path,
            language=request.language
        )
        return ocr_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active-window")
async def get_active_window():
    try:
        window = screen_manager.get_active_window()
        if window:
            return {
                "title": window.title,
                "process": window.process_name,
                "is_active": window.is_active
            }
        return {"message": "No active window found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
