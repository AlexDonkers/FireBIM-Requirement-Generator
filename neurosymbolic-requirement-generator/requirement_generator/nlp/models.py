from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import importlib
import subprocess
import sys

import spacy


@dataclass(frozen=True)
class LanguageModelSpec:
    label: str
    code: str
    candidates: tuple[str, ...]


# Prefer large pipelines because the existing FireBIM implementation uses
# nl_core_news_lg. If a large model is unavailable for a language, fall back
# to md and then sm. English uses the en_core_web_* naming convention.
SUPPORTED_LANGUAGES: tuple[LanguageModelSpec, ...] = (
    LanguageModelSpec("Danish", "da", ("da_core_news_lg", "da_core_news_md", "da_core_news_sm")),
    LanguageModelSpec("Dutch", "nl", ("nl_core_news_lg", "nl_core_news_md", "nl_core_news_sm")),
    LanguageModelSpec("English", "en", ("en_core_web_lg", "en_core_web_md", "en_core_web_sm")),
    LanguageModelSpec("Finnish", "fi", ("fi_core_news_lg", "fi_core_news_md", "fi_core_news_sm")),
    LanguageModelSpec("French", "fr", ("fr_core_news_lg", "fr_core_news_md", "fr_core_news_sm")),
    LanguageModelSpec("German", "de", ("de_core_news_lg", "de_core_news_md", "de_core_news_sm")),
    LanguageModelSpec("Greek", "el", ("el_core_news_lg", "el_core_news_md", "el_core_news_sm")),
    LanguageModelSpec("Italian", "it", ("it_core_news_lg", "it_core_news_md", "it_core_news_sm")),
    LanguageModelSpec("Lithuanian", "lt", ("lt_core_news_lg", "lt_core_news_md", "lt_core_news_sm")),
    LanguageModelSpec("Norwegian Bokmål", "nb", ("nb_core_news_lg", "nb_core_news_md", "nb_core_news_sm")),
    LanguageModelSpec("Polish", "pl", ("pl_core_news_lg", "pl_core_news_md", "pl_core_news_sm")),
    LanguageModelSpec("Portuguese", "pt", ("pt_core_news_lg", "pt_core_news_md", "pt_core_news_sm")),
    LanguageModelSpec("Romanian", "ro", ("ro_core_news_lg", "ro_core_news_md", "ro_core_news_sm")),
    LanguageModelSpec("Slovenian", "sl", ("sl_core_news_lg", "sl_core_news_md", "sl_core_news_sm")),
    LanguageModelSpec("Spanish", "es", ("es_core_news_lg", "es_core_news_md", "es_core_news_sm")),
    LanguageModelSpec("Swedish", "sv", ("sv_core_news_lg", "sv_core_news_md", "sv_core_news_sm")),
)

LANGUAGE_BY_LABEL = {spec.label: spec for spec in SUPPORTED_LANGUAGES}
LANGUAGE_BY_CODE = {spec.code: spec for spec in SUPPORTED_LANGUAGES}


def get_language_spec(language: str) -> LanguageModelSpec:
    if language in LANGUAGE_BY_LABEL:
        return LANGUAGE_BY_LABEL[language]
    if language in LANGUAGE_BY_CODE:
        return LANGUAGE_BY_CODE[language]
    raise ValueError(
        f"Unsupported regulation language '{language}'. "
        f"Supported languages: {', '.join(LANGUAGE_BY_LABEL)}"
    )


def _is_installed(model_name: str) -> bool:
    try:
        return spacy.util.is_package(model_name)
    except Exception:
        return False


def ensure_spacy_model(model_name: str) -> str:
    """Ensure a spaCy model is installed, downloading it if necessary.

    Returns the model name that can be passed to spacy.load().
    """
    if _is_installed(model_name):
        return model_name

    print(f"spaCy model '{model_name}' is not installed. Downloading it...")
    try:
        # Use spaCy's downloader so it selects a version compatible with the
        # currently installed spaCy version.
        from spacy.cli import download

        download(model_name)
        importlib.invalidate_caches()
    except Exception as exc:
        raise RuntimeError(
            f"Could not download spaCy model '{model_name}'. "
            "Make sure the machine has internet access and pip can install packages."
        ) from exc

    if not _is_installed(model_name):
        # A process reload is normally not required, but importing the package
        # explicitly can help Python discover a newly installed pipeline.
        try:
            importlib.import_module(model_name)
        except Exception:
            pass

    if not _is_installed(model_name):
        raise RuntimeError(
            f"spaCy model '{model_name}' was downloaded but is not visible to the current Python process. "
            "Restart the application and try again."
        )

    return model_name


def resolve_spacy_model(language: str) -> str:
    """Return an installed model for a language, downloading the best available one."""
    spec = get_language_spec(language)

    for candidate in spec.candidates:
        if _is_installed(candidate):
            return candidate

    errors: list[str] = []
    for candidate in spec.candidates:
        try:
            ensure_spacy_model(candidate)
            return candidate
        except Exception as exc:
            errors.append(f"{candidate}: {exc}")

    raise RuntimeError(
        f"No compatible spaCy pipeline could be installed for {spec.label}.\n"
        + "\n".join(errors)
    )


@lru_cache(maxsize=16)
def load_spacy_pipeline(model_name: str):
    """Load and cache a spaCy pipeline for repeated Streamlit executions."""
    ensure_spacy_model(model_name)
    return spacy.load(model_name)
