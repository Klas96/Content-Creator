import os
import re
import asyncio
from typing import Dict, Optional

from anthropic import Anthropic
from ..config import ANTHROPIC_KEY, TEST_MODE
from .base import ContentGenerator

class BookGenerator(ContentGenerator):
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.anthropic_client = Anthropic(api_key=ANTHROPIC_KEY)
        self.book_outline: Optional[Dict[str, str]] = None
        self.chapters_content: Dict[str, str] = {}
        self.output_path: Optional[str] = None # Path to the full_book.txt or directory

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Converts a string into a safe filename."""
        name = name.lower()
        name = re.sub(r'\s+', '_', name) # Replace spaces with underscores
        name = re.sub(r'[^\w\s-]', '', name) # Remove non-alphanumeric characters (except underscore/hyphen)
        name = name.strip('-_') # Remove leading/trailing underscores/hyphens
        return name[:100] # Limit length

    async def _generate_outline(self, topic: str, num_chapters: int = 5) -> Optional[Dict[str, str]]:
        if TEST_MODE:
            mock_outline = {}
            for i in range(1, num_chapters + 1):
                mock_outline[f"Chapter {i}: Mock Title {i}"] = f"This is a brief summary for mock chapter {i} about {topic}."
            return mock_outline

        prompt = f"""Human: Generate a book outline for a book about "{topic}".
The outline should consist of {num_chapters} chapters.
For each chapter, provide a chapter title and a concise one-sentence summary of what the chapter will cover.
Format the output as follows:
Chapter Title 1: Summary 1
Chapter Title 2: Summary 2
...

Assistant: Here is the book outline:"""
        try:
            response = await asyncio.to_thread(
                self.anthropic_client.completions.create,
                prompt=prompt,
                model=self.config.get("anthropic_model", "claude-2"), # Configurable model
                max_tokens_to_sample=self.config.get("outline_max_tokens", 1000),
                temperature=self.config.get("outline_temperature", 0.5)
            )

            outline_text = response.completion
            parsed_outline: Dict[str, str] = {}
            for line in outline_text.strip().split('\n'):
                if ':' in line:
                    parts = line.split(':', 1)
                    title = parts[0].strip()
                    summary = parts[1].strip()
                    if title and summary:
                        parsed_outline[title] = summary

            if not parsed_outline :
                self.status = "failed: empty outline from LLM"
                return None
            return parsed_outline
        except Exception as e:
            self.status = f"failed: LLM error during outline generation - {e}"
            return None

    async def _generate_chapter_content(self, chapter_title: str, chapter_summary: str, writing_style: str = "narrative", genre: str = "fiction") -> Optional[str]:
        if TEST_MODE:
            return f"This is the TEST MODE full content for chapter '{chapter_title}' (Summary: {chapter_summary}). It is written in a {writing_style} style for the {genre} genre."

        prompt = f"""Human: Write a full chapter for a book.
Chapter Title: "{chapter_title}"
Chapter Summary: "{chapter_summary}"
Writing Style: {writing_style}
Genre: {genre}

The chapter should be comprehensive, well-developed, and engaging, expanding significantly on the summary provided.
Ensure the chapter flows logically and fits the specified style and genre.

Assistant: Here is the content for the chapter "{chapter_title}":"""
        try:
            response = await asyncio.to_thread(
                self.anthropic_client.completions.create,
                prompt=prompt,
                model=self.config.get("anthropic_model", "claude-2"),
                max_tokens_to_sample=self.config.get("chapter_max_tokens", 3000), # Chapters can be longer
                temperature=self.config.get("chapter_temperature", 0.7)
            )
            return response.completion.strip()
        except Exception as e:
            self.status = f"failed: LLM error during chapter content generation for '{chapter_title}' - {e}"
            return None

    async def generate(self, topic: str, output_dir: str, num_chapters: int = 5, writing_style: str = "narrative", genre: str = "fiction", **kwargs):
        self.status = "processing"
        self.output_path = None # Reset from previous runs
        self.book_outline = None
        self.chapters_content = {}

        self.book_outline = await self._generate_outline(topic, num_chapters)

        if not self.book_outline:
            # Status already set by _generate_outline if it failed
            if self.status == "processing": # If it returned None without setting specific error
                 self.status = "failed: outline generation resulted in no outline"
            return

        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            self.status = f"failed: could not create output directory {output_dir} - {e}"
            return

        all_chapters_text = []
        chapter_num = 1
        for title, summary in self.book_outline.items():
            self.status = f"processing: chapter {chapter_num} - {title}"
            content = await self._generate_chapter_content(title, summary, writing_style, genre)
            if content is None:
                # Status already set by _generate_chapter_content
                # Potentially stop or try to continue with other chapters? For now, stop.
                return

            self.chapters_content[title] = content

            sanitized_title = self._sanitize_filename(f"chapter_{chapter_num}_{title}")
            chapter_filename = f"{sanitized_title}.txt"
            chapter_filepath = os.path.join(output_dir, chapter_filename)

            try:
                with open(chapter_filepath, "w", encoding="utf-8") as f:
                    f.write(f"Chapter: {title}\n\n{content}")
                all_chapters_text.append(f"Chapter: {title}\n\n{content}\n\n---\n\n")
            except IOError as e:
                self.status = f"failed: could not write chapter file {chapter_filepath} - {e}"
                return
            chapter_num += 1

        # Create a single full_book.txt
        full_book_filepath = os.path.join(output_dir, "full_book.txt")
        try:
            with open(full_book_filepath, "w", encoding="utf-8") as f:
                f.write("".join(all_chapters_text))
            self.output_path = full_book_filepath
            self.status = "completed"
            self.output = self.output_path # self.output from base class
        except IOError as e:
            self.status = f"failed: could not write full book file {full_book_filepath} - {e}"
            self.output_path = None # Ensure output_path is None if final write fails

    def get_status(self) -> str:
        if self.status == "completed":
            if self.output_path and os.path.exists(self.output_path):
                # Additionally, one might check if all individual chapter files exist if that's part of the contract
                return "completed"
            else:
                self.status = "failed: output file missing"
        return self.status

    def get_output(self):
        if self.status == "completed" and self.output_path:
            # Could also return a dict like:
            # {"full_book_path": self.output_path, "chapters": self.chapters_content, "outline": self.book_outline}
            return self.output_path
        return None
