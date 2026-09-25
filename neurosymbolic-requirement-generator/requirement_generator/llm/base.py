from abc import ABC, abstractmethod

from ..models import LLMGeneration


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> tuple[LLMGeneration, str]:
        """Return parsed generation result and raw response text."""
