import uvicorn
from api.rest.routes import app
from utils.logger import logger

if __name__ == "__main__":
    logger.info("Starting JARVIS Engineering Academic Copilot (v2.0)")
    uvicorn.run(app, host="0.0.0.0", port=8000)
