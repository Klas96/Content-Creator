import os
import numpy as np
from scipy.io import wavfile
from typing import Optional

from .base import ContentGenerator
from ..config import TEST_MODE

class MusicGenerator(ContentGenerator):
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.music_path = None
        # self.status is initialized in ContentGenerator base class to "pending"

    def _create_placeholder_music(self, duration: int, output_path: str, sample_rate: int = 44100, tempo: int = 120, genre: str = "electronic"):
        """
        Generates a simple placeholder music track.
        Varies slightly based on genre.
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

            # Base frequency (e.g., A4)
            base_freq = 440

            # Simple rhythmic pattern (beats per second)
            bps = tempo / 60

            signal = np.zeros_like(t)

            if genre == "electronic":
                # Simple arpeggiated sequence for electronic
                notes_in_beat = 4 # 16th notes
                for i in range(int(duration * bps * notes_in_beat)):
                    note_start_time = i / (bps * notes_in_beat)
                    note_duration = 1 / (bps * notes_in_beat * 2) # Staccato
                    if note_start_time + note_duration > duration:
                        break

                    freq_multiplier = (i % 4 + 1) * 0.5 + 0.5 # Simple arpeggio: C, E, G, C higher
                    current_freq = base_freq * (2**(((i%12) + 3)/12)) # Chromatic scale notes

                    note_indices = (t >= note_start_time) & (t < note_start_time + note_duration)
                    signal[note_indices] = np.sin(2 * np.pi * current_freq * t[note_indices])
                # Add a simple kick drum like beat
                for beat in range(int(duration * bps)):
                    beat_time = beat / bps
                    kick_indices = (t >= beat_time) & (t < beat_time + 0.05) # Short kick
                    signal[kick_indices] += np.sin(2 * np.pi * 60 * t[kick_indices]) * 0.5 # Low freq

            elif genre == "ambient":
                # Slow changing sine waves for ambient
                freq1 = base_freq / 4
                freq2 = base_freq / 2
                signal = (np.sin(2 * np.pi * freq1 * t) + np.sin(2 * np.pi * freq2 * t * 1.05)) * 0.5 # Slight detune for chorus
            else: # Default simple tone
                signal = np.sin(2 * np.pi * base_freq * t)

            # Normalize and convert to 16-bit PCM
            if np.max(np.abs(signal)) == 0: # Avoid division by zero if signal is silent
                audio = np.zeros_like(signal, dtype=np.int16)
            else:
                audio = (signal / np.max(np.abs(signal)) * 32767).astype(np.int16)

            wavfile.write(output_path, sample_rate, audio)
            self.status = "completed"
        except Exception as e:
            self.status = f"failed: {e}"
            # print(f"Error in _create_placeholder_music: {e}") # For debugging

    async def generate(self, output_path: str, duration: int = 60, tempo: int = 120, genre: str = "electronic", mood: Optional[str] = None, **kwargs):
        self.status = "processing"
        self.music_path = output_path # Store early

        actual_duration = duration
        if TEST_MODE:
            actual_duration = 2 # Short duration for testing

        try:
            # In a real scenario, this might involve more complex async operations or API calls
            # For now, the placeholder generation is synchronous but called from an async method
            # If _create_placeholder_music was truly async, we'd await it.
            # For now, we run it synchronously. If it were I/O bound, we could use asyncio.to_thread

            # Using a direct call as it's CPU bound and relatively quick for short durations
            self._create_placeholder_music(actual_duration, output_path, tempo=tempo, genre=genre)

            if self.status == "completed":
                self.music_path = output_path
                self.output = output_path # self.output is from base ContentGenerator
            else: # Placeholder creation failed
                self.music_path = None
                self.output = None
                # Status already set by _create_placeholder_music
        except Exception as e:
            self.status = f"failed: {e}"
            self.music_path = None
            self.output = None
            # print(f"Error in generate: {e}") # For debugging

        return self.music_path


    def get_status(self) -> str:
        # Check file existence only if status claims completion
        if self.status == "completed":
            if self.music_path and os.path.exists(self.music_path):
                return "completed"
            else:
                # This implies status was set to completed, but file is not found.
                self.status = "failed: output file missing"
        return self.status

    def get_output(self):
        # Return path only if generation was successful and path is set
        if self.status == "completed" and self.music_path and os.path.exists(self.music_path):
            return self.music_path
        return None
