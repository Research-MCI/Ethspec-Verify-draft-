"""Specification normalizer using LLM.

This module normalizes specification content into structured
requirements, constraints, and invariants using LLM processing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from src.core.entities.specification import (
    Constraint,
    EdgeCase,
    Invariant,
    NormalizedSpecification,
    Requirement,
    SpecCategory,
    TraceabilityHint,
)
from src.layers.layer2_rag.prompts.spec_extraction import get_spec_normalization_prompt
from src.shared.logger import LoggerMixin
from src.shared.utils.json_utils import extract_json_from_text

if TYPE_CHECKING:
    from src.core.entities.specification import SpecificationChunk, SpecificationDocument
    from src.core.interfaces.llm_provider import LLMProvider


class SpecificationNormalizer(LoggerMixin):
    """Normalizes specifications into structured format using LLM.

    Extracts:
    - Requirements (MUST, SHALL, SHOULD)
    - Constraints (limits, bounds)
    - Invariants (always-true properties)
    - Edge cases
    - Traceability hints
    """

    def __init__(self, llm_provider: LLMProvider) -> None:
        """Initialize the specification normalizer.

        Args:
            llm_provider: LLM provider for processing
        """
        self._llm = llm_provider

    async def normalize(
        self,
        document: SpecificationDocument,
        chunks: list[SpecificationChunk],
    ) -> NormalizedSpecification:
        """Normalize a specification document.

        Args:
            document: The parsed document
            chunks: Document chunks

        Returns:
            NormalizedSpecification
        """
        self.logger.info(
            "normalizing_specification",
            doc_id=document.doc_id,
            chunk_count=len(chunks),
        )

        # Combine chunk content for processing
        combined_content = self._combine_chunks(chunks)

        # Generate normalization prompt
        prompt = get_spec_normalization_prompt(
            spec_content=combined_content,
            fork_version=document.metadata.fork_version,
            category=document.metadata.category.value,
            source=document.metadata.file_path,
        )

        try:
            response = await self._llm.generate(
                prompt=prompt,
                temperature=0.2,
            )

            # Extract JSON from response
            json_results = extract_json_from_text(response.content)

            if json_results:
                return self._parse_normalized_spec(
                    json_results[0],
                    document,
                )

            # Fallback to rule-based extraction
            return self._rule_based_extraction(document, chunks)

        except Exception as e:
            self.logger.error("normalization_failed", error=str(e))
            return self._rule_based_extraction(document, chunks)

    def _combine_chunks(self, chunks: list[SpecificationChunk]) -> str:
        """Combine chunks into a single string.

        Args:
            chunks: List of chunks

        Returns:
            Combined content string
        """
        sections: dict[str, list[str]] = {}

        for chunk in chunks:
            section = chunk.parent_section or "main"
            if section not in sections:
                sections[section] = []
            sections[section].append(chunk.content)

        parts = []
        for section_name, contents in sections.items():
            parts.append(f"## {section_name}\n")
            parts.append("\n\n".join(contents))
            parts.append("\n")

        return "\n".join(parts)

    def _parse_normalized_spec(
        self,
        json_data: dict,
        document: SpecificationDocument,
    ) -> NormalizedSpecification:
        """Parse JSON response into NormalizedSpecification.

        Args:
            json_data: Parsed JSON data
            document: Source document

        Returns:
            NormalizedSpecification
        """
        # Parse requirements
        requirements: list[Requirement] = []
        for req in json_data.get("requirements", []):
            requirements.append(
                Requirement(
                    req_id=req.get("id", f"REQ-{uuid4().hex[:6]}"),
                    description=req.get("description", ""),
                    source_chunk=document.doc_id,
                    category=document.metadata.category,
                    priority=req.get("priority", 3),
                )
            )

        # Parse constraints
        constraints: list[Constraint] = []
        for con in json_data.get("constraints", []):
            constraints.append(
                Constraint(
                    constraint_id=con.get("id", f"CON-{uuid4().hex[:6]}"),
                    description=con.get("description", ""),
                    source_chunk=document.doc_id,
                    constraint_type=con.get("type", "general"),
                    is_hard=con.get("is_hard", True),
                )
            )

        # Parse invariants
        invariants: list[Invariant] = []
        for inv in json_data.get("invariants", []):
            invariants.append(
                Invariant(
                    invariant_id=inv.get("id", f"INV-{uuid4().hex[:6]}"),
                    description=inv.get("description", ""),
                    source_chunk=document.doc_id,
                    scope=inv.get("scope", "global"),
                )
            )

        # Parse edge cases
        edge_cases: list[EdgeCase] = []
        for edge in json_data.get("edge_cases", []):
            edge_cases.append(
                EdgeCase(
                    edge_case_id=edge.get("id", f"EDGE-{uuid4().hex[:6]}"),
                    description=edge.get("description", ""),
                    source_chunk=document.doc_id,
                    trigger_condition=edge.get("trigger", ""),
                    expected_behavior=edge.get("expected_behavior", ""),
                )
            )

        # Parse traceability hints
        hints: list[TraceabilityHint] = []
        for hint in json_data.get("traceability_hints", []):
            hints.append(
                TraceabilityHint(
                    hint_id=f"HINT-{uuid4().hex[:6]}",
                    spec_reference=hint.get("spec_reference", ""),
                    implementation_hint=hint.get("implementation_hint", ""),
                    keywords=tuple(hint.get("keywords", [])),
                )
            )

        # Get implementation implications
        implications = tuple(json_data.get("implementation_implications", []))

        return NormalizedSpecification(
            spec_id=f"spec-{uuid4().hex[:8]}",
            fork_version=document.metadata.fork_version,
            requirements=tuple(requirements),
            constraints=tuple(constraints),
            invariants=tuple(invariants),
            edge_cases=tuple(edge_cases),
            traceability_hints=tuple(hints),
            implementation_implications=implications,
            source_documents=(document.doc_id,),
        )

    def _rule_based_extraction(
        self,
        document: SpecificationDocument,
        chunks: list[SpecificationChunk],
    ) -> NormalizedSpecification:
        """Fallback rule-based extraction.

        Args:
            document: Source document
            chunks: Document chunks

        Returns:
            NormalizedSpecification
        """
        import re

        requirements: list[Requirement] = []
        constraints: list[Constraint] = []
        invariants: list[Invariant] = []

        req_pattern = re.compile(r"(must|shall|should|will|required)\s+(.+?)(?:\.|$)", re.IGNORECASE)
        const_pattern = re.compile(r"(maximum|minimum|limit|at most|at least)\s+(.+?)(?:\.|$)", re.IGNORECASE)
        inv_pattern = re.compile(r"(always|never|invariant|constant)\s+(.+?)(?:\.|$)", re.IGNORECASE)

        for chunk in chunks:
            content = chunk.content

            # Extract requirements
            for match in req_pattern.finditer(content):
                requirements.append(
                    Requirement(
                        req_id=f"REQ-{uuid4().hex[:6]}",
                        description=f"{match.group(1)} {match.group(2)}".strip(),
                        source_chunk=chunk.chunk_id,
                        category=document.metadata.category,
                    )
                )

            # Extract constraints
            for match in const_pattern.finditer(content):
                constraints.append(
                    Constraint(
                        constraint_id=f"CON-{uuid4().hex[:6]}",
                        description=f"{match.group(1)} {match.group(2)}".strip(),
                        source_chunk=chunk.chunk_id,
                    )
                )

            # Extract invariants
            for match in inv_pattern.finditer(content):
                invariants.append(
                    Invariant(
                        invariant_id=f"INV-{uuid4().hex[:6]}",
                        description=f"{match.group(1)} {match.group(2)}".strip(),
                        source_chunk=chunk.chunk_id,
                    )
                )

        return NormalizedSpecification(
            spec_id=f"spec-{uuid4().hex[:8]}",
            fork_version=document.metadata.fork_version,
            requirements=tuple(requirements[:50]),  # Limit count
            constraints=tuple(constraints[:20]),
            invariants=tuple(invariants[:20]),
            source_documents=(document.doc_id,),
        )
