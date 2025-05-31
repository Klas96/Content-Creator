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

    prompt = f"""Human: You are a podcast scriptwriter. Generate an engaging and informative podcast script about the topic: {topic}. The script should be approximately 3-5 minutes in reading length. Structure it with a brief introduction, a main body discussing key aspects of the topic, and a short conclusion. Make it conversational.

Assistant: Here's a podcast script about {topic}:"""
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

    prompt = """Human: You are a creative podcast scriptwriter. Generate an engaging podcast script on any interesting topic of your choice. The script should be suitable for a general audience, approximately 3-5 minutes in reading length, and have a clear narrative or informational flow. Surprise me with your creativity!

Assistant: Here's a podcast script on an interesting topic:"""
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
