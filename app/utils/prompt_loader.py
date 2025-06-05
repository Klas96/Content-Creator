from pathlib import Path
import os

PROMPTS_DIR = Path(os.path.dirname(__file__)).parent / "prompts"

def load_prompt(template_filename: str, **kwargs) -> str:
    try:
        prompt_template_path = PROMPTS_DIR / template_filename
        if not prompt_template_path.is_file():
             # Try one level up if utils is a direct subdir of app, and prompts is also subdir of app
            alt_prompts_dir = Path(os.path.dirname(__file__)).parent.parent / "prompts"
            prompt_template_path = alt_prompts_dir / template_filename
            if not prompt_template_path.is_file(): # Check again
                 # Try new path for utils being a subdir of app, and prompts being a subdir of root
                alt_prompts_dir = Path(os.path.dirname(__file__)).parent.parent / "prompts"
                prompt_template_path = alt_prompts_dir / template_filename
                if not prompt_template_path.is_file():
                    # Original path for PROMPTS_DIR assumes utils is a child of the same dir as prompts
                    # If utils is app/utils, then parent is app, then prompts should be app/prompts
                    # Path(__file__).resolve().parent.parent / "prompts"
                    # Let's assume PROMPTS_DIR should be relative to the project root 'app'
                    # If app/utils/prompt_loader.py, then Path(__file__).parent = app/utils
                    # Path(__file__).parent.parent = app
                    # So, app/prompts
                    current_file_path = Path(__file__).resolve() # app/utils/prompt_loader.py
                    app_dir = current_file_path.parent.parent # app
                    final_prompts_dir = app_dir / "prompts"
                    prompt_template_path = final_prompts_dir / template_filename
                    if not prompt_template_path.is_file():
                        # Fallback if script is run from project root for some reason
                        final_prompts_dir = Path.cwd() / "prompts"
                        prompt_template_path = final_prompts_dir / template_filename
                        if not prompt_template_path.is_file():
                             raise FileNotFoundError(f"Prompt template file '{template_filename}' not found after checking multiple common paths.")

                    # Update PROMPTS_DIR to the one that worked for future calls if needed, though this function is usually called once per generation.
                    # Or better, determine PROMPTS_DIR more robustly at module load.
                    # For now, this complex check is just to find it.

        with open(prompt_template_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        # Replace placeholders for optional sections first
        # to avoid errors if a section is not provided in kwargs
        section_placeholders = {
            "{custom_instructions_section}": kwargs.pop("custom_instructions_section", ""),
            "{call_to_action_section}": kwargs.pop("call_to_action_section", ""),
            "{characters_section}": kwargs.pop("characters_section", ""),
            "{plot_summary_section}": kwargs.pop("plot_summary_section", ""),
            "{previous_chapter_summary_section}": kwargs.pop("previous_chapter_summary_section", ""),
        }
        for placeholder, value in section_placeholders.items():
            if value: # Only add the section if value is not empty
                prompt_template = prompt_template.replace(placeholder, value)
            else: # Remove the placeholder line if the value is empty
                prompt_template = prompt_template.replace(placeholder + "\n", "") # common case is placeholder on its own line
                prompt_template = prompt_template.replace(placeholder, "") # in case it's not on its own line


        # Clean up empty lines that might result from removed optional sections
        lines = prompt_template.split('\n')
        cleaned_lines = [line for line in lines if line.strip()] # Remove empty or whitespace-only lines
        prompt_template = '\n'.join(cleaned_lines)

        return prompt_template.format(**kwargs)
    except FileNotFoundError:
        # This specific error message might be redundant if the FileNotFoundError above is raised
        return f"Error: Prompt template file '{template_filename}' not found at {PROMPTS_DIR / template_filename} or other checked paths."
    except KeyError as e:
        return f"Error: Missing placeholder {e} in prompt template '{template_filename}' for provided arguments: {list(kwargs.keys())}"
    except Exception as e:
        return f"Error loading prompt '{template_filename}': {str(e)}"
