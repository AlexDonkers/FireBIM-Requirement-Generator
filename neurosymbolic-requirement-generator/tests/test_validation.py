from requirement_generator.validation.shacl import validate_shacl_syntax


def test_valid_turtle():
    result = validate_shacl_syntax('''@prefix sh: <http://www.w3.org/ns/shacl#> .\n<http://example.org/S> a sh:NodeShape .''')
    assert result["valid"] is True


def test_invalid_turtle():
    result = validate_shacl_syntax('<not turtle')
    assert result["valid"] is False
