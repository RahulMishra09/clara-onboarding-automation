"""
LLM client wrapper supporting multiple providers (Anthropic, OpenAI, Ollama).
Provides unified interface for zero-cost extraction.
"""

import json
import time
from typing import Optional, Dict, Any
from pathlib import Path

from config import (
    LLM_PROVIDER,
    ANTHROPIC_API_KEY,
    OPENAI_API_KEY,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    MAX_RETRIES,
    TIMEOUT_SECONDS
)
from logger import get_extraction_logger

logger = get_extraction_logger()


class LLMClient:
    """Unified LLM client supporting multiple providers."""

    def __init__(self, provider: Optional[str] = None):
        """
        Initialize LLM client.

        Args:
            provider: Override default provider ('anthropic', 'openai', 'ollama')
        """
        self.provider = provider or LLM_PROVIDER
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the appropriate LLM client based on provider."""
        logger.info(f"Initializing LLM client: {self.provider}")

        try:
            if self.provider == "anthropic":
                import anthropic
                if not ANTHROPIC_API_KEY:
                    raise ValueError("ANTHROPIC_API_KEY not set")
                self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                logger.info("✅ Anthropic client initialized")

            elif self.provider == "openai":
                import openai
                if not OPENAI_API_KEY:
                    raise ValueError("OPENAI_API_KEY not set")
                self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
                logger.info("✅ OpenAI client initialized")

            elif self.provider == "ollama":
                import ollama
                self.client = ollama.Client(host=OLLAMA_BASE_URL)
                logger.info(f"✅ Ollama client initialized ({OLLAMA_MODEL})")

            else:
                raise ValueError(f"Unknown provider: {self.provider}")

        except ImportError as e:
            logger.error(f"❌ Failed to import {self.provider} library: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to initialize {self.provider} client: {e}")
            raise

    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.0
    ) -> str:
        """
        Get completion from LLM with retry logic.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 = deterministic)

        Returns:
            Generated text response
        """
        for attempt in range(MAX_RETRIES):
            try:
                logger.debug(f"Attempt {attempt + 1}/{MAX_RETRIES}")

                if self.provider == "anthropic":
                    response = self._complete_anthropic(
                        prompt, system_prompt, max_tokens, temperature
                    )
                elif self.provider == "openai":
                    response = self._complete_openai(
                        prompt, system_prompt, max_tokens, temperature
                    )
                elif self.provider == "ollama":
                    response = self._complete_ollama(
                        prompt, system_prompt, max_tokens, temperature
                    )
                else:
                    raise ValueError(f"Unknown provider: {self.provider}")

                logger.info(f"✅ Completion successful ({len(response)} chars)")
                return response

            except Exception as e:
                logger.warning(f"⚠️  Attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ All {MAX_RETRIES} attempts failed")
                    raise

    def _complete_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> str:
        """Complete using Anthropic Claude."""
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = self.client.messages.create(**kwargs)
        return response.content[0].text

    def _complete_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> str:
        """Complete using OpenAI GPT."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

        return response.choices[0].message.content

    def _complete_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> str:
        """Complete using local Ollama."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = self.client.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            options={
                "temperature": temperature,
                "num_predict": max_tokens
            }
        )

        return response['message']['content']

    def extract_json(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response (handles markdown code blocks).

        Args:
            text: LLM response text

        Returns:
            Parsed JSON object
        """
        # Remove markdown code blocks if present
        text = text.strip()

        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]

        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON: {e}")
            logger.error(f"Response text: {text[:500]}...")
            raise


def test_llm_client():
    """Test the LLM client with a simple prompt."""
    logger.info("Testing LLM client...")

    client = LLMClient()

    test_prompt = """
    Extract the company name from this text and return JSON:

    "Welcome to Acme Fire Protection Services. We've been serving the community since 1995."

    Return format: {"company_name": "..."}
    """

    try:
        response = client.complete(test_prompt, max_tokens=100)
        logger.info(f"Response: {response}")

        json_data = client.extract_json(response)
        logger.info(f"Extracted JSON: {json_data}")

        logger.info("✅ LLM client test passed!")
        return True

    except Exception as e:
        logger.error(f"❌ LLM client test failed: {e}")
        return False


if __name__ == "__main__":
    test_llm_client()
