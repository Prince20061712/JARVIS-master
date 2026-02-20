from fastapi import FastAPI, APIRouter
from api.rest.controllers import query_controller
from utils.logger import logger

app = FastAPI(title="JARVIS Backend API", version="2.0.0")

# Include Controllers
app.include_router(query_controller.router, prefix="/api/v1", tags=["Query"])

@app.get("/health")
async def health_check():
    return {"status": "online", "message": "JARVIS API is running"}

@app.get("/profile")
async def get_profile():
    # Placeholder for student profile
    return {"user_id": "student_123", "university": "MU", "semester": 4}

@app.get("/study/session")
async def get_study_session():
    # Placeholder for study session status
    return {"active": True, "duration_mins": 45, "current_topic": "Data Structures"}

@app.get("/documents")
async def list_documents():
    # Placeholder for ingested documents
    return {"documents": []}
