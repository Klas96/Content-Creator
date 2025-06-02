from anthropic import Anthropic
from ..config import ANTHROPIC_KEY, TEST_MODE
from .base import ContentGenerator

class StoryGenerator(ContentGenerator):
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.anthropic_client = Anthropic(api_key=ANTHROPIC_KEY)
        self.story_text = None

    async def generate(self, character_description: str, **kwargs):
        if TEST_MODE:
            self.story_text = """Once upon a time, there was a brave knight named Arthur. He lived in a castle on a hill.

One day, Arthur decided to go on an adventure. He packed his sword and shield.

After many days of travel, Arthur found a magical forest. The trees sparkled in the sunlight."""
            self.status = "completed"
            return self.story_text

        story_prompt = f"""\n\nHuman: Create a short story (maximum 3 paragraphs) based on the following character description:
        {character_description}

        The story should be engaging and have a clear beginning, middle, and end.
        Focus on creating vivid imagery and emotional impact.

\n\nAssistant: I'll create a short story based on the character description."""

        try:
            response = self.anthropic_client.completions.create(
                prompt=story_prompt,
                model="claude-2", # TODO: Make model configurable
                max_tokens_to_sample=1000, # TODO: Make max_tokens_to_sample configurable
                temperature=0.7 # TODO: Make temperature configurable
            )
            self.story_text = response.completion
            self.status = "completed"
        except Exception as e:
            self.status = f"failed: {e}"
            # Potentially re-raise or handle more gracefully
            raise
        return self.story_text

    def get_status(self) -> str:
        return self.status

    def get_output(self):
        return self.story_text