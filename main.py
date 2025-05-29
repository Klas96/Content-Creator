import os
from anthropic import Anthropic
import numpy as np
from scipy.io import wavfile
from generate_background_music import generate_background_music
from elevenlabs import ElevenLabs, Voice, VoiceSettings
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from stability_sdk import client as stability_client
import io
from PIL import Image
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import CompositeAudioClip
import re
import subprocess
from create_video import create_video
from generate_voice_over import generate_voice_over

# Test mode flag
TEST_MODE = True  # Set to False to use real APIs

# API Keys

# Initialize clients
anthropic_client = Anthropic(api_key=ANTHROPIC_KEY)
stability_client = stability_client.StabilityInference(key=STABILITY_KEY)

def create_mock_image(width=512, height=512, color=(100, 100, 200), text="Test Image"):
    """Create a simple test image with text."""
    img = Image.new('RGB', (width, height), color=color)
    return img

def create_mock_audio(duration=5, sample_rate=44100):
    """Create a simple sine wave audio file."""
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
    audio = (audio * 32767).astype(np.int16)  # Convert to 16-bit PCM
    return audio, sample_rate

def generate_mock_voice_over(text, output_path):
    """Create a mock voice-over file with a simple sine wave."""
    audio, sample_rate = create_mock_audio(duration=10)  # 10 seconds of audio
    wavfile.write(output_path, sample_rate, audio)

def generate_mock_image(prompt, output_path):
    """Create a mock image for testing."""
    img = create_mock_image(text=prompt[:20])  # Use first 20 chars of prompt as text
    img.save(output_path)

def load_text(directory, filename):
    file_path = os.path.join(directory, filename)
    with open(file_path, 'r') as f:
        text = f.read()
    return text

def create_video_task(character_description: str) -> str:
    # Create output directory
    output_dir = "short_story"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate story
    print("Generating story...")
    story = generate_short_story("", character_description) # Pass character_description here
    
    # Save story
    with open(os.path.join(output_dir, "story.txt"), 'w') as f:
        f.write(story)

    # Generate images for key scenes
    print("Generating images...")
    image_paths = []
    
    # Generate character portrait
    character_image_path = os.path.join(output_dir, "character.jpg")
    generate_image(f"Portrait of {character_description}, high quality digital art, detailed, professional photography", character_image_path)
    image_paths.append(character_image_path)
    
    # Generate scene images based on story paragraphs
    scene_prompts = create_scene_prompts(story)
    for i, prompt in enumerate(scene_prompts):
        scene_image_path = os.path.join(output_dir, f"scene_{i+1}.jpg")
        generate_image(prompt, scene_image_path)
        image_paths.append(scene_image_path)
    
    # Generate voice-over
    print("Generating voice-over...")
    voice_over_path = os.path.join(output_dir, "voice_over.mp3")
    if TEST_MODE:
        generate_mock_voice_over(story, voice_over_path.replace('.mp3', '.wav'))
    else:
        generate_voice_over(story, voice_over_path)
    
    # Generate background music (1 minute)
    print("Generating background music...")
    background_music_path = os.path.join(output_dir, "background_music.wav")
    generate_background_music(60, background_music_path)
    
    # Create video
    print("Creating video...")
    video_path = os.path.join(output_dir, "story_video.mp4")
    create_video(image_paths, voice_over_path, background_music_path, video_path)
    
    print(f"\nStory generation complete! All files are saved in the '{output_dir}' directory.")
    print("\nStory preview:")
    print("-" * 50)
    print(story[:200] + "...")
    print("-" * 50)
    return video_path

def generate_short_story(prompt, character_description):
    if TEST_MODE:
        # Return a test story
        return """Once upon a time, there was a brave knight named Arthur. He lived in a castle on a hill.

One day, Arthur decided to go on an adventure. He packed his sword and shield.

After many days of travel, Arthur found a magical forest. The trees sparkled in the sunlight."""
    
    story_prompt = f"""\n\nHuman: Create a short story (maximum 3 paragraphs) based on the following character description:
    {character_description}
    
    The story should be engaging and have a clear beginning, middle, and end.
    Focus on creating vivid imagery and emotional impact.

\n\nAssistant: I'll create a short story based on the character description."""
    
    response = anthropic_client.completions.create(
        prompt=story_prompt,
        model="claude-2",
        max_tokens_to_sample=1000,
        temperature=0.7
    )
    
    return response.completion

def generate_image(prompt, output_path):
    if TEST_MODE:
        return generate_mock_image(prompt, output_path)
        
    # Generate image using Stability AI API
    answers = stability_client.generate(
        prompt=prompt,
        seed=123,  # Fixed seed for reproducibility
        steps=30,  # Number of diffusion steps
        cfg_scale=7.0,  # How closely to follow the prompt
        width=512,
        height=512,
        samples=1,  # Number of images to generate
        sampler=generation.SAMPLER_K_DPMPP_2M  # Use a good default sampler
    )
    
    # Get the first image from the response
    for resp in answers:
        for artifact in resp.artifacts:
            if artifact.type == generation.ARTIFACT_IMAGE:
                # Convert the image data to a PIL Image
                img = Image.open(io.BytesIO(artifact.binary))
                # Save the image
                img.save(output_path)
                return

def create_scene_prompts(story):
    # Split story into paragraphs
    paragraphs = story.split('\n\n')
    prompts = []
    
    # Generate prompts for each paragraph
    for i, paragraph in enumerate(paragraphs):
        # Clean the paragraph text
        clean_text = re.sub(r'\s+', ' ', paragraph).strip()
        # Create a prompt for the scene
        prompt = f"Scene from the story: {clean_text[:200]}, cinematic, high quality digital art, detailed, professional photography"
        prompts.append(prompt)
    
    return prompts

def main():
    # Load character description
    character_description = load_text('input', 'characterDescriptions.txt')
    
    # Create video task
    video_path = create_video_task(character_description)
    
    # Print the path to the generated video
    print(f"Video created successfully: {video_path}")

if __name__ == "__main__":
    main()
