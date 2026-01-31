"""Verification result entity representing compliance check outcomes.

This module defines the data structures for verification results, findings,
and the final compliance decision output from Layer 3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ComplianceStatus(str, Enum):
    """Overall compliance status."""

    PASS = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"
    PENDING = "PENDING"


class FindingSeverity(str, Enum):
    """Severity level of a finding."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingCategory(str, Enum):
    """Category of finding."""

    SPECIFICATION_DRIFT = "specification_drift"
    MISSING_IMPLEMENTATION = "missing_implementation"
    INCORRECT_BEHAVIOR = "incorrect_behavior"
    CONSTRAINT_VIOLATION = "constraint_violation"
    INVARIANT_VIOLATION = "invariant_violation"
    EDGE_CASE_UNHANDLED = "edge_case_unhandled"
    TYPE_MISMATCH = "type_mismatch"
    STATE_INCONSISTENCY = "state_inconsistency"
    AMBIGUOUS = "ambiguous"
    OTHER = "other"


@dataclass(frozen=True)
class Finding:
    """Represents a single compliance finding.

    Attributes:
        finding_id: Unique finding identifier
        title: Short title describing the finding
        description: Detailed description of the finding
        severity: Severity level
        category: Finding category
        confidence: Confidence score (0.0 to 1.0)
        requirement_id: Related requirement ID
        code_location: Location in the code (file:line)
        spec_reference: Reference to specification
        evidence: Supporting evidence
        recommendation: Suggested fix or action
        is_false_positive: Whether marked as false positive
    """

    finding_id: str
    title: str
    description: str
    severity: FindingSeverity
    category: FindingCategory
    confidence: float
    requirement_id: str | None = None
    code_location: str | None = None
    spec_reference: str | None = None
    evidence: tuple[str, ...] = field(default_factory=tuple)
    recommendation: str | None = None
    is_false_positive: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert finding to dictionary representation."""
        return {
            "finding_id": self.finding_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "category": self.category.value,
            "confidence": self.confidence,
            "requirement_id": self.requirement_id,
            "code_location": self.code_location,
            "spec_reference": self.spec_reference,
            "evidence": list(self.evidence),
            "recommendation": self.recommendation,
            "is_false_positive": self.is_false_positive,
        }

    @property
    def is_blocking(self) -> bool:
        """Check if this finding should block CI/CD."""
        return (
            self.severity in (FindingSeverity.CRITICAL, FindingSeverity.HIGH)
            and self.confidence >= 0.7
            and not self.is_false_positive
        )


@dataclass(frozen=True)
class VerificationSummary:
    """Summary of verification results.

    Attributes:
        status: Overall compliance status
        confidence: Overall confidence score
        reason: Brief explanation of the status
        total_requirements: Total requirements checked
        passed_requirements: Requirements that passed
        failed_requirements: Requirements that failed
        ambiguous_requirements: Requirements with ambiguous results
    """

    status: ComplianceStatus
    confidence: float
    reason: str
    total_requirements: int = 0
    passed_requirements: int = 0
    failed_requirements: int = 0
    ambiguous_requirements: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert summary to dictionary representation."""
        return {
            "status": self.status.value,
            "confidence": self.confidence,
            "reason": self.reason,
            "total_requirements": self.total_requirements,
            "passed_requirements": self.passed_requirements,
            "failed_requirements": self.failed_requirements,
            "ambiguous_requirements": self.ambiguous_requirements,
        }


@dataclass(frozen=True)
class Metrics:
    """Verification metrics.

    Attributes:
        structural_completeness_score: Layer 1 SCS metric
        mean_reciprocal_rank: Layer 2 MRR metric
        expected_calibration_error: Layer 3 ECE metric
        verification_time_seconds: Total verification time
        llm_calls: Number of LLM API calls made
        tokens_used: Total tokens consumed
    """

    structural_completeness_score: float = 0.0
    mean_reciprocal_rank: float = 0.0
    expected_calibration_error: float = 0.0
    verification_time_seconds: float = 0.0
    llm_calls: int = 0
    tokens_used: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary representation."""
        return {
            "structural_completeness_score": self.structural_completeness_score,
            "mean_reciprocal_rank": self.mean_reciprocal_rank,
            "expected_calibration_error": self.expected_calibration_error,
            "verification_time_seconds": self.verification_time_seconds,
            "llm_calls": self.llm_calls,
            "tokens_used": self.tokens_used,
        }


@dataclass(frozen=True)
class VerificationDecision:
    """Final CI/CD decision based on verification results.

    Attributes:
        should_fail_ci: Whether CI/CD should fail
        blocking_reason: Reason for blocking (if applicable)
        requires_human_review: Whether human review is needed
        suggested_reviewers: Suggested reviewers for the PR
    """

    should_fail_ci: bool
    blocking_reason: str | None = None
    requires_human_review: bool = True
    suggested_reviewers: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Convert decision to dictionary representation."""
        return {
            "should_fail_ci": self.should_fail_ci,
            "blocking_reason": self.blocking_reason,
            "requires_human_review": self.requires_human_review,
            "suggested_reviewers": list(self.suggested_reviewers),
        }


@dataclass(frozen=True)
class VerificationResult:
    """Complete verification result from Layer 3.

    This is the final output of the verification pipeline, containing
    all findings, metrics, and the CI/CD decision.

    Attributes:
        run_id: Unique run identifier
        timestamp: Verification timestamp
        fork: Target fork version
        summary: Verification summary
        findings: List of findings
        metrics: Verification metrics
        decision: CI/CD decision
        behavioral_models_checked: IDs of behavioral models checked
        specifications_used: IDs of specifications used
        raw_cot_output: Raw Chain-of-Thought reasoning (for debugging)
    """

    run_id: str
    timestamp: datetime
    fork: str
    summary: VerificationSummary
    findings: tuple[Finding, ...]
    metrics: Metrics
    decision: VerificationDecision
    behavioral_models_checked: tuple[str, ...] = field(default_factory=tuple)
    specifications_used: tuple[str, ...] = field(default_factory=tuple)
    raw_cot_output: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert verification result to dictionary representation."""
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
            "fork": self.fork,
            "summary": self.summary.to_dict(),
            "findings": [f.to_dict() for f in self.findings],
            "metrics": self.metrics.to_dict(),
            "decision": self.decision.to_dict(),
            "behavioral_models_checked": list(self.behavioral_models_checked),
            "specifications_used": list(self.specifications_used),
        }

    @property
    def has_critical_findings(self) -> bool:
        """Check if there are any critical findings."""
        return any(
            f.severity == FindingSeverity.CRITICAL and not f.is_false_positive
            for f in self.findings
        )

    @property
    def blocking_findings(self) -> tuple[Finding, ...]:
        """Get all findings that would block CI/CD."""
        return tuple(f for f in self.findings if f.is_blocking)

    @classmethod
    def create_empty(cls, run_id: str, fork: str) -> VerificationResult:
        """Create an empty verification result."""
        return cls(
            run_id=run_id,
            timestamp=datetime.utcnow(),
            fork=fork,
            summary=VerificationSummary(
                status=ComplianceStatus.UNKNOWN,
                confidence=0.0,
                reason="Verification not yet performed",
            ),
            findings=tuple(),
            metrics=Metrics(),
            decision=VerificationDecision(
                should_fail_ci=False,
                requires_human_review=True,
            ),
        )
