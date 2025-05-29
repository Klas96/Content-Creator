from elevenlabs import ElevenLabs
from config import TEST_MODE
import os

# Initialize ElevenLabs client
ELEVENLABS_KEY = os.getenv('ELEVENLABS_KEY')
eleven_client = None

if not TEST_MODE:
    if not ELEVENLABS_KEY:
        raise ValueError("ELEVENLABS_KEY not found in environment variables. Set it or run in TEST_MODE.")
    eleven_client = ElevenLabs(api_key=ELEVENLABS_KEY)

def generate_voice_over(text, output_path):
    if TEST_MODE:
        # Use mock generation in test mode
        # This import needs to be here to avoid circular dependency if main also imports this file's functions
        from main import generate_mock_voice_over 
        return generate_mock_voice_over(text, output_path)

    if not eleven_client:
        raise RuntimeError("ElevenLabs client not initialized. Ensure ELEVENLABS_KEY is set when not in TEST_MODE.")

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