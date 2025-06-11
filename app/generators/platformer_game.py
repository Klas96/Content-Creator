import os
import json # For parsing LLM responses if structured
from pathlib import Path
import asyncio # For async operations if needed beyond FastAPI's handling
import aiofiles # For async file reading

from app.config import LLM_PROVIDER, OUTPUT_DIR
from app.utils.prompt_loader import load_prompt
from app.generators.openai_content import generate_story_openai
from app.generators.anthropic_content import generate_story_anthropic
from app.generators.image import generate_images

# Constants for game generation
DEFAULT_CANVAS_WIDTH = 800
DEFAULT_CANVAS_HEIGHT = 600
PROCESSING_GAME_TEMPLATE_PATH = "templates/processing_js_template/processing_game_template.html"
CONCEPT_PROMPT_FILE = "platformer_game_prompt.txt" # For initial game design
PROCESSING_CODE_PROMPT_FILE = "processing_game_code_prompt.txt" # For Processing.js code

async def generate_platformer_game(theme: str) -> str:
    """
    Generates a complete HTML file with embedded Processing.js game code
    based on the provided theme.
    """
    game_output_dir_name = theme.replace(" ", "_").replace("-", "_").lower()
    # Ensure game_output_dir_name is a valid directory name (e.g. no special chars beyond _-)
    game_output_dir_name = "".join(c if c.isalnum() or c in ['_', '-'] else '_' for c in game_output_dir_name)
    game_output_path = Path(OUTPUT_DIR) / "processing_games" / game_output_dir_name

    try:
        # 0. Create output directory
        game_output_path.mkdir(parents=True, exist_ok=True)

        # 1. Load HTML Template
        try:
            async with aiofiles.open(PROCESSING_GAME_TEMPLATE_PATH, mode='r', encoding='utf-8') as f:
                html_template_content = await f.read()
        except FileNotFoundError:
            return f"Error: HTML template file not found at {PROCESSING_GAME_TEMPLATE_PATH}."
        except Exception as e:
            return f"Error reading HTML template: {str(e)}"

        # 2. Generate Game Design Elements (Conceptual)
        try:
            conceptual_prompt = load_prompt(CONCEPT_PROMPT_FILE)
        except FileNotFoundError:
            return f"Error: Conceptual prompt file not found: {CONCEPT_PROMPT_FILE}"
        formatted_conceptual_prompt = conceptual_prompt.format(theme=theme)

        if LLM_PROVIDER == "openai":
            conceptual_design_text = await generate_story_openai(formatted_conceptual_prompt)
        elif LLM_PROVIDER == "anthropic":
            conceptual_design_text = await generate_story_anthropic(formatted_conceptual_prompt)
        else:
            return f"Error: Unsupported LLM_PROVIDER: {LLM_PROVIDER}"

        # Basic parsing of conceptual_design_text (rudimentary)
        player_name = theme + " Hero" # Default
        player_abilities = "jump" # Default
        level_description = f"A level in the world of {theme}" # Default

        # Attempt to find 'Name:' for player_name
        name_marker = "Name:"
        name_idx = conceptual_design_text.find(name_marker)
        if name_idx != -1:
            line_end_idx = conceptual_design_text.find("\n", name_idx)
            if line_end_idx != -1:
                player_name = conceptual_design_text[name_idx + len(name_marker):line_end_idx].strip()
            else:
                player_name = conceptual_design_text[name_idx + len(name_marker):].strip()

        abilities_marker = "Abilities:"
        abilities_idx = conceptual_design_text.find(abilities_marker)
        if abilities_idx != -1:
            line_end_idx = conceptual_design_text.find("\n", abilities_idx)
            if line_end_idx != -1:
                player_abilities = conceptual_design_text[abilities_idx + len(abilities_marker):line_end_idx].strip()
            else:
                 player_abilities = conceptual_design_text[abilities_idx + len(abilities_marker):].strip()


        # 3. Define Game Parameters and Asset Names
        canvas_width = DEFAULT_CANVAS_WIDTH
        canvas_height = DEFAULT_CANVAS_HEIGHT
        asset_names = {
            "player": "player.png", "enemy1": "enemy1.png", "platform": "platform.png",
            "background": "background.png", "collectible": "coin.png"
        }
        asset_paths_in_code = {key: name for key, name in asset_names.items()}

        # 4. Generate Image Assets
        image_gen_prompts = {
            "player": f"pixel art main character, {theme} theme", "enemy1": f"pixel art enemy, {theme} theme",
            "platform": f"pixel art platform tile, {theme} theme", "background": f"pixel art background, {theme} theme, side-scrolling",
            "collectible": f"pixel art coin, {theme} theme"
        }
        for asset_key, img_prompt_text in image_gen_prompts.items():
            await generate_images(
                prompt=img_prompt_text,
                topic=theme,
                output_dir=str(game_output_path),
                filename=asset_names[asset_key],
                content_type="story"
            )

        # 5. Prepare Data for Processing.js Code Prompt
        processing_prompt_data = {
            "GAME_THEME": theme, "PLAYER_NAME": player_name, "PLAYER_APPEARANCE": f"Hero of {theme}", # Appearance not parsed yet
            "PLAYER_ABILITIES": player_abilities, "PLAYER_SPRITE_PATH": asset_paths_in_code["player"],
            "ENEMY_CONCEPTS": json.dumps([{"name": "Generic Enemy", "appearance": f"Enemy from {theme}", "behavior": "patrols", "sprite_path": asset_paths_in_code["enemy1"]}]),
            "LEVEL_DESCRIPTION": level_description, "CANVAS_WIDTH": canvas_width, "CANVAS_HEIGHT": canvas_height,
            "BACKGROUND_IMAGE_PATH": asset_paths_in_code["background"],
            "PLATFORM_DATA": json.dumps([
                {"x": canvas_width / 2, "y": canvas_height - 20, "width": canvas_width, "height": 20, "sprite_path": asset_paths_in_code["platform"]},
                {"x": 200, "y": canvas_height - 150, "width": 150, "height": 20, "sprite_path": asset_paths_in_code["platform"]},
            ]),
            "COLLECTIBLE_DATA": json.dumps([{"x": 100, "y": canvas_height - 100, "sprite_path": asset_paths_in_code["collectible"]}])
        }

        # 6. Generate Processing.js Code
        try:
            processing_code_prompt_template = load_prompt(PROCESSING_CODE_PROMPT_FILE)
        except FileNotFoundError:
            return f"Error: Processing code prompt file not found: {PROCESSING_CODE_PROMPT_FILE}"

        formatted_processing_code_prompt = processing_code_prompt_template.format(**processing_prompt_data)

        if LLM_PROVIDER == "openai":
            processing_js_code = await generate_story_openai(formatted_processing_code_prompt)
        elif LLM_PROVIDER == "anthropic":
            processing_js_code = await generate_story_anthropic(formatted_processing_code_prompt)
        else:
            return f"Error: Unsupported LLM_PROVIDER: {LLM_PROVIDER}"

        # Basic cleanup of LLM output
        if processing_js_code.strip().startswith("```processing"):
            lines = processing_js_code.strip().splitlines()
            processing_js_code = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        elif processing_js_code.strip().startswith("```"):
            lines = processing_js_code.strip().splitlines()
            processing_js_code = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])


        # 7. Inject Code and Data into HTML Template
        final_html_content = html_template_content.replace("// --- PROCESSING.JS CODE WILL BE INSERTED HERE BY THE GENERATOR ---", processing_js_code)
        final_html_content = final_html_content.replace("{{CANVAS_WIDTH}}", str(canvas_width))
        final_html_content = final_html_content.replace("{{CANVAS_HEIGHT}}", str(canvas_height))
        final_html_content = final_html_content.replace("{{GAME_THEME}}", theme)

        # 8. Save HTML file
        output_html_file_path = game_output_path / "index.html"
        async with aiofiles.open(output_html_file_path, mode='w', encoding='utf-8') as f:
            await f.write(final_html_content)

        print(f"Successfully generated Processing.js game at: {output_html_file_path.resolve()}")
        return final_html_content

    except FileNotFoundError as fnf_error:
        error_message = f"Error: A required file was not found: {str(fnf_error)}"
        print(error_message)
        return f"<html><body><h1>Generation Failed</h1><p>{error_message}</p></body></html>"
    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}"
        print(error_message)
        # Consider logging the traceback for debugging
        import traceback
        print(traceback.format_exc())
        return f"<html><body><h1>Generation Failed</h1><p>{error_message}</p><pre>{traceback.format_exc()}</pre></body></html>"
