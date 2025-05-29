from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from datetime import datetime, timedelta
import uuid
from pydantic import BaseModel
from typing import Optional, Literal, List
import shutil
from pathlib import Path

from .generators.story import generate_story
from .generators.educational import generate_educational_content
from .generators.image import generate_images
from .generators.audio import generate_voice_over, generate_background_music
from .generators.video import create_video_async
from .config import OUTPUT_DIR

# Define request models
class ContentRequest(BaseModel):
    content_type: Literal["story", "educational"]
    topic: str  # character_description for stories, topic for educational content
    video_prompt: Optional[str] = None
    educational_style: Optional[Literal["lecture", "tutorial", "explainer"]] = None
    difficulty_level: Optional[Literal["beginner", "intermediate", "advanced"]] = None

# Add new models
class VideoInfo(BaseModel):
    job_id: str
    content_type: str
    created_at: str
    video_url: str
    thumbnail_url: Optional[str] = None
    duration: Optional[float] = None

app = FastAPI(
    title="Content Maker API",
    description="API for generating AI-powered stories and educational videos with images, voice-overs, and background music",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active jobs
active_jobs = {}

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create necessary directories
os.makedirs("static/videos", exist_ok=True)
os.makedirs("static/thumbnails", exist_ok=True)

@app.get("/")
async def root():
    return {"message": "Welcome to Content Maker API"}

@app.post("/generate")
async def generate_content_endpoint(request: ContentRequest, background_tasks: BackgroundTasks):
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    
    # Create a unique output directory for this job
    output_dir = os.path.join(OUTPUT_DIR, job_id)
    os.makedirs(output_dir, exist_ok=True)
    
    # Store job information
    active_jobs[job_id] = {
        "status": "processing",
        "created_at": datetime.now().isoformat(),
        "output_dir": output_dir,
        "content_type": request.content_type,
        "video_prompt": request.video_prompt
    }
    
    # Start the generation process in the background
    background_tasks.add_task(
        process_content_generation,
        job_id,
        request,
        output_dir
    )
    
    return {
        "job_id": job_id,
        "status": "processing",
        "message": f"{request.content_type.capitalize()} generation started"
    }

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return active_jobs[job_id]

@app.get("/download/{job_id}")
async def download_content(job_id: str):
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_info = active_jobs[job_id]
    if job_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="Content generation not completed")
    
    video_path = os.path.join(job_info["output_dir"], "content_video.mp4")
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=f"{job_info['content_type']}_{job_id}.mp4"
    )

@app.get("/videos", response_model=List[VideoInfo])
async def list_videos(
    content_type: Optional[str] = None,
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(10, ge=1, le=100)
):
    """List available videos with optional filtering."""
    videos = []
    cutoff_date = datetime.now() - timedelta(days=days)
    
    for job_id, job_info in active_jobs.items():
        if job_info["status"] != "completed":
            continue
            
        if content_type and job_info["content_type"] != content_type:
            continue
            
        created_at = datetime.fromisoformat(job_info["created_at"])
        if created_at < cutoff_date:
            continue
            
        video_path = os.path.join(job_info["output_dir"], "content_video.mp4")
        if not os.path.exists(video_path):
            continue
            
        # Create public URL for the video
        public_path = f"static/videos/{job_id}.mp4"
        if not os.path.exists(public_path):
            shutil.copy2(video_path, public_path)
            
        videos.append(VideoInfo(
            job_id=job_id,
            content_type=job_info["content_type"],
            created_at=job_info["created_at"],
            video_url=f"/static/videos/{job_id}.mp4"
        ))
    
    return sorted(videos, key=lambda x: x.created_at, reverse=True)[:limit]

@app.get("/video/{job_id}/stream")
async def stream_video(job_id: str):
    """Stream video content."""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Video not found")
    
    job_info = active_jobs[job_id]
    if job_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="Video generation not completed")
    
    video_path = os.path.join(job_info["output_dir"], "content_video.mp4")
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return StreamingResponse(
        open(video_path, "rb"),
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Disposition": f'attachment; filename="{job_info["content_type"]}_{job_id}.mp4"'
        }
    )

@app.get("/video/{job_id}/embed")
async def get_video_embed(job_id: str):
    """Get HTML embed code for the video."""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Video not found")
    
    job_info = active_jobs[job_id]
    if job_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="Video generation not completed")
    
    video_url = f"/static/videos/{job_id}.mp4"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{job_info['content_type'].capitalize()} Video</title>
        <style>
            body {{ margin: 0; padding: 20px; background: #f0f0f0; }}
            .video-container {{ max-width: 800px; margin: 0 auto; }}
            video {{ width: 100%; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        </style>
    </head>
    <body>
        <div class="video-container">
            <video controls>
                <source src="{video_url}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

@app.get("/video/{job_id}/info")
async def get_video_info(job_id: str):
    """Get detailed information about a video."""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Video not found")
    
    job_info = active_jobs[job_id]
    if job_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="Video generation not completed")
    
    video_path = os.path.join(job_info["output_dir"], "content_video.mp4")
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    # Get video file size
    file_size = os.path.getsize(video_path)
    
    return {
        "job_id": job_id,
        "content_type": job_info["content_type"],
        "created_at": job_info["created_at"],
        "completed_at": job_info["completed_at"],
        "file_size": file_size,
        "download_url": f"/download/{job_id}",
        "stream_url": f"/video/{job_id}/stream",
        "embed_url": f"/video/{job_id}/embed",
        "static_url": f"/static/videos/{job_id}.mp4"
    }

async def process_content_generation(job_id: str, request: ContentRequest, output_dir: str):
    try:
        # Generate content based on type
        if request.content_type == "story":
            content = await generate_story(request.topic)  # topic is character_description
        else:
            content = await generate_educational_content(
                request.topic,
                request.educational_style,
                request.difficulty_level
            )
        
        # Save content
        content_path = os.path.join(output_dir, "content.txt")
        with open(content_path, 'w') as f:
            f.write(content)
        
        # Generate images
        image_paths = await generate_images(
            content,
            request.topic,
            output_dir,
            content_type=request.content_type
        )
        
        # Generate voice-over
        voice_over_path = os.path.join(output_dir, "voice_over.mp3")
        await generate_voice_over(content, voice_over_path)
        
        # Generate background music
        background_music_path = os.path.join(output_dir, "background_music.wav")
        await generate_background_music(60, background_music_path)
        
        # Create video
        video_path = os.path.join(output_dir, "content_video.mp4")
        await create_video_async(
            image_paths,
            voice_over_path,
            background_music_path,
            video_path,
            video_prompt=request.video_prompt,
            content_type=request.content_type
        )
        
        # Update job status
        active_jobs[job_id]["status"] = "completed"
        active_jobs[job_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        active_jobs[job_id]["status"] = "failed"
        active_jobs[job_id]["error"] = str(e)
        active_jobs[job_id]["failed_at"] = datetime.now().isoformat() 