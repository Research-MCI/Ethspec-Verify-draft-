"""Core domain entities representing the main business objects."""

from src.core.entities.behavioral_model import (
    ASTNode,
    BehavioralModel,
    CFGEdge,
    CFGNode,
    ControlFlowGraph,
    DataFlowInfo,
)
from src.core.entities.confidence_score import (
    ConfidenceBreakdown,
    ConfidenceScore,
    EvidenceItem,
    EvidenceType,
)
from src.core.entities.specification import (
    Constraint,
    EdgeCase,
    Invariant,
    NormalizedSpecification,
    Requirement,
    SpecificationChunk,
    SpecificationDocument,
    SpecificationMetadata,
    TraceabilityHint,
)
from src.core.entities.verification_result import (
    ComplianceStatus,
    Finding,
    FindingSeverity,
    Metrics,
    VerificationDecision,
    VerificationResult,
    VerificationSummary,
)

__all__ = [
    # Behavioral Model
    "ASTNode",
    "BehavioralModel",
    "CFGEdge",
    "CFGNode",
    "ControlFlowGraph",
    "DataFlowInfo",
    # Confidence Score
    "ConfidenceBreakdown",
    "ConfidenceScore",
    "EvidenceItem",
    "EvidenceType",
    # Specification
    "Constraint",
    "EdgeCase",
    "Invariant",
    "NormalizedSpecification",
    "Requirement",
    "SpecificationChunk",
    "SpecificationDocument",
    "SpecificationMetadata",
    "TraceabilityHint",
    # Verification Result
    "ComplianceStatus",
    "Finding",
    "FindingSeverity",
    "Metrics",
    "VerificationDecision",
    "VerificationResult",
    "VerificationSummary",
]
