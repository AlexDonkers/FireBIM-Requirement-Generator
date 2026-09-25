from __future__ import annotations

from rdflib import Graph


def validate_shacl_syntax(shacl_text: str) -> dict:
    """Parse generated Turtle and return a small validation report."""
    graph = Graph()
    try:
        graph.parse(data=shacl_text, format="turtle")
    except Exception as exc:
        return {"valid": False, "error": str(exc)}
    return {"valid": True, "triples": len(graph)}
