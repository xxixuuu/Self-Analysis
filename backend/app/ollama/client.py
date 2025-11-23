"""
Ollama client for local LLM interactions.
"""
import logging
from typing import Optional, List, Dict, Any
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama API."""

    def __init__(self):
        """Initialize Ollama client."""
        self.base_url = settings.ollama_base_url
        self.default_model = settings.ollama_model
        self.timeout = settings.ollama_timeout

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Optional[str]:
        """
        Generate text using Ollama.

        Args:
            prompt: Input prompt
            model: Model name (default: llama3.2)
            system: System prompt
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text or None if error
        """
        model = model or self.default_model

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                    }
                }

                if system:
                    payload["system"] = system

                if max_tokens:
                    payload["options"]["num_predict"] = max_tokens

                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "")
                else:
                    logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Error calling Ollama API: {e}")
            return None

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Optional[str]:
        """
        Chat with Ollama using conversation history.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name
            temperature: Temperature for generation

        Returns:
            Assistant's response or None if error
        """
        model = model or self.default_model

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                        }
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("message", {}).get("content", "")
                else:
                    logger.error(f"Ollama chat error: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Error in Ollama chat: {e}")
            return None

    async def list_models(self) -> List[str]:
        """
        List available Ollama models.

        Returns:
            List of model names
        """
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{self.base_url}/api/tags")

                if response.status_code == 200:
                    result = response.json()
                    return [model["name"] for model in result.get("models", [])]
                else:
                    logger.error(f"Failed to list models: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}")
            return []

    async def check_health(self) -> bool:
        """
        Check if Ollama server is healthy.

        Returns:
            True if healthy
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False


# Global Ollama client instance
ollama_client = OllamaClient()
