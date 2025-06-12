import pytest
from unittest.mock import patch, AsyncMock, mock_open, call
import os
from pathlib import Path

# Assuming OUTPUT_DIR is available from config or can be hardcoded for test if not easily importable
# For this example, let's assume it's 'output' as used before. If it's from app.config, mock it or import it.
TEST_OUTPUT_DIR = "output"

os.environ['TEST_MODE'] = 'True'

# Import the function to test AFTER setting TEST_MODE and potentially mocking app.config.OUTPUT_DIR
from app.generators.platformer_game import generate_platformer_game, PROCESSING_GAME_TEMPLATE_PATH, CONCEPT_PROMPT_FILE, PROCESSING_CODE_PROMPT_FILE, DEFAULT_CANVAS_WIDTH, DEFAULT_CANVAS_HEIGHT
# Note: If app.config.OUTPUT_DIR is used by platformer_game.py at its module level (not just inside the function),
# then the patch for OUTPUT_DIR needs to be applied before platformer_game is imported.
# However, platformer_game.py imports OUTPUT_DIR from app.config. So we patch where it's LOOKED UP.
# Patching 'app.generators.platformer_game.OUTPUT_DIR' assumes OUTPUT_DIR is a global in that module,
# or imported into its namespace like 'from app.config import OUTPUT_DIR'.

@pytest.mark.asyncio
@patch('app.generators.platformer_game.OUTPUT_DIR', TEST_OUTPUT_DIR) # Mock OUTPUT_DIR where it's used
@patch('app.generators.platformer_game.LLM_PROVIDER', 'openai')
@patch('app.generators.platformer_game.load_prompt')
@patch('app.generators.platformer_game.generate_story_openai', new_callable=AsyncMock)
@patch('app.generators.platformer_game.generate_image', new_callable=AsyncMock) # CHANGED: from generate_images to generate_image
@patch('app.generators.platformer_game.Path.mkdir') # Patching Path.mkdir directly on the class
@patch('app.generators.platformer_game.aiofiles.open', new_callable=AsyncMock) # Mock async open for the module
async def test_generate_platformer_game_processing_js(
    mock_aiofiles_open_call, # This is the mock object for the aiofiles.open function itself
    mock_path_mkdir_method,   # This is the mock for the Path.mkdir method
    mock_generate_image_func, # Mock name can remain, but it now mocks generate_image
    mock_llm_openai_func,
    mock_load_prompt_func
):
    # --- Setup Mocks (largely the same) ---
    test_theme = "Jungle Adventure"
    test_job_id = "test-job-123"

    # Constants from app.generators.platformer_game, if not imported directly
    # PROCESSING_GAME_TEMPLATE_PATH = "templates/processing_js_template/processing_game_template.html"
    # CONCEPT_PROMPT_FILE = "platformer_game_prompt.txt"
    # PROCESSING_CODE_PROMPT_FILE = "processing_game_code_prompt.txt"
    # DEFAULT_CANVAS_WIDTH = 800
    # DEFAULT_CANVAS_HEIGHT = 600

    mock_load_prompt_func.side_effect = [
        "Conceptual prompt for {theme}. Player: TestPlayer. Abilities: Jump.", # Simplified conceptual prompt output
        "Processing.js prompt for {GAME_THEME} with assets: {PLAYER_SPRITE_PATH}, etc. Canvas: {CANVAS_WIDTH}x{CANVAS_HEIGHT}."
    ]
    conceptual_llm_output = "Player Name: TestPlayer. Abilities: Jump, Run. Level: A jungle." # This is what the first LLM call returns
    mock_processing_code = "void setup() { size(800, 600); Processing.println('Game Started!'); } void draw() { background(0); }"
    mock_llm_openai_func.side_effect = [conceptual_llm_output, mock_processing_code]

    html_template_content = """
    <!DOCTYPE html>
    <html><head><title>Generated Platformer Game</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/processing.js/1.6.6/processing.min.js"></script>
    </head>
    <body>
        <canvas id="gamecanvas"></canvas>
        <script type="text/processing" data-processing-target="gamecanvas">
        // Game Theme: {{GAME_THEME}}
        // Canvas Size: {{CANVAS_WIDTH}} x {{CANVAS_HEIGHT}}
        // --- PROCESSING.JS CODE WILL BE INSERTED HERE BY THE GENERATOR ---
        </script>
    </body></html>
    """

    # Mocks for async file operations (template read, index.html write)
    mock_template_file_handle = AsyncMock()
    mock_template_file_handle.read = AsyncMock(return_value=html_template_content)
    mock_template_file_handle.__aenter__.return_value = mock_template_file_handle

    mock_index_file_handle = AsyncMock()
    mock_index_file_handle.write = AsyncMock()
    mock_index_file_handle.__aenter__.return_value = mock_index_file_handle

    def open_side_effect_func(path_arg, mode, encoding):
        if PROCESSING_GAME_TEMPLATE_PATH in str(path_arg):
            return mock_template_file_handle
        elif "index.html" in str(path_arg):
            return mock_index_file_handle
        raise FileNotFoundError(f"Test mock: Unexpected file open: {path_arg}")

    mock_aiofiles_open_call.side_effect = open_side_effect_func

    async def mock_generate_image_side_effect_func(prompt, output_path): # Changed signature
        # generate_image is expected to handle the full path including filename
        Path(output_path).parent.mkdir(parents=True, exist_ok=True) # Simulate dir creation if needed by mock
        with open(output_path, 'w') as f: f.write("mock image data") # Simulate file creation
        return output_path # Or whatever generate_image returns
    mock_generate_image_func.side_effect = mock_generate_image_side_effect_func

    # --- Call the function under test ---
    html_output = await generate_platformer_game(theme=test_theme, job_id=test_job_id)

    # --- Assertions ---
    assert isinstance(html_output, str)
    assert mock_processing_code in html_output
    assert f"// Canvas Size: {DEFAULT_CANVAS_WIDTH} x {DEFAULT_CANVAS_HEIGHT}" in html_output
    assert f"// Game Theme: {test_theme}" in html_output

    mock_load_prompt_func.assert_has_calls([
        call(CONCEPT_PROMPT_FILE), call(PROCESSING_CODE_PROMPT_FILE)
    ])
    assert mock_llm_openai_func.call_count == 2

    expected_output_dir = Path(TEST_OUTPUT_DIR) / test_job_id
    expected_assets_dir = expected_output_dir / "assets"

    mkdir_calls_made = [ args[0] for args, _ in mock_path_mkdir_method.call_args_list ]
    assert expected_output_dir in mkdir_calls_made
    assert expected_assets_dir in mkdir_calls_made
    mock_path_mkdir_method.assert_has_calls([
        call(expected_output_dir, parents=True, exist_ok=True),
        call(expected_assets_dir, parents=True, exist_ok=True)
    ], any_order=True)

    # Assert image generation calls (UPDATED)
    expected_image_prompts_and_paths = [
        (f"pixel art style, main player character for a 2D platformer game with a '{test_theme}' theme", str(expected_assets_dir / "player.png")),
        (f"pixel art style, common enemy for a 2D platformer game with a '{test_theme}' theme", str(expected_assets_dir / "enemy1.png")),
        (f"pixel art style, basic platform tile or ground block for a 2D platformer game with a '{test_theme}' theme", str(expected_assets_dir / "platform.png")),
        (f"pixel art style, parallax background for a 2D platformer game with a '{test_theme}' theme, side-scrolling view", str(expected_assets_dir / "background.png")),
        (f"pixel art style, collectible item (e.g., coin, gem, or fruit) for a 2D platformer game with a '{test_theme}' theme", str(expected_assets_dir / "collectible.png")),
    ]
    expected_image_calls = [
        call(prompt=p, output_path=op)
        for p, op in expected_image_prompts_and_paths
    ]
    mock_generate_image_func.assert_has_calls(expected_image_calls, any_order=True)
    assert mock_generate_image_func.call_count == len(expected_image_calls)

    # Assert file open calls
    expected_index_html_path = expected_output_dir / "index.html"
    mock_aiofiles_open_call.assert_any_call(PROCESSING_GAME_TEMPLATE_PATH, mode='r', encoding='utf-8')
    mock_aiofiles_open_call.assert_any_call(expected_index_html_path, mode='w', encoding='utf-8')
    mock_index_file_handle.write.assert_called_once_with(html_output)

    assert mock_template_file_handle.__aenter__.called
    assert mock_index_file_handle.__aenter__.called
```
