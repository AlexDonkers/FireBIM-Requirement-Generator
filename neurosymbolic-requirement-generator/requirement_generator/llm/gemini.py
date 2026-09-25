from __future__ import annotations

from google import genai
from google.genai import types

from .base import LLMProvider
from ..models import LLMGeneration


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str, temperature: float = 0.0, max_output_tokens: int = 4096):
        if not api_key:
            raise ValueError("A Gemini API key is required.")
        self.model = model
        self.client = genai.Client(api_key=api_key)
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens


    @staticmethod
    def list_models(api_key: str) -> list[str]:
        """Return Gemini models that advertise generateContent support."""
        if not api_key:
            return []
        client = genai.Client(api_key=api_key)
        models: list[str] = []
        for model in client.models.list():
            actions = getattr(model, "supported_actions", None) or []
            name = getattr(model, "name", "") or ""
            if "generateContent" not in actions or not name:
                continue
            models.append(name.removeprefix("models/"))
        return sorted(set(models))

    def generate(self, prompt: str) -> tuple[LLMGeneration, str]:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_output_tokens,
                response_mime_type="application/json",
                response_schema=LLMGeneration,
            ),
        )
        parsed = response.parsed or LLMGeneration.model_validate_json(response.text)
        return parsed, response.text
