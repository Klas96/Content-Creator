import os
import numpy as np
from scipy.io import wavfile
from elevenlabs import ElevenLabs
from ..config import ELEVENLABS_KEY, TEST_MODE
from .base import ContentGenerator

def _create_mock_audio(duration=5, sample_rate=44100):
    """Helper function to create a simple sine wave audio file."""
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
    audio = (audio * 32767).astype(np.int16)  # Convert to 16-bit PCM
    return audio, sample_rate

class VoiceOverGenerator(ContentGenerator):
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.eleven_client = ElevenLabs(api_key=ELEVENLABS_KEY)
        self.output_path = None

    async def generate(self, text: str, output_path: str, **kwargs):
        """Generate voice-over for the story."""
        self.output_path = output_path
        self.status = "processing"
        try:
            if TEST_MODE:
                audio, sample_rate = _create_mock_audio(duration=10)  # 10 seconds of audio
                wavfile.write(self.output_path, sample_rate, audio)
                self.status = "completed"
                return

            # Generate audio using the text-to-speech endpoint
            # TODO: Make voice_id configurable
            audio_stream = self.eleven_client.text_to_speech.convert(
                text=text,
                voice_id="21m00Tcm4TlvDq8ikWAM"  # Rachel voice - professional narrator
            )

            # Convert generator to bytes
            audio_data = b''.join(chunk for chunk in audio_stream)

            # Save the audio
            with open(self.output_path, 'wb') as f:
                f.write(audio_data)
            self.status = "completed"
        except Exception as e:
            self.status = f"failed: {e}"
            # Potentially re-raise or handle more gracefully
            raise

    def get_status(self) -> str:
        if self.status == "completed":
            if self.output_path and os.path.exists(self.output_path):
                return "completed"
            else:
                return "failed: output file missing"
        return self.status

    def get_output(self):
        return self.output_path