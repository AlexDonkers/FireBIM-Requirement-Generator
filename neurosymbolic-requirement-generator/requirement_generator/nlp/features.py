from __future__ import annotations

from .models import load_spacy_pipeline


class FeatureExtractor:
    """Extract noun chunks and content words using a language-specific spaCy pipeline."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.nlp = load_spacy_pipeline(model_name)

    def extract(self, text: str) -> list[str]:
        doc = self.nlp(text)
        noun_chunks = [chunk.text.strip() for chunk in doc.noun_chunks if chunk.text.strip()]
        tokens = [
            token.text.strip()
            for token in doc
            if token.text.strip()
            and token.pos_ not in {"PUNCT", "SYM", "SPACE"}
            and not token.is_stop
        ]
        return list(dict.fromkeys(noun_chunks + tokens))
