from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field


class MappingItem(BaseModel):
    source_term: str = Field(description="The regulatory phrase or concept being mapped.")
    ontology_label: str = Field(description="The selected ontology label.")
    ontology_uri: str = Field(description="The ontology URI selected for the concept.")
    reason: str = Field(default="", description="Brief reason for the mapping.")


class LLMGeneration(BaseModel):
    mapping_table: list[MappingItem]
    fol: str
    shacl: str


@dataclass
class OntologyTerm:
    uri: str
    label: str
    comment: str = ""


@dataclass
class OntologyMatch:
    feature: str
    uri: str
    label: str
    similarity: float


@dataclass
class GenerationResult:
    regulation_text: str
    features: list[str]
    ontology_matches: list[OntologyMatch]
    mapping_table: list[MappingItem]
    fol: str
    shacl: str
    raw_response: str = ""
    validation: dict[str, Any] = field(default_factory=dict)
    diagram: str = ""
