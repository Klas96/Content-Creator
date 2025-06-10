from ..config import LLM_PROVIDER
from .openai_content import generate_story_openai
from .anthropic_content import generate_story_anthropic

async def generate_story(character_description: str) -> str:
    """Generate a story using the configured LLM provider."""
    if LLM_PROVIDER == "openai":
        return await generate_story_openai(character_description)
    else:
        return await generate_story_anthropic(character_description) 