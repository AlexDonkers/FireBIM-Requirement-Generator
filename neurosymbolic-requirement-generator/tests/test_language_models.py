from requirement_generator.nlp.models import get_language_spec


def test_dutch_prefers_large_model():
    spec = get_language_spec("Dutch")
    assert spec.code == "nl"
    assert spec.candidates[0] == "nl_core_news_lg"


def test_english_uses_web_model_naming():
    spec = get_language_spec("English")
    assert spec.candidates[0] == "en_core_web_lg"


def test_code_lookup():
    assert get_language_spec("de").label == "German"
