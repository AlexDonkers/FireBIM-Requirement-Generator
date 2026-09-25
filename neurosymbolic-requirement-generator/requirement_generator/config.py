from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationConfig:
    embedding_model: str = "sentence-transformers/all-mpnet-base-v2"
    spacy_model: str = "nl_core_news_lg"
    top_n_ontology_terms: int = 10
    temperature: float = 0.0
    max_output_tokens: int = 4096
