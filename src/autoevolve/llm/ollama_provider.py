"""Ollama local model provider."""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

from autoevolve.errors import ProviderError
from autoevolve.llm.base import Provider


class OllamaProvider(Provider):
    """LLM provider using a local Ollama instance via HTTP API."""

    def __init__(self, model: str = "llama3", temperature: float = 0.2) -> None:
        self.model = model
        self.temperature = temperature
        self.host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    def generate(self, prompt: str, *, metadata: dict[str, Any] | None = None) -> str:
        """Generate a response via Ollama's HTTP API."""
        url = f"{self.host}/api/generate"
        payload = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": self.temperature},
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                data = json.loads(response.read().decode("utf-8"))
                return data.get("response", "")
        except urllib.error.URLError as e:
            raise ProviderError(
                f"Ollama API call failed (is Ollama running at {self.host}?): {e}"
            )
        except Exception as e:
            raise ProviderError(f"Ollama API call failed: {e}")
