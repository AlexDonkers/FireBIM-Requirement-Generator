from __future__ import annotations

import json

import requests

from .base import LLMProvider
from ..models import LLMGeneration


class OllamaProvider(LLMProvider):
    """Use a local Ollama instance through its local REST API."""

    def __init__(self, model: str, base_url: str = "http://localhost:11434", timeout: int = 600):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate(self, prompt: str) -> tuple[LLMGeneration, str]:
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "format": "json",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        raw = payload["message"]["content"]
        return LLMGeneration.model_validate(json.loads(raw)), raw
