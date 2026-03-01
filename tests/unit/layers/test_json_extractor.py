import pytest
from src.layers.layer1_ast.json_extractor import (
    extract_json_candidates,
    ParsingFailedError,
)


# ----------------------------
# Multiple JSON Objects
# ----------------------------
def test_multiple_json_objects():
    raw = """
    Attempt 1:
    { "type": "A" }

    Attempt 2:
    { "type": "B" }
    """

    result = extract_json_candidates(raw)

    assert len(result.valid) == 2
    assert result.valid[0]["type"] == "A"
    assert result.valid[1]["type"] == "B"


# ----------------------------
# Recoverable Malformed JSON
# ----------------------------
def test_recoverable_malformed_json():
    raw = """
    {
        "type": "Transfer",
        "amount": 10,
    }
    """

    result = extract_json_candidates(raw)

    assert len(result.valid) == 1
    assert result.valid[0]["type"] == "Transfer"
    assert result.valid[0]["amount"] == 10


# ----------------------------
#  Completely Invalid JSON
# ----------------------------
def test_invalid_json_raises_parsing_failed():
    raw = """
    Here is your AST:
    { invalid json }
    """

    with pytest.raises(ParsingFailedError):
        extract_json_candidates(raw)


# ----------------------------
# Nested JSON Structure
# ----------------------------
def test_nested_json_structure():
    raw = """
    {
        "type": "Function",
        "body": {
            "if": {
                "condition": "x > 0",
                "then": { "action": "decrement" }
            }
        }
    }
    """

    result = extract_json_candidates(raw)

    assert len(result.valid) == 1
    assert result.valid[0]["body"]["if"]["condition"] == "x > 0"


# ----------------------------
# Valid JSON but Not Dict
# ----------------------------
def test_json_not_dict_filtered():
    raw = """
    [1, 2, 3]
    """

    with pytest.raises(ParsingFailedError):
        extract_json_candidates(raw)