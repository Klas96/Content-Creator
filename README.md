# Content Creator

An AI-powered application that generates various types of content including stories, educational videos, podcasts, articles, tweet threads, and book chapters.

## Features

- Multiple content generation types:
  - Stories with images, voice-over, and background music
  - Educational videos with customizable style and difficulty
  - Podcasts (custom text, topic-based, or free generation)
  - Articles with customizable style and length
  - Tweet threads with configurable number of tweets
  - Book chapters with plot and character support

- Advanced AI Integration:
  - Content generation using Claude AI
  - Image generation using Stable Diffusion
  - Text-to-speech voice-over
  - Background music generation
  - Organized output in structured directories

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
   - Get an API key from Anthropic (https://console.anthropic.com)
   - Get an API key from Stability AI (https://stability.ai)
   - Update the API keys in `config.py`

4. Create necessary directories:
```bash
mkdir -p static/videos static/thumbnails static/audios
```

## API Usage

The application provides a REST API with the following endpoints:

### Content Generation

1. Generate content:
```bash
POST /generate
```
Request body:
```json
{
  "content_type": "story|educational|podcast|article|tweet_thread|book_chapter",
  "topic": "your topic or character description",
  "video_prompt": "optional video prompt",
  "educational_style": "lecture|tutorial|explainer",
  "difficulty_level": "beginner|intermediate|advanced",
  "podcast_options": {
    "podcast_type": "custom_text|topic_based|free_generation",
    "custom_text": "optional custom text",
    "topic": "optional topic"
  },
  "article_options": {
    "custom_instructions": "optional instructions"
  },
  "tweet_options": {
    "num_tweets": 3,
    "call_to_action": "optional CTA"
  },
  "book_chapter_options": {
    "plot_summary": "optional plot summary",
    "chapter_topic": "optional chapter topic",
    "previous_chapter_summary": "optional previous chapter",
    "characters": ["character1", "character2"],
    "genre": "optional genre"
  },
  "desired_length_words": 0,
  "style_tone": "optional style"
}
```

2. Check generation status:
```bash
GET /status/{job_id}
```

3. Download generated content:
```bash
GET /download/{job_id}
```

4. Get podcast information (for podcast content):
```bash
GET /podcast/{job_id}/info
```

### Output Structure

The generated content is organized in the following structure:
```
output/
  {job_id}/
    content.txt (or podcast_script.txt, article.txt, etc.)
    content_video.mp4 (for video content)
    podcast_audio.mp3 (for podcast content)
    images/
      scene_1.png
      scene_2.png
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
- Background music is generated using advanced audio synthesis
- All content is generated asynchronously and can be monitored via the status endpoint
- Generated content is automatically cleaned up after 24 hours

## Running the Application

1. Start the server:
```bash
uvicorn app.main:app --reload
```

The server will start on `http://127.0.0.1:8000` by default.

### Troubleshooting

If you see the error `[Errno 98] Address already in use`, it means another instance of the server is already running. You can:

1. Find and stop the existing process:
```bash
# Find the process using port 8000
lsof -i :8000
# Kill the process (replace PID with the process ID from above)
kill PID
```

2. Or use a different port:
```bash
uvicorn app.main:app --reload --port 8001
``` 