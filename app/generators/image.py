import os
import io
from PIL import Image
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from stability_sdk import client as stability_client_sdk
from anthropic import Anthropic # Added as per instruction, though not used in current logic
from ..config import STABILITY_KEY, ANTHROPIC_KEY, TEST_MODE
from .base import ContentGenerator

def _create_mock_image(width=512, height=512, color=(100, 100, 200), text="Test Image"):
    """Helper function to create a simple test image with text."""
    img = Image.new('RGB', (width, height), color=color)
    # Simple text drawing - consider adding a font for better display if needed
    # from PIL import ImageDraw
    # draw = ImageDraw.Draw(img)
    # draw.text((10, 10), text, fill=(255,255,255))
    return img

class ImageGenerator(ContentGenerator):
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.stability_client = stability_client_sdk.StabilityInference(key=STABILITY_KEY)
        self.anthropic_client = Anthropic(api_key=ANTHROPIC_KEY) # Initialized as per instruction
        self.image_paths = []

    async def _generate_single_image(self, prompt: str, output_path: str):
        """Generate a single image from a prompt."""
        if TEST_MODE:
            img = _create_mock_image(text=prompt[:20]) # Use helper
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            img.save(output_path)
            self.status = "completed" # individual image status
            return

        try:
            # Generate image using Stability AI API
            # TODO: Make parameters like seed, steps, cfg_scale, width, height, sampler configurable
            answers = self.stability_client.generate(
                prompt=prompt,
                seed=123,
                steps=30,
                cfg_scale=7.0,
                width=512,
                height=512,
                samples=1,
                sampler=generation.SAMPLER_K_DPMPP_2M
            )

            for resp in answers:
                for artifact in resp.artifacts:
                    if artifact.type == generation.ARTIFACT_IMAGE:
                        img = Image.open(io.BytesIO(artifact.binary))
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        img.save(output_path)
                        self.status = "completed" # individual image status
                        return
            self.status = "failed: no image artifact returned"
        except Exception as e:
            self.status = f"failed: {e}"
            # Potentially re-raise or handle more gracefully
            raise

    async def generate(
        self,
        text_content: str,
        base_filename_prefix: str,
        output_dir: str,
        num_images: int = 3, # This parameter is tricky with current logic.
        content_type: str = "story",
        **kwargs
    ) -> list[str]:
        """Generate images for the content."""
        self.status = "processing"
        self.image_paths = []

        os.makedirs(output_dir, exist_ok=True)

        # Infer topic from text_content for prompts (simplified)
        # A more sophisticated topic extraction might be needed for robust performance.
        topic_guess = text_content.split('.')[0][:50] # Use first 50 chars of first sentence as topic guess

        # Generate main image (similar to old logic, adapting to new params)
        main_image_name = f"{base_filename_prefix}_main.jpg"
        main_image_path = os.path.join(output_dir, main_image_name)

        if content_type == "story":
            main_prompt = f"Portrait of character/scene based on: {topic_guess}, high quality digital art, detailed, professional photography"
        else: # educational
            main_prompt = f"Educational illustration about {topic_guess}, professional diagram, clean design, educational style"

        await self._generate_single_image(main_prompt, main_image_path)
        if os.path.exists(main_image_path):
            self.image_paths.append(main_image_path)

        # Generate content-specific images from paragraphs
        # The num_images parameter is used here to limit the number of paragraph images.
        # If num_images is less than 2, only main image might be generated.
        paragraphs = text_content.split('\n\n')
        # Max (num_images - 1) paragraph images to respect num_images approximately
        # (1 for main image, rest for paragraphs)
        num_paragraph_images_to_generate = max(0, num_images - 1)

        for i, paragraph in enumerate(paragraphs[:num_paragraph_images_to_generate]):
            scene_image_name = f"{base_filename_prefix}_scene_{i+1}.jpg"
            scene_image_path = os.path.join(output_dir, scene_image_name)

            if content_type == "story":
                scene_prompt = f"Scene from the story: {paragraph[:150]}, cinematic, high quality digital art"
            else: # educational
                scene_prompt = f"Educational illustration for content: {paragraph[:150]}, professional diagram, educational style"

            await self._generate_single_image(scene_prompt, scene_image_path)
            if os.path.exists(scene_image_path):
                self.image_paths.append(scene_image_path)
        
        if not self.image_paths:
            self.status = "failed: no images were generated"
        elif len(self.image_paths) < num_images and self.status != "processing": # Check if any specific error occurred
             # If fewer images than requested and no specific error, it might be due to fewer paragraphs
            pass # Status would be 'completed' from last successful _generate_single_image or 'failed' if an error occurred

        # Final status check
        if all(os.path.exists(p) for p in self.image_paths) and self.image_paths:
             self.status = "completed"
        elif not self.image_paths:
             self.status = "failed: No images generated"
        # If some images generated but not all, status might be partial or reflect last error

        return self.image_paths

    def get_status(self) -> str:
        if self.status == "completed":
            if not self.image_paths:
                return "failed: no image paths recorded"
            # Check if all files recorded actually exist
            if all(os.path.exists(p) for p in self.image_paths):
                return "completed"
            else:
                return "failed: one or more image files are missing"
        return self.status # Could be "processing", "pending", or "failed: {error}"

    def get_output(self):
        return self.image_paths