import pytest
from unittest.mock import AsyncMock, patch
from app.generators.book import generate_book_chapter

pytestmark = pytest.mark.asyncio

async def test_generate_book_chapter_test_mode():
    """Test generate_book_chapter in TEST_MODE."""
    with patch('app.generators.book.TEST_MODE', True):
        result = await generate_book_chapter(
            genre="Fantasy",
            style_tone="Epic",
            chapter_topic="The Dragon's Lair",
            plot_summary="A quest to find a hidden treasure.",
            characters=["Hero", "Wizard"],
            previous_chapter_summary="They found a map.",
            desired_length_words=1000,
            custom_instructions="Make it grand."
        )
        assert "Test Mode: Book chapter." in result
        assert "Genre: Fantasy" in result
        assert "Style: Epic" in result
        assert "Chapter Topic: The Dragon's Lair" in result
        assert "Plot Summary: A quest to find a hidden treasure." in result
        assert "Characters: Hero, Wizard" in result
        assert "Previous Chapter Summary: They found a map." in result
        assert "Desired Length: 1000 words." in result
        assert "Custom Instructions: Make it grand." in result

@patch('app.generators.book.generate_text_completion', new_callable=AsyncMock)
@patch('app.generators.book.load_prompt')
async def test_generate_book_chapter_normal_mode(mock_load_prompt, mock_generate_text_completion):
    """Test generate_book_chapter in normal mode."""
    with patch('app.generators.book.TEST_MODE', False):
        genre = "Sci-Fi"
        style = "Thought-provoking"
        topic = "AI Consciousness"
        length = 2500
        plot = "An AI becomes self-aware."
        chars = ["Dr. Aris", "Unit 734"]
        prev_summary = "Unit 734 started asking unusual questions."
        instructions = "Explore philosophical themes."

        mock_prompt_template = "Prompt for {genre}, topic {chapter_topic}, etc."
        mock_load_prompt.return_value = mock_prompt_template

        mock_llm_response = "This is a mock sci-fi chapter about AI consciousness..."
        mock_generate_text_completion.return_value = mock_llm_response

        result = await generate_book_chapter(
            plot_summary=plot,
            chapter_topic=topic,
            previous_chapter_summary=prev_summary,
            characters=chars,
            genre=genre,
            style_tone=style,
            desired_length_words=length,
            custom_instructions=instructions
        )

        expected_chars_section = f"Key characters in this chapter might include: {', '.join(chars)}."
        expected_plot_section = f"Overall plot summary of the book: {plot}"
        expected_prev_summary_section = (
            f"Summary of the previous chapter: {prev_summary}\n"
            "Ensure this new chapter follows logically from the previous one."
        )
        expected_instructions_section = f"Follow these additional instructions: {instructions}"

        mock_load_prompt.assert_called_once_with(
            "book_chapter_generator_prompt.txt",
            genre=genre,
            style_tone=style,
            characters_section=expected_chars_section,
            plot_summary_section=expected_plot_section,
            previous_chapter_summary_section=expected_prev_summary_section,
            chapter_topic=topic,
            desired_length_words=str(length),
            custom_instructions_section=expected_instructions_section
        )

        # Expected max_tokens: int(2500 * 1.6) = 4000
        mock_generate_text_completion.assert_called_once_with(
            prompt=mock_prompt_template,
            temperature=0.75,
            max_tokens=4000
        )
        assert result == mock_llm_response

@patch('app.generators.book.load_prompt')
async def test_generate_book_chapter_load_prompt_error(mock_load_prompt):
    """Test generate_book_chapter when load_prompt returns an error."""
    with patch('app.generators.book.TEST_MODE', False):
        mock_load_prompt.return_value = "Error: Prompt file not found for book chapter"
        result = await generate_book_chapter(chapter_topic="Any topic")
        assert result == "Error: Prompt file not found for book chapter"

@patch('app.generators.book.generate_text_completion', new_callable=AsyncMock)
@patch('app.generators.book.load_prompt')
async def test_generate_book_chapter_llm_error(mock_load_prompt, mock_generate_text_completion):
    """Test generate_book_chapter when generate_text_completion returns an error."""
    with patch('app.generators.book.TEST_MODE', False):
        mock_load_prompt.return_value = "Valid book chapter prompt template"
        mock_generate_text_completion.return_value = "Error: LLM for book chapter failed"

        result = await generate_book_chapter(chapter_topic="Any topic")

        assert result == "Error generating book chapter: Error: LLM for book chapter failed"
