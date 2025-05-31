import pytest
import json
from unittest.mock import AsyncMock, patch
from app.generators.social import generate_tweet_thread

pytestmark = pytest.mark.asyncio

async def test_generate_tweet_thread_test_mode():
    """Test generate_tweet_thread in TEST_MODE."""
    with patch('app.generators.social.TEST_MODE', True):
        topic = "Test Topic"
        num_tweets = 2
        style = "Test Style"
        cta = "Test CTA"
        instructions = "Test Instructions"

        result = await generate_tweet_thread(topic, num_tweets, style, cta, instructions)

        expected = [
            f"Test Mode: Tweet 1/2 about '{topic}'. Style: {style}. CTA: {cta}. Instructions: {instructions}",
            f"Test Mode: Tweet 2/2 about '{topic}'. Style: {style}. CTA: {cta}. Instructions: {instructions}"
        ]
        assert result == expected

@patch('app.generators.social.generate_text_completion', new_callable=AsyncMock)
@patch('app.generators.social.load_prompt')
async def test_generate_tweet_thread_normal_mode(mock_load_prompt, mock_generate_text_completion):
    """Test generate_tweet_thread in normal mode."""
    with patch('app.generators.social.TEST_MODE', False):
        topic = "New Product Launch"
        num_tweets = 3
        style = "exciting"
        cta = "Buy now!"
        instructions = "Use emojis"

        mock_prompt_template = "Prompt for {topic}, num_tweets {num_tweets}, etc."
        mock_load_prompt.return_value = mock_prompt_template

        mock_llm_response_json = json.dumps(["Tweet 1 about new product", "Tweet 2 with details", f"Tweet 3: {cta}"])
        mock_generate_text_completion.return_value = mock_llm_response_json

        result = await generate_tweet_thread(topic, num_tweets, style, cta, instructions)

        expected_cta_section = f"The last tweet should include this call to action: '{cta}'."
        expected_instructions_section = f"Follow these additional instructions: '{instructions}'"
        mock_load_prompt.assert_called_once_with(
            "tweet_thread_generator_prompt.txt",
            num_tweets=str(num_tweets),
            topic=topic,
            style_tone=style,
            call_to_action_section=expected_cta_section,
            custom_instructions_section=expected_instructions_section
        )

        # Max tokens: (3 * 150) + 200 = 450 + 200 = 650
        mock_generate_text_completion.assert_called_once_with(
            prompt=mock_prompt_template,
            temperature=0.6,
            max_tokens=650
        )
        assert result == ["Tweet 1 about new product", "Tweet 2 with details", f"Tweet 3: {cta}"]

@patch('app.generators.social.generate_text_completion', new_callable=AsyncMock)
@patch('app.generators.social.load_prompt')
async def test_generate_tweet_thread_json_decode_error(mock_load_prompt, mock_generate_text_completion):
    """Test handling of JSON decoding errors from LLM output."""
    with patch('app.generators.social.TEST_MODE', False):
        mock_load_prompt.return_value = "Valid prompt"
        invalid_json_output = "This is not JSON, it's just a plain string without brackets."
        mock_generate_text_completion.return_value = invalid_json_output

        result = await generate_tweet_thread("Any topic")

        assert len(result) == 1
        assert result[0].startswith("Error: LLM output was not in the expected JSON array format.")
        assert invalid_json_output[:100] in result[0] # Check if part of the failing output is included

@patch('app.generators.social.generate_text_completion', new_callable=AsyncMock)
@patch('app.generators.social.load_prompt')
async def test_generate_tweet_thread_llm_error(mock_load_prompt, mock_generate_text_completion):
    """Test when generate_text_completion returns a direct error."""
    with patch('app.generators.social.TEST_MODE', False):
        mock_load_prompt.return_value = "Valid prompt"
        mock_generate_text_completion.return_value = "Error: LLM infrastructure failure."

        result = await generate_tweet_thread("Any topic")
        assert result == ["Error: LLM infrastructure failure."]

@patch('app.generators.social.load_prompt')
async def test_generate_tweet_thread_load_prompt_error(mock_load_prompt):
    """Test when load_prompt itself returns an error."""
    with patch('app.generators.social.TEST_MODE', False):
        mock_load_prompt.return_value = "Error: Could not load prompt file."
        result = await generate_tweet_thread("Any topic")
        assert result == ["Error: Could not load prompt file."]

@patch('app.generators.social.generate_text_completion', new_callable=AsyncMock)
@patch('app.generators.social.load_prompt')
async def test_generate_tweet_thread_llm_returns_invalid_json_structure(mock_load_prompt, mock_generate_text_completion):
    """Test when LLM returns valid JSON but not a list of strings."""
    with patch('app.generators.social.TEST_MODE', False):
        mock_load_prompt.return_value = "Valid prompt"
        # Valid JSON, but not List[str]
        mock_llm_response_json = json.dumps({"tweet1": "content", "tweet2": "content"})
        mock_generate_text_completion.return_value = mock_llm_response_json

        result = await generate_tweet_thread("Any topic")
        assert len(result) == 1
        assert result[0].startswith("Error: LLM did not return a valid JSON list of tweet strings.")
