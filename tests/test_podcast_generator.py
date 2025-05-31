import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from app.generators.podcast import (
    generate_podcast_from_custom_text,
    generate_podcast_from_topic,
    generate_free_podcast
)

# Pytest needs to discover async tests
pytestmark = pytest.mark.asyncio

# --- Tests for generate_podcast_from_custom_text ---

async def test_generate_podcast_from_custom_text_normal_mode():
    """Test generate_podcast_from_custom_text in normal mode."""
    with patch('app.generators.podcast.TEST_MODE', False):
        text = "Hello world, this is a custom podcast."
        result = await generate_podcast_from_custom_text(text)
        assert result == text

async def test_generate_podcast_from_custom_text_test_mode():
    """Test generate_podcast_from_custom_text in TEST_MODE."""
    with patch('app.generators.podcast.TEST_MODE', True):
        text = "Test input for custom text."
        result = await generate_podcast_from_custom_text(text)
        assert result == f"Test mode: Custom text received: {text}"

# --- Tests for generate_podcast_from_topic ---

async def test_generate_podcast_from_topic_test_mode():
    """Test generate_podcast_from_topic in TEST_MODE."""
    with patch('app.generators.podcast.TEST_MODE', True):
        topic = "the history of jazz"
        result = await generate_podcast_from_topic(topic)
        assert result == f"Test mode: Podcast for topic: {topic}"

@patch('app.llm_clients.generate_text_completion', new_callable=AsyncMock)
async def test_generate_podcast_from_topic_normal_mode(mock_generate_text):
    """Test generate_podcast_from_topic in normal mode with mocked generic LLM client."""
    with patch('app.generators.podcast.TEST_MODE', False):
        topic = "artificial intelligence ethics"
        expected_script = f"Mocked podcast script about {topic} from generic client"
        mock_generate_text.return_value = expected_script

        result = await generate_podcast_from_topic(topic)

        mock_generate_text.assert_called_once()
        # We can check specific arguments if needed:
        # args, kwargs = mock_generate_text.call_args
        # assert topic in kwargs['prompt']
        # assert kwargs['temperature'] == 0.7
        # assert kwargs['max_tokens'] == 2000
        assert result == expected_script

@patch('app.llm_clients.generate_text_completion', new_callable=AsyncMock)
async def test_generate_podcast_from_topic_api_error(mock_generate_text):
    """Test generate_podcast_from_topic when the generic LLM client returns an error string."""
    with patch('app.generators.podcast.TEST_MODE', False):
        topic = "quantum physics"
        # Simulate an error message returned by generate_text_completion
        mock_generate_text.return_value = "Error: Underlying API Communication Error"
        # Or, to simulate an exception raised by generate_text_completion itself
        # mock_generate_text.side_effect = Exception("LLM Client Exception")


        result = await generate_podcast_from_topic(topic)

        mock_generate_text.assert_called_once()
        # The error message from podcast.py includes the original error.
        assert "Error: Could not generate podcast for topic 'quantum physics'." in result
        assert "Details: Error: Underlying API Communication Error" in result


# --- Tests for generate_free_podcast ---

async def test_generate_free_podcast_test_mode():
    """Test generate_free_podcast in TEST_MODE."""
    with patch('app.generators.podcast.TEST_MODE', True):
        result = await generate_free_podcast()
        assert result == "Test mode: Freeform podcast generated."

@patch('app.llm_clients.generate_text_completion', new_callable=AsyncMock)
async def test_generate_free_podcast_normal_mode(mock_generate_text):
    """Test generate_free_podcast in normal mode with mocked generic LLM client."""
    with patch('app.generators.podcast.TEST_MODE', False):
        expected_script = "Mocked creative freeform podcast script from generic client."
        mock_generate_text.return_value = expected_script

        result = await generate_free_podcast()

        mock_generate_text.assert_called_once()
        assert result == expected_script

@patch('app.llm_clients.generate_text_completion', new_callable=AsyncMock)
async def test_generate_free_podcast_api_error(mock_generate_text):
    """Test generate_free_podcast when the generic LLM client returns an error string."""
    with patch('app.generators.podcast.TEST_MODE', False):
        # Simulate an error message returned by generate_text_completion
        mock_generate_text.return_value = "Error: Underlying API Freeform Error"
        # Or, to simulate an exception raised by generate_text_completion itself
        # mock_generate_text.side_effect = Exception("LLM Client Exception")

        result = await generate_free_podcast()

        mock_generate_text.assert_called_once()
        assert "Error: Could not generate freeform podcast." in result
        assert "Details: Error: Underlying API Freeform Error" in result

if __name__ == '__main__':
    # This block allows running tests with `python tests/test_podcast_generator.py`
    # However, it's recommended to use `pytest` for better output and features.
    async def run_tests():
        # Test functions would be called here, e.g.:
        await test_generate_podcast_from_custom_text_normal_mode()
        await test_generate_podcast_from_custom_text_test_mode()
        # ... and so on for all tests
        # For mocked tests, the @patch decorator handles the mock within the test's scope.
        print("Basic test execution finished. For full features, run with pytest.")

    asyncio.run(run_tests())
