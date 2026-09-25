from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from requirement_generator import RequirementGenerator
from requirement_generator.llm.gemini import GeminiProvider
from requirement_generator.config import GenerationConfig
from requirement_generator.nlp import SUPPORTED_LANGUAGES, resolve_spacy_model
from requirement_generator.visualisation.mermaid import render_mermaid_html

st.set_page_config(page_title="FireBIM Requirement Generator", layout="wide")
st.title("FireBIM Requirement Generator")
st.caption("Neuro-symbolic generation of SHACL-based digital building requirements")

language_labels = [spec.label for spec in SUPPORTED_LANGUAGES]

with st.sidebar:
    st.header("Language")
    language = st.selectbox(
        "Regulation language",
        language_labels,
        index=language_labels.index("Dutch"),
        help="The selected language determines which spaCy pipeline is used for linguistic analysis. "
             "The required model is downloaded automatically on first use.",
    )
    selected_spec = next(spec for spec in SUPPORTED_LANGUAGES if spec.label == language)
    st.caption(f"spaCy preference: `{selected_spec.candidates[0]}` (falls back to smaller compatible models if needed)")

    st.header("LLM")
    provider = st.radio("Provider", ["gemini", "local"], horizontal=True)

    if provider == "gemini":
        env_key = os.getenv("GEMINI_API_KEY", "")
        api_key = st.text_input("Gemini API key", value=env_key, type="password")
        try:
            gemini_models = GeminiProvider.list_models(api_key) if api_key else []
        except Exception as exc:
            gemini_models = []
            st.caption(f"Could not query Gemini models: {exc}")

        model_options = gemini_models or ["gemini-3.1-pro"]
        model = st.selectbox(
            "Model",
            model_options,
            index=0,
            help="Models are queried from the Gemini API when an API key is provided; only models supporting generateContent are listed.",
        )
        base_url = "http://localhost:11434"
    else:
        api_key = ""
        model = st.text_input("Local model", value="gemma4")
        base_url = st.text_input("Ollama URL", value="http://localhost:11434")

    top_n = st.slider("Ontology matches per feature", 1, 20, 10)

st.subheader("Input")
regulation = st.text_area(
    "Regulatory statement",
    height=180,
    placeholder="Enter a regulatory statement here...",
)

uploads = st.file_uploader(
    "Upload ontology files (.ttl)",
    type=["ttl"],
    accept_multiple_files=True,
    help="Upload the FireBIM Building Ontology and any additional ontologies required by the rule.",
)

run = st.button("Generate requirement", type="primary", disabled=not regulation.strip() or not uploads)

if run:
    temp_paths: list[str] = []
    try:
        for upload in uploads:
            suffix = Path(upload.name).suffix.lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(upload.getvalue())
                temp_paths.append(tmp.name)

        with st.spinner(f"Preparing {language} language model and generating rule..."):
            spacy_model = resolve_spacy_model(language)
            config = GenerationConfig(
                spacy_model=spacy_model,
                top_n_ontology_terms=top_n,
            )
            llm = RequirementGenerator.create_provider(
                provider,
                model,
                api_key=api_key,
                base_url=base_url,
                config=config,
            )
            generator = RequirementGenerator(llm, config)
            result = generator.generate(regulation, temp_paths)

        st.success(f"Language: {language} · spaCy: `{spacy_model}`")
        st.subheader("Output")
        tabs = st.tabs(["Diagram", "Mapping", "FOL", "SHACL", "Features", "Validation", "Raw response"])

        with tabs[0]:
            if result.diagram:
                # Render the full Mermaid source, including ontology links.
                # The custom renderer patches the SVG with xmlns:xlink before
                # inserting it, which avoids XML parsing errors when clickable
                # Mermaid nodes are serialised by the browser.
                components.html(
                    render_mermaid_html(result.diagram, height=760),
                    height=780,
                    scrolling=True,
                )

                st.download_button(
                    "Download Mermaid source",
                    result.diagram,
                    file_name="rule_diagram.mmd",
                    mime="text/plain",
                    on_click="ignore",
                )
            else:
                st.warning(result.validation.get("diagram_error", "No diagram could be generated."))

        with tabs[1]:
            df = pd.DataFrame([item.model_dump() for item in result.mapping_table])
            st.dataframe(df, use_container_width=True, hide_index=True)

        with tabs[2]:
            st.code(result.fol, language="text")

        with tabs[3]:
            st.code(result.shacl, language="turtle")
            st.download_button(
                "Download SHACL",
                result.shacl,
                file_name="generated_rule.ttl",
                mime="text/turtle",
                on_click="ignore",
            )

        with tabs[4]:
            st.dataframe(pd.DataFrame({"Feature": result.features}), use_container_width=True, hide_index=True)

        with tabs[5]:
            if result.validation.get("valid"):
                st.success(f"Valid Turtle / SHACL graph ({result.validation['triples']} triples)")
            else:
                st.error(result.validation.get("error", "Invalid SHACL output"))

        with tabs[6]:
            st.code(result.raw_response, language="json")

    except Exception as exc:
        st.exception(exc)
    finally:
        for path in temp_paths:
            try:
                Path(path).unlink(missing_ok=True)
            except OSError:
                pass
