import httpx
import json
import asyncio # Added for potential direct anthropic call if not using to_thread
from app.config import OLLAMA_API_BASE_URL, OLLAMA_MODEL_NAME, ANTHROPIC_KEY, LLM_PROVIDER
from anthropic import Anthropic

# Initialize Anthropic client (if ANTHROPIC_KEY is available)
if ANTHROPIC_KEY:
    anthropic_client = Anthropic(api_key=ANTHROPIC_KEY)
else:
    anthropic_client = None # Or handle this case more gracefully depending on requirements

# Define a timeout for HTTP requests (e.g., 60 seconds)
DEFAULT_TIMEOUT = 60.0

async def generate_ollama_completion(prompt: str, model: str = None, temperature: float = 0.7, num_predict: int = -1) -> str:
    """
    Generates a text completion using a locally running Ollama instance.
    Assumes Ollama API is compatible with the OpenAI completions API structure for the /api/generate endpoint.
    Ref: https://github.com/ollama/ollama/blob/main/docs/api.md#generate-a-completion
    """
    if model is None:
        model = OLLAMA_MODEL_NAME

    api_url = f"{OLLAMA_API_BASE_URL}/api/generate" # Standard Ollama API endpoint for generation

    payload_options = {"temperature": temperature}
    if num_predict > 0:
        payload_options["num_predict"] = num_predict

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False, # Get the full response at once
        "options": payload_options
    }

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(api_url, json=payload)
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

            # The response from Ollama's /api/generate when stream=False is a single JSON object
            # where each line is a JSON object if stream=True.
            # For stream=False, it's a single JSON response.
            # Example: {"model":"llama2","created_at":"...","response":"Hello!","done":true,"context":[...], ...}
            response_data = response.json()

            if response_data.get("done"):
                return response_data.get("response", "").strip()
            else:
                # This case should ideally not happen with stream=False if the request is successful
                return "Error: Ollama generation did not complete as expected."

    except httpx.HTTPStatusError as e:
        # Log the error or handle it more gracefully
        error_message = f"Ollama API request failed with status {e.response.status_code}: {e.response.text}"
        print(error_message) # Or use proper logging
        return f"Error: Ollama API request failed. {e.response.status_code}"
    except httpx.RequestError as e:
        # Handle network errors, timeout, etc.
        error_message = f"Ollama API request failed: {str(e)}"
        print(error_message) # Or use proper logging
        return f"Error: Ollama API request failed. {str(e)}"
    except json.JSONDecodeError as e:
        error_message = f"Failed to decode JSON response from Ollama: {str(e)}"
        print(error_message)
        return "Error: Invalid JSON response from Ollama."

async def generate_text_completion(prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
    """
    Generates a text completion using the configured LLM provider.
    """
    if LLM_PROVIDER == "ollama":
        # Note: max_tokens isn't directly passed to generate_ollama_completion's current payload. # This comment is now less relevant
        # Ollama's /api/generate might have a 'num_predict' in options, but it's not standard for all models. # This comment is now less relevant
        # This could be a future enhancement for the Ollama client. # This comment is now less relevant
        try:
            return await generate_ollama_completion(prompt, temperature=temperature, num_predict=max_tokens)
        except Exception as e:
            # Log or handle specific errors from Ollama client if needed
            print(f"Error during Ollama completion: {e}")
            return f"Error: Ollama generation failed. Reason: {e}"

    elif LLM_PROVIDER == "anthropic":
        if not anthropic_client:
            return "Error: Anthropic client not initialized. Check ANTHROPIC_KEY."
        try:
            # Consider using asyncio.to_thread for blocking I/O if not already handled by the library
            # For httpx based libraries like new Anthropic SDK, it's usually async native.
            # The current anthropic SDK (0.7.4 as per requirements) uses httpx and is async friendly.
            completion_obj = await asyncio.to_thread( # Using to_thread for safety with older SDKs or if unsure.
                anthropic_client.completions.create,
                prompt=prompt,
                model="claude-2", # As specified
                max_tokens_to_sample=max_tokens,
                temperature=temperature
            )
            return completion_obj.completion.strip()
        except Exception as e:
            print(f"Error during Anthropic completion: {e}")
            return f"Error: Anthropic generation failed. Reason: {e}"
    else:
        print(f"Error: Unknown LLM_PROVIDER configured: {LLM_PROVIDER}")
        return "Error: Unknown LLM provider configured."

# Example usage (optional, for direct testing of this file)
if __name__ == "__main__":
    import asyncio

    async def main():
        # Ensure your Ollama server is running and the model is available
        # (e.g., ollama run llama2)
        test_prompt = "Why is the sky blue?"
        print(f"Sending prompt to Ollama: '{test_prompt}' using model '{OLLAMA_MODEL_NAME}' at {OLLAMA_API_BASE_URL}")

        # Temporarily override OLLAMA_MODEL_NAME for testing if needed
        # from app import config
        # config.OLLAMA_MODEL_NAME = "your_test_model"

        completion = await generate_ollama_completion(test_prompt)
        print(f"Ollama response:\n{completion}")

    # asyncio.run(main()) # Commented out to prevent execution during subtask
