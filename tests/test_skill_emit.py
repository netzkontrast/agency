from unittest.mock import patch
from agency.skill_emit import _render_tier_b_anchor

def test_render_tier_b_anchor_valid_callable():
    def my_verb(a: int, b: str = "foo"):
        pass

    result = _render_tier_b_anchor("my_verb", my_verb, "A valid verb.")
    assert "## my_verb" in result
    assert "A valid verb." in result
    assert "(a: int, b: str = 'foo')" in result

def test_render_tier_b_anchor_no_callable():
    result = _render_tier_b_anchor("my_verb", None, "No callable provided.")
    assert "## my_verb" in result
    assert "No callable provided." in result
    assert "Parameters: `()`." in result

def test_render_tier_b_anchor_type_error():
    class InvalidCallable:
        pass

    result = _render_tier_b_anchor("my_verb", InvalidCallable(), "Raises TypeError.")
    assert "## my_verb" in result
    assert "Raises TypeError." in result
    assert "Parameters: `()`." in result

@patch('inspect.signature')
def test_render_tier_b_anchor_value_error(mock_signature):
    mock_signature.side_effect = ValueError("Mocked ValueError")

    def dummy_verb():
        pass

    result = _render_tier_b_anchor("my_verb", dummy_verb, "Raises ValueError.")
    assert "## my_verb" in result
    assert "Raises ValueError." in result
    assert "Parameters: `()`." in result
