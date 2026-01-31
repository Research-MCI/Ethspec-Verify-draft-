"""Chain-of-Thought reasoning engine.

This module implements the CoT reasoning process for systematic
compliance verification.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from src.core.entities.verification_result import (
    Finding,
    FindingCategory,
    FindingSeverity,
)
from src.layers.layer3_cot.prompts.verification import get_verification_prompt
from src.shared.logger import LoggerMixin
from src.shared.utils.json_utils import extract_json_from_text

if TYPE_CHECKING:
    from src.core.entities.behavioral_model import BehavioralModel
    from src.core.entities.specification import NormalizedSpecification
    from src.core.interfaces.llm_provider import LLMProvider
    from src.core.interfaces.vector_store import SearchResult


class CoTReasoningEngine(LoggerMixin):
    """Chain-of-Thought reasoning engine for compliance verification.

    Implements systematic reasoning to compare implementation behavior
    against specification requirements.
    """

    def __init__(self, llm_provider: LLMProvider) -> None:
        """Initialize the CoT reasoning engine.

        Args:
            llm_provider: LLM provider for reasoning
        """
        self._llm = llm_provider

    async def reason(
        self,
        behavioral_model: BehavioralModel,
        specification: NormalizedSpecification,
        context: list[SearchResult],
    ) -> tuple[list[Finding], str]:
        """Perform CoT reasoning for compliance verification.

        Args:
            behavioral_model: Code behavioral model
            specification: Normalized specification
            context: Retrieved specification context

        Returns:
            Tuple of (list of findings, raw CoT output)
        """
        self.logger.info(
            "starting_cot_reasoning",
            source_file=behavioral_model.source_file,
            requirement_count=specification.total_items,
            context_count=len(context),
        )

        # Build context strings
        spec_context = self._build_specification_context(specification, context)
        impl_context = self._build_implementation_context(behavioral_model)

        # Generate verification prompt
        prompt = get_verification_prompt(
            specification_context=spec_context,
            implementation_context=impl_context,
        )

        try:
            response = await self._llm.generate(
                prompt=prompt,
                temperature=0.2,
                max_tokens=4096,
            )

            raw_output = response.content

            # Parse the response
            findings = self._parse_findings(raw_output, behavioral_model.source_file)

            self.logger.info(
                "cot_reasoning_complete",
                finding_count=len(findings),
            )

            return findings, raw_output

        except Exception as e:
            self.logger.error("cot_reasoning_failed", error=str(e))
            # Return empty findings on error
            return [], f"Error: {e}"

    def _build_specification_context(
        self,
        specification: NormalizedSpecification,
        context: list[SearchResult],
    ) -> str:
        """Build specification context string.

        Args:
            specification: Normalized specification
            context: Retrieved context chunks

        Returns:
            Formatted specification context
        """
        parts = []

        # Add requirements
        if specification.requirements:
            parts.append("### Requirements")
            for req in specification.requirements[:10]:  # Limit to 10
                parts.append(f"- **{req.req_id}**: {req.description}")

        # Add constraints
        if specification.constraints:
            parts.append("\n### Constraints")
            for con in specification.constraints[:5]:
                parts.append(f"- **{con.constraint_id}**: {con.description}")

        # Add invariants
        if specification.invariants:
            parts.append("\n### Invariants")
            for inv in specification.invariants[:5]:
                parts.append(f"- **{inv.invariant_id}**: {inv.description}")

        # Add retrieved context
        if context:
            parts.append("\n### Supporting Excerpts")
            for i, result in enumerate(context[:5]):
                parts.append(f"\n**Excerpt {i + 1}** (relevance: {result.score:.2f})")
                parts.append(result.content[:500])

        return "\n".join(parts)

    def _build_implementation_context(
        self,
        behavioral_model: BehavioralModel,
    ) -> str:
        """Build implementation context string.

        Args:
            behavioral_model: Code behavioral model

        Returns:
            Formatted implementation context
        """
        parts = [
            f"**Source File**: `{behavioral_model.source_file}`",
            f"**Semantic Score**: {behavioral_model.semantic_score:.2f}",
        ]

        # Behavioral aspects
        if behavioral_model.precondition:
            parts.append(f"\n**Precondition**: {behavioral_model.precondition}")
        if behavioral_model.postcondition:
            parts.append(f"**Postcondition**: {behavioral_model.postcondition}")
        if behavioral_model.invariant:
            parts.append(f"**Invariant**: {behavioral_model.invariant}")

        # Data flow
        df = behavioral_model.data_flow
        if df.state_writes:
            parts.append(f"\n**State Modifications**: {', '.join(list(df.state_writes)[:10])}")
        if df.constants:
            parts.append(f"**Constants**: {', '.join(str(c) for c in df.constants[:5])}")
        if df.function_calls:
            parts.append(f"**Function Calls**: {', '.join(list(df.function_calls)[:10])}")
        if df.imports:
            parts.append(f"**Imports**: {', '.join(list(df.imports)[:5])}")

        return "\n".join(parts)

    def _parse_findings(
        self,
        response: str,
        source_file: str,
    ) -> list[Finding]:
        """Parse LLM response into Finding objects.

        Args:
            response: Raw LLM response
            source_file: Source file path

        Returns:
            List of Finding objects
        """
        findings: list[Finding] = []

        json_results = extract_json_from_text(response)

        if not json_results:
            return findings

        result = json_results[0]
        raw_findings = result.get("findings", [])

        for raw in raw_findings:
            # Map status to category
            status = raw.get("status", "AMBIGUOUS")
            if status == "MISMATCH":
                category = FindingCategory.SPECIFICATION_DRIFT
            elif status == "AMBIGUOUS":
                category = FindingCategory.AMBIGUOUS
            else:
                category = FindingCategory.OTHER

            # Map severity
            severity_str = raw.get("severity", "medium").lower()
            severity_map = {
                "critical": FindingSeverity.CRITICAL,
                "high": FindingSeverity.HIGH,
                "medium": FindingSeverity.MEDIUM,
                "low": FindingSeverity.LOW,
                "info": FindingSeverity.INFO,
            }
            severity = severity_map.get(severity_str, FindingSeverity.MEDIUM)

            # Only create findings for non-matches
            if status != "MATCH":
                finding = Finding(
                    finding_id=f"FIND-{uuid4().hex[:8]}",
                    title=raw.get("title", "Compliance Issue"),
                    description=raw.get("description", ""),
                    severity=severity,
                    category=category,
                    confidence=raw.get("confidence", 0.5),
                    requirement_id=raw.get("requirement_id"),
                    code_location=source_file,
                    evidence=tuple(raw.get("evidence", [])),
                    recommendation=raw.get("recommendation"),
                )
                findings.append(finding)

        return findings


class SimpleCoTReasoner:
    """Simplified CoT reasoner for testing.

    Provides basic reasoning without full LLM calls.
    """

    def __init__(self) -> None:
        """Initialize simple reasoner."""
        pass

    async def reason(
        self,
        behavioral_model: BehavioralModel,
        specification: NormalizedSpecification,
        context: list[SearchResult],
    ) -> tuple[list[Finding], str]:
        """Perform simple rule-based reasoning.

        Args:
            behavioral_model: Code behavioral model
            specification: Normalized specification
            context: Retrieved context

        Returns:
            Tuple of (findings, reasoning trace)
        """
        findings: list[Finding] = []
        reasoning_parts = ["Starting verification analysis..."]

        # Check for missing state modifications
        expected_writes = set()
        for req in specification.requirements:
            # Extract potential state variables from requirement
            words = req.description.lower().split()
            for word in words:
                if word.isupper() or word.startswith("state"):
                    expected_writes.add(word)

        actual_writes = set(behavioral_model.data_flow.state_writes)

        missing = expected_writes - actual_writes
        if missing:
            reasoning_parts.append(f"Missing state modifications: {missing}")
            findings.append(
                Finding(
                    finding_id=f"FIND-{uuid4().hex[:8]}",
                    title="Potentially missing state modification",
                    description=f"Expected modifications not found: {missing}",
                    severity=FindingSeverity.MEDIUM,
                    category=FindingCategory.MISSING_IMPLEMENTATION,
                    confidence=0.5,
                    code_location=behavioral_model.source_file,
                )
            )

        reasoning_parts.append(f"Analysis complete. Found {len(findings)} potential issues.")

        return findings, "\n".join(reasoning_parts)
