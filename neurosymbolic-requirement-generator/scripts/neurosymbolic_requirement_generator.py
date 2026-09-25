"""Standalone FireBIM neuro-symbolic requirement generator.

Edit CONFIG and run this script directly, or use the package/CLI instead.
"""
from __future__ import annotations

import os
from pathlib import Path

from requirement_generator import RequirementGenerator
from requirement_generator.config import GenerationConfig
from requirement_generator.nlp import resolve_spacy_model

CONFIG = {
    "REGULATION_LANGUAGE": "Dutch",
    "REGULATORY_STATEMENT": "An enclosed space is located in a fire compartment.",
    "DOMAIN_ONTOLOGIES": [r"C:\path\to\fbo.ttl"],
    "LLM_PROVIDER": "gemini",  # gemini or local
    "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
    "GEMINI_MODEL": "gemini-3.1-pro",
    "OLLAMA_BASE_URL": "http://localhost:11434",
    "OLLAMA_MODEL": "gemma4",
    "TOP_N_ONTOLOGY_TERMS": 10,
    "OUTPUT_DIRECTORY": "output",
}


def main() -> None:
    language = CONFIG["REGULATION_LANGUAGE"]
    spacy_model = resolve_spacy_model(language)
    config = GenerationConfig(
        spacy_model=spacy_model,
        top_n_ontology_terms=CONFIG["TOP_N_ONTOLOGY_TERMS"],
    )

    provider_name = CONFIG["LLM_PROVIDER"]
    model = (
        CONFIG["GEMINI_MODEL"]
        if provider_name == "gemini"
        else CONFIG["OLLAMA_MODEL"]
    )
    provider = RequirementGenerator.create_provider(
        provider_name,
        model,
        api_key=CONFIG["GEMINI_API_KEY"],
        base_url=CONFIG["OLLAMA_BASE_URL"],
        config=config,
    )

    generator = RequirementGenerator(provider, config)
    result = generator.generate(
        CONFIG["REGULATORY_STATEMENT"],
        [Path(p) for p in CONFIG["DOMAIN_ONTOLOGIES"]],
    )

    output = Path(CONFIG["OUTPUT_DIRECTORY"])
    output.mkdir(parents=True, exist_ok=True)
    (output / "features.txt").write_text("\n".join(result.features), encoding="utf-8")
    (output / "mapping.json").write_text(
        "[\n" + ",\n".join(
            "  " + item.model_dump_json(indent=2).replace("\n", "\n  ")
            for item in result.mapping_table
        ) + "\n]\n",
        encoding="utf-8",
    )
    (output / "fol.txt").write_text(result.fol, encoding="utf-8")
    (output / "shape.ttl").write_text(result.shacl, encoding="utf-8")
    (output / "rule_diagram.mmd").write_text(result.diagram, encoding="utf-8")

    print(f"Language: {language}")
    print(f"spaCy model: {spacy_model}")
    print(f"SHACL syntax valid: {result.validation.get('valid')}")
    print(f"Outputs written to: {output.resolve()}")


if __name__ == "__main__":
    main()
