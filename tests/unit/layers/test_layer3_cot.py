"""Unit tests for Layer 3: CoT Verification Engine."""

from __future__ import annotations

import pytest

from src.core.entities.verification_result import FindingCategory, FindingSeverity
from src.layers.layer3_cot.confidence_calculator import ConfidenceCalculator
from src.layers.layer3_cot.requirement_comparator import (
    ComparisonResult,
    RequirementComparator,
)


class TestRequirementComparator:
    """Tests for RequirementComparator."""

    def test_compare_matching_requirement(
        self, sample_normalized_spec, sample_behavioral_model
    ) -> None:
        """Test comparison with matching requirement."""
        comparator = RequirementComparator()

        # The sample has FORK_CRITERIA in state_writes
        requirement = sample_normalized_spec.requirements[0]  # About fork criteria
        result = comparator.compare_requirement(requirement, sample_behavioral_model)

        assert result.result in (ComparisonResult.MATCH, ComparisonResult.PARTIAL)
        assert result.confidence > 0

    def test_compare_constraint(
        self, sample_normalized_spec, sample_behavioral_model
    ) -> None:
        """Test constraint comparison."""
        comparator = RequirementComparator()

        constraint = sample_normalized_spec.constraints[0]  # About max block size
        result = comparator.compare_constraint(constraint, sample_behavioral_model)

        # 1048576 is in the constants
        assert result.confidence > 0
        assert len(result.evidence) > 0

    def test_compare_invariant(
        self, sample_normalized_spec, sample_behavioral_model
    ) -> None:
        """Test invariant comparison."""
        comparator = RequirementComparator()

        invariant = sample_normalized_spec.invariants[0]
        result = comparator.compare_invariant(invariant, sample_behavioral_model)

        # Should find some relationship
        assert result.result in (
            ComparisonResult.MATCH,
            ComparisonResult.PARTIAL,
            ComparisonResult.AMBIGUOUS,
        )

    def test_extract_key_terms(self) -> None:
        """Test key term extraction."""
        comparator = RequirementComparator()

        text = "The fork criteria must be defined by a specific block number."
        terms = comparator._extract_key_terms(text)

        assert "fork" in terms
        assert "criteria" in terms
        assert "block" in terms
        # Common words should be excluded
        assert "the" not in terms
        assert "must" not in terms


class TestConfidenceCalculator:
    """Tests for ConfidenceCalculator."""

    def test_calculate_confidence(self, sample_finding) -> None:
        """Test confidence calculation."""
        from src.core.interfaces.vector_store import SearchResult

        calculator = ConfidenceCalculator()

        evidence = [
            SearchResult(
                chunk_id="chunk-1",
                content="Relevant specification text",
                score=0.9,
                metadata={},
            ),
        ]

        confidence = calculator.calculate(sample_finding, evidence)

        assert 0.0 <= confidence.score <= 1.0
        assert confidence.breakdown is not None
        assert len(confidence.evidence_items) > 0

    def test_confidence_with_no_evidence(self, sample_finding) -> None:
        """Test confidence with no evidence."""
        calculator = ConfidenceCalculator()

        confidence = calculator.calculate(sample_finding, [])

        # Should still produce a score, but lower
        assert 0.0 <= confidence.score <= 1.0
        assert "No specification excerpts retrieved" in confidence.uncertainty_factors

    def test_confidence_breakdown_weights(self) -> None:
        """Test that confidence weights sum to 1."""
        calculator = ConfidenceCalculator()

        total_weight = (
            calculator.evidence_weight
            + calculator.context_weight
            + calculator.reasoning_weight
            + calculator.coverage_weight
        )

        assert abs(total_weight - 1.0) < 0.01

    def test_high_confidence_for_strong_evidence(self, sample_finding) -> None:
        """Test that strong evidence produces high confidence."""
        from src.core.interfaces.vector_store import SearchResult

        calculator = ConfidenceCalculator()

        # Create strong evidence
        evidence = [
            SearchResult(chunk_id=f"chunk-{i}", content="Strong evidence", score=0.95, metadata={})
            for i in range(5)
        ]

        confidence = calculator.calculate(sample_finding, evidence)

        assert confidence.score >= 0.6  # Should be reasonably high


class TestReportGenerator:
    """Tests for JSONReportGenerator."""

    @pytest.mark.asyncio
    async def test_generate_json_report(self, sample_verification_result) -> None:
        """Test JSON report generation."""
        import json

        from src.core.interfaces.report_generator import ReportFormat
        from src.layers.layer3_cot.report_generator import JSONReportGenerator

        generator = JSONReportGenerator()
        report = await generator.generate(sample_verification_result, ReportFormat.JSON)

        # Should be valid JSON
        data = json.loads(report)
        assert "run_id" in data
        assert "summary" in data
        assert "findings" in data

    @pytest.mark.asyncio
    async def test_generate_markdown_report(self, sample_verification_result) -> None:
        """Test Markdown report generation."""
        from src.core.interfaces.report_generator import ReportFormat
        from src.layers.layer3_cot.report_generator import JSONReportGenerator

        generator = JSONReportGenerator()
        report = await generator.generate(sample_verification_result, ReportFormat.MARKDOWN)

        assert "# Specification Compliance Report" in report
        assert sample_verification_result.run_id in report

    @pytest.mark.asyncio
    async def test_generate_pr_comment(self, sample_verification_result) -> None:
        """Test PR comment generation."""
        from src.layers.layer3_cot.report_generator import JSONReportGenerator

        generator = JSONReportGenerator()
        comment = await generator.generate_pr_comment(sample_verification_result)

        assert "## " in comment  # Has header
        assert sample_verification_result.summary.status.value in comment

    @pytest.mark.asyncio
    async def test_generate_sarif(self, sample_verification_result) -> None:
        """Test SARIF report generation."""
        from src.layers.layer3_cot.report_generator import JSONReportGenerator

        generator = JSONReportGenerator()
        sarif = await generator.generate_sarif(sample_verification_result)

        assert "$schema" in sarif
        assert "runs" in sarif
        assert len(sarif["runs"]) == 1
