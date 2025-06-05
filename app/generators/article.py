from typing import Optional
from app.llm_clients import generate_text_completion
from app.config import TEST_MODE
from app.utils import load_prompt # Import the new utility

async def generate_article(
    topic: str,
    desired_length_words: int = 0, # 0 for model default
    style_tone: Optional[str] = None,
    custom_instructions: Optional[str] = None
) -> str:
    """
    Generates an article on a given topic using the configured LLM.
    """
    if TEST_MODE:
        return f"Test Mode: Article about '{topic}' with style '{style_tone}'. Length: {desired_length_words} words. Instructions: {custom_instructions}"

    # Construct optional sections for the prompt template
    custom_instructions_section = ""
    if custom_instructions:
        custom_instructions_section = f"Follow these additional instructions: {custom_instructions}"

    # Provide default values for formatting if None
    style_tone_str = style_tone if style_tone else "neutral"
    desired_length_str = str(desired_length_words) if desired_length_words > 0 else "not specified"

    prompt = load_prompt(
        "article_generator_prompt.txt",
        topic=topic,
        style_tone=style_tone_str,
        desired_length_words=desired_length_str,
        custom_instructions_section=custom_instructions_section
    )

    if prompt.startswith("Error:"): # Check for errors from load_prompt
        return prompt # Propagate error

    # Determine max_tokens based on desired_length_words (e.g., 1.5 words per token as a rough estimate)
    # Or use a sensible default if desired_length_words is 0.
    # The current `generate_text_completion` takes `max_tokens`.
    # Let's calculate roughly: 1 word ~ 1.33 tokens. So max_tokens = desired_length_words * 1.33
    # If desired_length_words is 0, use a default like 1500 tokens.

    calculated_max_tokens = 0
    if desired_length_words > 0:
        calculated_max_tokens = int(desired_length_words * 1.5) # Adjusted factor for safety, 1 word is often > 1 token
    else:
        calculated_max_tokens = 2000 # Default for moderate length article, was 1500 in comment

    article_text = await generate_text_completion(
        prompt=prompt,
        temperature=0.7, # Standard temperature
        max_tokens=calculated_max_tokens
    )

    if article_text.startswith("Error:"): # Propagate errors from the LLM client
        return f"Error generating article: {article_text}" # Or handle more gracefully

    return article_text

# Example usage (optional)
# if __name__ == "__main__":
#     import asyncio
#     async def test_article():
#         topic = "The Benefits of Renewable Energy"
#         style = "informative and slightly optimistic"
#         length = 500
#         # Assuming LLM_PROVIDER is configured, and ANTHROPIC_KEY is set if using anthropic
#         # from app.config import LLM_PROVIDER, ANTHROPIC_KEY
#         # print(f"Using LLM Provider: {LLM_PROVIDER}")
#         # if LLM_PROVIDER == 'anthropic' and not ANTHROPIC_KEY:
#         #     print("ANTHROPIC_KEY not set. Exiting.")
#         #     return

#         article = await generate_article(topic, length, style, custom_instructions="Mention solar and wind power specifically.")
#         print(f"--- Article on: {topic} ---\n{article}")

#         # Test TEST_MODE
#         # from app import config
#         # config.TEST_MODE = True
#         # test_mode_article = await generate_article("Test Topic", 100, "test style", "test instructions")
#         # print(f"\n--- Test Mode Article ---\n{test_mode_article}")

#     asyncio.run(test_article())
