from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from uuid import uuid4
import shutil
import os
from pathlib import Path
import asyncio
from pydantic import BaseModel

from app.generators.platformer_game import generate_platformer_game
from app.config import OUTPUT_DIR

router = APIRouter()

# In-memory job store: {job_id: {status, theme, output_dir, zip_path, error}}
jobs = {}

class GameRequest(BaseModel):
    theme: str

@router.post("/games/")
async def start_game_generation(request: GameRequest, background_tasks: BackgroundTasks):
    theme = request.theme
    job_id = str(uuid4())
    output_dir = Path(OUTPUT_DIR) / "processing_games" / theme.replace(" ", "_").replace("-", "_").lower()
    zip_path = output_dir / "game.zip"
    jobs[job_id] = {"status": "pending", "theme": theme, "output_dir": output_dir, "zip_path": zip_path, "error": None}
    
    def run_generation():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            jobs[job_id]["status"] = "running"
            loop.run_until_complete(generate_platformer_game(theme))
            # Zip the output directory
            shutil.make_archive(str(zip_path.with_suffix("").absolute()), 'zip', str(output_dir))
            jobs[job_id]["status"] = "done"
        except Exception as e:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = str(e)
        finally:
            loop.close()
    
    background_tasks.add_task(run_generation)
    return {"job_id": job_id}

@router.get("/games/{job_id}/status")
async def check_game_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": job["status"], "error": job["error"]}

@router.get("/games/{job_id}/download")
async def download_game_zip(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "done":
        raise HTTPException(status_code=400, detail="Game not ready for download")
    zip_path = job["zip_path"]
    if not zip_path.exists():
        raise HTTPException(status_code=500, detail="Zip file not found")
    return FileResponse(str(zip_path), filename="game.zip", media_type="application/zip") 