import pytest
from unittest.mock import AsyncMock, patch
from app.generators.article import generate_article

pytestmark = pytest.mark.asyncio

async def test_generate_article_test_mode():
    """Test generate_article in TEST_MODE."""
    with patch('app.generators.article.TEST_MODE', True):
        topic = "Test Topic"
        style = "Test Style"
        length = 100
        instructions = "Test Instructions"
        result = await generate_article(topic, length, style, instructions)
        assert result == f"Test Mode: Article about '{topic}' with style '{style}'. Length: {length} words. Instructions: {instructions}"

@patch('app.generators.article.generate_text_completion', new_callable=AsyncMock)
@patch('app.generators.article.load_prompt')
async def test_generate_article_normal_mode(mock_load_prompt, mock_generate_text_completion):
    """Test generate_article in normal mode."""
    with patch('app.generators.article.TEST_MODE', False):
        topic = "Renewable Energy"
        style = "informative"
        length = 500
        instructions = "Mention solar and wind."

        mock_prompt_template = "Generated prompt for {topic} with style {style_tone}, length {desired_length_words}, and instructions: {custom_instructions_section}"
        mock_load_prompt.return_value = mock_prompt_template

        mock_llm_response = "This is a mock article about renewable energy, focusing on solar and wind."
        mock_generate_text_completion.return_value = mock_llm_response

        result = await generate_article(topic, length, style, instructions)

        expected_custom_instructions_section = f"Follow these additional instructions: {instructions}"
        mock_load_prompt.assert_called_once_with(
            "article_generator_prompt.txt",
            topic=topic,
            style_tone=style,
            desired_length_words=str(length), # Was passed as int, converted to str by generator
            custom_instructions_section=expected_custom_instructions_section
        )

        # Expected max_tokens: int(500 * 1.5) = 750
        mock_generate_text_completion.assert_called_once_with(
            prompt=mock_prompt_template,
            temperature=0.7,
            max_tokens=750
        )
        assert result == mock_llm_response

async def test_generate_article_normal_mode_no_optional_params():
    """Test generate_article with no optional parameters."""
    with patch('app.generators.article.TEST_MODE', False), \
         patch('app.generators.article.load_prompt') as mock_load_prompt, \
         patch('app.generators.article.generate_text_completion', new_callable=AsyncMock) as mock_generate_text_completion:

        topic = "Minimalism"
        mock_prompt_template = "Prompt for {topic}, style {style_tone}, length {desired_length_words}, instructions {custom_instructions_section}"
        mock_load_prompt.return_value = mock_prompt_template
        mock_llm_response = "Minimalist article."
        mock_generate_text_completion.return_value = mock_llm_response

        result = await generate_article(topic=topic) # Only topic provided

        mock_load_prompt.assert_called_once_with(
            "article_generator_prompt.txt",
            topic=topic,
            style_tone="neutral", # Default value
            desired_length_words="not specified", # Default value
            custom_instructions_section="" # Empty string for no instructions
        )
        # Default max_tokens when length is 0 (or not specified) is 2000
        mock_generate_text_completion.assert_called_once_with(
            prompt=mock_prompt_template,
            temperature=0.7,
            max_tokens=2000
        )
        assert result == mock_llm_response


@patch('app.generators.article.load_prompt')
async def test_generate_article_load_prompt_error(mock_load_prompt):
    """Test generate_article when load_prompt returns an error."""
    with patch('app.generators.article.TEST_MODE', False):
        mock_load_prompt.return_value = "Error: Prompt file not found"
        result = await generate_article("Any topic")
        assert result == "Error: Prompt file not found"

@patch('app.generators.article.generate_text_completion', new_callable=AsyncMock)
@patch('app.generators.article.load_prompt') # Still need to mock load_prompt to avoid FileNotFoundError
async def test_generate_article_llm_error(mock_load_prompt, mock_generate_text_completion):
    """Test generate_article when generate_text_completion returns an error."""
    with patch('app.generators.article.TEST_MODE', False):
        mock_load_prompt.return_value = "Valid prompt template" # Assume prompt loading is fine
        mock_generate_text_completion.return_value = "Error: LLM failed"

        result = await generate_article("Any topic")

        # The error from generate_text_completion is prepended by "Error generating article: "
        assert result == "Error generating article: Error: LLM failed"
