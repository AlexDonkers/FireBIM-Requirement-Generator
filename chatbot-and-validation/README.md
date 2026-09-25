# Chatbot and Validation Notebook

The Chatbot and Validation Notebook is a training and demonstration environment showing how digital fire regulations can be explored through RDF and SPARQL, enriched with thematic metadata, retrieved using natural-language questions, and applied as SHACL constraints to building data.

The notebook complements the reusable software components described in FireBIM Deliverables 2.3 and 2.4. It is intentionally presented as a step-by-step training artifact rather than as a reusable Python package.

## Purpose

The notebook demonstrates five connected activities:

1. loading and exploring a FireBIM Regulation Graph;
2. loading the FireBIM Regulation Ontology and adding thematic metadata to regulatory statements;
3. translating natural-language questions into SPARQL and retrieving regulatory content;
4. summarising retrieved regulations for a specific stakeholder, task, and design phase;
5. validating building data against SHACL shapes with `pySHACL`.

A small Gradio interface at the end of the notebook wraps the natural-language retrieval workflow as a chatbot.

## Workflow

```text
Natural-language question
        ↓
LLM-based SPARQL generation
        ↓
Regulation + thematic RDF graph
        ↓
Retrieved regulatory statements
        ↓
Stakeholder / task / design-phase context
        ↓
Context-aware summary

Digital rule + building data
        ↓
SHACL validation
        ↓
Validation report
```

The LLM generates the SPARQL query and the contextual summary. The regulatory content itself is retrieved directly from the RDF graph, and the generated SPARQL query is displayed so that the interpretation can be inspected.

## Notebook structure

The notebook is organised into the following modules:

- **Module 1 — Exploring an RDF Graph and SPARQL**
- **Module 2 — RDF + OWL: Ontology Loading and Thematic Enrichment**
- **Module 3 — Natural Language to SPARQL using LLMs**
- **Stakeholder-, task-, and phase-aware summaries**
- **Module 4 — SHACL validation**
- **Module 5 — A small FireBIM chatbot**

The stakeholder context is represented as RDF using a small construction-role knowledge graph. Three configuration variables determine the interpretation context:

```python
STAKEHOLDER = "Architect"
TASK = "coordinate the architectural layout and its fire-safety information"
DESIGN_PHASE = "early design phase"
```

The role context is kept separate from the retrieved regulatory content so that stakeholder responsibilities are not confused with the regulations themselves.

## Input files

For the standard Colab workflow, upload:

```text
RegulationGraph.ttl
```

After running the thematic enrichment section, the notebook creates:

```text
FireRegulations_themes_only.ttl
```

The second file is then combined with the regulation graph for the GraphRAG demonstration.

## Requirements

The notebook installs the required Python packages in its first cell, including RDFLib, PyVis, NetworkX, pandas, requests, pySHACL, and Gradio.

A Gemini API key is required for the LLM-based sections. The key is requested interactively and is not written into the notebook.

## Relation to D2.4

See **ITEA4 22003 FireBIM D2.4 – Requirement Generator**, section on the chatbot and validation training notebook. The notebook demonstrates the downstream use of digital rules generated within the FireBIM workflow and provides an inspectable training environment for natural-language rule retrieval and compliance validation.

[Back to the FireBIM Requirement Generator →](../)
