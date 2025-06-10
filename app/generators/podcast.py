import asyncio
# from anthropic import Anthropic # Removed
# from ..config import ANTHROPIC_KEY, TEST_MODE # ANTHROPIC_KEY removed, TEST_MODE kept
from ..config import TEST_MODE # Keep TEST_MODE
from ..llm_clients import generate_text_completion # Import new function

# # Initialize Anthropic client # Removed
# anthropic_client = Anthropic(api_key=ANTHROPIC_KEY)

async def generate_podcast_from_custom_text(text: str) -> str:
    """Generates podcast content directly from custom text."""
    if TEST_MODE:
        return f"Test mode: Custom text received: {text}"
    return text

async def generate_podcast_from_topic(topic: str) -> str:
    """Generates podcast content based on a given topic."""
    if TEST_MODE:
        return f"Test mode: Podcast for topic: {topic}"

    prompt = f"""Create a natural, engaging podcast script about {topic}. 
    Write it as a single, flowing narrative without any labels or formatting.
    The script should be approximately 3-5 minutes in reading length.
    Start with a brief introduction, then dive into the main content, and end with a conclusion.
    Make it conversational and engaging, as if you're speaking directly to the listener.
    Do not include any labels like 'Host:', 'Introduction:', or 'Conclusion:'.
    Just write the natural flow of the conversation."""

    try:
        # response = await asyncio.to_thread( # Replaced
        #     anthropic_client.completions.create,
        #     prompt=prompt,
        #     model="claude-2",
        #     max_tokens_to_sample=2000,
        #     temperature=0.7
        # )
        # return response.completion
        generated_script = await generate_text_completion(
            prompt=prompt,
            temperature=0.7,
            max_tokens=2000
        )
        if generated_script.startswith("Error:"): # Check if our new function returned an error
            raise Exception(generated_script)
        return generated_script
    except Exception as e:
        print(f"Error generating podcast from topic: {e}")
        return f"Error: Could not generate podcast for topic '{topic}'. Details: {e}"

async def generate_free_podcast() -> str:
    """Generates a freeform podcast on an engaging topic."""
    if TEST_MODE:
        return "Test mode: Freeform podcast generated."

    prompt = """Create a natural, engaging podcast script on any interesting topic of your choice.
    Write it as a single, flowing narrative without any labels or formatting.
    The script should be suitable for a general audience and approximately 3-5 minutes in reading length.
    Make it conversational and engaging, as if you're speaking directly to the listener.
    Do not include any labels like 'Host:', 'Introduction:', or 'Conclusion:'.
    Just write the natural flow of the conversation."""

    try:
        # response = await asyncio.to_thread( # Replaced
        #     anthropic_client.completions.create,
        #     prompt=prompt,
        #     model="claude-2",
        #     max_tokens_to_sample=2000,
        #     temperature=0.7
        # )
        # return response.completion
        generated_script = await generate_text_completion(
            prompt=prompt,
            temperature=0.7,
            max_tokens=2000
        )
        if generated_script.startswith("Error:"): # Check if our new function returned an error
            raise Exception(generated_script)
        return generated_script
    except Exception as e:
        print(f"Error generating freeform podcast: {e}")
        return f"Error: Could not generate freeform podcast. Details: {e}"

if __name__ == '__main__':
    # Example usage (for testing purposes)
    async def main():
        if TEST_MODE:
            print("Running in TEST_MODE")

        print("\n--- Custom Text Podcast ---")
        custom_text_output = await generate_podcast_from_custom_text("This is a test of the custom text podcast.")
        print(custom_text_output)

        print("\n--- Topic-Based Podcast (e.g., 'The Future of AI') ---")
        topic_output = await generate_podcast_from_topic("The Future of AI")
        print(topic_output)

        print("\n--- Freeform Podcast ---")
        freeform_output = await generate_free_podcast()
        print(freeform_output)

    asyncio.run(main())
