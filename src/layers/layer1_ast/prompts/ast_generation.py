"""Prompts for AST generation and behavioral extraction.

This module contains the prompts used by the LLM to generate AST
representations and extract behavioral information from source code.
"""

from __future__ import annotations

AST_GENERATION_PROMPT = '''You are an expert code analyzer. Your task is to generate an Abstract Syntax Tree (AST) representation of the provided source code in JSON format.

## Instructions

1. Parse the source code and create a structured AST representation
2. Output ONLY valid JSON - no explanations, no markdown code blocks
3. Include all relevant information: imports, functions, classes, assignments, control flow
4. Preserve type annotations and constants
5. Include line numbers for key nodes

## AST Node Schema

Each node should follow this structure:
{
  "type": "<node_type>",
  "name": "<optional_name>",
  "value": "<optional_value>",
  "children": [<child_nodes>],
  "line": <line_number>,
  "metadata": {<additional_info>}
}

## Node Types

- module: Root node for the entire file
- import: Import statements
- function: Function definitions
- class: Class definitions
- assignment: Variable assignments
- if: If statements
- for: For loops
- while: While loops
- return: Return statements
- call: Function calls
- constant: Literal values
- name: Variable references
- attribute: Attribute access
- binary_op: Binary operations
- compare: Comparisons
- subscript: Subscript/index access
- list: List literals
- dict: Dictionary literals
- try: Try/except blocks
- raise: Raise statements
- assert: Assert statements
- with: Context managers

## Source Code

{source_code}

## Output

Generate the AST JSON:'''


BEHAVIORAL_EXTRACTION_PROMPT = '''You are an expert in formal methods and software verification. Analyze the provided code analysis results and extract behavioral specifications.

## Instructions

1. Identify preconditions (what must be true before execution)
2. Identify postconditions (what will be true after execution)
3. Identify invariants (what remains constant)
4. Consider state modifications, function calls, and control flow
5. Be specific and formal in your descriptions

## Code Analysis

### AST Summary
{ast_summary}

### Control Flow Graph
{cfg_summary}

### Data Flow Information
- State Reads: {state_reads}
- State Writes: {state_writes}
- Constants: {constants}
- Function Calls: {function_calls}

## Output Format

Respond with ONLY a JSON object:
{{
  "precondition": "<description of preconditions>",
  "postcondition": "<description of postconditions>",
  "invariant": "<description of invariants>"
}}

## Analysis Output:'''


def get_ast_generation_prompt(source_code: str, language: str = "python") -> str:
    """Generate the AST generation prompt with source code.

    Args:
        source_code: The source code to analyze
        language: Programming language of the source

    Returns:
        Formatted prompt string
    """
    language_note = ""
    if language != "python":
        language_note = f"\n\nNote: The source code is in {language}. Adapt the AST node types appropriately.\n"

    return AST_GENERATION_PROMPT.format(source_code=source_code) + language_note


def get_behavioral_extraction_prompt(
    ast_summary: str,
    cfg_summary: str,
    state_reads: list[str],
    state_writes: list[str],
    constants: list[str],
    function_calls: list[str],
) -> str:
    """Generate the behavioral extraction prompt.

    Args:
        ast_summary: Summary of the AST
        cfg_summary: Summary of the CFG
        state_reads: List of state variables read
        state_writes: List of state variables written
        constants: List of constants defined
        function_calls: List of function calls made

    Returns:
        Formatted prompt string
    """
    return BEHAVIORAL_EXTRACTION_PROMPT.format(
        ast_summary=ast_summary,
        cfg_summary=cfg_summary,
        state_reads=", ".join(state_reads) if state_reads else "None",
        state_writes=", ".join(state_writes) if state_writes else "None",
        constants=", ".join(str(c) for c in constants) if constants else "None",
        function_calls=", ".join(function_calls) if function_calls else "None",
    )
