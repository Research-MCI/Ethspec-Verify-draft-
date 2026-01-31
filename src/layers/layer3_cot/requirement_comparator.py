"""Requirement-Code comparison logic.

This module provides detailed comparison between individual
requirements and code behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.entities.behavioral_model import BehavioralModel
    from src.core.entities.specification import Constraint, Invariant, Requirement


class ComparisonResult(str, Enum):
    """Result of requirement comparison."""

    MATCH = "match"
    MISMATCH = "mismatch"
    PARTIAL = "partial"
    AMBIGUOUS = "ambiguous"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class ComparisonDetail:
    """Detailed comparison result.

    Attributes:
        result: The comparison result
        confidence: Confidence in the result
        evidence: Supporting evidence
        explanation: Human-readable explanation
        suggestion: Suggestion for resolution
    """

    result: ComparisonResult
    confidence: float
    evidence: list[str]
    explanation: str
    suggestion: str | None = None


class RequirementComparator:
    """Compares requirements against code behavior.

    Uses heuristics and pattern matching to determine if
    code behavior satisfies requirements.
    """

    def __init__(self) -> None:
        """Initialize the comparator."""
        # Keywords indicating required behavior
        self._must_keywords = {"must", "shall", "required", "mandatory"}
        self._should_keywords = {"should", "recommended"}
        self._may_keywords = {"may", "optional", "can"}

    def compare_requirement(
        self,
        requirement: Requirement,
        behavioral_model: BehavioralModel,
    ) -> ComparisonDetail:
        """Compare a requirement against behavioral model.

        Args:
            requirement: The requirement to check
            behavioral_model: Code behavioral model

        Returns:
            ComparisonDetail with results
        """
        evidence: list[str] = []
        explanation_parts: list[str] = []

        # Analyze requirement text
        req_lower = requirement.description.lower()
        is_mandatory = any(kw in req_lower for kw in self._must_keywords)

        # Extract key terms from requirement
        key_terms = self._extract_key_terms(requirement.description)

        # Check against behavioral model
        matches = 0
        total_checks = 0

        # Check data flow
        for term in key_terms:
            total_checks += 1

            # Check state writes
            if any(term in w.lower() for w in behavioral_model.data_flow.state_writes):
                matches += 1
                evidence.append(f"State modification matches: {term}")

            # Check function calls
            elif any(term in f.lower() for f in behavioral_model.data_flow.function_calls):
                matches += 1
                evidence.append(f"Function call matches: {term}")

            # Check constants
            elif any(term in str(c).lower() for c in behavioral_model.data_flow.constants):
                matches += 1
                evidence.append(f"Constant matches: {term}")

        # Check behavioral aspects
        if behavioral_model.postcondition:
            for term in key_terms:
                if term in behavioral_model.postcondition.lower():
                    matches += 1
                    evidence.append(f"Postcondition mentions: {term}")

        # Determine result
        if total_checks == 0:
            result = ComparisonResult.AMBIGUOUS
            confidence = 0.3
            explanation_parts.append("Could not extract key terms to verify")
        elif matches == 0:
            if is_mandatory:
                result = ComparisonResult.MISMATCH
                confidence = 0.6
                explanation_parts.append("No evidence of required behavior found")
            else:
                result = ComparisonResult.AMBIGUOUS
                confidence = 0.4
                explanation_parts.append("Optional requirement - no matching behavior found")
        elif matches < total_checks / 2:
            result = ComparisonResult.PARTIAL
            confidence = 0.5
            explanation_parts.append(f"Partial match: {matches}/{total_checks} terms found")
        else:
            result = ComparisonResult.MATCH
            confidence = 0.7 + (0.2 * matches / total_checks)
            explanation_parts.append(f"Good match: {matches}/{total_checks} terms found")

        return ComparisonDetail(
            result=result,
            confidence=min(confidence, 1.0),
            evidence=evidence,
            explanation="; ".join(explanation_parts),
            suggestion=self._generate_suggestion(result, requirement),
        )

    def compare_constraint(
        self,
        constraint: Constraint,
        behavioral_model: BehavioralModel,
    ) -> ComparisonDetail:
        """Compare a constraint against behavioral model.

        Args:
            constraint: The constraint to check
            behavioral_model: Code behavioral model

        Returns:
            ComparisonDetail with results
        """
        evidence: list[str] = []
        desc_lower = constraint.description.lower()

        # Look for numeric constraints
        import re

        numbers = re.findall(r"\d+", constraint.description)

        # Check if constants match expected values
        constant_strs = [str(c) for c in behavioral_model.data_flow.constants]
        matches = sum(1 for n in numbers if n in constant_strs)

        if numbers and matches > 0:
            evidence.append(f"Constant values present: {matches}/{len(numbers)}")
            result = ComparisonResult.MATCH if matches == len(numbers) else ComparisonResult.PARTIAL
            confidence = 0.6 + (0.3 * matches / len(numbers))
        elif "maximum" in desc_lower or "minimum" in desc_lower:
            # Need to check for bound enforcement
            result = ComparisonResult.AMBIGUOUS
            confidence = 0.4
            evidence.append("Bound constraint - requires deeper analysis")
        else:
            result = ComparisonResult.AMBIGUOUS
            confidence = 0.3
            evidence.append("Cannot automatically verify constraint")

        return ComparisonDetail(
            result=result,
            confidence=confidence,
            evidence=evidence,
            explanation=f"Constraint verification: {result.value}",
        )

    def compare_invariant(
        self,
        invariant: Invariant,
        behavioral_model: BehavioralModel,
    ) -> ComparisonDetail:
        """Compare an invariant against behavioral model.

        Args:
            invariant: The invariant to check
            behavioral_model: Code behavioral model

        Returns:
            ComparisonDetail with results
        """
        evidence: list[str] = []

        # Check if the behavioral model's invariant mentions similar concepts
        if behavioral_model.invariant:
            model_inv_lower = behavioral_model.invariant.lower()
            inv_lower = invariant.description.lower()

            # Simple word overlap check
            inv_words = set(inv_lower.split())
            model_words = set(model_inv_lower.split())

            overlap = inv_words & model_words
            if overlap:
                evidence.append(f"Invariant overlap: {overlap}")
                result = ComparisonResult.MATCH
                confidence = 0.6 + (0.3 * len(overlap) / len(inv_words))
            else:
                result = ComparisonResult.AMBIGUOUS
                confidence = 0.4
                evidence.append("No direct invariant correspondence found")
        else:
            result = ComparisonResult.AMBIGUOUS
            confidence = 0.3
            evidence.append("No invariant extracted from code")

        return ComparisonDetail(
            result=result,
            confidence=confidence,
            evidence=evidence,
            explanation=f"Invariant check: {result.value}",
        )

    def _extract_key_terms(self, text: str) -> list[str]:
        """Extract key terms from requirement text.

        Args:
            text: Requirement text

        Returns:
            List of key terms
        """
        import re

        # Remove common words
        stop_words = {
            "the", "a", "an", "is", "are", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "must", "shall",
            "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "this", "that", "these", "those", "it", "its",
            "and", "or", "but", "if", "then", "when", "where",
        }

        # Extract words
        words = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", text.lower())

        # Filter and return unique terms
        terms = [w for w in words if w not in stop_words and len(w) > 2]
        return list(set(terms))[:10]  # Limit to 10 terms

    def _generate_suggestion(
        self,
        result: ComparisonResult,
        requirement: Requirement,
    ) -> str | None:
        """Generate a suggestion based on comparison result.

        Args:
            result: Comparison result
            requirement: The requirement

        Returns:
            Suggestion string or None
        """
        if result == ComparisonResult.MATCH:
            return None
        elif result == ComparisonResult.MISMATCH:
            return f"Review implementation to ensure it addresses: {requirement.description[:100]}"
        elif result == ComparisonResult.PARTIAL:
            return "Implementation may be incomplete - verify all aspects of the requirement"
        elif result == ComparisonResult.AMBIGUOUS:
            return "Manual review recommended - automated verification inconclusive"
        else:
            return None
