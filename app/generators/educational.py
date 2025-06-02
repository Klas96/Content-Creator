from anthropic import Anthropic
from ..config import ANTHROPIC_KEY, TEST_MODE
from .base import ContentGenerator

class EducationalContentGenerator(ContentGenerator):
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.anthropic_client = Anthropic(api_key=ANTHROPIC_KEY)
        self.content = None

    async def generate(
        self,
        topic: str,
        style: str = "lecture",
        difficulty: str = "beginner",
        **kwargs
    ) -> str:
        """Generate educational content based on the topic, style, and difficulty level."""
        self.status = "processing"
        if TEST_MODE:
            self.content = f"""Introduction to {topic}

{topic} is a fascinating subject that we'll explore in this {style}.

Let's break down the key concepts of {topic} for {difficulty} level learners."""
            self.status = "completed"
            return self.content

        prompt = f"""\n\nHuman: Create an educational {style} about {topic} for {difficulty} level learners.
        The content should be engaging, informative, and well-structured.
        Include:
        1. An introduction to the topic
        2. Key concepts and definitions
        3. Examples or applications
        4. A summary or conclusion

        Make it suitable for {difficulty} level understanding.

\n\nAssistant: I'll create an educational {style} about {topic}."""

        try:
            response = self.anthropic_client.completions.create(
                prompt=prompt,
                model="claude-2", # TODO: Make model configurable
                max_tokens_to_sample=1000, # TODO: Make max_tokens_to_sample configurable
                temperature=0.7 # TODO: Make temperature configurable
            )
            self.content = response.completion
            self.status = "completed"
        except Exception as e:
            self.status = f"failed: {e}"
            raise
        return self.content

    def get_status(self) -> str:
        return self.status

    def get_output(self):
        return self.content