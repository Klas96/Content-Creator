import os
import numpy as np
from scipy.io import wavfile
from elevenlabs import ElevenLabs
from ..config import ELEVENLABS_KEY, TEST_MODE, ELEVENLABS_VOICES, DEFAULT_VOICE

eleven_client = ElevenLabs(api_key=ELEVENLABS_KEY)

def create_mock_audio(duration=5, sample_rate=44100):
    """Create a simple sine wave audio file."""
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
    audio = (audio * 32767).astype(np.int16)  # Convert to 16-bit PCM
    return audio, sample_rate

async def generate_voice_over(text: str, output_path: str, voice_name: str = None):
    """
    Generate voice-over for the text.
    
    Args:
        text (str): The text to convert to speech
        output_path (str): Where to save the audio file
        voice_name (str, optional): Name of the voice to use. Must be one of:
            - rachel (default): Professional female voice
            - domi: Professional female voice
            - bella: Professional female voice
            - antoni: Professional male voice
            - elli: Professional female voice
            - josh: Professional male voice
            - arnold: Professional male voice
            - adam: Professional male voice
            - sam: Professional male voice
    """
    if TEST_MODE:
        audio, sample_rate = create_mock_audio(duration=10)  # 10 seconds of audio
        wavfile.write(output_path, sample_rate, audio)
        return
    
    # Get the voice ID
    voice_name = voice_name.lower() if voice_name else DEFAULT_VOICE
    if voice_name not in ELEVENLABS_VOICES:
        print(f"Warning: Unknown voice '{voice_name}'. Using default voice '{DEFAULT_VOICE}'.")
        voice_name = DEFAULT_VOICE
    
    voice_id = ELEVENLABS_VOICES[voice_name]
    
    # Generate audio using the text-to-speech endpoint
    audio_stream = eleven_client.text_to_speech.convert(
        text=text,
        voice_id=voice_id
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