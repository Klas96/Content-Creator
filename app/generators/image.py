import os
import io
from PIL import Image
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from stability_sdk import client as stability_client
from ..config import STABILITY_KEY, TEST_MODE

stability_client = stability_client.StabilityInference(key=STABILITY_KEY)

def create_mock_image(width=512, height=512, color=(100, 100, 200), text="Test Image"):
    """Create a simple test image with text."""
    img = Image.new('RGB', (width, height), color=color)
    return img

async def generate_images(
    content: str,
    topic: str,
    output_dir: str,
    content_type: str = "story"
) -> list[str]:
    """Generate images for the content."""
    image_paths = []
    
    # Generate main image
    main_image_path = os.path.join(output_dir, "main.jpg")
    if content_type == "story":
        prompt = f"Portrait of {topic}, high quality digital art, detailed, professional photography"
    else:
        prompt = f"Educational illustration about {topic}, professional diagram, clean design, educational style"
    
    await generate_image(prompt, main_image_path)
    image_paths.append(main_image_path)
    
    # Generate content-specific images
    paragraphs = content.split('\n\n')
    for i, paragraph in enumerate(paragraphs):
        scene_image_path = os.path.join(output_dir, f"scene_{i+1}.jpg")
        if content_type == "story":
            prompt = f"Scene from the story: {paragraph[:200]}, cinematic, high quality digital art"
        else:
            prompt = f"Educational illustration: {paragraph[:200]}, professional diagram, educational style"
        
        await generate_image(prompt, scene_image_path)
        image_paths.append(scene_image_path)
    
    return image_paths

async def generate_image(prompt: str, output_path: str):
    """Generate a single image from a prompt."""
    if TEST_MODE:
        img = create_mock_image(text=prompt[:20])
        img.save(output_path)
        return
    
    # Generate image using Stability AI API
    answers = stability_client.generate(
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
                img.save(output_path)
                return 