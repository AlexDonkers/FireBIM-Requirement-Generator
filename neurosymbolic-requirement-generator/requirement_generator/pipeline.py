from __future__ import annotations

from pathlib import Path

from .config import GenerationConfig
from .llm import GeminiProvider, LLMProvider, OllamaProvider
from .models import GenerationResult
from .nlp.features import FeatureExtractor
from .ontology.loader import OntologyLoader
from .ontology.optimizer import OntologyOptimizer
from .prompting.templates import build_prompt
from .validation.shacl import validate_shacl_syntax
from .visualisation.mermaid import SHACLDiagramGenerator


class RequirementGenerator:
    """Reusable neuro-symbolic requirement generation pipeline."""

    def __init__(
        self,
        llm_provider: LLMProvider,
        config: GenerationConfig | None = None,
    ) -> None:
        self.config = config or GenerationConfig()
        self.llm = llm_provider
        self.feature_extractor = FeatureExtractor(self.config.spacy_model)
        self.ontology_loader = OntologyLoader()
        self.ontology_optimizer = OntologyOptimizer(self.config.embedding_model)
        self.diagram_generator = SHACLDiagramGenerator()

    def generate(
        self,
        regulation_text: str,
        ontology_files: list[str | Path],
    ) -> GenerationResult:
        if not regulation_text.strip():
            raise ValueError("Regulatory text cannot be empty.")
        if not ontology_files:
            raise ValueError("At least one ontology file is required.")

        _, ontology_terms = self.ontology_loader.load_files(ontology_files)
        features = self.feature_extractor.extract(regulation_text)
        matches = self.ontology_optimizer.find_relevant_terms(
            features,
            ontology_terms,
            top_n=self.config.top_n_ontology_terms,
        )

        prompt = build_prompt(regulation_text, features, matches)
        llm_result, raw_response = self.llm.generate(prompt)
        validation = validate_shacl_syntax(llm_result.shacl)
        diagram = ""
        if validation.get("valid"):
            try:
                diagram = self.diagram_generator.generate(llm_result.shacl)
            except Exception as exc:
                validation["diagram_error"] = str(exc)

        return GenerationResult(
            regulation_text=regulation_text,
            features=features,
            ontology_matches=matches,
            mapping_table=llm_result.mapping_table,
            fol=llm_result.fol,
            shacl=llm_result.shacl,
            raw_response=raw_response,
            validation=validation,
            diagram=diagram,
        )

    @staticmethod
    def create_provider(
        provider: str,
        model: str,
        *,
        api_key: str | None = None,
        base_url: str = "http://localhost:11434",
        config: GenerationConfig | None = None,
    ) -> LLMProvider:
        cfg = config or GenerationConfig()
        if provider == "gemini":
            return GeminiProvider(
                api_key=api_key or "",
                model=model,
                temperature=cfg.temperature,
                max_output_tokens=cfg.max_output_tokens,
            )
        if provider == "local":
            return OllamaProvider(model=model, base_url=base_url)
        raise ValueError(f"Unknown LLM provider: {provider}")
