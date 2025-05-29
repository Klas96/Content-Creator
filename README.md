# Story Maker

An AI-powered application that generates short stories with images, voice-over, and background music.

## Features

- Story generation using Claude AI
- Image generation using Stable Diffusion
- Text-to-speech voice-over
- Background music generation
- Organized output in chapter and scene directories

## Setup

1. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your API keys:
   - Copy the example environment file `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Open the `.env` file and fill in your API keys for:
     - `ANTHROPIC_KEY`: Get from Anthropic (https://console.anthropic.com)
     - `STABILITY_KEY`: Get from Stability AI (https://stability.ai)
     - `ELEVENLABS_KEY`: Get from ElevenLabs (https://elevenlabs.io/)

4. Prepare your input files in the `input` directory (for `main.py` script):
   - `chapters.txt`: Your story chapters (if using the story generation features of `main.py`)
   - `characterDescriptions.txt`: Character descriptions (used by `main.py` and the API)

## Video Generation API

This project also provides a FastAPI-based API for generating videos programmatically.

### Running the API Server

To start the API server, run the following command from the project root:
```bash
uvicorn api:app --reload
```
The API will be available at `http://127.0.0.1:8000` by default.

### API Endpoints

#### `POST /videos`
- **Purpose**: Submits a new video generation task.
- **Request Body**: JSON object containing `character_description` (string).
- **Example (`curl`)**:
  ```bash
  curl -X POST "http://127.0.0.1:8000/videos" -H "Content-Type: application/json" -d '{"character_description": "A curious robot exploring a lush forest"}'
  ```
- **Successful Response**: JSON object with `task_id` and `status` (e.g., `{"task_id": "some-uuid", "status": "processing", "message": "Video generation task started."}`).

#### `GET /videos/{task_id}`
- **Purpose**: Checks the status and result of a video generation task.
- **Example (`curl`)**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/videos/your_task_id_here"
  ```
- **Response**: JSON object with the task's current `status`. If completed, it includes the `video_path`. If failed, it includes an `error` message. (e.g., `{"task_id": "some-uuid", "status": "completed", "video_path": "short_story/story_video.mp4", "error": null, "details": null}`).

### API Documentation
Interactive API documentation (Swagger UI) is available at:
`http://127.0.0.1:8000/docs`

Alternative API documentation (ReDoc) is available at:
`http://127.0.0.1:8000/redoc`

## Command-Line Usage (main.py)

1. Run the application:
```bash
python main.py
```

2. The output will be organized in the following structure:
```
chapter_1/
  scene_1/
    scene_description.txt
    scene_image.png
    voice_over.wav
    background_music.wav
  scene_2/
    ...
chapter_2/
  ...
```

## Requirements

- Python 3.8+
- CUDA-capable GPU (recommended for image generation)
- At least 8GB of RAM
- 20GB of free disk space

## Notes

- The image generation uses Stable Diffusion, which requires a GPU for reasonable performance
- Voice-over generation uses the LJSpeech model
- Background music is currently generated as simple sine waves (can be enhanced with more sophisticated music generation) 