def get_image_prompts(file_path):
    with open(file_path, 'r') as file:
        data = file.read()

    prompts = [prompt for prompt in data.split('\n') if prompt.startswith('<image_prompt_')]
    return prompts
