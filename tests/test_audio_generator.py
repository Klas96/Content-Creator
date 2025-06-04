import pytest
import asyncio
import os
import shutil
from typing import Optional, List
from unittest.mock import AsyncMock, patch, MagicMock, mock_open

from pydub import AudioSegment
from scipy.io import wavfile # For reading mock audio data if needed
import numpy as np

# Module to test
from app.generators.audio import generate_voice_over, generate_dialogue_audio, create_mock_audio
from app.config import TEST_MODE as APP_TEST_MODE # To control global test mode if needed, or patch locally

# Pytest needs to discover async tests
pytestmark = pytest.mark.asyncio

# --- Fixtures ---
@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for test outputs."""
    output_dir = tmp_path / "audio_outputs"
    output_dir.mkdir()
    yield str(output_dir)
    # shutil.rmtree(output_dir) # tmp_path fixture handles cleanup

@pytest.fixture
def temp_segment_dir(tmp_path):
    """Create a temporary directory for audio segments."""
    segment_dir = tmp_path / "segments"
    segment_dir.mkdir()
    yield str(segment_dir)
    # shutil.rmtree(segment_dir) # tmp_path fixture handles cleanup

# --- Tests for create_mock_audio ---

def test_create_mock_audio_returns_data(temp_output_dir):
    """Test that create_mock_audio returns audio data and sample rate."""
    audio, sample_rate = create_mock_audio(duration=0.1)
    assert isinstance(audio, np.ndarray)
    assert audio.ndim == 1 # Mono
    assert len(audio) > 0
    assert sample_rate == 44100 # Default sample rate

def test_create_mock_audio_saves_file(temp_output_dir):
    """Test that create_mock_audio saves a file when file_path is provided."""
    duration = 0.05 # Short duration for quick test
    sample_rate = 22050 # Non-default sample rate
    file_path = os.path.join(temp_output_dir, "mock_audio.wav")

    audio_data, sr = create_mock_audio(duration=duration, sample_rate=sample_rate, file_path=file_path)

    assert os.path.exists(file_path), "Audio file was not created"
    assert os.path.getsize(file_path) > 0, "Audio file is empty"

    # Optionally, read it back and verify properties
    sr_read, data_read = wavfile.read(file_path)
    assert sr_read == sample_rate
    assert len(data_read) == int(duration * sample_rate)
    assert data_read.dtype == np.int16

    # Check returned data matches saved data characteristics
    assert sr == sample_rate
    assert len(audio_data) == int(duration * sample_rate)

def test_create_mock_audio_no_save_if_no_path():
    """Test that create_mock_audio does not attempt to save if no path is given."""
    # We can't directly check for "no save occurred" easily without file system mocks,
    # but we can ensure it runs without error and returns data.
    # The main check is that it doesn't REQUIRE file_path.
    audio, sr = create_mock_audio(duration=0.01)
    assert audio is not None
    assert sr is not None
    # No assertion about file creation here

# --- Tests for generate_voice_over ---

@patch('app.generators.audio.eleven_client.text_to_speech.convert')
@patch('builtins.open', new_callable=mock_open)
async def test_generate_voice_over_normal_mode(mock_file_open, mock_eleven_convert, temp_output_dir):
    """Test generate_voice_over in normal mode with mocked ElevenLabs client."""
    with patch('app.generators.audio.TEST_MODE', False):
        text_to_speak = "Hello, this is a voice over test."
        output_path = os.path.join(temp_output_dir, "voice_over.mp3")
        test_voice_id = "test_voice_123"

        # Simulate the stream of bytes from ElevenLabs
        mock_audio_chunks = [b"chunk1", b"chunk2", b"chunk3"]
        mock_eleven_convert.return_value = mock_audio_chunks

        await generate_voice_over(text_to_speak, output_path, voice_id=test_voice_id)

        mock_eleven_convert.assert_called_once_with(text=text_to_speak, voice_id=test_voice_id)
        mock_file_open.assert_called_once_with(output_path, 'wb')

        # Check that write was called with the concatenated chunks
        handle = mock_file_open()
        handle.write.assert_called_once_with(b"chunk1chunk2chunk3")

@patch('app.generators.audio.print') # To capture print statements
@patch('app.generators.audio.create_mock_audio')
async def test_generate_voice_over_test_mode(mock_create_audio, mock_print, temp_output_dir):
    """Test generate_voice_over in TEST_MODE."""
    with patch('app.generators.audio.TEST_MODE', True):
        text_to_speak = "Test mode voice over."
        output_path = os.path.join(temp_output_dir, "test_voice_over.wav") # Test mode creates wav
        test_voice_id = "test_voice_456"

        # Ensure create_mock_audio doesn't actually save a file here, just that it's called
        mock_create_audio.return_value = (np.array([1,2,3]), 44100)


        await generate_voice_over(text_to_speak, output_path, voice_id=test_voice_id)

        # Check that create_mock_audio was called with the output_path
        # The duration is fixed at 3 in the generate_voice_over's TEST_MODE
        mock_create_audio.assert_called_once_with(duration=3, file_path=output_path)

        # Check that the print statement includes the voice_id and text
        mock_print.assert_any_call(f"TEST_MODE: Would use voice_id '{test_voice_id}' for text: '{text_to_speak[:50]}...'")

        # In TEST_MODE, generate_voice_over directly calls create_mock_audio to save the file.
        # So, we expect the file to exist if create_mock_audio was not fully mocked to prevent saving.
        # For this test, we're verifying create_mock_audio was called correctly.
        # If we want to ensure the file is written by the *actual* create_mock_audio in test mode,
        # we would not mock create_mock_audio itself, but let it run.
        # Since create_mock_audio is already tested separately for file saving,
        # mocking it here is fine to isolate the logic of generate_voice_over.

# --- Tests for generate_dialogue_audio ---

@patch('app.generators.audio.print') # To capture print statements
@patch('app.generators.audio.create_mock_audio') # To verify calls for segments
@patch('pydub.AudioSegment.from_wav') # To mock loading segments
@patch('pydub.AudioSegment.export') # To mock final export
async def test_generate_dialogue_audio_test_mode(
    mock_audio_export, mock_audio_from_wav, mock_create_segment_audio, mock_print,
    temp_output_dir, temp_segment_dir
):
    """Test generate_dialogue_audio in TEST_MODE."""
    with patch('app.generators.audio.TEST_MODE', True):
        script_text = "Speaker A: Hello.\nSpeaker B: Hi there.\nSpeaker A: How are you?"
        speaker_voice_ids = ["voice_a_test", "voice_b_test"]
        output_path = os.path.join(temp_output_dir, "dialogue_test_mode.wav") # Test mode saves as wav

        # Mock AudioSegment instances returned by from_wav
        mock_segment = MagicMock(spec=AudioSegment)
        mock_segment.duration = 1000 # milliseconds
        def side_effect_from_wav(path):
            # print(f"Mock from_wav called with {path}")
            return mock_segment
        mock_audio_from_wav.side_effect = side_effect_from_wav

        # Mock the '+' operation for AudioSegment if it's not automatically handled by MagicMock spec
        # This helps simulate concatenation
        accumulated_audio_mock = MagicMock(spec=AudioSegment)
        accumulated_audio_mock.duration = 0
        def mock_add(other_segment):
            accumulated_audio_mock.duration += other_segment.duration
            return accumulated_audio_mock

        # For the initial AudioSegment.empty()
        empty_segment_mock = MagicMock(spec=AudioSegment)
        empty_segment_mock.duration = 0
        empty_segment_mock.__add__ = mock_add # type: ignore

        with patch('pydub.AudioSegment.empty', return_value=empty_segment_mock):
            await generate_dialogue_audio(script_text, speaker_voice_ids, output_path, temp_dir=temp_segment_dir)

        # Assertions for create_mock_audio (used for segments in test mode)
        # Expected 3 lines = 3 segments from the mock_speaker_lines in generate_dialogue_audio's TEST_MODE
        assert mock_create_segment_audio.call_count == 3
        for i, call_args in enumerate(mock_create_segment_audio.call_args_list):
            args, kwargs = call_args
            assert kwargs['duration'] == 2 # Duration for mock segments in test mode is 2s
            expected_segment_path = os.path.join(temp_segment_dir, f"segment_{i}_") # Path prefix
            assert kwargs['file_path'].startswith(expected_segment_path)
            # Check that a .wav extension is used for segments
            assert kwargs['file_path'].endswith(".wav")


        # Assertions for AudioSegment.from_wav
        assert mock_audio_from_wav.call_count == 3 # For each mock segment created

        # Assertion for final export
        # The output path might be adjusted to .wav in TEST_MODE if not already.
        expected_export_path = output_path
        if not expected_export_path.lower().endswith(".wav"):
             expected_export_path += ".wav"
        mock_audio_export.assert_called_once()
        args, kwargs = mock_audio_export.call_args
        # The first argument to export is the AudioSegment object itself
        # The second is the path, the third is the format
        assert args[1] == expected_export_path
        assert kwargs['format'] == "wav"


        # Assert that temp_dir is cleaned up
        assert not os.path.exists(temp_segment_dir), "Temporary segment directory was not cleaned up"

        # Check print logs for key information
        mock_print.assert_any_call(f"TEST_MODE: Generating dialogue audio for script: '{script_text[:100]}...'")
        mock_print.assert_any_call(f"TEST_MODE: Speaker voice IDs: {speaker_voice_ids}")
        mock_print.assert_any_call(f"TEST_MODE: Temp directory: {temp_segment_dir}")
        mock_print.assert_any_call(f"TEST_MODE: Concatenating 3 mock segments.")
        mock_print.assert_any_call(f"TEST_MODE: Exporting combined mock audio to {expected_export_path}")
        mock_print.assert_any_call(f"Cleaning up temporary directory: {temp_segment_dir}")


@patch('app.generators.audio.generate_voice_over', new_callable=AsyncMock)
@patch('pydub.AudioSegment.from_mp3') # Assuming normal mode generates mp3 segments via generate_voice_over
@patch('pydub.AudioSegment.export')
async def test_generate_dialogue_audio_normal_mode(
    mock_audio_export, mock_audio_from_mp3, mock_gvo,
    temp_output_dir, temp_segment_dir
):
    """Test generate_dialogue_audio in normal (non-TEST) mode."""
    with patch('app.generators.audio.TEST_MODE', False):
        script_text = "Speaker Alpha: First line.\nSpeaker Beta: Second line, more words.\nSpeaker Alpha: Short response."
        speaker_voice_ids = ["voice_alpha_norm", "voice_beta_norm"]
        output_path = os.path.join(temp_output_dir, "dialogue_normal_mode.mp3")

        # Mock for generate_voice_over: it needs to create a file for AudioSegment.from_mp3 to "load"
        async def gvo_side_effect(text, path, voice_id):
            # print(f"Mock gvo called: text='{text}', path='{path}', voice_id='{voice_id}'")
            # Create a tiny dummy mp3-like file (or just any file if from_mp3 is fully mocked)
            with open(path, 'wb') as f:
                f.write(b"dummy mp3 data") # Content doesn't matter if from_mp3 is mocked well
            return
        mock_gvo.side_effect = gvo_side_effect

        # Mock AudioSegment instances returned by from_mp3
        mock_segment = MagicMock(spec=AudioSegment)
        mock_segment.duration = 1500 # milliseconds
        mock_audio_from_mp3.return_value = mock_segment

        accumulated_audio_mock = MagicMock(spec=AudioSegment)
        accumulated_audio_mock.duration = 0
        def mock_add(other_segment):
            accumulated_audio_mock.duration += other_segment.duration
            return accumulated_audio_mock

        empty_segment_mock = MagicMock(spec=AudioSegment)
        empty_segment_mock.duration = 0
        empty_segment_mock.__add__ = mock_add # type: ignore

        with patch('pydub.AudioSegment.empty', return_value=empty_segment_mock):
            await generate_dialogue_audio(script_text, speaker_voice_ids, output_path, temp_dir=temp_segment_dir)

        # Assertions for generate_voice_over calls
        assert mock_gvo.call_count == 3
        expected_calls_gvo = [
            (("First line.", os.path.join(temp_segment_dir, "segment_0_Speaker_Alpha.mp3"), "voice_alpha_norm"), {}),
            (("Second line, more words.", os.path.join(temp_segment_dir, "segment_1_Speaker_Beta.mp3"), "voice_beta_norm"), {}),
            (("Short response.", os.path.join(temp_segment_dir, "segment_2_Speaker_Alpha.mp3"), "voice_alpha_norm"), {}),
        ]
        for i, actual_call in enumerate(mock_gvo.call_args_list):
            args, kwargs = actual_call
            expected_args, expected_kwargs = expected_calls_gvo[i]
            assert args[0] == expected_args[0] # text
            assert args[1] == expected_args[1] # path
            assert args[2] == expected_args[2] # voice_id
            assert kwargs == expected_kwargs

        # Assertions for AudioSegment.from_mp3
        assert mock_audio_from_mp3.call_count == 3
        for i in range(3):
            call_path = mock_audio_from_mp3.call_args_list[i][0][0]
            assert call_path.startswith(temp_segment_dir)
            assert call_path.endswith(".mp3")

        # Assertion for final export
        mock_audio_export.assert_called_once()
        args_export, kwargs_export = mock_audio_export.call_args
        assert args_export[1] == output_path # Path
        assert kwargs_export['format'] == "mp3" # Format

        # Assert that temp_dir is cleaned up
        assert not os.path.exists(temp_segment_dir), "Temporary segment directory was not cleaned up"
