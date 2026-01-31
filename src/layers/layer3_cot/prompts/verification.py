"""Prompts for Chain-of-Thought verification.

This module contains prompts used by the LLM for systematic
compliance verification using CoT reasoning.
"""

from __future__ import annotations

VERIFICATION_PROMPT = '''You are an expert in Ethereum protocol specification compliance verification. Analyze whether the implementation correctly satisfies the specification requirements.

## Instructions

1. Carefully analyze each requirement against the implementation
2. Use step-by-step reasoning to evaluate compliance
3. Identify any deviations, missing implementations, or incorrect behaviors
4. Provide evidence-based findings with confidence assessments
5. Be precise and technical in your analysis

## Specification Requirements

{specification_context}

## Implementation Under Analysis

{implementation_context}

## Verification Task

For each requirement, determine:
- MATCH: Implementation correctly satisfies the requirement
- MISMATCH: Implementation deviates from the requirement
- AMBIGUOUS: Cannot determine with available information

## Output Format

Respond with ONLY a JSON object:
{{
  "reasoning_trace": "<your step-by-step reasoning>",
  "findings": [
    {{
      "requirement_id": "<requirement ID being checked>",
      "status": "MATCH|MISMATCH|AMBIGUOUS",
      "title": "<brief finding title>",
      "description": "<detailed description>",
      "severity": "critical|high|medium|low|info",
      "evidence": ["<evidence point 1>", "<evidence point 2>"],
      "recommendation": "<suggested fix if applicable>",
      "confidence": 0.0-1.0
    }}
  ],
  "overall_assessment": {{
    "compliance_level": "full|partial|non-compliant",
    "key_concerns": ["<concern 1>", "<concern 2>"],
    "confidence": 0.0-1.0
  }}
}}

## Analysis:'''


def get_verification_prompt(
    specification_context: str,
    implementation_context: str,
) -> str:
    """Generate the verification prompt.

    Args:
        specification_context: Formatted specification content
        implementation_context: Formatted implementation details

    Returns:
        Formatted prompt string
    """
    return VERIFICATION_PROMPT.format(
        specification_context=specification_context,
        implementation_context=implementation_context,
    )


SINGLE_REQUIREMENT_PROMPT = '''You are verifying a single Ethereum protocol requirement against an implementation.

## Requirement
ID: {requirement_id}
Description: {requirement_description}

## Specification Context
{spec_context}

## Implementation
{implementation_summary}

## Task
Determine if the implementation satisfies this specific requirement.

Think step by step:
1. What exactly does the requirement demand?
2. What does the implementation do?
3. Do they match?

Respond with JSON:
{{
  "reasoning": "<your step-by-step analysis>",
  "status": "MATCH|MISMATCH|AMBIGUOUS",
  "confidence": 0.0-1.0,
  "evidence": ["<evidence>"],
  "issues": ["<issue if any>"]
}}'''


def get_single_requirement_prompt(
    requirement_id: str,
    requirement_description: str,
    spec_context: str,
    implementation_summary: str,
) -> str:
    """Generate prompt for single requirement verification.

    Args:
        requirement_id: Requirement identifier
        requirement_description: Requirement text
        spec_context: Supporting specification context
        implementation_summary: Implementation summary

    Returns:
        Formatted prompt
    """
    return SINGLE_REQUIREMENT_PROMPT.format(
        requirement_id=requirement_id,
        requirement_description=requirement_description,
        spec_context=spec_context,
        implementation_summary=implementation_summary,
    )
