from anthropic import Anthropic
from ..config import ANTHROPIC_KEY, TEST_MODE

anthropic_client = Anthropic(api_key=ANTHROPIC_KEY)

async def generate_story_anthropic(character_description: str) -> str:
    """Generate a story using Anthropic's Claude."""
    if TEST_MODE:
        return """Once upon a time, there was a brave knight named Arthur. He lived in a castle on a hill.

One day, Arthur decided to go on an adventure. He packed his sword and shield.

After many days of travel, Arthur found a magical forest. The trees sparkled in the sunlight."""
    
    story_prompt = f"""\n\nHuman: Create a short story (maximum 3 paragraphs) based on the following character description:
    {character_description}
    
    The story should be engaging and have a clear beginning, middle, and end.
    Focus on creating vivid imagery and emotional impact.

\n\nAssistant: I'll create a short story based on the character description."""
    
    response = anthropic_client.completions.create(
        prompt=story_prompt,
        model="claude-2",
        max_tokens_to_sample=1000,
        temperature=0.7
    )
    
    return response.completion

async def generate_educational_content_anthropic(
    topic: str,
    style: str = "lecture",
    difficulty: str = "intermediate"
) -> str:
    """Generate educational content using Anthropic's Claude."""
    if TEST_MODE:
        return f"""Introduction to {topic}

This is a {difficulty} level {style} about {topic}.

Key points to remember:
1. First important point
2. Second important point
3. Third important point

Conclusion: Summary of main points."""
    
    prompt = f"""\n\nHuman: Create educational content about {topic} in a {style} style.
    The content should be at a {difficulty} difficulty level.
    Include clear explanations and examples where appropriate.
    Structure the content with an introduction, main points, and conclusion.

\n\nAssistant: I'll create educational content about {topic}."""
    
    response = anthropic_client.completions.create(
        prompt=prompt,
        model="claude-2",
        max_tokens_to_sample=1000,
        temperature=0.7
    )
    
    return response.completion

async def generate_podcast_script_anthropic(
    topic: str,
    style: str = "professional",
    length_words: int = 500
) -> str:
    """Generate a podcast script using Anthropic's Claude."""
    if TEST_MODE:
        return f"""Welcome to our podcast about {topic}!

Today we'll be discussing {topic} in detail.

Let's dive right in...

[Main content would go here]

Thanks for listening! Don't forget to subscribe for more content."""
    
    prompt = f"""\n\nHuman: Create a podcast script about {topic} in a {style} style.
    The script should be approximately {length_words} words long.
    Include an introduction, main content, and conclusion.
    Make it engaging and conversational.

\n\nAssistant: I'll create a podcast script about {topic}."""
    
    response = anthropic_client.completions.create(
        prompt=prompt,
        model="claude-2",
        max_tokens_to_sample=1000,
        temperature=0.7
    )
    
    return response.completion 