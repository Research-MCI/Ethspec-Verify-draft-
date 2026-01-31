"""Document parser for specification files.

This module handles parsing of various specification document formats
including Python source files, Markdown, and reStructuredText.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from src.core.entities.specification import (
    SpecCategory,
    SpecificationDocument,
    SpecificationMetadata,
)
from src.shared.logger import LoggerMixin

if TYPE_CHECKING:
    pass


class DocumentParser(LoggerMixin):
    """Parser for Ethereum specification documents.

    Supports multiple formats:
    - Python source files (execution-specs style)
    - Markdown files
    - reStructuredText files
    """

    def __init__(self) -> None:
        """Initialize the document parser."""
        self._section_pattern = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
        self._python_docstring_pattern = re.compile(r'"""(.*?)"""', re.DOTALL)
        self._rst_section_pattern = re.compile(r"^(.+)\n[=\-~^]+$", re.MULTILINE)

    async def parse(
        self,
        content: str,
        metadata: SpecificationMetadata,
    ) -> SpecificationDocument:
        """Parse specification content.

        Args:
            content: Raw content string
            metadata: Document metadata

        Returns:
            Parsed SpecificationDocument
        """
        self.logger.info(
            "parsing_document",
            file_path=metadata.file_path,
            category=metadata.category.value,
        )

        # Detect format from file extension
        file_path = metadata.file_path
        if file_path.endswith(".py"):
            return self._parse_python(content, metadata)
        elif file_path.endswith((".md", ".markdown")):
            return self._parse_markdown(content, metadata)
        elif file_path.endswith(".rst"):
            return self._parse_rst(content, metadata)
        else:
            return self._parse_generic(content, metadata)

    async def parse_file(
        self,
        file_path: str,
        metadata: SpecificationMetadata,
    ) -> SpecificationDocument:
        """Parse a specification file.

        Args:
            file_path: Path to the file
            metadata: Document metadata

        Returns:
            Parsed SpecificationDocument
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Specification file not found: {file_path}")

        content = path.read_text(encoding="utf-8")

        # Update metadata with actual file path if different
        if metadata.file_path != file_path:
            metadata = SpecificationMetadata(
                source_repo=metadata.source_repo,
                fork_version=metadata.fork_version,
                category=metadata.category,
                file_path=file_path,
                commit_hash=metadata.commit_hash,
                last_updated=metadata.last_updated,
                eip_number=metadata.eip_number,
            )

        return await self.parse(content, metadata)

    def _parse_python(
        self,
        content: str,
        metadata: SpecificationMetadata,
    ) -> SpecificationDocument:
        """Parse Python specification file.

        Args:
            content: Python source content
            metadata: Document metadata

        Returns:
            SpecificationDocument
        """
        sections: dict[str, str] = {}

        # Extract module docstring
        docstring_match = self._python_docstring_pattern.search(content)
        if docstring_match:
            sections["module_docstring"] = docstring_match.group(1).strip()

        # Extract function and class definitions with docstrings
        function_pattern = re.compile(
            r'def\s+(\w+)\s*\([^)]*\)(?:\s*->\s*[^:]+)?:\s*(?:"""(.*?)""")?',
            re.DOTALL,
        )

        for match in function_pattern.finditer(content):
            func_name = match.group(1)
            func_doc = match.group(2)
            if func_doc:
                sections[f"function:{func_name}"] = func_doc.strip()

        # Extract constants (uppercase assignments)
        const_pattern = re.compile(r"^([A-Z][A-Z0-9_]*)\s*[:=]\s*(.+)$", re.MULTILINE)
        constants = []
        for match in const_pattern.finditer(content):
            constants.append(f"{match.group(1)} = {match.group(2)}")

        if constants:
            sections["constants"] = "\n".join(constants)

        # Generate title from file name or docstring
        title = self._extract_title(content, metadata.file_path)

        return SpecificationDocument(
            doc_id=f"doc-{uuid4().hex[:8]}",
            title=title,
            content=content,
            metadata=metadata,
            sections=sections,
        )

    def _parse_markdown(
        self,
        content: str,
        metadata: SpecificationMetadata,
    ) -> SpecificationDocument:
        """Parse Markdown specification file.

        Args:
            content: Markdown content
            metadata: Document metadata

        Returns:
            SpecificationDocument
        """
        sections: dict[str, str] = {}

        # Extract title from first heading
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1) if title_match else Path(metadata.file_path).stem

        # Extract sections by headings
        current_section = "introduction"
        current_content: list[str] = []

        for line in content.split("\n"):
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if heading_match:
                # Save previous section
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()

                # Start new section
                current_section = heading_match.group(2).lower().replace(" ", "_")
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_content:
            sections[current_section] = "\n".join(current_content).strip()

        return SpecificationDocument(
            doc_id=f"doc-{uuid4().hex[:8]}",
            title=title,
            content=content,
            metadata=metadata,
            sections=sections,
        )

    def _parse_rst(
        self,
        content: str,
        metadata: SpecificationMetadata,
    ) -> SpecificationDocument:
        """Parse reStructuredText specification file.

        Args:
            content: RST content
            metadata: Document metadata

        Returns:
            SpecificationDocument
        """
        sections: dict[str, str] = {}

        # Extract title from first section header
        title = Path(metadata.file_path).stem

        # Find section headers (text followed by line of = or -)
        section_matches = list(self._rst_section_pattern.finditer(content))

        for i, match in enumerate(section_matches):
            section_name = match.group(1).strip().lower().replace(" ", "_")

            # Get content until next section
            start = match.end()
            end = section_matches[i + 1].start() if i + 1 < len(section_matches) else len(content)

            sections[section_name] = content[start:end].strip()

            # Use first section as title
            if i == 0:
                title = match.group(1).strip()

        return SpecificationDocument(
            doc_id=f"doc-{uuid4().hex[:8]}",
            title=title,
            content=content,
            metadata=metadata,
            sections=sections,
        )

    def _parse_generic(
        self,
        content: str,
        metadata: SpecificationMetadata,
    ) -> SpecificationDocument:
        """Parse generic text file.

        Args:
            content: Text content
            metadata: Document metadata

        Returns:
            SpecificationDocument
        """
        title = Path(metadata.file_path).stem

        return SpecificationDocument(
            doc_id=f"doc-{uuid4().hex[:8]}",
            title=title,
            content=content,
            metadata=metadata,
            sections={"full_content": content},
        )

    def _extract_title(self, content: str, file_path: str) -> str:
        """Extract title from content or file path.

        Args:
            content: Document content
            file_path: File path

        Returns:
            Extracted title
        """
        # Try module docstring first line
        docstring_match = self._python_docstring_pattern.search(content)
        if docstring_match:
            first_line = docstring_match.group(1).strip().split("\n")[0]
            if first_line:
                return first_line

        # Fall back to file name
        return Path(file_path).stem.replace("_", " ").title()
