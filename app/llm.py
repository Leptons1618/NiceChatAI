\
import httpx
import json
from typing import List, Dict, AsyncIterator, Optional
import logging

from . import config # Use relative import

# Setup logging
logger = logging.getLogger(__name__)

async def check_ollama_connection() -> bool:
    # \"\"\"Check if the Ollama server is running and reachable.\"\"\"
    cfg = config.get_config()
    base_url = cfg.get("ollama_base_url", config.DEFAULT_CONFIG["ollama_base_url"])
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url, timeout=5)
            response.raise_for_status()
        logger.info("Ollama server connection successful.")
        return True
    except httpx.RequestError as e:
        logger.warning(f"Ollama server not reachable at {base_url}: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during Ollama connection check: {e}")
        return False

async def get_available_models() -> List[str]:
    # \"\"\"Fetch the list of available models from the Ollama server.\"\"\"
    cfg = config.get_config()
    base_url = cfg.get("ollama_base_url", config.DEFAULT_CONFIG["ollama_base_url"])

    if not await check_ollama_connection():
        # No ui.notify here, handle in UI layer
        return []
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/tags", timeout=10)
            response.raise_for_status()
        models_data = response.json()
        available_models = sorted([model['name'] for model in models_data.get('models', [])])
        logger.info(f"Fetched available models: {available_models}")
        # Update cache
        config.set_available_models_cache(available_models)
        # Set default if not already set and models are available
        if not config.get_default_model() and available_models:
             config.set_default_model(available_models[0])
        config.save_config() # Save cache and potentially new default
        return available_models
    except httpx.RequestError as e:
        logger.error(f"Error fetching Ollama models: {e}")
        return []
    except json.JSONDecodeError:
        logger.error("Failed to parse Ollama models response.")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred fetching Ollama models: {e}")
        return []

async def generate_ollama_response(
    client_id: str,
    user_input: str,
    model_name: str,
    system_prompt: Optional[str] = None # Add system_prompt parameter
) -> AsyncIterator[str]:
    """Generate a chatbot response using the specified Ollama model via streaming."""
    cfg = config.get_config()
    base_url = cfg.get("ollama_base_url", config.DEFAULT_CONFIG["ollama_base_url"])
    timeout = cfg.get("ollama_timeout", config.DEFAULT_CONFIG["ollama_timeout"])

    # Define a default system prompt if none is provided
    if system_prompt is None:
        system_prompt = (
            "You are a helpful, knowledgeable assistant. Respond with well-structured, clear answers using Markdown formatting. "
            "For code examples, always use triple backticks with the language specified (e.g., ```python, ```javascript). "
            "When appropriate, include explanations with your code. Format lists, tables, and headings properly with Markdown. "
            "If you're unsure about something, acknowledge the uncertainty rather than providing incorrect information. "
            "Keep responses concise but thorough, focusing on accuracy and clarity."
        )

    if not model_name:
        yield "[Error: No model selected.]"
        return
    if not await check_ollama_connection():
        yield "[Error: Ollama server not reachable.]"
        return

    logger.info(f"Streaming prompt to model {model_name} for client {client_id}...")

    try:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                'POST',
                f"{base_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": user_input, # Use user_input directly as prompt
                    "system": system_prompt, # Add the system prompt
                    "stream": True
                },
                timeout=timeout
            ) as response:
                if response.status_code != 200:
                    error_content = await response.aread()
                    logger.error(f"Ollama API request failed for client {client_id} with status {response.status_code}: {error_content.decode()}")
                    yield f"\\n[Error: Ollama API request failed with status {response.status_code}]"
                    return

                async for line in response.aiter_lines():
                    if line:
                        try:
                            chunk_data = json.loads(line)
                            if 'response' in chunk_data:
                                yield chunk_data['response']
                            if chunk_data.get('error'):
                                logger.error(f"Ollama stream error for client {client_id}: {chunk_data['error']}")
                                yield f"\\n[Error from Ollama: {chunk_data['error']}]"
                            if chunk_data.get('done'):
                                logger.info(f"Ollama stream finished for client {client_id}.")
                                break
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse stream chunk for client {client_id}: {line}")
                        except Exception as e:
                            logger.error(f"Error processing stream chunk for client {client_id}: {e}")
                            yield f"\\n[Error processing stream: {e}]"

    except httpx.TimeoutException:
        logger.warning(f"Ollama generation timed out for client {client_id}.")
        yield f"\\n[Error: Ollama generation timed out after {timeout} seconds.]"
    except httpx.RequestError as e:
        logger.error(f"Ollama API request failed for client {client_id}: {e}")
        yield f"\\n[Error: Ollama API request failed: {e}]"
    except Exception as e:
        logger.error(f"An unexpected error occurred during Ollama generation for client {client_id}: {e}")
        yield f"\\n[Error: An unexpected error occurred during generation: {e}]"

