from anthropic import Anthropic
from ..config import ANTHROPIC_KEY, TEST_MODE

anthropic_client = Anthropic(api_key=ANTHROPIC_KEY)

async def generate_story(character_description: str) -> str:
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