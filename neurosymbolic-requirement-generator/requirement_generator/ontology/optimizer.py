from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from ..models import OntologyMatch, OntologyTerm


class OntologyOptimizer:
    """Reduce the ontology context to terms relevant to the input sentence."""

    def __init__(self, model_name: str) -> None:
        self.model = SentenceTransformer(model_name)

    def find_relevant_terms(
        self,
        features: list[str],
        ontology_terms: list[OntologyTerm],
        top_n: int = 10,
    ) -> list[OntologyMatch]:
        if not features or not ontology_terms:
            return []

        feature_embeddings = self.model.encode(
            features, normalize_embeddings=True, convert_to_numpy=True
        )
        term_texts = [f"{term.label} {term.comment}".strip() for term in ontology_terms]
        term_embeddings = self.model.encode(
            term_texts, normalize_embeddings=True, convert_to_numpy=True
        )
        similarities = cosine_similarity(feature_embeddings, term_embeddings)

        selected: dict[int, float] = {}
        for row in similarities:
            indices = np.argsort(row)[-top_n:][::-1]
            for index in indices:
                selected[index] = max(selected.get(index, -1.0), float(row[index]))

        matches: list[OntologyMatch] = []
        for index, score in sorted(selected.items(), key=lambda item: item[1], reverse=True):
            term = ontology_terms[index]
            feature_index = int(np.argmax(similarities[:, index]))
            matches.append(
                OntologyMatch(
                    feature=features[feature_index],
                    uri=term.uri,
                    label=term.label,
                    similarity=round(score, 4),
                )
            )
        return matches
