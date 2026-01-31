"""Confidence score calculation.

This module calculates confidence scores for verification findings
based on evidence strength, context consistency, and reasoning coherence.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.entities.confidence_score import (
    ConfidenceBreakdown,
    ConfidenceScore,
    EvidenceItem,
    EvidenceType,
)

if TYPE_CHECKING:
    from src.core.entities.verification_result import Finding
    from src.core.interfaces.vector_store import SearchResult


class ConfidenceCalculator:
    """Calculates confidence scores for verification findings.

    Considers:
    - Evidence strength and quantity
    - Context consistency (agreement between sources)
    - Reasoning coherence (logical consistency)
    - Coverage (how much of the requirement was verified)
    """

    def __init__(
        self,
        evidence_weight: float = 0.35,
        context_weight: float = 0.25,
        reasoning_weight: float = 0.25,
        coverage_weight: float = 0.15,
    ) -> None:
        """Initialize the confidence calculator.

        Args:
            evidence_weight: Weight for evidence score
            context_weight: Weight for context score
            reasoning_weight: Weight for reasoning score
            coverage_weight: Weight for coverage score
        """
        self.evidence_weight = evidence_weight
        self.context_weight = context_weight
        self.reasoning_weight = reasoning_weight
        self.coverage_weight = coverage_weight

    def calculate(
        self,
        finding: Finding,
        evidence: list[SearchResult],
    ) -> ConfidenceScore:
        """Calculate confidence score for a finding.

        Args:
            finding: The finding to score
            evidence: Supporting evidence from RAG

        Returns:
            ConfidenceScore
        """
        # Build evidence items
        evidence_items = self._build_evidence_items(finding, evidence)

        # Calculate component scores
        evidence_score = self._calculate_evidence_score(evidence_items, evidence)
        context_score = self._calculate_context_score(evidence)
        reasoning_score = self._calculate_reasoning_score(finding)
        coverage_score = self._calculate_coverage_score(finding, evidence)

        # Calculate breakdown
        breakdown = ConfidenceBreakdown(
            evidence_score=evidence_score,
            context_score=context_score,
            reasoning_score=reasoning_score,
            coverage_score=coverage_score,
            evidence_weight=self.evidence_weight,
            context_weight=self.context_weight,
            reasoning_weight=self.reasoning_weight,
            coverage_weight=self.coverage_weight,
        )

        # Identify uncertainty factors
        uncertainty_factors = self._identify_uncertainty_factors(
            finding, evidence, breakdown
        )

        # Calculate final score
        final_score = breakdown.weighted_score

        # Apply calibration adjustment if needed
        calibration_adjustment = self._calculate_calibration_adjustment(
            finding, final_score
        )

        return ConfidenceScore(
            score=min(max(final_score + calibration_adjustment, 0.0), 1.0),
            breakdown=breakdown,
            evidence_items=tuple(evidence_items),
            uncertainty_factors=tuple(uncertainty_factors),
            calibration_adjustment=calibration_adjustment,
        )

    def _build_evidence_items(
        self,
        finding: Finding,
        evidence: list[SearchResult],
    ) -> list[EvidenceItem]:
        """Build evidence items from finding and search results.

        Args:
            finding: The finding
            evidence: Search results

        Returns:
            List of EvidenceItem
        """
        items: list[EvidenceItem] = []

        # Add evidence from the finding itself
        for ev in finding.evidence:
            items.append(
                EvidenceItem(
                    evidence_type=EvidenceType.DIRECT_MATCH,
                    description=ev,
                    strength=0.7,
                    source="finding",
                )
            )

        # Add evidence from search results
        for result in evidence[:5]:  # Top 5 results
            strength = result.score  # Use relevance score as strength
            items.append(
                EvidenceItem(
                    evidence_type=EvidenceType.SEMANTIC_SIMILARITY,
                    description=result.content[:100] + "...",
                    strength=strength,
                    source=result.chunk_id,
                    metadata={"relevance_score": result.score},
                )
            )

        return items

    def _calculate_evidence_score(
        self,
        evidence_items: list[EvidenceItem],
        search_results: list[SearchResult],
    ) -> float:
        """Calculate evidence strength score.

        Args:
            evidence_items: Evidence items
            search_results: Search results

        Returns:
            Evidence score (0.0 to 1.0)
        """
        if not evidence_items:
            return 0.3  # Base score for no evidence

        # Average strength of evidence
        avg_strength = sum(e.strength for e in evidence_items) / len(evidence_items)

        # Boost for quantity of evidence
        quantity_boost = min(0.2, len(evidence_items) * 0.04)

        # Boost for high-relevance search results
        if search_results:
            high_relevance = sum(1 for r in search_results if r.score > 0.8)
            relevance_boost = min(0.1, high_relevance * 0.02)
        else:
            relevance_boost = 0

        return min(1.0, avg_strength + quantity_boost + relevance_boost)

    def _calculate_context_score(
        self,
        evidence: list[SearchResult],
    ) -> float:
        """Calculate context consistency score.

        Args:
            evidence: Search results

        Returns:
            Context score (0.0 to 1.0)
        """
        if not evidence:
            return 0.5  # Neutral score for no context

        # Check consistency of evidence scores
        scores = [r.score for r in evidence[:5]]

        if len(scores) < 2:
            return 0.6

        # Calculate variance in relevance scores
        avg_score = sum(scores) / len(scores)
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)

        # Lower variance = higher consistency
        consistency = 1.0 - min(variance * 2, 0.5)

        # Also consider average relevance
        relevance_factor = avg_score

        return (consistency + relevance_factor) / 2

    def _calculate_reasoning_score(
        self,
        finding: Finding,
    ) -> float:
        """Calculate reasoning coherence score.

        Args:
            finding: The finding

        Returns:
            Reasoning score (0.0 to 1.0)
        """
        score = 0.5  # Base score

        # Check if finding has description
        if finding.description:
            # Longer, more detailed descriptions indicate better reasoning
            desc_length = len(finding.description)
            if desc_length > 100:
                score += 0.2
            elif desc_length > 50:
                score += 0.1

        # Check if finding has evidence
        if finding.evidence:
            score += min(0.2, len(finding.evidence) * 0.05)

        # Check if finding has recommendation
        if finding.recommendation:
            score += 0.1

        # Check if requirement is linked
        if finding.requirement_id:
            score += 0.1

        return min(1.0, score)

    def _calculate_coverage_score(
        self,
        finding: Finding,
        evidence: list[SearchResult],
    ) -> float:
        """Calculate requirement coverage score.

        Args:
            finding: The finding
            evidence: Search results

        Returns:
            Coverage score (0.0 to 1.0)
        """
        if not finding.requirement_id:
            return 0.7  # Default for findings without specific requirement

        # Check if we have evidence related to the requirement
        if evidence:
            # At least some evidence suggests coverage
            return 0.8

        return 0.6

    def _identify_uncertainty_factors(
        self,
        finding: Finding,
        evidence: list[SearchResult],
        breakdown: ConfidenceBreakdown,
    ) -> list[str]:
        """Identify factors contributing to uncertainty.

        Args:
            finding: The finding
            evidence: Search results
            breakdown: Score breakdown

        Returns:
            List of uncertainty factors
        """
        factors: list[str] = []

        if breakdown.evidence_score < 0.5:
            factors.append("Limited supporting evidence")

        if breakdown.context_score < 0.5:
            factors.append("Inconsistent context")

        if breakdown.reasoning_score < 0.5:
            factors.append("Weak reasoning chain")

        if not evidence:
            factors.append("No specification excerpts retrieved")

        if not finding.evidence:
            factors.append("No direct evidence provided")

        if finding.confidence < 0.5:
            factors.append("Low initial confidence")

        return factors

    def _calculate_calibration_adjustment(
        self,
        finding: Finding,
        base_score: float,
    ) -> float:
        """Calculate calibration adjustment based on severity.

        Higher severity findings may need adjustment to avoid
        false positives being too confident.

        Args:
            finding: The finding
            base_score: Base confidence score

        Returns:
            Calibration adjustment
        """
        from src.core.entities.verification_result import FindingSeverity

        # For high/critical findings, be more conservative
        if finding.severity in (FindingSeverity.CRITICAL, FindingSeverity.HIGH):
            if base_score > 0.8:
                return -0.1  # Reduce overconfidence
            elif base_score < 0.4:
                return 0.05  # Slight boost for low-confidence critical
        elif finding.severity == FindingSeverity.INFO:
            # Info findings can be more confident
            if base_score > 0.5:
                return 0.05

        return 0.0
