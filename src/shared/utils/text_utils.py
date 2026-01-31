"""Text processing utility functions.

This module provides utilities for text cleaning, normalization,
and extraction operations.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace and normalizing.

    Args:
        text: Input text

    Returns:
        Cleaned text
    """
    # Remove null bytes and other problematic characters
    text = text.replace("\x00", "")

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove excessive blank lines (more than 2 consecutive)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading/trailing whitespace
    return text.strip()


def normalize_whitespace(text: str) -> str:
    """Normalize all whitespace to single spaces.

    Args:
        text: Input text

    Returns:
        Text with normalized whitespace
    """
    return " ".join(text.split())


def truncate_text(
    text: str,
    max_length: int,
    suffix: str = "...",
    word_boundary: bool = True,
) -> str:
    """Truncate text to a maximum length.

    Args:
        text: Input text
        max_length: Maximum length (including suffix)
        suffix: Suffix to append when truncated
        word_boundary: Whether to truncate at word boundaries

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    truncate_at = max_length - len(suffix)

    if word_boundary:
        # Find the last space before the truncation point
        last_space = text.rfind(" ", 0, truncate_at)
        if last_space > 0:
            truncate_at = last_space

    return text[:truncate_at].rstrip() + suffix


@dataclass
class CodeBlock:
    """Represents an extracted code block.

    Attributes:
        language: Programming language (if specified)
        code: The code content
        start_line: Starting line in original text
    """

    language: str | None
    code: str
    start_line: int


def extract_code_blocks(text: str) -> list[CodeBlock]:
    """Extract code blocks from markdown-style text.

    Supports both fenced code blocks (```) and indented code blocks.

    Args:
        text: Input text containing code blocks

    Returns:
        List of CodeBlock objects
    """
    blocks: list[CodeBlock] = []

    # Pattern for fenced code blocks
    fenced_pattern = r"```(\w*)\n([\s\S]*?)```"
    for match in re.finditer(fenced_pattern, text):
        language = match.group(1) or None
        code = match.group(2).strip()
        start_line = text[: match.start()].count("\n") + 1
        blocks.append(CodeBlock(language=language, code=code, start_line=start_line))

    # Pattern for indented code blocks (4 spaces or 1 tab)
    lines = text.split("\n")
    in_indented_block = False
    current_block: list[str] = []
    block_start = 0

    for i, line in enumerate(lines):
        is_indented = line.startswith("    ") or line.startswith("\t")
        is_empty = not line.strip()

        if is_indented and not in_indented_block:
            in_indented_block = True
            block_start = i + 1
            current_block = [line[4:] if line.startswith("    ") else line[1:]]
        elif is_indented and in_indented_block:
            current_block.append(line[4:] if line.startswith("    ") else line[1:])
        elif is_empty and in_indented_block:
            current_block.append("")
        elif in_indented_block:
            # End of indented block
            code = "\n".join(current_block).strip()
            if code:
                blocks.append(CodeBlock(language=None, code=code, start_line=block_start))
            in_indented_block = False
            current_block = []

    # Handle block at end of text
    if in_indented_block and current_block:
        code = "\n".join(current_block).strip()
        if code:
            blocks.append(CodeBlock(language=None, code=code, start_line=block_start))

    return blocks


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences.

    Args:
        text: Input text

    Returns:
        List of sentences
    """
    # Simple sentence splitting (handles common cases)
    # Doesn't split on abbreviations like Mr., Dr., etc.
    pattern = r"(?<=[.!?])\s+(?=[A-Z])"
    sentences = re.split(pattern, text)
    return [s.strip() for s in sentences if s.strip()]


def extract_identifiers(code: str) -> list[str]:
    """Extract identifier names from code.

    Args:
        code: Source code

    Returns:
        List of unique identifiers
    """
    # Pattern for Python/JS-style identifiers
    pattern = r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b"
    matches = re.findall(pattern, code)

    # Filter out common keywords
    keywords = {
        "if",
        "else",
        "elif",
        "for",
        "while",
        "def",
        "class",
        "return",
        "import",
        "from",
        "as",
        "try",
        "except",
        "finally",
        "with",
        "True",
        "False",
        "None",
        "and",
        "or",
        "not",
        "in",
        "is",
        "lambda",
        "yield",
        "async",
        "await",
        "pass",
        "break",
        "continue",
        "raise",
        "global",
        "nonlocal",
        "assert",
        "del",
    }

    return list(set(m for m in matches if m not in keywords))


def compute_text_similarity(text1: str, text2: str) -> float:
    """Compute simple text similarity based on word overlap.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Similarity score between 0.0 and 1.0
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union)  # Jaccard similarity
