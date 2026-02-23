"""
Profile Controller for Handling Student Profiles
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import os
from pathlib import Path

router = APIRouter()

# Path to the current profile JSON
# It is located in the backend root directory
PROFILE_PATH = Path(__file__).resolve().parent.parent.parent.parent / "prince_profile.json"

class ProfileUpdate(BaseModel):
    # Depending on what the frontend sends, this can be customized
    # Using a generic dict for now to accept arbitrary updates to the JSON structure
    updates: Dict[str, Any]

@router.get("/")
async def get_profile():
    """
    Retrieve the current student profile from prince_profile.json
    """
    try:
        if not PROFILE_PATH.exists():
            # Return a default empty structure if file doesn't exist
            return {"message": "Profile not found", "data": {}}
            
        with open(PROFILE_PATH, "r") as f:
            profile_data = json.load(f)
            
        return {"data": profile_data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading profile: {str(e)}")

@router.post("/")
async def update_profile(request: ProfileUpdate):
    """
    Update specific fields in the student profile
    """
    try:
        # Load existing
        profile_data = {}
        if PROFILE_PATH.exists():
            with open(PROFILE_PATH, "r") as f:
                profile_data = json.load(f)
                
        # Update with new values
        for key, value in request.updates.items():
            profile_data[key] = value
            
        # Save back
        with open(PROFILE_PATH, "w") as f:
            json.dump(profile_data, f, indent=2)
            
        return {"message": "Profile updated successfully", "data": profile_data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating profile: {str(e)}")