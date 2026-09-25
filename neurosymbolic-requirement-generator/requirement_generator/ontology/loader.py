from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

from rdflib import Graph

from ..models import OntologyTerm


class OntologyLoader:
    """Load one or more Turtle ontologies and extract Dutch labels/comments."""

    def load_files(self, paths: list[str | Path]) -> tuple[Graph, list[OntologyTerm]]:
        graph = Graph()
        for path in paths:
            graph.parse(path, format="turtle")
        return graph, self.extract_terms(graph)

    def load_texts(self, documents: list[str]) -> tuple[Graph, list[OntologyTerm]]:
        graph = Graph()
        for document in documents:
            graph.parse(data=document, format="turtle")
        return graph, self.extract_terms(graph)

    def extract_terms(self, graph: Graph) -> list[OntologyTerm]:
        terms: list[OntologyTerm] = []
        query = """
        SELECT ?uri ?label ?comment WHERE {
            ?uri rdfs:label ?label .
            OPTIONAL {
                ?uri rdfs:comment ?comment .
                FILTER(LANG(?comment) = 'nl' || LANG(?comment) = '')
            }
            FILTER(LANG(?label) = 'nl' || LANG(?label) = '')
        }
        """
        for row in graph.query(query):
            terms.append(
                OntologyTerm(
                    uri=str(row.uri),
                    label=str(row.label),
                    comment=str(row.comment or ""),
                )
            )
        return terms
