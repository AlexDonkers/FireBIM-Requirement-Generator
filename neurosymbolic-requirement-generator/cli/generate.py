from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

from requirement_generator import RequirementGenerator
from requirement_generator.config import GenerationConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SHACL from a regulatory statement.")
    parser.add_argument("--provider", choices=["gemini", "local"], required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--api-key", default=os.getenv("GEMINI_API_KEY"))
    parser.add_argument("--base-url", default="http://localhost:11434")
    parser.add_argument("--regulation", required=True)
    parser.add_argument("--ontology", action="append", required=True)
    parser.add_argument("--output", default="output")
    args = parser.parse_args()

    regulation = Path(args.regulation).read_text(encoding="utf-8")
    provider = RequirementGenerator.create_provider(
        args.provider,
        args.model,
        api_key=args.api_key,
        base_url=args.base_url,
    )
    generator = RequirementGenerator(provider, GenerationConfig())
    result = generator.generate(regulation, args.ontology)

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    (out / "features.txt").write_text("\n".join(result.features), encoding="utf-8")
    (out / "fol.txt").write_text(result.fol, encoding="utf-8")
    (out / "shape.ttl").write_text(result.shacl, encoding="utf-8")
    print(f"SHACL syntax valid: {result.validation.get('valid')}")
    print(f"Outputs written to {out.resolve()}")


if __name__ == "__main__":
    main()
