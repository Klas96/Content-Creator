import asyncio
import os
from typing import Literal, Optional, Dict

from ..config import TEST_MODE, ELEVENLABS_KEY, ANTHROPIC_KEY # ANTHROPIC_KEY needed if llm_clients doesn't handle it
from ..llm_clients import generate_text_completion # Assuming this uses ANTHROPIC_KEY internally
from .base import ContentGenerator
from elevenlabs import ElevenLabs
# For mock audio in TEST_MODE
import numpy as np
from scipy.io import wavfile

def _create_mock_audio_file(output_path: str, duration=5, sample_rate=44100):
    """Helper function to create a simple sine wave audio file for testing."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    audio = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
    audio = (audio * 32767 / np.max(np.abs(audio))).astype(np.int16) # Normalize and convert to 16-bit PCM
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    wavfile.write(output_path, sample_rate, audio)

class PodcastGenerator(ContentGenerator):
    def __init__(self, config: dict = None):
        super().__init__(config)
        # Assuming generate_text_completion uses Anthropic client internally,
        # no separate anthropic_client needed here unless direct access is required.
        # self.anthropic_client = Anthropic(api_key=ANTHROPIC_KEY) # If needed
        self.eleven_client = ElevenLabs(api_key=ELEVENLABS_KEY)
        self.script_path = None
        self.audio_path = None

    async def _generate_script(self, podcast_type: str, custom_text: Optional[str], topic: Optional[str]) -> str:
        if podcast_type == "custom_text":
            if not custom_text:
                raise ValueError("Custom text must be provided for 'custom_text' podcast type.")
            if TEST_MODE:
                return f"Test mode: Custom text received: {custom_text}"
            return custom_text

        elif podcast_type == "topic_based":
            if not topic:
                raise ValueError("Topic must be provided for 'topic_based' podcast type.")
            if TEST_MODE:
                return f"Test mode: Podcast script for topic: {topic}"
            prompt_template = """Human: You are a podcast scriptwriter. Generate an engaging and informative podcast script about the topic: {topic}. The script should be approximately 3-5 minutes in reading length. Structure it with a brief introduction, a main body discussing key aspects of the topic, and a short conclusion. Make it conversational.

Assistant: Here's a podcast script about {topic}:"""
            prompt = prompt_template.format(topic=topic)

        elif podcast_type == "free_generation":
            if TEST_MODE:
                return "Test mode: Freeform podcast script generated."
            prompt = """Human: You are a creative podcast scriptwriter. Generate an engaging podcast script on any interesting topic of your choice. The script should be suitable for a general audience, approximately 3-5 minutes in reading length, and have a clear narrative or informational flow. Surprise me with your creativity!

Assistant: Here's a podcast script on an interesting topic:"""
        else:
            raise ValueError(f"Invalid podcast_type: {podcast_type}")

        try:
            # TODO: Make model, max_tokens, temperature configurable via self.config
            generated_script = await generate_text_completion(
                prompt=prompt,
                temperature=0.7,
                max_tokens=2000
            )
            if generated_script.startswith("Error:"):
                raise Exception(generated_script)
            return generated_script
        except Exception as e:
            # Log error or handle more gracefully
            raise Exception(f"Error generating podcast script: {e}")


    async def _generate_audio_for_script(self, script_text: str, output_audio_path: str):
        os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)
        if TEST_MODE:
            _create_mock_audio_file(output_audio_path, duration=len(script_text) // 15) # Approx duration
            return

        try:
            # TODO: Make voice_id configurable via self.config
            audio_stream = self.eleven_client.text_to_speech.convert(
                text=script_text,
                voice_id="21m00Tcm4TlvDq8ikWAM"  # Example voice: Rachel
            )

            audio_data = b''.join(chunk for chunk in audio_stream)

            with open(output_audio_path, 'wb') as f:
                f.write(audio_data)
        except Exception as e:
            # Log error or handle more gracefully
            raise Exception(f"Error generating audio for podcast script: {e}")

    async def generate(
        self,
        podcast_type: Literal["custom_text", "topic_based", "free_generation"],
        output_script_path: str,
        output_audio_path: str,
        custom_text: Optional[str] = None,
        topic: Optional[str] = None,
        **kwargs
    ) -> Dict[str, str]:
        self.status = "processing"
        self.script_path = output_script_path
        self.audio_path = output_audio_path

        script_content = ""
        try:
            # 1. Generate Script
            script_content = await self._generate_script(podcast_type, custom_text, topic)
            os.makedirs(os.path.dirname(self.script_path), exist_ok=True)
            with open(self.script_path, "w", encoding="utf-8") as f:
                f.write(script_content)

            # 2. Generate Audio from Script
            await self._generate_audio_for_script(script_content, self.audio_path)

            self.status = "completed"
            self.output = {"script_path": self.script_path, "audio_path": self.audio_path} # self.output from base
            return self.output
        except Exception as e:
            self.status = f"failed: {e}"
            # Clean up partial files if any error occurs
            if os.path.exists(self.script_path) and not script_content : # script failed before write
                 pass # no script to clean
            if os.path.exists(self.audio_path) and self.status.startswith("failed"): # audio failed
                try: os.remove(self.audio_path)
                except OSError: pass
            # If script writing failed, it might not exist or be partial.
            # If script succeeded but audio failed, script remains. This behavior can be adjusted.
            raise

    def get_status(self) -> str:
        if self.status == "completed":
            script_ok = self.script_path and os.path.exists(self.script_path)
            audio_ok = self.audio_path and os.path.exists(self.audio_path)
            if script_ok and audio_ok:
                return "completed"
            elif not script_ok:
                self.status = "failed: output script file missing"
            elif not audio_ok:
                self.status = "failed: output audio file missing"
        return self.status

    def get_output(self):
        if self.script_path and self.audio_path:
            return {"script_path": self.script_path, "audio_path": self.audio_path}
        return None

# Keep the __main__ block for potential direct testing if desired,
# but update it to use the new class structure.
if __name__ == '__main__':
    async def main_test():
        if TEST_MODE:
            print("Running PodcastGenerator in TEST_MODE")

        podcast_gen = PodcastGenerator()

        # Test custom text
        print("\n--- Custom Text Podcast ---")
        try:
            output_paths_custom = await podcast_gen.generate(
                podcast_type="custom_text",
                custom_text="This is a test script for our custom podcast.",
                output_script_path="output/podcast_custom/script.txt",
                output_audio_path="output/podcast_custom/audio.wav"
            )
            print(f"Custom Podcast Output: {output_paths_custom}, Status: {podcast_gen.get_status()}")
        except Exception as e:
            print(f"Error in custom podcast generation: {e}")

        # Test topic-based
        print("\n--- Topic-Based Podcast (e.g., 'The Wonders of Space Exploration') ---")
        try:
            output_paths_topic = await podcast_gen.generate(
                podcast_type="topic_based",
                topic="The Wonders of Space Exploration",
                output_script_path="output/podcast_topic/script.txt",
                output_audio_path="output/podcast_topic/audio.wav"
            )
            print(f"Topic Podcast Output: {output_paths_topic}, Status: {podcast_gen.get_status()}")
        except Exception as e:
            print(f"Error in topic-based podcast generation: {e}")

        # Test free generation
        print("\n--- Freeform Podcast ---")
        try:
            output_paths_free = await podcast_gen.generate(
                podcast_type="free_generation",
                output_script_path="output/podcast_free/script.txt",
                output_audio_path="output/podcast_free/audio.wav"
            )
            print(f"Freeform Podcast Output: {output_paths_free}, Status: {podcast_gen.get_status()}")
        except Exception as e:
            print(f"Error in freeform podcast generation: {e}")

    asyncio.run(main_test())
