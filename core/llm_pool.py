"""
Unified Google Gemini Multi-Key Pool with Automatic Rotation and Resilient Fallbacks.
"""
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types

from config.settings import GEMINI_API_KEYS, GEMINI_MODEL

logger = logging.getLogger(__name__)

FALLBACK_MODELS: List[str] = [
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.5-flash",
]


class LLMPool:
    """Manages a pool of Gemini API keys with automatic failover and rotation."""

    def __init__(self, api_keys: Optional[List[str]] = None, default_model: str = "gemini-flash-latest"):
        self.api_keys = [k.strip() for k in (api_keys or GEMINI_API_KEYS) if k and k.strip()]
        self.default_model = default_model
        self._key_index = 0
        self._clients: List[genai.Client] = []

        for key in self.api_keys:
            try:
                self._clients.append(genai.Client(api_key=key))
            except Exception as e:
                logger.warning(f"Failed to initialize client for key ...{key[-6:]}: {e}")

        logger.info(f"LLMPool initialized with {len(self._clients)} active API keys.")

    @property
    def is_ready(self) -> bool:
        return len(self._clients) > 0

    @property
    def active_client(self) -> Optional[genai.Client]:
        if not self._clients:
            return None
        return self._clients[self._key_index % len(self._clients)]

    def rotate_key(self, reason: str = ""):
        """Rotates to next key in pool upon rate limit or failure."""
        if len(self._clients) > 1:
            prev = self._key_index % len(self._clients)
            self._key_index = (self._key_index + 1) % len(self._clients)
            curr = self._key_index % len(self._clients)
            print(f"[LLMPool] Rotated Key #{prev + 1} -> Key #{curr + 1} of {len(self._clients)} ({reason})")

    def generate_content(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.4,
        max_output_tokens: int = 4000,
        model: Optional[str] = None
    ) -> str:
        """Generates text using active client with automatic model and key failover."""
        if not self._clients:
            raise RuntimeError("No active Gemini API clients available.")

        models_to_try = [model or self.default_model] + [m for m in FALLBACK_MODELS if m != (model or self.default_model)]
        last_error = None

        total_attempts = len(self._clients) * 2
        for attempt in range(total_attempts):
            client = self.active_client
            active_model = models_to_try[attempt % len(models_to_try)]
            try:
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                )

                response = client.models.generate_content(
                    model=active_model,
                    contents=prompt,
                    config=config
                )

                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                err_str = str(e).lower()
                last_error = e
                if "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str:
                    self.rotate_key("Quota / Rate Limit")
                    time.sleep(1)
                elif "404" in err_str or "not found" in err_str:
                    continue
                else:
                    logger.warning(f"Model {active_model} error: {e}")
                    time.sleep(1)

        raise RuntimeError(f"All LLMPool attempts failed. Last error: {last_error}")

    def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """Generates structured JSON directly from Gemini."""
        if not self._clients:
            raise RuntimeError("No active Gemini API clients available.")

        models_to_try = [self.default_model] + [m for m in FALLBACK_MODELS if m != self.default_model]
        last_error = None

        total_attempts = len(self._clients) * 2
        for attempt in range(total_attempts):
            client = self.active_client
            active_model = models_to_try[attempt % len(models_to_try)]
            try:
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=temperature,
                    response_mime_type="application/json",
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                )

                response = client.models.generate_content(
                    model=active_model,
                    contents=prompt,
                    config=config
                )

                raw = (response.text or "").strip()
                parsed = self._parse_json_safely(raw)
                if isinstance(parsed, dict):
                    return parsed
                if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict):
                    return parsed[0]
            except Exception as e:
                err_str = str(e).lower()
                last_error = e
                if "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str:
                    self.rotate_key("Quota / Rate Limit")
                    time.sleep(1)
                else:
                    time.sleep(1)

        raise RuntimeError(f"JSON generation failed after {total_attempts} attempts: {last_error}")

    @staticmethod
    def _parse_json_safely(raw: str) -> Any:
        cleaned = raw.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            return json.loads(cleaned)
        except Exception:
            match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            raise
