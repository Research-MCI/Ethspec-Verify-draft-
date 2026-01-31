"""Prompts for specification extraction and normalization.

This module contains prompts used by the LLM to extract and normalize
requirements, constraints, and invariants from specification documents.
"""

from __future__ import annotations

SPEC_NORMALIZATION_PROMPT = '''You are an expert in Ethereum protocol specifications. Analyze the provided specification content and extract structured requirements.

## Instructions

1. Extract all requirements (MUST, SHALL, SHOULD statements)
2. Identify constraints (limits, bounds, restrictions)
3. Identify invariants (properties that must always hold)
4. Note edge cases and exceptional conditions
5. Provide implementation hints where applicable

## Specification Content

{spec_content}

## Context

Fork Version: {fork_version}
Category: {category}
Source: {source}

## Output Format

Respond with ONLY a JSON object:
{{
  "requirements": [
    {{
      "id": "REQ-001",
      "description": "<requirement description>",
      "priority": 1-5,
      "keywords": ["<keyword1>", "<keyword2>"]
    }}
  ],
  "constraints": [
    {{
      "id": "CON-001",
      "description": "<constraint description>",
      "type": "<constraint_type>",
      "is_hard": true/false
    }}
  ],
  "invariants": [
    {{
      "id": "INV-001",
      "description": "<invariant description>",
      "scope": "<scope>"
    }}
  ],
  "edge_cases": [
    {{
      "id": "EDGE-001",
      "description": "<edge case description>",
      "trigger": "<trigger condition>",
      "expected_behavior": "<expected behavior>"
    }}
  ],
  "traceability_hints": [
    {{
      "spec_reference": "<reference in spec>",
      "implementation_hint": "<where to look in code>",
      "keywords": ["<keyword>"]
    }}
  ],
  "implementation_implications": [
    "<implication for implementers>"
  ]
}}

## Analysis:'''


def get_spec_normalization_prompt(
    spec_content: str,
    fork_version: str,
    category: str,
    source: str,
) -> str:
    """Generate the specification normalization prompt.

    Args:
        spec_content: The specification content to analyze
        fork_version: Target fork version
        category: Specification category
        source: Source document reference

    Returns:
        Formatted prompt string
    """
    # Truncate very long content
    max_content_length = 10000
    if len(spec_content) > max_content_length:
        spec_content = spec_content[:max_content_length] + "\n\n[Content truncated...]"

    return SPEC_NORMALIZATION_PROMPT.format(
        spec_content=spec_content,
        fork_version=fork_version,
        category=category,
        source=source,
    )
