import os
import re # Added import for re
import asyncio
from typing import Optional

from anthropic import Anthropic
from ..config import ANTHROPIC_KEY, TEST_MODE
from .base import ContentGenerator

class PostGenerator(ContentGenerator):
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.anthropic_client = Anthropic(api_key=ANTHROPIC_KEY)
        self.post_content: Optional[str] = None
        self.output_path: Optional[str] = None

    async def generate(self, topic: str, output_dir: str, style: str = "informative", length: str = "medium", target_audience: Optional[str] = None, **kwargs):
        self.status = "processing"
        self.post_content = None # Reset from previous run
        self.output_path = None # Reset from previous run

        if TEST_MODE:
            self.post_content = f"This is a TEST post about {topic}, written in an {style} style, of {length} length."
            if target_audience:
                self.post_content += f" It is targeted at {target_audience}."
            # In TEST_MODE, we directly proceed to saving this mock content.
        else:
            length_map = {
                "short": "~200 words (about 150-250 tokens)", # Adjusted token estimates
                "medium": "~500 words (about 350-600 tokens)",
                "long": "~1000 words (about 700-1200 tokens)"
            }
            length_description = length_map.get(length.lower(), length) # Use provided length if not in map

            prompt_parts = [
                f"Human: Write a blog post or article on the topic: \"{topic}\".",
                f"The desired style for the post is: {style}.",
                f"The desired length for the post is: {length_description}.",
            ]
            if target_audience:
                prompt_parts.append(f"The target audience for this post is: {target_audience}.")

            prompt_parts.append("\nPlease ensure the content is well-structured, engaging, and directly addresses the topic.")
            prompt_parts.append("\nAssistant: Here is the post:")
            prompt = "\n".join(prompt_parts)

            try:
                response = await asyncio.to_thread(
                    self.anthropic_client.completions.create,
                    prompt=prompt,
                    model=self.config.get("anthropic_model", "claude-2"),
                    max_tokens_to_sample=self.config.get("post_max_tokens", 1500), # Default max, can be overridden by length
                    temperature=self.config.get("post_temperature", 0.7)
                )
                self.post_content = response.completion.strip()
            except Exception as e:
                self.status = f"failed: LLM error during content generation - {e}"
                self.post_content = None # Ensure content is None if LLM fails
                # Return early if LLM failed
                return

        if self.post_content:
            try:
                os.makedirs(output_dir, exist_ok=True)
            except OSError as e:
                self.status = f"failed: could not create output directory {output_dir} - {e}"
                return

            # Sanitize topic for filename, similar to BookGenerator's sanitize
            sanitized_topic = topic.lower()
            sanitized_topic = re.sub(r'\s+', '_', sanitized_topic)
            sanitized_topic = re.sub(r'[^\w\s-]', '', sanitized_topic)
            sanitized_topic = sanitized_topic.strip('-_')[:50] # Limit length

            filename = f"post_{sanitized_topic}.txt" if sanitized_topic else "post.txt"
            self.output_path = os.path.join(output_dir, filename)

            try:
                with open(self.output_path, "w", encoding="utf-8") as f:
                    f.write(self.post_content)
                self.status = "completed"
                self.output = self.output_path # self.output from base class
            except IOError as e:
                self.status = f"failed: could not write post file {self.output_path} - {e}"
                self.output_path = None # Ensure output_path is None if write fails
        else:
            # This case would be hit if TEST_MODE was false and LLM somehow returned empty content
            # without raising an exception, or if self.post_content was manually set to None after TEST_MODE.
            if self.status == "processing": # Avoid overwriting a more specific "failed: LLM error..."
                self.status = "failed: content generation resulted in empty content"

    def get_status(self) -> str:
        if self.status == "completed":
            if self.output_path and os.path.exists(self.output_path):
                return "completed"
            else:
                self.status = "failed: output file missing"
        return self.status

    def get_output(self):
        if self.status == "completed" and self.output_path:
            return self.output_path
        return None
