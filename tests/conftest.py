"""Pytest configuration and fixtures."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from src.core.entities.behavioral_model import (
    ASTNode,
    BehavioralModel,
    CFGEdge,
    CFGNode,
    ControlFlowGraph,
    DataFlowInfo,
    NodeType,
)
from src.core.entities.specification import (
    Constraint,
    Invariant,
    NormalizedSpecification,
    Requirement,
    SpecCategory,
    SpecificationChunk,
    SpecificationDocument,
    SpecificationMetadata,
)
from src.core.entities.verification_result import (
    ComplianceStatus,
    Finding,
    FindingCategory,
    FindingSeverity,
    Metrics,
    VerificationDecision,
    VerificationResult,
    VerificationSummary,
)


@pytest.fixture
def sample_source_code() -> str:
    """Sample Python source code for testing."""
    return '''"""Fork criteria module for Ethereum."""

FORK_CRITERIA = 12244000
MAX_BLOCK_SIZE = 1048576

def apply_fork(state, block_number):
    """Apply fork rules to the state."""
    if block_number >= FORK_CRITERIA:
        return apply_new_rules(state)
    return state

def validate_block(block):
    """Validate a block against fork rules."""
    if len(block.data) > MAX_BLOCK_SIZE:
        raise ValueError("Block too large")
    return True
'''


@pytest.fixture
def sample_ast_json() -> dict[str, Any]:
    """Sample AST JSON structure."""
    return {
        "type": "module",
        "children": [
            {
                "type": "assignment",
                "name": "FORK_CRITERIA",
                "value": 12244000,
                "line": 3,
            },
            {
                "type": "assignment",
                "name": "MAX_BLOCK_SIZE",
                "value": 1048576,
                "line": 4,
            },
            {
                "type": "function",
                "name": "apply_fork",
                "line": 6,
                "children": [
                    {
                        "type": "if",
                        "children": [
                            {"type": "compare"},
                            {"type": "return", "children": [{"type": "call", "name": "apply_new_rules"}]},
                        ],
                    },
                    {"type": "return", "children": [{"type": "name", "name": "state"}]},
                ],
            },
            {
                "type": "function",
                "name": "validate_block",
                "line": 12,
                "children": [
                    {
                        "type": "if",
                        "children": [
                            {"type": "compare"},
                            {"type": "raise"},
                        ],
                    },
                    {"type": "return", "children": [{"type": "constant", "value": True}]},
                ],
            },
        ],
    }


@pytest.fixture
def sample_ast_node() -> ASTNode:
    """Sample ASTNode instance."""
    return ASTNode(
        node_type=NodeType.MODULE,
        children=(
            ASTNode(
                node_type=NodeType.ASSIGNMENT,
                name="FORK_CRITERIA",
                value=12244000,
                line_number=3,
            ),
            ASTNode(
                node_type=NodeType.FUNCTION,
                name="apply_fork",
                line_number=6,
                children=(
                    ASTNode(node_type=NodeType.IF),
                    ASTNode(node_type=NodeType.RETURN),
                ),
            ),
        ),
    )


@pytest.fixture
def sample_cfg() -> ControlFlowGraph:
    """Sample Control Flow Graph."""
    nodes = (
        CFGNode(node_id="n1", node_type="entry", label="Entry", is_entry=True),
        CFGNode(node_id="n2", node_type="condition", label="if condition"),
        CFGNode(node_id="n3", node_type="block", label="then"),
        CFGNode(node_id="n4", node_type="block", label="else"),
        CFGNode(node_id="n5", node_type="exit", label="Exit", is_exit=True),
    )
    edges = (
        CFGEdge(source="n1", target="n2"),
        CFGEdge(source="n2", target="n3", condition="True", edge_type="true_branch"),
        CFGEdge(source="n2", target="n4", condition="False", edge_type="false_branch"),
        CFGEdge(source="n3", target="n5"),
        CFGEdge(source="n4", target="n5"),
    )
    return ControlFlowGraph(
        nodes=nodes,
        edges=edges,
        entry_node="n1",
        exit_nodes=("n5",),
    )


@pytest.fixture
def sample_data_flow() -> DataFlowInfo:
    """Sample DataFlowInfo."""
    return DataFlowInfo(
        state_reads=("state", "block_number"),
        state_writes=("FORK_CRITERIA", "MAX_BLOCK_SIZE"),
        constants=(12244000, 1048576),
        imports=(),
        function_calls=("apply_new_rules", "len"),
        type_definitions=(),
        global_refs=("FORK_CRITERIA", "MAX_BLOCK_SIZE"),
    )


@pytest.fixture
def sample_behavioral_model(
    sample_ast_node: ASTNode,
    sample_cfg: ControlFlowGraph,
    sample_data_flow: DataFlowInfo,
) -> BehavioralModel:
    """Sample BehavioralModel."""
    return BehavioralModel(
        source_file="test/fork.py",
        ast=sample_ast_node,
        sbt="(module (assignment [FORK_CRITERIA] )assignment (function [apply_fork] )function )module",
        cfg=sample_cfg,
        data_flow=sample_data_flow,
        precondition="Module loaded, state object available",
        postcondition="Fork rules applied if criteria met",
        invariant="FORK_CRITERIA value remains constant",
        semantic_score=0.75,
        raw_source="...",
    )


@pytest.fixture
def sample_spec_metadata() -> SpecificationMetadata:
    """Sample SpecificationMetadata."""
    return SpecificationMetadata(
        source_repo="ethereum/execution-specs",
        fork_version="cancun",
        category=SpecCategory.FORK,
        file_path="src/ethereum/cancun/fork.py",
        commit_hash="abc123",
    )


@pytest.fixture
def sample_spec_chunks(sample_spec_metadata: SpecificationMetadata) -> list[SpecificationChunk]:
    """Sample specification chunks."""
    return [
        SpecificationChunk(
            chunk_id="chunk-001",
            content="The fork criteria must be defined by a specific block number.",
            metadata=sample_spec_metadata,
        ),
        SpecificationChunk(
            chunk_id="chunk-002",
            content="Once a fork activation block is set, it must not be modified.",
            metadata=sample_spec_metadata,
        ),
    ]


@pytest.fixture
def sample_normalized_spec() -> NormalizedSpecification:
    """Sample NormalizedSpecification."""
    return NormalizedSpecification(
        spec_id="spec-001",
        fork_version="cancun",
        requirements=(
            Requirement(
                req_id="REQ-001",
                description="The fork criteria must be defined by a specific block number.",
                source_chunk="chunk-001",
                category=SpecCategory.FORK,
            ),
            Requirement(
                req_id="REQ-002",
                description="Block validation must check size limits.",
                source_chunk="chunk-002",
                category=SpecCategory.BLOCK,
            ),
        ),
        constraints=(
            Constraint(
                constraint_id="CON-001",
                description="Maximum block size is 1048576 bytes.",
                source_chunk="chunk-002",
            ),
        ),
        invariants=(
            Invariant(
                invariant_id="INV-001",
                description="Fork criteria value must not change after initialization.",
                source_chunk="chunk-001",
            ),
        ),
    )


@pytest.fixture
def sample_finding() -> Finding:
    """Sample Finding."""
    return Finding(
        finding_id="FIND-001",
        title="Fork criteria constant defined",
        description="The FORK_CRITERIA constant is correctly defined with block number 12244000.",
        severity=FindingSeverity.INFO,
        category=FindingCategory.OTHER,
        confidence=0.85,
        requirement_id="REQ-001",
        code_location="test/fork.py:3",
        evidence=("Constant FORK_CRITERIA = 12244000 found",),
    )


@pytest.fixture
def sample_verification_result(sample_finding: Finding) -> VerificationResult:
    """Sample VerificationResult."""
    from datetime import datetime

    return VerificationResult(
        run_id="test-run-001",
        timestamp=datetime(2026, 1, 23, 19, 10, 4),
        fork="cancun",
        summary=VerificationSummary(
            status=ComplianceStatus.PASS,
            confidence=0.85,
            reason="No compliance issues detected",
            total_requirements=2,
            passed_requirements=2,
        ),
        findings=(sample_finding,),
        metrics=Metrics(
            verification_time_seconds=1.5,
            llm_calls=3,
            tokens_used=1500,
        ),
        decision=VerificationDecision(
            should_fail_ci=False,
            requires_human_review=False,
        ),
    )
