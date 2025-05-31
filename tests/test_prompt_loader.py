import pytest
from unittest.mock import patch, mock_open
from app.utils.prompt_loader import load_prompt, PROMPTS_DIR # Assuming PROMPTS_DIR is accessible for context, though we mock 'open'

# Test `test_load_prompt_success`
def test_load_prompt_success_with_all_args():
    dummy_template = "Hello {name}. Topic: {topic}. Optional: {optional_section} Custom: {custom_instructions_section}"
    m = mock_open(read_data=dummy_template)
    with patch('builtins.open', m):
        with patch('app.utils.prompt_loader.Path.is_file', return_value=True): # Ensure path check passes
            result = load_prompt(
                "dummy_prompt.txt",
                name="World",
                topic="Testing",
                optional_section="This is optional.",
                custom_instructions_section="Custom instruction here."
            )
    m.assert_called_once_with(PROMPTS_DIR / "dummy_prompt.txt", "r", encoding="utf-8")
    assert result == "Hello World. Topic: Testing. Optional: This is optional. Custom: Custom instruction here."

def test_load_prompt_success_optional_section_empty():
    dummy_template = "Hello {name}. Topic: {topic}.\n{optional_section}\nKeep this line."
    m = mock_open(read_data=dummy_template)
    with patch('builtins.open', m):
        with patch('app.utils.prompt_loader.Path.is_file', return_value=True):
            result = load_prompt(
                "dummy_prompt.txt",
                name="World",
                topic="Testing",
                optional_section="" # Empty optional section
            )
    # The placeholder line {optional_section} should be removed if empty
    assert result == "Hello World. Topic: Testing.\nKeep this line."

def test_load_prompt_success_optional_section_not_provided():
    dummy_template = "Hello {name}. Topic: {topic}.\n{optional_section}\nKeep this line."
    m = mock_open(read_data=dummy_template)
    with patch('builtins.open', m):
        with patch('app.utils.prompt_loader.Path.is_file', return_value=True):
            result = load_prompt(
                "dummy_prompt.txt",
                name="World",
                topic="Testing"
                # optional_section is not provided
            )
    # The placeholder line {optional_section} should be removed
    assert result == "Hello World. Topic: Testing.\nKeep this line."


# Test `test_load_prompt_file_not_found`
def test_load_prompt_file_not_found():
    # Simulate Path(..).is_file() returning False for all attempts in prompt_loader
    with patch('app.utils.prompt_loader.Path.is_file', return_value=False):
        result = load_prompt("non_existent_prompt.txt")
    assert "Error: Prompt template file 'non_existent_prompt.txt' not found" in result

# Test `test_load_prompt_missing_placeholder_in_kwargs` (KeyError from .format)
def test_load_prompt_missing_formatter_kwargs():
    dummy_template = "Hello {name}. Topic: {topic}."
    m = mock_open(read_data=dummy_template)
    with patch('builtins.open', m):
        with patch('app.utils.prompt_loader.Path.is_file', return_value=True):
            result = load_prompt("dummy_prompt.txt", name="World") # Missing 'topic'
    assert "Error: Missing placeholder" in result
    assert "'topic'" in result


# Test `test_load_prompt_section_placeholder_logic`
def test_load_prompt_section_placeholder_logic_filled():
    dummy_template = "Main content.\n{custom_instructions_section}\nEnd content."
    m = mock_open(read_data=dummy_template)
    with patch('builtins.open', m):
        with patch('app.utils.prompt_loader.Path.is_file', return_value=True):
            result = load_prompt("dummy_prompt.txt", custom_instructions_section="Follow this instruction.")
    assert result == "Main content.\nFollow this instruction.\nEnd content."

def test_load_prompt_section_placeholder_logic_empty():
    # Test when section is empty string
    dummy_template = "Main content.\n{custom_instructions_section}\nEnd content."
    m = mock_open(read_data=dummy_template)
    with patch('builtins.open', m):
        with patch('app.utils.prompt_loader.Path.is_file', return_value=True):
            result = load_prompt("dummy_prompt.txt", custom_instructions_section="")
    assert result == "Main content.\nEnd content." # Line with placeholder removed

def test_load_prompt_section_placeholder_logic_not_provided():
    # Test when section kwarg is not provided at all
    dummy_template = "Main content.\n{custom_instructions_section}\nEnd content."
    m = mock_open(read_data=dummy_template)
    with patch('builtins.open', m):
        with patch('app.utils.prompt_loader.Path.is_file', return_value=True):
            result = load_prompt("dummy_prompt.txt") # No section kwarg
    assert result == "Main content.\nEnd content." # Line with placeholder removed

def test_load_prompt_multiple_sections_mixed():
    dummy_template = "Start.\n{section_a}\nMiddle.\n{section_b}\nEnd."
    m = mock_open(read_data=dummy_template)
    with patch('builtins.open', m):
        with patch('app.utils.prompt_loader.Path.is_file', return_value=True):
            # Provide section_a, omit section_b
            result = load_prompt("dummy_prompt.txt", section_a="Content for A")
    assert result == "Start.\nContent for A\nMiddle.\nEnd."

    # Provide section_b, omit section_a
    m = mock_open(read_data=dummy_template) # Reset mock_open for fresh read_data
    with patch('builtins.open', m):
        with patch('app.utils.prompt_loader.Path.is_file', return_value=True):
            result = load_prompt("dummy_prompt.txt", section_b="Content for B")
    assert result == "Start.\nMiddle.\nContent for B\nEnd."

    # Provide both
    m = mock_open(read_data=dummy_template)
    with patch('builtins.open', m):
        with patch('app.utils.prompt_loader.Path.is_file', return_value=True):
            result = load_prompt("dummy_prompt.txt", section_a="Content for A", section_b="Content for B")
    assert result == "Start.\nContent for A\nMiddle.\nContent for B\nEnd."

    # Provide neither
    m = mock_open(read_data=dummy_template)
    with patch('builtins.open', m):
        with patch('app.utils.prompt_loader.Path.is_file', return_value=True):
            result = load_prompt("dummy_prompt.txt")
    assert result == "Start.\nMiddle.\nEnd."

def test_load_prompt_handles_io_error_gracefully():
    with patch('app.utils.prompt_loader.Path.is_file', return_value=True):
        with patch('builtins.open', mock_open()) as m:
            m.side_effect = IOError("Disk full")
            result = load_prompt("any_prompt.txt")
    assert "Error loading prompt 'any_prompt.txt': Disk full" in result
