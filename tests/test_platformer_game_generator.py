import pytest
from unittest.mock import patch, AsyncMock, mock_open, call
import os
from pathlib import Path # Import Path for assertions

# Set TEST_MODE for image generation mocking if your image generator uses it.
# This should be set before importing app.config if it reads it at import time.
os.environ['TEST_MODE'] = 'True'

# Import the function to test AFTER setting TEST_MODE
from app.generators.platformer_game import generate_platformer_game, PROCESSING_GAME_TEMPLATE_PATH, CONCEPT_PROMPT_FILE, PROCESSING_CODE_PROMPT_FILE, DEFAULT_CANVAS_WIDTH, DEFAULT_CANVAS_HEIGHT
from app.config import OUTPUT_DIR # For constructing expected paths

@pytest.mark.asyncio
@patch('app.generators.platformer_game.LLM_PROVIDER', 'openai') # Assuming OpenAI for this test
@patch('app.generators.platformer_game.load_prompt')
@patch('app.generators.platformer_game.generate_story_openai', new_callable=AsyncMock) # Mocks the LLM call
@patch('app.generators.platformer_game.generate_images', new_callable=AsyncMock) # Mocks image generation
@patch('app.generators.platformer_game.Path.mkdir') # Mocks directory creation
@patch('app.generators.platformer_game.aiofiles.open') # Mocks async file operations
async def test_generate_platformer_game_processing_js(
    mock_aio_open, # Corresponds to aiofiles.open
    mock_path_mkdir, # Corresponds to Path.mkdir
    mock_generate_images_func, # Corresponds to generate_images
    mock_llm_generate_story, # Corresponds to generate_story_openai
    mock_load_prompt_func  # Corresponds to load_prompt
):
    # --- Setup Mocks ---
    test_theme = "Jungle Adventure"
    sanitized_theme_for_path = "jungle_adventure" # From platformer_game.py logic

    # Setup for mock_load_prompt_func
    mock_load_prompt_func.side_effect = [
        "Conceptual prompt for {theme}", # For CONCEPT_PROMPT_FILE
        "Processing.js prompt for {GAME_THEME} with assets: {PLAYER_SPRITE_PATH}, etc." # For PROCESSING_CODE_PROMPT_FILE
    ]

    # Setup for mock_llm_generate_story
    # First call is for conceptual design, second for Processing.js code.
    conceptual_design_output = "Player Name: TestPlayer. Abilities: Jump. Level: A jungle." # Simplified
    mock_processing_code = "void setup() { size(800, 600); } void draw() { background(0); }"
    mock_llm_generate_story.side_effect = [
        conceptual_design_output, # Output for conceptual design prompt
        mock_processing_code      # Output for Processing.js code prompt
    ]

    # Setup for mock_aio_open (for reading template and writing output)
    html_template_content = """<!DOCTYPE html>
    <html><head><title>Game</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/processing.js/1.6.6/processing.min.js"></script>
    </head><body>
        <canvas id="gamecanvas"></canvas>
        <script type="text/processing" data-processing-target="gamecanvas">
        // --- PROCESSING.JS CODE WILL BE INSERTED HERE BY THE GENERATOR ---
        // Game Theme: {{GAME_THEME}}
        // Canvas Size: {{CANVAS_WIDTH}} x {{CANVAS_HEIGHT}}
        </script>
    </body></html>"""

    # Mock for async file operations
    async_file_mock_read = AsyncMock()
    async_file_mock_read.read = AsyncMock(return_value=html_template_content)

    async_file_mock_write = AsyncMock()
    async_file_mock_write.write = AsyncMock()

    # __aenter__ returns the async context manager, __aexit__ handles cleanup
    mock_template_open_cm = AsyncMock()
    mock_template_open_cm.__aenter__.return_value = async_file_mock_read

    mock_output_file_cm = AsyncMock()
    mock_output_file_cm.__aenter__.return_value = async_file_mock_write

    mock_aio_open.side_effect = [
        mock_template_open_cm, # For reading template
        mock_output_file_cm    # For writing index.html
    ]

    # Mock for generate_images: should return the filename as it's used for asset_paths_in_code
    async def mock_generate_images_side_effect(prompt, output_dir, filename):
        # Returns the full path, but platformer_game.py extracts filename from it
        return os.path.join(output_dir, filename)
    mock_generate_images_func.side_effect = mock_generate_images_side_effect


    # --- Call the function ---
    html_output = await generate_platformer_game(test_theme)

    # --- Assertions ---
    assert isinstance(html_output, str)
    assert "<!DOCTYPE html>" in html_output
    assert '<canvas id="gamecanvas">' in html_output
    assert '<script src="https://cdnjs.cloudflare.com/ajax/libs/processing.js/1.6.6/processing.min.js">' in html_output
    assert mock_processing_code in html_output
    # Check replacement of placeholders in the HTML template part (not just the JS code)
    assert f"// Game Theme: {test_theme}" in html_output
    assert f"// Canvas Size: {DEFAULT_CANVAS_WIDTH} x {DEFAULT_CANVAS_HEIGHT}" in html_output

    # Assert load_prompt calls
    expected_prompt_calls = [
        call(CONCEPT_PROMPT_FILE),
        call(PROCESSING_CODE_PROMPT_FILE)
    ]
    mock_load_prompt_func.assert_has_calls(expected_prompt_calls, any_order=False) # Order matters here

    # Assert LLM calls (conceptual design + processing code)
    assert mock_llm_generate_story.call_count == 2
    # Could add assertions here for the content of the prompts passed to the LLM if needed

    # Assert directory creation
    expected_game_output_dir = Path(OUTPUT_DIR) / "processing_games" / sanitized_theme_for_path
    mock_path_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    # Check that the mock_path_mkdir was called on the correct Path object instance
    # The mock is on Path.mkdir, so the first arg to the mock is the Path instance itself.
    assert mock_path_mkdir.call_args[0][0] == expected_game_output_dir


    # Assert image generation calls
    asset_names = { "player": "player.png", "enemy1": "enemy1.png", "platform": "platform.png", "background": "background.png", "collectible": "coin.png"}
    image_gen_prompts_expected = {
        "player": f"pixel art main character for a 2D platformer game with a {test_theme} theme",
        "enemy1": f"pixel art enemy for a 2D platformer game with a {test_theme} theme",
        "platform": f"pixel art platform tile for a 2D platformer game with a {test_theme} theme",
        "background": f"pixel art background for a 2D platformer game level with a {test_theme} theme, side-scrolling view",
        "collectible": f"pixel art coin collectible for a 2D platformer game with a {test_theme} theme"
    }
    expected_image_calls = []
    for asset_key, filename in asset_names.items():
        expected_image_calls.append(
            call(prompt=image_gen_prompts_expected[asset_key], output_dir=str(expected_game_output_dir), filename=filename)
        )
    mock_generate_images_func.assert_has_calls(expected_image_calls, any_order=True) # Order might not be guaranteed by dict iteration
    assert mock_generate_images_func.call_count == len(asset_names)

    # Assert file operations
    # First call to aiofiles.open is for reading the template
    mock_aio_open.assert_any_call(PROCESSING_GAME_TEMPLATE_PATH, mode='r', encoding='utf-8')
    # Second call to aiofiles.open is for writing index.html
    expected_index_html_path = expected_game_output_dir / "index.html"
    mock_aio_open.assert_any_call(expected_index_html_path, mode='w', encoding='utf-8')

    # Check that write was called on the correct mock object with the html_output
    async_file_mock_write.write.assert_called_once_with(html_output)

    # Verify that __aenter__ and __aexit__ were called for both file operations
    assert mock_template_open_cm.__aenter__.called
    assert mock_output_file_cm.__aenter__.called
    # __aexit__ calls are not explicitly checked here but would be in a full context manager test
```
