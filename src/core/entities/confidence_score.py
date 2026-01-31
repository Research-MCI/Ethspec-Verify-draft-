"""Confidence score entity for verification results.

This module defines data structures for confidence scoring based on
evidence strength, context consistency, and reasoning coherence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EvidenceType(str, Enum):
    """Types of evidence supporting a finding."""

    DIRECT_MATCH = "direct_match"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    STRUCTURAL_MATCH = "structural_match"
    BEHAVIORAL_MATCH = "behavioral_match"
    CONSTRAINT_CHECK = "constraint_check"
    INVARIANT_CHECK = "invariant_check"
    EDGE_CASE_COVERAGE = "edge_case_coverage"
    CODE_PATTERN = "code_pattern"
    DOCUMENTATION = "documentation"
    INFERENCE = "inference"


@dataclass(frozen=True)
class EvidenceItem:
    """A single piece of evidence supporting a finding.

    Attributes:
        evidence_type: Type of evidence
        description: Description of the evidence
        strength: Evidence strength (0.0 to 1.0)
        source: Source of the evidence (e.g., spec chunk ID, code location)
        metadata: Additional metadata about the evidence
    """

    evidence_type: EvidenceType
    description: str
    strength: float
    source: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert evidence item to dictionary representation."""
        return {
            "evidence_type": self.evidence_type.value,
            "description": self.description,
            "strength": self.strength,
            "source": self.source,
            "metadata": self.metadata,
        }

    @property
    def is_strong(self) -> bool:
        """Check if this is strong evidence."""
        return self.strength >= 0.7


@dataclass(frozen=True)
class ConfidenceBreakdown:
    """Breakdown of confidence score components.

    Attributes:
        evidence_score: Score based on evidence strength (0.0 to 1.0)
        context_score: Score based on context consistency (0.0 to 1.0)
        reasoning_score: Score based on reasoning coherence (0.0 to 1.0)
        coverage_score: Score based on requirement coverage (0.0 to 1.0)
        evidence_weight: Weight for evidence score
        context_weight: Weight for context score
        reasoning_weight: Weight for reasoning score
        coverage_weight: Weight for coverage score
    """

    evidence_score: float
    context_score: float
    reasoning_score: float
    coverage_score: float = 1.0
    evidence_weight: float = 0.35
    context_weight: float = 0.25
    reasoning_weight: float = 0.25
    coverage_weight: float = 0.15

    def to_dict(self) -> dict[str, Any]:
        """Convert breakdown to dictionary representation."""
        return {
            "evidence_score": self.evidence_score,
            "context_score": self.context_score,
            "reasoning_score": self.reasoning_score,
            "coverage_score": self.coverage_score,
            "weights": {
                "evidence": self.evidence_weight,
                "context": self.context_weight,
                "reasoning": self.reasoning_weight,
                "coverage": self.coverage_weight,
            },
        }

    @property
    def weighted_score(self) -> float:
        """Calculate the weighted confidence score."""
        return (
            self.evidence_score * self.evidence_weight
            + self.context_score * self.context_weight
            + self.reasoning_score * self.reasoning_weight
            + self.coverage_score * self.coverage_weight
        )


@dataclass(frozen=True)
class ConfidenceScore:
    """Complete confidence score for a verification finding.

    Attributes:
        score: Overall confidence score (0.0 to 1.0)
        breakdown: Detailed breakdown of score components
        evidence_items: Supporting evidence items
        uncertainty_factors: Factors contributing to uncertainty
        calibration_adjustment: Adjustment based on historical calibration
    """

    score: float
    breakdown: ConfidenceBreakdown
    evidence_items: tuple[EvidenceItem, ...] = field(default_factory=tuple)
    uncertainty_factors: tuple[str, ...] = field(default_factory=tuple)
    calibration_adjustment: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert confidence score to dictionary representation."""
        return {
            "score": self.score,
            "breakdown": self.breakdown.to_dict(),
            "evidence_items": [e.to_dict() for e in self.evidence_items],
            "uncertainty_factors": list(self.uncertainty_factors),
            "calibration_adjustment": self.calibration_adjustment,
        }

    @property
    def is_high_confidence(self) -> bool:
        """Check if this is a high confidence score."""
        return self.score >= 0.8

    @property
    def is_low_confidence(self) -> bool:
        """Check if this is a low confidence score."""
        return self.score < 0.5

    @property
    def requires_human_review(self) -> bool:
        """Check if human review is recommended."""
        return self.score < 0.7 or len(self.uncertainty_factors) > 2

    @classmethod
    def create_high_confidence(
        cls,
        evidence_items: tuple[EvidenceItem, ...],
    ) -> ConfidenceScore:
        """Create a high confidence score with strong evidence."""
        avg_strength = (
            sum(e.strength for e in evidence_items) / len(evidence_items)
            if evidence_items
            else 0.0
        )
        breakdown = ConfidenceBreakdown(
            evidence_score=avg_strength,
            context_score=0.9,
            reasoning_score=0.9,
            coverage_score=0.9,
        )
        return cls(
            score=breakdown.weighted_score,
            breakdown=breakdown,
            evidence_items=evidence_items,
        )

    @classmethod
    def create_low_confidence(
        cls,
        reason: str,
        evidence_items: tuple[EvidenceItem, ...] = tuple(),
    ) -> ConfidenceScore:
        """Create a low confidence score with uncertainty."""
        avg_strength = (
            sum(e.strength for e in evidence_items) / len(evidence_items)
            if evidence_items
            else 0.3
        )
        breakdown = ConfidenceBreakdown(
            evidence_score=avg_strength,
            context_score=0.4,
            reasoning_score=0.4,
            coverage_score=0.5,
        )
        return cls(
            score=breakdown.weighted_score,
            breakdown=breakdown,
            evidence_items=evidence_items,
            uncertainty_factors=(reason,),
        )
