import pytest
from unittest.mock import patch, AsyncMock
from app.llm_clients import generate_text_completion

# Pytest needs to discover async tests
pytestmark = pytest.mark.asyncio

@pytest.mark.asyncio
async def test_generate_text_completion_uses_anthropic_default():
    """Test that Anthropic is used by default if LLM_PROVIDER is not 'ollama'."""
    # Patch LLM_PROVIDER to something other than 'ollama', or ensure it's default 'anthropic'
    # Also patch the actual client call to prevent real API calls and check it was called.
    with patch('app.config.LLM_PROVIDER', 'anthropic'), \
         patch('app.llm_clients.anthropic_client.completions.create', new_callable=AsyncMock) as mock_anthropic_call:

        # Ensure anthropic_client itself is not None for this test path
        with patch('app.llm_clients.anthropic_client', new_callable=AsyncMock) as mock_client_instance:
            # Configure the mock client instance's create method
            mock_client_instance.completions.create = mock_anthropic_call
            mock_anthropic_call.return_value.completion = "Anthropic response"

            await generate_text_completion("test prompt for anthropic")
            mock_anthropic_call.assert_called_once()

@pytest.mark.asyncio
async def test_generate_text_completion_uses_ollama():
    """Test that Ollama client is used when LLM_PROVIDER is 'ollama'."""
    with patch('app.config.LLM_PROVIDER', 'ollama'), \
         patch('app.llm_clients.generate_ollama_completion', new_callable=AsyncMock) as mock_ollama_call:
        mock_ollama_call.return_value = "Ollama response"

        await generate_text_completion("test prompt for ollama")
        mock_ollama_call.assert_called_once()

@pytest.mark.asyncio
async def test_generate_text_completion_unknown_provider():
    """Test handling of an unknown LLM_PROVIDER."""
    with patch('app.config.LLM_PROVIDER', 'unknown_provider'):
        result = await generate_text_completion("test prompt for unknown")
        assert "Error: Unknown LLM provider configured." in result

@pytest.mark.asyncio
async def test_generate_text_completion_anthropic_init_error():
    """Test handling if Anthropic client failed to initialize (e.g. no key)."""
    with patch('app.config.LLM_PROVIDER', 'anthropic'), \
         patch('app.llm_clients.anthropic_client', None): # Simulate client being None
        result = await generate_text_completion("test prompt for anthropic no client")
        assert "Error: Anthropic client not initialized." in result

# It might also be useful to test the error propagation from underlying clients,
# e.g., if generate_ollama_completion itself returns an "Error: ..." string.
@pytest.mark.asyncio
async def test_generate_text_completion_ollama_returns_error():
    """Test that an error string from generate_ollama_completion is passed through."""
    with patch('app.config.LLM_PROVIDER', 'ollama'), \
         patch('app.llm_clients.generate_ollama_completion', new_callable=AsyncMock) as mock_ollama_call:
        mock_ollama_call.return_value = "Error: Ollama internal failure."

        result = await generate_text_completion("test prompt for ollama error")
        assert result == "Error: Ollama internal failure."

@pytest.mark.asyncio
async def test_generate_text_completion_anthropic_api_exception():
    """Test that an exception from anthropic_client.completions.create is handled."""
    with patch('app.config.LLM_PROVIDER', 'anthropic'), \
         patch('app.llm_clients.anthropic_client.completions.create', new_callable=AsyncMock) as mock_anthropic_call:

        # Ensure anthropic_client itself is not None for this test path
        with patch('app.llm_clients.anthropic_client', new_callable=AsyncMock) as mock_client_instance:
            mock_client_instance.completions.create = mock_anthropic_call
            mock_anthropic_call.side_effect = Exception("Anthropic API Error")

            result = await generate_text_completion("test prompt for anthropic exception")
            assert "Error: Anthropic generation failed. Reason: Anthropic API Error" in result
