# Thematic Metadata Enrichment

The Thematic Metadata Enrichment tool adds semantic links between individual regulatory statements and concepts from the FireBIM domain ontology. It extends the regulation graph with thematic metadata so that regulatory content can be explored and retrieved using domain concepts rather than only the structural organisation of the document.

This tool implements the semantic enrichment approach described in FireBIM Deliverable 2.3 and documented as a software component in Deliverable 2.4.

## Purpose

The tool enriches a regulation graph with ontology-based topic annotations. This enables queries such as retrieving all regulatory statements related to a concept such as a fire compartment or a building function.

## Input

The process operates on:

- regulatory statements represented in the regulation graph;
- a set of domain ontology concepts used as candidate topics.

## Output

Relevant statements are linked to ontology concepts using an `fro:isAbout` relation:

```text
ex:Statement fro:isAbout fbo:Topic
```

The original regulatory text and document structure remain unchanged.

## Method

The implementation evaluates individual regulatory statements using a zero-shot text-classification approach. The association score between a statement and a candidate topic is compared with a configurable threshold. Topics exceeding the threshold are written back into the regulation graph as semantic metadata.

The resulting enrichment supports semantic retrieval and allows ontology hierarchies to be used when navigating regulatory content.

## Limitations

Tagging is performed at statement level. A theme explicitly assigned to one statement is not automatically propagated to related statements such as exceptions or other statements within the same article.

## Relation to D2.4

See **ITEA4 22003 FireBIM D2.4 – Requirement Generator**, section on thematic metadata enrichment and rule exploration.

[Back to the FireBIM Requirement Generator →](../)
