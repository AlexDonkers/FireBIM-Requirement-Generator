# FireBIM Requirement Generator

This repository collects the software tools developed in the FireBIM project for the digitalisation, interpretation, retrieval, and validation of fire safety regulations. The tools are described in **ITEA4 22003 FireBIM Deliverable 2.4 – Requirement Generator** and implement complementary parts of the workflows developed in Deliverable 2.3.

The collection contains four software tools. The **Neuro-symbolic Requirement Generator** is the main implementation in this deliverable and provides the most extensive, reusable software package. The other tools provide supporting implementations and prototypes for semantic enrichment, NLP-based rule generation, and end-to-end rule retrieval and validation.

## Software tools

### 1. Thematic Metadata Enrichment

Adds semantic topic metadata to regulatory statements by linking them to concepts from the FireBIM domain ontology. The enriched regulation graph can subsequently be queried using domain concepts.

[Open the Thematic Metadata Enrichment tool →](./thematic-metadata-enrichment/)

### 2. NLP-based SHACL Generator

A lightweight NLP prototype that analyses a regulatory sentence with dependency parsing and noun-chunk extraction and constructs an initial SHACL representation from the detected subject, relation, and object.

[Open the NLP-based SHACL Generator →](./nlp-based-shacl-generator/)

### 3. Neuro-symbolic Requirement Generator

The main software tool of D2.4. It combines language-specific NLP, ontology-based semantic grounding, embedding-based ontology optimisation, structured LLM generation, FOL formalisation, SHACL generation, validation, and Mermaid visualisation.

[Open the Neuro-symbolic Requirement Generator →](./neurosymbolic-requirement-generator/)
[Open the web-app →](.https://neurosymbolic-requirement-generator.streamlit.app/)

### 4. Chatbot and Validation Notebook

A training and demonstration notebook combining natural-language retrieval of digital regulations with SHACL-based validation of building data.

[Open the Chatbot and Validation Notebook →](./chatbot-and-validation/)

## Relation to FireBIM Deliverable 2.4

The software in this repository accompanies **ITEA4 22003 FireBIM D2.4, Requirement Generator**. D2.4 documents the implementation of the software components and their role in the FireBIM digitalisation workflow.

The repository is organised around the four tools exposed as reusable software artifacts:

```text
FireBIM Requirement Generator
├── thematic-metadata-enrichment
├── nlp-based-shacl-generator
├── neurosymbolic-requirement-generator
└── chatbot-and-validation
```

The Neuro-symbolic Requirement Generator is the main implementation and builds on the sentence-to-SHACL approach developed in D2.3. It retains intermediate linguistic features, ontology mappings, and a First-Order Logic representation before generating the final SHACL rule. The resulting SHACL shape can be inspected through a Mermaid representation and validated against building data where a data graph is available.

The other tools represent complementary or earlier implementation approaches discussed in the deliverables. They are intentionally kept as separate software artifacts so that their individual methods can be inspected, executed, and reused independently.

## FireBIM

The tools are part of the wider FireBIM project on digitalisation of fire safety regulations and automated compliance checking.

[Visit FireBIM.org →](https://www.firebim.org/)

