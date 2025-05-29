from anthropic import Anthropic
from ..config import ANTHROPIC_KEY, TEST_MODE

anthropic_client = Anthropic(api_key=ANTHROPIC_KEY)

async def generate_educational_content(
    topic: str,
    style: str = "lecture",
    difficulty: str = "beginner"
) -> str:
    """Generate educational content based on the topic, style, and difficulty level."""
    if TEST_MODE:
        return f"""Introduction to {topic}

{topic} is a fascinating subject that we'll explore in this {style}.

Let's break down the key concepts of {topic} for {difficulty} level learners."""

    prompt = f"""\n\nHuman: Create an educational {style} about {topic} for {difficulty} level learners.
    The content should be engaging, informative, and well-structured.
    Include:
    1. An introduction to the topic
    2. Key concepts and definitions
    3. Examples or applications
    4. A summary or conclusion
    
    Make it suitable for {difficulty} level understanding.

\n\nAssistant: I'll create an educational {style} about {topic}."""
    
    response = anthropic_client.completions.create(
        prompt=prompt,
        model="claude-2",
        max_tokens_to_sample=1000,
        temperature=0.7
    )
    
    return response.completion 