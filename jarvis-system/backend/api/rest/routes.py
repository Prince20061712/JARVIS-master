from fastapi import FastAPI, APIRouter
from api.rest.controllers import query_controller, study_controller, profile_controller, screen_controller
from utils.logger import logger
from adaptive_learning.api.flashcard_controller import router as flashcard_router
from adaptive_learning.api.viva_controller import router as viva_router

app = FastAPI(title="JARVIS Backend API", version="2.0.0")

# Include Controllers
app.include_router(query_controller.router, prefix="/query", tags=["Query"])
app.include_router(study_controller.router, prefix="/study", tags=["Study"])
app.include_router(profile_controller.router, prefix="/profile", tags=["Profile"])
app.include_router(screen_controller.router, prefix="/screen", tags=["Screen"])

# Adaptive Learning Routers
app.include_router(flashcard_router, prefix="/adaptive", tags=["Adaptive Learning"])
app.include_router(viva_router, prefix="/adaptive", tags=["Adaptive Learning"])

@app.get("/health")
async def health_check():
    return {"status": "online", "message": "JARVIS Modular API is running"}
