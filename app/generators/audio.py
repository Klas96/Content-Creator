import os
import re # Added for parsing speaker lines
import shutil # Added for temp_dir cleanup
import numpy as np
from scipy.io import wavfile
from pydub import AudioSegment # Added for audio concatenation
from elevenlabs import ElevenLabs
from typing import Optional, List # List for type hint
from ..config import ELEVENLABS_KEY, TEST_MODE

eleven_client = ElevenLabs(api_key=ELEVENLABS_KEY)

def create_mock_audio(duration=5, sample_rate=44100, file_path: Optional[str] = None):
    """
    Create a simple sine wave audio.
    Optionally saves it to a file if file_path is provided.
    """
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
    audio = (audio * 32767).astype(np.int16)  # Convert to 16-bit PCM

    if file_path:
        wavfile.write(file_path, sample_rate, audio)

    return audio, sample_rate

async def generate_voice_over(text: str, output_path: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM"):
    """Generate voice-over for the text using a specific voice_id."""
    if TEST_MODE:
        print(f"TEST_MODE: Would use voice_id '{voice_id}' for text: '{text[:50]}...'")
        create_mock_audio(duration=3, file_path=output_path) # Shorter mock for segments
        return
    
    # Generate audio using the text-to-speech endpoint
    audio_stream = eleven_client.text_to_speech.convert(
        text=text,
        voice_id=voice_id  # Use the provided voice_id
    )
    
    # Convert generator to bytes
    audio_data = b''.join(chunk for chunk in audio_stream)
    
    # Save the audio
    with open(output_path, 'wb') as f:
        f.write(audio_data)

async def generate_dialogue_audio(script_text: str, speaker_voice_ids: List[str], output_path: str, temp_dir: str = "temp_audio_segments"):
    """
    Generates dialogue audio from a script with multiple speakers.
    Each speaker line should be prefixed e.g., "Speaker A: ..." or "Speaker 1: ..."
    """
    if not speaker_voice_ids or len(speaker_voice_ids) < 1:
        raise ValueError("speaker_voice_ids must contain at least one voice ID.")

    os.makedirs(temp_dir, exist_ok=True)
    segment_paths = []
    combined_audio = AudioSegment.empty()

    try:
        if TEST_MODE:
            print(f"TEST_MODE: Generating dialogue audio for script: '{script_text[:100]}...'")
            print(f"TEST_MODE: Speaker voice IDs: {speaker_voice_ids}")
            print(f"TEST_MODE: Temp directory: {temp_dir}")

            # Simulate parsing and segment generation
            mock_speaker_lines = [
                ("Speaker A", "This is a test line for speaker A."),
                ("Speaker B", "And this is speaker B responding."),
                ("Speaker A", "Okay, sounds good.")
            ]
            if len(speaker_voice_ids) < 2: # Adjust if only one voice_id provided for test
                 mock_speaker_lines = [
                    ("Speaker A", "This is a test line for speaker A."),
                    ("Speaker A", "And this is speaker A again."),
                    ("Speaker A", "Okay, sounds good.")
                ]


            for i, (speaker_tag, line_text) in enumerate(mock_speaker_lines):
                segment_path = os.path.join(temp_dir, f"segment_{i}_{speaker_tag.replace(' ', '_')}.wav")
                # Determine voice_id based on speaker_tag (simplified for test)
                voice_idx = 0 if "A" in speaker_tag or "1" in speaker_tag else (1 if len(speaker_voice_ids) > 1 else 0)
                actual_voice_id = speaker_voice_ids[voice_idx % len(speaker_voice_ids)]
                print(f"TEST_MODE: Generating mock segment {i} for {speaker_tag} with voice {actual_voice_id} at {segment_path}")
                create_mock_audio(duration=2, file_path=segment_path) # Short mock segments
                segment_paths.append(segment_path)

            # Simulate concatenation
            print(f"TEST_MODE: Concatenating {len(segment_paths)} mock segments.")
            for segment_path in segment_paths:
                segment_audio = AudioSegment.from_wav(segment_path)
                combined_audio += segment_audio

            # Simulate export
            # In TEST_MODE, create_mock_audio creates WAV, so we export combined as WAV too.
            # If output_path is .mp3, pydub would need ffmpeg, let's keep it simple.
            final_output_path = output_path
            if not final_output_path.lower().endswith(".wav"):
                final_output_path += ".wav" # Ensure it's wav for mock
            print(f"TEST_MODE: Exporting combined mock audio to {final_output_path}")
            combined_audio.export(final_output_path, format="wav")
            print(f"TEST_MODE: Mock dialogue audio generated at {final_output_path}")

        else: # Non-TEST_MODE
            # Simple parsing: "Speaker X: Dialogue"
            # More robust parsing might be needed for complex cases.
            lines = script_text.strip().split('\n')
            speaker_pattern = re.compile(r"^(Speaker\s+[A-Za-z0-9]+):\s*(.*)")

            current_speaker_map = {} # Maps "Speaker A" to voice_ids index

            for i, line in enumerate(lines):
                match = speaker_pattern.match(line)
                if not match:
                    print(f"Warning: Skipping line due to format mismatch: {line}")
                    continue

                speaker_tag = match.group(1) # e.g., "Speaker A"
                dialogue_text = match.group(2)

                if not dialogue_text.strip():
                    print(f"Warning: Skipping empty dialogue for {speaker_tag}")
                    continue

                if speaker_tag not in current_speaker_map:
                    # Assign next available voice_id to new speaker tag
                    if len(current_speaker_map) < len(speaker_voice_ids):
                        current_speaker_map[speaker_tag] = len(current_speaker_map)
                    else:
                        # If more speaker tags than voice_ids, cycle through voice_ids
                        print(f"Warning: More speaker tags than available voice IDs. Reusing voice IDs for {speaker_tag}.")
                        current_speaker_map[speaker_tag] = len(current_speaker_map) % len(speaker_voice_ids)

                voice_idx = current_speaker_map[speaker_tag]
                actual_voice_id = speaker_voice_ids[voice_idx]

                segment_filename = f"segment_{i}_{speaker_tag.replace(' ', '_').replace(':', '')}.mp3"
                segment_path = os.path.join(temp_dir, segment_filename)

                print(f"Generating segment {i} for {speaker_tag} with voice {actual_voice_id}...")
                await generate_voice_over(dialogue_text, segment_path, actual_voice_id)
                segment_paths.append(segment_path)

            # Concatenate segments
            print(f"Concatenating {len(segment_paths)} audio segments...")
            for segment_path in segment_paths:
                # Assuming generate_voice_over saves as mp3 if not in test_mode
                segment_audio = AudioSegment.from_mp3(segment_path)
                combined_audio += segment_audio

            # Export combined audio
            print(f"Exporting combined audio to {output_path}...")
            combined_audio.export(output_path, format="mp3")
            print(f"Dialogue audio successfully generated at {output_path}")

    except Exception as e:
        print(f"Error generating dialogue audio: {e}")
        # Optionally re-raise or handle more gracefully
        raise
    finally:
        if os.path.exists(temp_dir):
            print(f"Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)


async def generate_background_music(duration: int, output_path: str):
    """Generate background music."""
    if TEST_MODE:
        create_mock_audio(duration=duration, file_path=output_path) # Use modified mock audio
        return
    
    # TODO: Implement real background music generation
    # For now, just create a mock audio file
    create_mock_audio(duration=duration, file_path=output_path) # Use modified mock audio