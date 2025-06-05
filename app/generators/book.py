from typing import Optional, List
from app.llm_clients import generate_text_completion
from app.config import TEST_MODE
from app.utils import load_prompt # Import the new utility

async def generate_book_chapter(
    plot_summary: Optional[str] = None,
    chapter_topic: Optional[str] = None,
    previous_chapter_summary: Optional[str] = None,
    characters: Optional[List[str]] = None,
    genre: Optional[str] = None,
    style_tone: Optional[str] = None, # Added from ContentRequest common params
    desired_length_words: int = 0, # Added from ContentRequest common params
    custom_instructions: Optional[str] = None # Added for consistency
) -> str:
    """
    Generates a book chapter using the configured LLM.
    This is a basic version and can be significantly enhanced.
    """
    if TEST_MODE:
        return (f"Test Mode: Book chapter. Genre: {genre}, Style: {style_tone}.\n"
                f"Chapter Topic: {chapter_topic}\nPlot Summary: {plot_summary}\n"
                f"Characters: {', '.join(characters) if characters else 'N/A'}\n"
                f"Previous Chapter Summary: {previous_chapter_summary}\n"
                f"Desired Length: {desired_length_words} words.\n"
                f"Custom Instructions: {custom_instructions}")

    # Construct optional sections
    characters_section_str = ""
    if characters:
        characters_section_str = f"Key characters in this chapter might include: {', '.join(characters)}."

    plot_summary_section_str = ""
    if plot_summary:
        plot_summary_section_str = f"Overall plot summary of the book: {plot_summary}"

    previous_chapter_summary_section_str = ""
    if previous_chapter_summary:
        previous_chapter_summary_section_str = (
            f"Summary of the previous chapter: {previous_chapter_summary}\n"
            "Ensure this new chapter follows logically from the previous one."
        )

    custom_instructions_section_str = ""
    if custom_instructions:
        custom_instructions_section_str = f"Follow these additional instructions: {custom_instructions}"

    prompt = load_prompt(
        "book_chapter_generator_prompt.txt",
        genre=genre if genre else "not specified",
        style_tone=style_tone if style_tone else "neutral",
        characters_section=characters_section_str,
        plot_summary_section=plot_summary_section_str,
        previous_chapter_summary_section=previous_chapter_summary_section_str,
        chapter_topic=chapter_topic if chapter_topic else "not specified", # Or let template handle it
        desired_length_words=str(desired_length_words) if desired_length_words > 0 else "not specified",
        custom_instructions_section=custom_instructions_section_str
    )

    if prompt.startswith("Error:"): # Check for errors from load_prompt
        return prompt # Propagate error

    calculated_max_tokens = 0
    if desired_length_words > 0:
        calculated_max_tokens = int(desired_length_words * 1.6) # Slightly higher factor for prose
    else:
        # Default for a chapter can be quite large, e.g., 3000-4000 words.
        # Anthropic's Claude-2 has a 100k token context window, but max_tokens_to_sample is often less for one-off completion.
        # Let's set a large default, but be mindful of LLM limits for single call.
        calculated_max_tokens = 3000 # Default tokens, might be ~2000 words. Can be increased.

    chapter_text = await generate_text_completion(
        prompt=prompt,
        temperature=0.75, # Slightly higher temp for more creative writing
        max_tokens=calculated_max_tokens
    )

    if chapter_text.startswith("Error:"): # Propagate errors
        return f"Error generating book chapter: {chapter_text}" # Or handle more gracefully

    return chapter_text

# Example usage (optional)
# if __name__ == "__main__":
#     import asyncio
#     async def test_chapter():
#         # from app.config import LLM_PROVIDER, ANTHROPIC_KEY
#         # print(f"Using LLM Provider: {LLM_PROVIDER}")
#         # if LLM_PROVIDER == 'anthropic' and not ANTHROPIC_KEY:
#         #     print("ANTHROPIC_KEY not set. Exiting.")
#         #     return

#         chapter = await generate_book_chapter(
#             genre="science fiction",
#             style_tone="suspenseful and thought-provoking",
#             characters=["Captain Eva Rostova", "Dr. Aris Thorne", "The AI Entity 'Oracle'"],
#             plot_summary="A crew on a deep space mission discovers an ancient alien artifact that "
#                          "challenges their understanding of the universe and their own existence.",
#             previous_chapter_summary="The crew successfully decoded the first layer of the artifact, "
#                                      "revealing a star map to an unknown galaxy, but also triggering a "
#                                      "strange energy surge that affected the ship's AI.",
#             chapter_topic="The immediate aftermath of the energy surge and the crew's first attempt "
#                           "to communicate with the altered AI.",
#             desired_length_words=1500,
#             custom_instructions="Focus on Eva's internal conflict and her suspicion of Oracle."
#         )
#         print(f"--- Book Chapter ---\n{chapter}")

#         # Test TEST_MODE
#         # from app import config
#         # config.TEST_MODE = True
#         # test_mode_chapter = await generate_book_chapter(
#         #     genre="Fantasy", chapter_topic="The dragon's secret", desired_length_words=100
#         # )
#         # print(f"\n--- Test Mode Chapter ---\n{test_mode_chapter}")

#     asyncio.run(test_chapter())
