"""Use case for verifying specification compliance.

This use case orchestrates Layer 3 operations to verify that code
implementations comply with specifications.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Protocol
from uuid import uuid4

if TYPE_CHECKING:
    from src.core.entities.behavioral_model import BehavioralModel
    from src.core.entities.confidence_score import ConfidenceScore
    from src.core.entities.specification import NormalizedSpecification
    from src.core.entities.verification_result import Finding, VerificationResult
    from src.core.interfaces.vector_store import SearchResult


class RAGRetrieverProtocol(Protocol):
    """Protocol for RAG retriever dependency."""

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filter_metadata: dict | None = None,
    ) -> list[SearchResult]: ...


class CoTReasonerProtocol(Protocol):
    """Protocol for Chain-of-Thought reasoner dependency."""

    async def reason(
        self,
        behavioral_model: BehavioralModel,
        specification: NormalizedSpecification,
        context: list[SearchResult],
    ) -> tuple[list[Finding], str]: ...


class ConfidenceCalculatorProtocol(Protocol):
    """Protocol for confidence calculator dependency."""

    def calculate(
        self,
        finding: Finding,
        evidence: list[SearchResult],
    ) -> ConfidenceScore: ...


class ReportGeneratorProtocol(Protocol):
    """Protocol for report generator dependency."""

    async def generate(
        self,
        result: VerificationResult,
        format: str,
    ) -> str: ...


@dataclass
class VerifyComplianceResult:
    """Result from compliance verification.

    Attributes:
        verification_result: The complete verification result
        is_success: Whether verification completed successfully
        error_message: Error message if verification failed
    """

    verification_result: VerificationResult | None
    is_success: bool
    error_message: str | None = None


class VerifyComplianceUseCase:
    """Use case for verifying specification compliance.

    This use case coordinates the Layer 3 pipeline:
    1. Retrieve relevant specification context via RAG
    2. Perform Chain-of-Thought reasoning
    3. Compare requirements with code behavior
    4. Calculate confidence scores
    5. Generate verification results
    """

    def __init__(
        self,
        rag_retriever: RAGRetrieverProtocol,
        cot_reasoner: CoTReasonerProtocol,
        confidence_calculator: ConfidenceCalculatorProtocol,
    ) -> None:
        """Initialize the use case with required dependencies.

        Args:
            rag_retriever: RAG retrieval implementation
            cot_reasoner: Chain-of-Thought reasoning implementation
            confidence_calculator: Confidence calculation implementation
        """
        self._rag_retriever = rag_retriever
        self._cot_reasoner = cot_reasoner
        self._confidence_calculator = confidence_calculator

    async def execute(
        self,
        behavioral_model: BehavioralModel,
        specification: NormalizedSpecification,
        fork: str,
    ) -> VerifyComplianceResult:
        """Execute compliance verification.

        Args:
            behavioral_model: The behavioral model from Layer 1
            specification: The normalized specification from Layer 2
            fork: Target fork version

        Returns:
            VerifyComplianceResult containing the verification result or error
        """
        from src.core.entities.verification_result import (
            ComplianceStatus,
            Finding,
            Metrics,
            VerificationDecision,
            VerificationResult,
            VerificationSummary,
        )

        run_id = f"verify-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}"
        start_time = datetime.utcnow()

        try:
            # Step 1: Retrieve relevant context via RAG
            query = self._build_retrieval_query(behavioral_model, specification)
            context = await self._rag_retriever.retrieve(
                query=query,
                top_k=20,
                filter_metadata={"fork_version": fork},
            )

            # Step 2: Perform Chain-of-Thought reasoning
            findings, raw_cot = await self._cot_reasoner.reason(
                behavioral_model=behavioral_model,
                specification=specification,
                context=context,
            )

            # Step 3: Calculate confidence scores for each finding
            scored_findings: list[Finding] = []
            for finding in findings:
                confidence = self._confidence_calculator.calculate(finding, context)
                # Create new finding with updated confidence
                scored_finding = Finding(
                    finding_id=finding.finding_id,
                    title=finding.title,
                    description=finding.description,
                    severity=finding.severity,
                    category=finding.category,
                    confidence=confidence.score,
                    requirement_id=finding.requirement_id,
                    code_location=finding.code_location,
                    spec_reference=finding.spec_reference,
                    evidence=finding.evidence,
                    recommendation=finding.recommendation,
                )
                scored_findings.append(scored_finding)

            # Step 4: Calculate summary and metrics
            summary = self._calculate_summary(scored_findings, specification)
            end_time = datetime.utcnow()
            metrics = Metrics(
                verification_time_seconds=(end_time - start_time).total_seconds(),
            )

            # Step 5: Determine CI/CD decision
            decision = self._make_decision(scored_findings)

            # Create verification result
            verification_result = VerificationResult(
                run_id=run_id,
                timestamp=start_time,
                fork=fork,
                summary=summary,
                findings=tuple(scored_findings),
                metrics=metrics,
                decision=decision,
                behavioral_models_checked=(behavioral_model.source_file,),
                specifications_used=(specification.spec_id,),
                raw_cot_output=raw_cot,
            )

            return VerifyComplianceResult(
                verification_result=verification_result,
                is_success=True,
            )

        except Exception as e:
            return VerifyComplianceResult(
                verification_result=None,
                is_success=False,
                error_message=f"Verification failed: {e}",
            )

    def _build_retrieval_query(
        self,
        behavioral_model: BehavioralModel,
        specification: NormalizedSpecification,
    ) -> str:
        """Build a query for RAG retrieval.

        Args:
            behavioral_model: The behavioral model
            specification: The specification

        Returns:
            Query string for retrieval
        """
        components = []

        # Include state writes (important for compliance)
        if behavioral_model.data_flow.state_writes:
            components.append(f"State modifications: {', '.join(behavioral_model.data_flow.state_writes)}")

        # Include function calls
        if behavioral_model.data_flow.function_calls:
            components.append(f"Functions: {', '.join(behavioral_model.data_flow.function_calls[:10])}")

        # Include behavioral aspects
        if behavioral_model.precondition:
            components.append(f"Precondition: {behavioral_model.precondition}")
        if behavioral_model.postcondition:
            components.append(f"Postcondition: {behavioral_model.postcondition}")

        return " | ".join(components) if components else "general specification requirements"

    def _calculate_summary(
        self,
        findings: list[Finding],
        specification: NormalizedSpecification,
    ) -> VerificationSummary:
        """Calculate verification summary.

        Args:
            findings: List of findings
            specification: The specification

        Returns:
            VerificationSummary
        """
        from src.core.entities.verification_result import (
            ComplianceStatus,
            FindingSeverity,
            VerificationSummary,
        )

        # Count findings by type
        critical_high = sum(
            1
            for f in findings
            if f.severity in (FindingSeverity.CRITICAL, FindingSeverity.HIGH)
            and not f.is_false_positive
        )
        total_findings = len([f for f in findings if not f.is_false_positive])

        # Calculate overall confidence
        if findings:
            avg_confidence = sum(f.confidence for f in findings) / len(findings)
        else:
            avg_confidence = 1.0

        # Determine status
        if critical_high > 0:
            status = ComplianceStatus.FAIL
            reason = f"{critical_high} critical/high severity findings detected"
        elif total_findings > 5:
            status = ComplianceStatus.PARTIAL
            reason = f"{total_findings} findings require review"
        elif total_findings > 0:
            status = ComplianceStatus.PARTIAL
            reason = f"{total_findings} minor findings detected"
        else:
            status = ComplianceStatus.PASS
            reason = "No compliance issues detected"

        return VerificationSummary(
            status=status,
            confidence=avg_confidence,
            reason=reason,
            total_requirements=specification.total_items,
            passed_requirements=specification.total_items - total_findings,
            failed_requirements=critical_high,
            ambiguous_requirements=total_findings - critical_high,
        )

    def _make_decision(self, findings: list[Finding]) -> VerificationDecision:
        """Make CI/CD decision based on findings.

        Args:
            findings: List of findings

        Returns:
            VerificationDecision
        """
        from src.core.entities.verification_result import (
            FindingSeverity,
            VerificationDecision,
        )

        blocking_findings = [f for f in findings if f.is_blocking]

        if blocking_findings:
            severities = [f.severity.value for f in blocking_findings]
            return VerificationDecision(
                should_fail_ci=True,
                blocking_reason=(
                    f"{len(blocking_findings)} blocking findings: "
                    f"{', '.join(set(severities))} severity issues detected"
                ),
                requires_human_review=True,
            )

        # Check for medium findings that need review
        medium_findings = [
            f
            for f in findings
            if f.severity == FindingSeverity.MEDIUM and not f.is_false_positive
        ]

        if len(medium_findings) > 3:
            return VerificationDecision(
                should_fail_ci=False,
                requires_human_review=True,
            )

        return VerificationDecision(
            should_fail_ci=False,
            requires_human_review=len(findings) > 0,
        )
