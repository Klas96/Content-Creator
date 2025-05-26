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
   - Get an API key from Anthropic (https://console.anthropic.com)
   - Get an API key from Stability AI (https://stability.ai)
   - Update the API keys in `main.py`

4. Prepare your input files in the `input` directory:
   - `chapters.txt`: Your story chapters
   - `characterDescriptions.txt`: Character descriptions

## Usage

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