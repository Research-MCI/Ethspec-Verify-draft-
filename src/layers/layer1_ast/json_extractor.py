import re
import json
from typing import List, Dict, Any, Tuple


class ParsingFailedError(Exception):
    """Raised when no valid JSON could be extracted."""
    pass


class JSONExtractionResult:
    def __init__(self):
        self.valid: List[Dict[str, Any]] = []
        self.invalid: List[Tuple[str, str]] = []


def normalize_text(text: str) -> str:
    text = re.sub(r"```json", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)
    return text.strip()


def extract_balanced_json_blocks(text: str) -> List[str]:
    blocks = []
    stack = []
    start_idx = None

    for i, char in enumerate(text):
        if char == "{":
            if not stack:
                start_idx = i
            stack.append("{")

        elif char == "}":
            if stack:
                stack.pop()
                if not stack and start_idx is not None:
                    blocks.append(text[start_idx:i+1])
                    start_idx = None

    return blocks


def attempt_repair(json_str: str) -> str:
    json_str = re.sub(r",\s*}", "}", json_str)
    json_str = re.sub(r",\s*]", "]", json_str)

    if "'" in json_str and '"' not in json_str:
        json_str = json_str.replace("'", '"')

    return json_str


def parse_with_recovery(block: str):
    try:
        return json.loads(block)
    except json.JSONDecodeError:
        repaired = attempt_repair(block)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError as e:
            raise e


def extract_json_candidates(raw_text: str, strict: bool = True) -> JSONExtractionResult:
    result = JSONExtractionResult()

    normalized = normalize_text(raw_text)
    blocks = extract_balanced_json_blocks(normalized)

    for block in blocks:
        try:
            parsed = parse_with_recovery(block)

            if isinstance(parsed, dict):
                result.valid.append(parsed)
            else:
                result.invalid.append((block, "Top-level JSON is not an object"))

        except json.JSONDecodeError as e:
            result.invalid.append((block, str(e)))

    if strict and not result.valid:
        raise ParsingFailedError("Parsing Failed: No valid JSON objects found.")

    return result