import uuid
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any # Ensure Optional is imported
import asyncio # Import asyncio for potential async operations in future
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Assuming main.py is in the same directory and contains create_video_task
# Ensure this import works with your project structure.
# You might need to adjust it if main.py is elsewhere or if it causes circular dependencies.
from main import create_video_task, TEST_MODE # Import TEST_MODE as well
from config import ANTHROPIC_KEY, STABILITY_KEY, ELEVENLABS_KEY # Import API keys to check if they are loaded

app = FastAPI(
    title="Video Generation API",
    description="An API to generate short videos based on character descriptions. Allows submitting tasks and checking their status.",
    version="0.1.0"
)

# In-memory store for task statuses and results
tasks = {}

class VideoRequest(BaseModel):
    character_description: str
    # Add other potential parameters here in the future, e.g.,
    # story_prompt: Optional[str] = None
    # style_preference: Optional[str] = None

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    video_path: Optional[str] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None # For any other details

class TaskCreationResponse(BaseModel):
    task_id: str
    status: str
    message: Optional[str] = None

# Helper function to run the video creation in the background
def run_video_creation(task_id: str, character_description: str):
    try:
        logger.info(f"Starting video creation for task_id: {task_id}")
        # Ensure API keys are loaded before starting the task, otherwise raise an error early
        if not TEST_MODE and (not ANTHROPIC_KEY or not STABILITY_KEY or not ELEVENLABS_KEY):
            logger.error("API keys are missing. Cannot proceed with video generation.")
            tasks[task_id] = {"status": "failed", "error": "Missing API keys. Configure them in .env file."}
            return

        video_path = create_video_task(character_description)
        tasks[task_id] = {"status": "completed", "video_path": video_path}
        logger.info(f"Video creation completed for task_id: {task_id}. Video at: {video_path}")
    except Exception as e:
        logger.error(f"Error during video creation for task_id {task_id}: {e}", exc_info=True)
        tasks[task_id] = {"status": "failed", "error": str(e)}

@app.post("/videos", response_model=TaskCreationResponse, summary="Create Video Generation Task", description="Submit a new video generation task with a character description.")
async def create_video_endpoint(video_request: VideoRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "processing"}
    
    logger.info(f"Received request to generate video for task_id: {task_id} with description: {video_request.character_description}")
    
    background_tasks.add_task(run_video_creation, task_id, video_request.character_description)
    
    return {"task_id": task_id, "status": "processing", "message": "Video generation task started."}

@app.get("/videos/{task_id}", response_model=TaskStatusResponse, summary="Get Video Task Status", description="Retrieve the status and result of a video generation task.")
async def get_video_status(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with ID '{task_id}' not found.") # More specific error
    
    # Return the full task object which should align with TaskStatusResponse
    # Ensure 'video_path' and 'error' are None if not applicable for a given status
    return {
        "task_id": task_id,
        "status": task["status"],
        "video_path": task.get("video_path"),
        "error": task.get("error")
    }

# Add a root endpoint for basic API health check
@app.get("/", summary="API Health Check")
async def read_root():
    return {"message": "Video Generation API is running."}

# To run this app, use uvicorn:
# uvicorn api:app --reload
