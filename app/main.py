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
from .generators import (
    StoryGenerator,
    EducationalContentGenerator,
    ImageGenerator,
    VoiceOverGenerator,
    VideoGenerator, # Replaces create_video_async
    PodcastGenerator, # Replaces individual podcast functions
    MusicGenerator,   # Replaces generate_background_music
    BookGenerator,
    PostGenerator
)
# Old direct imports like generate_story, generate_educational_content, generate_images,
# generate_voice_over, generate_background_music, create_video_async,
# and individual podcast functions (generate_podcast_from_custom_text, etc.)
# will be removed implicitly if they are no longer called directly.
# The new generator classes will be used instead.

from .config import OUTPUT_DIR

# Define new options classes first as they are used in ContentRequest
class BookGenerationOptions(BaseModel):
    num_chapters: Optional[int] = 5
    writing_style: Optional[str] = "narrative"
    genre: Optional[str] = "fiction"

class MusicGenerationOptions(BaseModel):
    duration: Optional[int] = 60  # seconds
    tempo: Optional[int] = 120  # BPM
    genre: Optional[str] = "electronic"
    mood: Optional[str] = None

class PostGenerationOptions(BaseModel):
    style: Optional[str] = "informative"
    length: Optional[Literal["short", "medium", "long"]] = "medium"
    target_audience: Optional[str] = None

# Define request models
class PodcastGenerationOptions(BaseModel):
    podcast_type: Literal["custom_text", "topic_based", "free_generation"]
    custom_text: Optional[str] = None
    topic: Optional[str] = None # Topic specific to podcast, if different from main topic

class ContentRequest(BaseModel):
    content_type: Literal["story", "educational", "podcast", "book", "music", "post"]
    topic: str  # Main topic for all content types
    video_prompt: Optional[str] = None # Keep for story/educational video workflow
    educational_style: Optional[Literal["lecture", "tutorial", "explainer"]] = None
    difficulty_level: Optional[Literal["beginner", "intermediate", "advanced"]] = None
    podcast_options: Optional[PodcastGenerationOptions] = None
    book_options: Optional[BookGenerationOptions] = None
    music_options: Optional[MusicGenerationOptions] = None
    post_options: Optional[PostGenerationOptions] = None

# Add new models
class VideoInfo(BaseModel): # This seems to be for listing videos, might need a more generic name or specific ones for other types
    job_id: str
    content_type: str
    created_at: str
    video_url: str
    thumbnail_url: Optional[str] = None
    duration: Optional[float] = None

class MusicInfo(BaseModel):
    job_id: str
    content_type: str
    created_at: str
    completed_at: Optional[str] = None
    music_url: Optional[str] = None # URL to the static file
    download_url: str
    duration: Optional[float] = None # Placeholder, actual duration extraction might be complex
    file_size: Optional[int] = None

class BookInfo(BaseModel):
    job_id: str
    content_type: str
    topic: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    book_url: Optional[str] = None # Link to the full book in static dir
    download_url: str
    num_chapters: Optional[int] = None
    chapter_list: Optional[List[str]] = None # List of chapter filenames (not full paths)
    file_size: Optional[int] = None # For the full_book.txt

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
os.makedirs("static/thumbnails", exist_ok=True) # Assuming thumbnails are still relevant for videos
os.makedirs("static/audios", exist_ok=True) # For podcast audio and potentially voice-overs
os.makedirs("static/music", exist_ok=True)  # For MusicGenerator outputs
os.makedirs("static/books", exist_ok=True)  # For BookGenerator outputs (e.g. full_book.txt)
os.makedirs("static/posts", exist_ok=True)  # For PostGenerator outputs

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
    job_data = {
        "status": "processing",
        "created_at": datetime.now().isoformat(),
        "output_dir": output_dir,
        "content_type": request.content_type,
        "topic": request.topic # Store main topic
        # Removed "video_prompt" directly, will be part of request_options if needed
    }

    # Store relevant options based on content type
    options_to_store = {}
    if request.content_type == "story" or request.content_type == "educational":
        options_to_store["educational_style"] = request.educational_style
        options_to_store["difficulty_level"] = request.difficulty_level
        options_to_store["video_prompt"] = request.video_prompt # Still relevant for this flow
        if request.music_options: # For background music in video
            options_to_store["music_options"] = request.music_options.dict()
    elif request.content_type == "podcast" and request.podcast_options:
        options_to_store["podcast_options"] = request.podcast_options.dict()
    elif request.content_type == "book" and request.book_options:
        options_to_store["book_options"] = request.book_options.dict()
    elif request.content_type == "music" and request.music_options:
        options_to_store["music_options"] = request.music_options.dict()
    elif request.content_type == "post" and request.post_options:
        options_to_store["post_options"] = request.post_options.dict()

    job_data["request_options"] = options_to_store
    active_jobs[job_id] = job_data
    
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
        raise HTTPException(status_code=400, detail="Content generation not completed or failed.")

    output_file_path = job_info.get("output_file")
    if not output_file_path or not os.path.exists(output_file_path):
        # Try to construct path if output_file is not absolute (though it should be)
        if output_file_path: # if path is stored but file missing
             output_file_path = os.path.join(job_info["output_dir"], Path(output_file_path).name) # Use job_info["output_dir"]

        if not output_file_path or not os.path.exists(output_file_path): # Check again
            raise HTTPException(status_code=404, detail="Primary output file not found for this job.")

    content_type = job_info["content_type"]
    filename_ext = Path(output_file_path).suffix.lower() # e.g. .mp4, .mp3, .txt, .wav

    media_type_map = {
        ".mp4": "video/mp4",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".txt": "text/plain",
        # Add .zip if book chapters are zipped, etc.
    }
    default_media_type = "application/octet-stream"
    media_type = media_type_map.get(filename_ext, default_media_type)

    # Construct a meaningful filename for download
    download_filename = f"{content_type}_{job_id}{filename_ext}"

    return FileResponse(
        output_file_path,
        media_type=media_type,
        filename=download_filename
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
        final_output_path = None # To store the primary output file path for the job

        if request.content_type == "story" or request.content_type == "educational":
            text_content = None
            if request.content_type == "story":
                story_gen = StoryGenerator()
                # Assuming StoryGenerator's generate method takes 'character_description'
                text_content = await story_gen.generate(character_description=request.topic)
                if story_gen.get_status() != "completed":
                    raise Exception(f"Story generation failed: {story_gen.get_status()}")
            else: # educational
                edu_gen = EducationalContentGenerator()
                text_content = await edu_gen.generate(
                    topic=request.topic,
                    style=request.educational_style,
                    difficulty=request.difficulty_level
                )
                if edu_gen.get_status() != "completed":
                    raise Exception(f"Educational content generation failed: {edu_gen.get_status()}")

            if not text_content:
                 raise Exception("Text content generation returned empty.")

            # Save content (optional, as generators might save their own primary output)
            content_path = os.path.join(output_dir, f"{request.content_type}_content.txt")
            with open(content_path, 'w', encoding='utf-8') as f:
                f.write(text_content)

            # Generate images
            img_gen = ImageGenerator()
            # Assuming ImageGenerator needs text_content, a prefix, output_dir.
            # 'topic' can be used for base_filename_prefix or passed if model uses it.
            image_paths = await img_gen.generate(
                text_content=text_content,
                base_filename_prefix=request.content_type, # e.g., "story" or "educational"
                output_dir=os.path.join(output_dir, "images"),
                content_type=request.content_type
            )
            if img_gen.get_status() != "completed":
                raise Exception(f"Image generation failed: {img_gen.get_status()}")

            # Generate voice-over
            vo_gen = VoiceOverGenerator()
            voice_over_path = os.path.join(output_dir, "voice_over.mp3")
            await vo_gen.generate(text=text_content, output_path=voice_over_path)
            if vo_gen.get_status() != "completed":
                raise Exception(f"Voice-over generation failed: {vo_gen.get_status()}")

            # Generate background music using MusicGenerator
            music_gen = MusicGenerator()
            music_output_path = os.path.join(output_dir, "background_music.wav") # .wav or .mp3 based on MusicGenerator output
            music_options = request.music_options or MusicGenerationOptions() # Use defaults if not provided
            await music_gen.generate(
                output_path=music_output_path,
                duration=music_options.duration, # Default is 60s
                tempo=music_options.tempo,
                genre=music_options.genre,
                mood=music_options.mood
            )
            if music_gen.get_status() != "completed":
                raise Exception(f"Music generation failed: {music_gen.get_status()}")

            background_music_actual_path = music_gen.get_output()
            if not background_music_actual_path:
                 raise Exception("Music generation did not return an output path.")


            # Create video
            video_gen = VideoGenerator()
            video_path = os.path.join(output_dir, "content_video.mp4")
            # VideoGenerator now expects a single audio_path (pre-mixed).
            # For this flow, we are still providing separate voice-over and music.
            # This implies VideoGenerator needs to be able to mix them, or we pre-mix here.
            # The prompt for VideoGenerator refactor said: "assume audio_path is the final audio track"
            # This part of the flow needs reconciliation with VideoGenerator's new interface.
            # For now, let's assume VideoGenerator *can* take both and mix, or we prioritize voice_over.
            # Re-reading VideoGenerator: it takes ONE audio_path.
            # This means we need to decide: either VoiceOver only, or Music only, or pre-mix.
            # Let's prioritize VoiceOver for now if both are generated.
            # A better solution would be a separate audio mixing step or VideoGenerator enhancement.
            # For this iteration, we'll use the voice_over_path as the main audio for video.
            # The background_music_actual_path will be ignored by VideoGenerator for now.
            # This is a simplification based on VideoGenerator's current interface.
            # A real solution: create a composite audio track here or enhance VideoGenerator.

            # Simplification: Using voice_over_path as main audio for video
            # A proper solution would be to mix voice_over_path and background_music_actual_path
            # into a new file and pass that to VideoGenerator.
            # For now, background music generated above is not used in the video.
            # This is a known limitation of this refactoring step.
            # TODO: Implement audio mixing before passing to VideoGenerator or update VideoGenerator.

            await video_gen.generate(
                image_paths=image_paths,
                audio_path=voice_over_path, # Using voice_over only
                output_video_path=video_path,
                video_prompt=request.video_prompt, # video_prompt is optional in VideoGenerator
                content_type=request.content_type
            )
            if video_gen.get_status() != "completed":
                raise Exception(f"Video generation failed: {video_gen.get_status()}")
            final_output_path = video_gen.get_output()

        elif request.content_type == "podcast":
            if not request.podcast_options:
                raise ValueError("Podcast options not provided for podcast content type.")

            podcast_gen = PodcastGenerator()
            podcast_script_path = os.path.join(output_dir, "podcast_script.txt")
            podcast_audio_path = os.path.join(output_dir, "podcast_audio.mp3")

            podcast_output_map = await podcast_gen.generate(
                podcast_type=request.podcast_options.podcast_type,
                output_script_path=podcast_script_path,
                output_audio_path=podcast_audio_path,
                custom_text=request.podcast_options.custom_text,
                topic=request.podcast_options.topic or request.topic # Use specific topic if provided, else main topic
            )
            if podcast_gen.get_status() != "completed":
                raise Exception(f"Podcast generation failed: {podcast_gen.get_status()}")

            final_output_path = podcast_output_map.get("audio_path")
            active_jobs[job_id]["script_file"] = podcast_output_map.get("script_path") # Store script path too

            # Copy podcast audio to static directory for /podcast/{job_id}/info endpoint
            if final_output_path and os.path.exists(final_output_path):
                audio_filename_static = f"{job_id}_podcast.mp3" # More specific filename
                public_audio_path_static = os.path.join("static/audios", audio_filename_static)
                shutil.copy2(final_output_path, public_audio_path_static)
                active_jobs[job_id]["audio_url"] = f"/static/audios/{audio_filename_static}"
            else:
                active_jobs[job_id]["audio_url"] = None # Or raise error if audio path is critical
                # If audio_url is critical and not found, perhaps an error should be raised earlier.

        elif request.content_type == "book":
            book_gen = BookGenerator()
            book_options = request.book_options or BookGenerationOptions()
            # BookGenerator saves chapters and a full_book.txt inside output_dir
            await book_gen.generate(
                topic=request.topic,
                output_dir=os.path.join(output_dir, "book_content"), # Specific subdirectory for book files
                num_chapters=book_options.num_chapters,
                writing_style=book_options.writing_style,
                genre=book_options.genre
            )
            if book_gen.get_status() != "completed":
                raise Exception(f"Book generation failed: {book_gen.get_status()}")
            final_output_path = book_gen.get_output() # Path to full_book.txt or main output
            # Optionally copy to static/books if direct download/serving is needed
            if final_output_path and os.path.exists(final_output_path):
                 book_filename_static = f"{job_id}_full_book.txt" # Corrected filename
                 public_book_path_static = os.path.join("static/books", book_filename_static)
                 shutil.copy2(final_output_path, public_book_path_static)
                 active_jobs[job_id]["book_url"] = f"/static/books/{book_filename_static}"
                 # Store chapter details if available from generator (not currently, but for future)
                 # active_jobs[job_id]["chapters"] = book_gen.chapters_content # Example if generator stored this


        elif request.content_type == "music":
            music_gen = MusicGenerator()
            music_options = request.music_options or MusicGenerationOptions()
            # Define output path for the music file
            generated_music_filename = "generated_music.wav" # .wav or .mp3 based on MusicGenerator
            music_file_path = os.path.join(output_dir, generated_music_filename)

            await music_gen.generate(
                output_path=music_file_path,
                duration=music_options.duration,
                tempo=music_options.tempo,
                genre=music_options.genre,
                mood=music_options.mood
                # request.topic could be used as a theme/seed if generator supports it.
            )
            if music_gen.get_status() != "completed":
                raise Exception(f"Music generation failed: {music_gen.get_status()}")
            final_output_path = music_gen.get_output()

            # Copy music to static directory for direct URL access
            if final_output_path and os.path.exists(final_output_path):
                music_filename_static = f"{job_id}_music.wav" # Match output type
                public_music_path_static = os.path.join("static/music", music_filename_static)
                shutil.copy2(final_output_path, public_music_path_static)
                active_jobs[job_id]["music_url"] = f"/static/music/{music_filename_static}"
            else:
                active_jobs[job_id]["music_url"] = None

        elif request.content_type == "post":
            post_gen = PostGenerator()
            post_options = request.post_options or PostGenerationOptions()
            # PostGenerator saves post.txt (or similar) inside output_dir
            await post_gen.generate(
                topic=request.topic,
                output_dir=os.path.join(output_dir, "post_content"), # Specific subdirectory
                style=post_options.style,
                length=post_options.length,
                target_audience=post_options.target_audience
            )
            if post_gen.get_status() != "completed":
                raise Exception(f"Post generation failed: {post_gen.get_status()}")
            final_output_path = post_gen.get_output()
            # Optionally copy to static/posts
            if final_output_path and os.path.exists(final_output_path):
                 post_filename_static = f"{job_id}_post.txt"
                 public_post_path_static = os.path.join("static/posts", post_filename_static)
                 shutil.copy2(final_output_path, public_post_path_static)
                 active_jobs[job_id]["post_url"] = f"/static/posts/{post_filename_static}"

        # Common status update logic
        current_job_status = active_jobs[job_id].get("status", "processing")
        if current_job_status == "processing": # Only update if not already set to failed by a specific exception
            if final_output_path and os.path.exists(final_output_path):
                active_jobs[job_id]["output_file"] = final_output_path
                active_jobs[job_id]["status"] = "completed"
                active_jobs[job_id]["completed_at"] = datetime.now().isoformat()
            else:
                # This case means a generator reported success, but its get_output() was None or file missing
                active_jobs[job_id]["status"] = "failed"
                active_jobs[job_id]["error"] = "Generation reported success, but output file is missing or not set by generator."
                active_jobs[job_id]["failed_at"] = datetime.now().isoformat()
        # If current_job_status was already "failed" due to an exception in the try block, it remains "failed".

    except Exception as e:
        # This outer catch ensures any unhandled exception during the process leads to a failed status
        if active_jobs[job_id].get("status") != "failed": # Avoid overwriting a more specific failure message if one was set
            active_jobs[job_id]["status"] = "failed"
        active_jobs[job_id]["error"] = str(e)
        active_jobs[job_id]["failed_at"] = datetime.now().isoformat()

@app.get("/podcast/{job_id}/info")
async def get_podcast_info(job_id: str):
    """Get detailed information about a podcast job."""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job_info = active_jobs[job_id]
    if job_info["content_type"] != "podcast":
        raise HTTPException(status_code=400, detail="Job is not a podcast type.")

    if job_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="Podcast generation not completed.")

    return {
        "job_id": job_id,
        "content_type": job_info["content_type"],
        "created_at": job_info["created_at"],
        "completed_at": job_info["completed_at"],
        "audio_url": job_info.get("audio_url"),
        "download_url": f"/download/{job_id}",
        # "script_url": f"/download/{job_id}?type=script" # Example for future script download
    }

@app.get("/music/{job_id}/info", response_model=MusicInfo)
async def get_music_info(job_id: str):
    """Get detailed information about a music generation job."""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job_info = active_jobs[job_id]
    if job_info["content_type"] != "music":
        raise HTTPException(status_code=400, detail="Job is not a music type.")

    if job_info["status"] != "completed":
        # Allow fetching info even if failed, to see the error.
        # But some fields might be missing.
        if job_info["status"] != "failed":
             raise HTTPException(status_code=400, detail=f"Music generation status: {job_info['status']}.")

    file_size = None
    output_file = job_info.get("output_file")
    if output_file and os.path.exists(output_file):
        try:
            file_size = os.path.getsize(output_file)
        except OSError:
            file_size = None # File might have been removed or inaccessible

    # Duration is harder to get without loading the audio file with a library.
    # For now, we'll omit it or use a placeholder if available from options.
    duration_placeholder = None
    if job_info.get("request_options", {}).get("music_options", {}):
        duration_placeholder = job_info["request_options"]["music_options"].get("duration")


    return MusicInfo(
        job_id=job_id,
        content_type=job_info["content_type"],
        created_at=job_info["created_at"],
        completed_at=job_info.get("completed_at"),
        music_url=job_info.get("music_url"), # This should be set if generation was successful
        download_url=f"/download/{job_id}",
        duration=duration_placeholder, # Placeholder
        file_size=file_size
    )

@app.get("/book/{job_id}/info", response_model=BookInfo)
async def get_book_info(job_id: str):
    """Get detailed information about a book generation job."""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job_info = active_jobs[job_id]
    if job_info["content_type"] != "book":
        raise HTTPException(status_code=400, detail="Job is not a book type.")

    if job_info["status"] != "completed":
        if job_info["status"] != "failed":
            raise HTTPException(status_code=400, detail=f"Book generation status: {job_info['status']}.")

    file_size = None
    output_file = job_info.get("output_file") # This is full_book.txt path
    if output_file and os.path.exists(output_file):
        try:
            file_size = os.path.getsize(output_file)
        except OSError:
            file_size = None

    num_chapters = None
    if job_info.get("request_options", {}).get("book_options", {}):
        num_chapters = job_info["request_options"]["book_options"].get("num_chapters")

    chapter_list = []
    # The BookGenerator saves chapters in a subdirectory "book_content" within the job's output_dir
    book_content_dir = os.path.join(job_info["output_dir"], "book_content")
    if os.path.isdir(book_content_dir):
        try:
            for f_name in os.listdir(book_content_dir):
                if f_name.startswith("chapter_") and f_name.endswith(".txt") and f_name != "full_book.txt":
                    chapter_list.append(f_name)
            if not chapter_list and num_chapters is None and job_info["status"] == "completed":
                # If no chapters found and num_chapters wasn't in options, it's odd for a completed job
                pass # Or log a warning
        except OSError:
            pass # Could not list directory

    return BookInfo(
        job_id=job_id,
        content_type=job_info["content_type"],
        topic=job_info.get("topic"), # Main topic stored at job creation
        created_at=job_info["created_at"],
        completed_at=job_info.get("completed_at"),
        book_url=job_info.get("book_url"),
        download_url=f"/download/{job_id}", # This downloads full_book.txt
        num_chapters=num_chapters or (len(chapter_list) if chapter_list else None),
        chapter_list=chapter_list if chapter_list else None,
        file_size=file_size
    )