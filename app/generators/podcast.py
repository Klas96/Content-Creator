import asyncio
# from anthropic import Anthropic # Removed
# from ..config import ANTHROPIC_KEY, TEST_MODE # ANTHROPIC_KEY removed, TEST_MODE kept
from ..config import TEST_MODE # Keep TEST_MODE
from ..llm_clients import generate_text_completion # Import new function
import os
from typing import List, Tuple
from openai import OpenAI
from ..config import OPENAI_KEY

# # Initialize Anthropic client # Removed
# anthropic_client = Anthropic(api_key=ANTHROPIC_KEY)

client = OpenAI(api_key=OPENAI_KEY)

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

def create_mock_dialogue() -> List[Tuple[int, str]]:
    """Create a mock dialogue for testing."""
    print("\n⚠️ WARNING: Using mock dialogue - this indicates a failure in the actual dialogue generation!")
    print("The generated content will be generic and not specific to your topic.\n")
    return [
        (1, "Let's discuss the key aspects of this topic. What are the fundamental principles we should focus on?"),
        (2, "The core principles are crucial. We need to consider both theoretical foundations and practical applications."),
        (1, "What are some best practices that developers should follow when implementing these principles?"),
        (2, "Following established patterns and maintaining consistency are essential. We should also consider scalability."),
        (1, "What challenges do you typically encounter in real-world implementations?"),
        (2, "Performance optimization and maintaining code quality are common challenges that require careful consideration.")
    ]

async def generate_dialogue_content(topic: str, num_exchanges: int = 6) -> List[Tuple[int, str]]:
    """
    Generate a natural dialogue between two speakers about a given topic.
    
    Args:
        topic (str): The topic to discuss
        num_exchanges (int): Number of dialogue exchanges to generate (default: 6)
    
    Returns:
        List[Tuple[int, str]]: List of (speaker_number, text) tuples
    """
    if TEST_MODE:
        print("\n⚠️ WARNING: Running in TEST_MODE - using mock dialogue\n")
        return create_mock_dialogue()
    
    print(f"\nGenerating dialogue for topic: {topic}")
    print(f"Requested number of exchanges: {num_exchanges}\n")
    
    # Define specific aspects to cover based on the topic
    aspects = [
        "core principles and fundamentals",
        "best practices and implementation strategies",
        "common challenges and solutions",
        "performance considerations",
        "future trends and developments"
    ]
    
    prompt = f"""Create a focused, technical dialogue between two experts discussing {topic}. 
    The dialogue must:
    1. Stay strictly focused on {topic} - do not deviate from this topic
    2. Cover these specific aspects in order:
       - {aspects[0]}
       - {aspects[1]}
       - {aspects[2]}
       - {aspects[3]}
       - {aspects[4]}
    3. Each exchange should:
       - Address one specific aspect of {topic}
       - Include concrete examples or use cases
       - Reference specific technologies or techniques when relevant
       - Build upon previous exchanges
    4. Maintain a professional, technical tone
    5. End with practical takeaways or next steps
    
    Format each line as "Speaker X: [text]" where X is 1 or 2.
    Generate exactly {num_exchanges} exchanges.
    """
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            print(f"Attempt {retry_count + 1}/{max_retries} to generate dialogue...")
            
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model="gpt-4",
                messages=[
                    {
                        "role": "system", 
                        "content": f"""You are a dialogue generator creating a technical discussion about {topic}.
                        Rules:
                        1. Stay strictly on topic - every exchange must directly relate to {topic}
                        2. Each exchange must cover one of the specified aspects
                        3. Use specific examples and technical details
                        4. Maintain a logical flow between exchanges
                        5. Keep responses concise and focused
                        6. Ensure both speakers contribute equally
                        7. Do not include generic or off-topic content
                        8. Never start with a generic question about AI or other unrelated topics"""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                presence_penalty=0.3,
                frequency_penalty=0.3
            )
            
            # Parse the response into dialogue format
            dialogue_text = response.choices[0].message.content
            dialogue_lines = dialogue_text.strip().split('\n')
            
            # Convert to list of tuples (speaker_number, text)
            dialogue = []
            for line in dialogue_lines:
                if line.startswith('Speaker '):
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        speaker_num = int(parts[0].split()[1])
                        text = parts[1].strip()
                        dialogue.append((speaker_num, text))
            
            # Validate the dialogue
            if len(dialogue) < num_exchanges:
                print(f"⚠️ Warning: Generated {len(dialogue)} exchanges instead of {num_exchanges}")
                print("Continuing with available exchanges...")
                
            # Check if the first line contains any off-topic content
            first_line = dialogue[0][1].lower()
            if "artificial intelligence" in first_line or "ai" in first_line:
                print("❌ Error: Generated dialogue started with off-topic content")
                retry_count += 1
                continue
            
            print(f"✅ Successfully generated dialogue with {len(dialogue)} exchanges")
            return dialogue
            
        except Exception as e:
            print(f"❌ Error generating dialogue (attempt {retry_count + 1}/{max_retries}): {str(e)}")
            retry_count += 1
            if retry_count == max_retries:
                print("\n❌ All retry attempts failed. Check the error messages above for details.")
                return create_mock_dialogue()
            await asyncio.sleep(1)  # Wait a bit before retrying

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
