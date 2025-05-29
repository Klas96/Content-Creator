import os
import numpy as np
from scipy.io import wavfile
from elevenlabs import ElevenLabs
from ..config import ELEVENLABS_KEY, TEST_MODE

eleven_client = ElevenLabs(api_key=ELEVENLABS_KEY)

def create_mock_audio(duration=5, sample_rate=44100):
    """Create a simple sine wave audio file."""
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
    audio = (audio * 32767).astype(np.int16)  # Convert to 16-bit PCM
    return audio, sample_rate

async def generate_voice_over(text: str, output_path: str):
    """Generate voice-over for the story."""
    if TEST_MODE:
        audio, sample_rate = create_mock_audio(duration=10)  # 10 seconds of audio
        wavfile.write(output_path, sample_rate, audio)
        return
    
    # Generate audio using the text-to-speech endpoint
    audio_stream = eleven_client.text_to_speech.convert(
        text=text,
        voice_id="21m00Tcm4TlvDq8ikWAM"  # Rachel voice - professional narrator
    )
    
    # Convert generator to bytes
    audio_data = b''.join(chunk for chunk in audio_stream)
    
    # Save the audio
    with open(output_path, 'wb') as f:
        f.write(audio_data)

async def generate_background_music(duration: int, output_path: str):
    """Generate background music."""
    if TEST_MODE:
        audio, sample_rate = create_mock_audio(duration=duration)
        wavfile.write(output_path, sample_rate, audio)
        return
    
    # TODO: Implement real background music generation
    # For now, just create a mock audio file
    audio, sample_rate = create_mock_audio(duration=duration)
    wavfile.write(output_path, sample_rate, audio)