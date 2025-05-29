from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import CompositeAudioClip, AudioClip
import numpy as np
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

def create_video(image_paths, voice_over_path, background_music_path, output_path, video_prompt=None, content_type=None, fps=1):
    """
    Create a video from images, voice-over, and background music.
    
    Args:
        image_paths (list): List of paths to images
        voice_over_path (str): Path to voice-over audio file
        background_music_path (str): Path to background music file
        output_path (str): Path where the output video will be saved
        video_prompt (str, optional): Custom instructions for video generation
        content_type (str, optional): Type of content ("story" or "educational")
        fps (int, optional): Frames per second. Defaults to 1.
    """
    # Verify all input files exist
    for path in [voice_over_path, background_music_path] + image_paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Required file not found: {path}")
    
    # Create video from images
    clip = ImageSequenceClip(image_paths, fps=fps)
    
    try:
        # Load audio files
        voice_over = AudioFileClip(voice_over_path)
        background_music = AudioFileClip(background_music_path)
        
        # If voice over is longer than background music, loop the background music
        if voice_over.duration > background_music.duration:
            # Calculate how many times we need to loop the background music
            n_loops = int(np.ceil(voice_over.duration / background_music.duration))
            # Create a looped version of the background music
            background_music = background_music.loop(n=n_loops)
            # Adjust background music duration to match voice over
            background_music = background_music.resize(voice_over.duration)
        
        # Set volume factors based on content type
        voice_volume = 1.0  # Full volume for voice
        music_volume = 0.3 if content_type == "educational" else 0.5  # Lower for educational content
        
        # Create volume-adjusted audio clips
        def make_voice_audio(t):
            return voice_over.get_frame(t) * voice_volume
            
        def make_music_audio(t):
            return background_music.get_frame(t) * music_volume
        
        # Create new audio clips with the volume adjustment functions
        voice_audio = AudioClip(make_voice_audio, duration=voice_over.duration)
        music_audio = AudioClip(make_music_audio, duration=background_music.duration)
        
        # Combine audio tracks
        final_audio = CompositeAudioClip([voice_audio, music_audio])
        
        # Set the audio of the video
        clip = clip.with_audio(final_audio)
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write the result to a file
        clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        return output_path
    
    finally:
        # Clean up resources
        if 'voice_over' in locals():
            voice_over.close()
        if 'background_music' in locals():
            background_music.close()
        if 'clip' in locals():
            clip.close()

async def create_video_async(image_paths, voice_over_path, background_music_path, output_path, video_prompt=None, content_type=None, fps=1):
    """
    Asynchronous wrapper for create_video function.
    """
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(
            pool,
            create_video,
            image_paths,
            voice_over_path,
            background_music_path,
            output_path,
            video_prompt,
            content_type,
            fps
        )