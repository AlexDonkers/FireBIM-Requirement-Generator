# FireBIM Requirement Generator

The FireBIM Requirement Generator is a Python implementation of the neuro-symbolic sentence-to-SHACL approach developed in FireBIM Deliverable 2.3. It converts a regulatory statement into a machine-interpretable SHACL rule while retaining intermediate representations for validation.

## Features

- Language-specific NLP preprocessing with automatic spaCy model installation
- Embedding-based optimisation of domain ontology context
- Structured LLM generation of mapping table, First-Order Logic (FOL), and SHACL
- Gemini API and local Ollama providers
- RDF/Turtle syntax validation
- SHACL-to-Mermaid visualisation of applicability, logical structure, requirements, and compliance outcomes
- Clickable ontology and SHACL-shape links in the Mermaid diagram
- Streamlit web application
- Command-line interface and standalone Python script

## Get started

### Windows: one-command startup

From the project directory:

```powershell
.\run.ps1
```

The script creates `.venv` when needed, installs the dependencies declared in `pyproject.toml`, and starts the Streamlit application. The selected regulation language controls which spaCy pipeline is prepared; a fitting model is downloaded automatically on first use.

### Manual startup

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m streamlit run app\streamlit_app.py
```

## Web application

Open the local Streamlit URL shown in the terminal. Select:

1. regulation language;
2. Gemini or local Ollama provider;
3. Gemini model or local Ollama model;
4. ontology Turtle files;
5. the regulatory statement.

The output is presented as separate tabs for the generated diagram, ontology mapping, FOL, SHACL, extracted linguistic features, validation, and the raw structured LLM response.

The Mermaid diagram is rendered directly in the application and can also be downloaded as `.mmd`. Ontology terms and the generated SHACL shape are represented as clickable links.

## Processing pipeline

```text
Regulatory statement
        |
        v
Language-specific spaCy NLP
        |
        v
Ontology loading + semantic optimisation
        |
        v
Structured LLM generation
   |          |          |
 Mapping     FOL       SHACL
                         |
                         v
              RDF/SHACL syntax check
                         |
                         v
                 Mermaid visualisation
```

The intermediate mapping and FOL representations are retained rather than treating the process as a direct text-to-SHACL transformation.

## Language-specific NLP

The application supports the language configurations defined in `requirement_generator/nlp/models.py`. For each language, the implementation prefers a large spaCy pipeline and falls back to smaller compatible pipelines when available. The model is downloaded automatically when it is not installed locally.

The language selection affects linguistic preprocessing only. The ontology and SHACL generation stages remain language-independent.

## Ontology processing

Ontology files are loaded as RDF graphs with RDFLib. Terms with `rdfs:label` and optional `rdfs:comment` are extracted and compared with the linguistic features of the regulation. Sentence-transformers embeddings and cosine similarity are used to retain a smaller set of candidate ontology terms for the LLM context.

## Structured generation

The LLM is instructed to produce three related outputs:

- `mapping_table`: mappings between extracted regulatory concepts and ontology terms;
- `fol`: an explicit logical representation of the regulatory requirement;
- `shacl`: the executable Turtle/SHACL representation.

The result is validated with Pydantic before the SHACL text is parsed as Turtle.

## SHACL-to-Mermaid visualisation

The visualisation is generated from the parsed SHACL graph rather than from the original regulatory text. The diagram distinguishes:

- antecedent/applicability conditions;
- consequent/requirements;
- logical operators such as AND and OR;
- compliance and non-compliance outcomes;
- out-of-scope outcomes when applicability conditions are not met.

This is an explanatory representation. The SHACL graph remains the machine-interpretable source of truth.

Mermaid links use the documented `click ... href ... "tooltip" _blank` syntax and the browser renderer uses `securityLevel: "loose"` so ontology links remain interactive.

## Gemini model discovery

When a Gemini API key is supplied, the web interface queries the Gemini API for models that advertise `generateContent` support and presents those models in the selector. This avoids relying on a permanently hard-coded model list.

## CLI

```powershell
firebim-generate `
  --provider gemini `
  --model gemini-3.1-pro `
  --language Dutch `
  --regulation examples\regulation.txt `
  --ontology path\to\fbo.ttl
```

For a local Ollama model:

```powershell
firebim-generate `
  --provider local `
  --model gemma4 `
  --language Dutch `
  --regulation examples\regulation.txt `
  --ontology path\to\fbo.ttl
```

The CLI writes the extracted features, FOL, SHACL, and Mermaid diagram to the output directory.

## Standalone script

`scripts/neurosymbolic_requirement_generator.py` contains a thin configuration-driven entry point for users who prefer a single Python script. It reuses the same package pipeline instead of maintaining a separate implementation.

Edit the `CONFIG` dictionary and run:

```powershell
.\.venv\Scripts\python.exe scripts\neurosymbolic_requirement_generator.py
```

## Project structure

```text
requirement-generator/
├── app/
│   └── streamlit_app.py
├── cli/
│   └── generate.py
├── examples/
│   └── regulation.txt
├── requirement_generator/
│   ├── cli/
│   ├── llm/
│   ├── nlp/
│   ├── ontology/
│   ├── parsing/
│   ├── prompting/
│   ├── validation/
│   └── visualisation/
├── scripts/
│   └── neurosymbolic_requirement_generator.py
├── tests/
├── .env.example
├── pyproject.toml
└── run.ps1
```

## Main dependencies

| Package | Role |
|---|---|
| RDFLib | RDF/Turtle graph handling |
| spaCy | Language-specific linguistic preprocessing |
| sentence-transformers | Semantic embeddings for ontology optimisation |
| scikit-learn | Cosine similarity |
| google-genai | Gemini API integration |
| requests | Ollama REST integration |
| Pydantic | Structured LLM response validation |
| pySHACL | SHACL validation support |
| Streamlit | Web interface |
| Mermaid.js | Browser-side rule visualisation |
| PyTorch / torchvision | Sentence-transformers runtime dependencies |

## Development

Run the tests with:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The core pipeline is implemented once in `RequirementGenerator` and reused by the Streamlit application, CLI, and standalone script.

## Limitations

The quality of the generated rule still depends on linguistic parsing, ontology coverage and semantic candidate selection, and LLM interpretation. Automatically downloaded spaCy models may differ in coverage and performance between languages. Local LLM output can also vary by model and structured-output support.

The Mermaid representation is intended for inspection and human validation. It does not replace execution by a SHACL validator.
