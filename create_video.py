from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import CompositeAudioClip
import numpy as np

def create_video(image_paths, voice_over_path, background_music_path, output_path, fps=1):
    # Create video from images
    clip = ImageSequenceClip(image_paths, fps=fps)
    
    # Load audio files
    voice_over = AudioFileClip(voice_over_path)
    background_music = AudioFileClip(background_music_path)
    
    # If voice over is longer than background music, loop the background music
    if voice_over.duration > background_music.duration:
        # Calculate how many times we need to loop the background music
        n_loops = int(np.ceil(voice_over.duration / background_music.duration))
        # Create a looped version of the background music
        background_music = background_music.loop(n=n_loops)
        # Trim to match voice over duration
        background_music = background_music.subclipped(0, voice_over.duration)
    else:
        # If background music is longer, trim it to match voice over
        background_music = background_music.subclipped(0, voice_over.duration)
    
    # Combine audio tracks with adjusted volume
    final_audio = CompositeAudioClip([
        voice_over,
        background_music  # Adjust volume using set_volume
    ])
    
    # Set the audio of the video
    clip = clip.with_audio(final_audio)
    
    # Write the result to a file
    clip.write_videofile(output_path, codec='libx264', audio_codec='aac')