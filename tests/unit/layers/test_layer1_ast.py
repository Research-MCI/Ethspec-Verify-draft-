"""Unit tests for Layer 1: AST-Based Code Analysis."""

from __future__ import annotations

from typing import Any

import pytest

from src.core.entities.behavioral_model import ASTNode, NodeType
from src.layers.layer1_ast.cfg_generator import CFGGenerator
from src.layers.layer1_ast.data_flow_analyzer import DataFlowAnalyzer
from src.layers.layer1_ast.json_validator import ASTJSONValidator
from src.layers.layer1_ast.sbt_transformer import CompactSBTTransformer, SBTTransformer
from src.layers.layer1_ast.semantic_scorer import SemanticScorer


class TestASTJSONValidator:
    """Tests for ASTJSONValidator."""

    def test_validate_valid_ast(self, sample_ast_json: dict[str, Any]) -> None:
        """Test validation of valid AST JSON."""
        validator = ASTJSONValidator()
        is_valid, errors = validator.validate(sample_ast_json)

        assert is_valid
        assert len(errors) == 0

    def test_validate_missing_type(self) -> None:
        """Test validation fails without type field."""
        validator = ASTJSONValidator()
        invalid_ast = {"name": "test", "children": []}

        is_valid, errors = validator.validate(invalid_ast)

        assert not is_valid
        assert any("type" in e.lower() for e in errors)

    def test_validate_invalid_children(self) -> None:
        """Test validation fails with non-array children."""
        validator = ASTJSONValidator()
        invalid_ast = {"type": "module", "children": "not an array"}

        is_valid, errors = validator.validate(invalid_ast)

        assert not is_valid
        assert any("children" in e.lower() for e in errors)

    def test_validate_empty_ast(self) -> None:
        """Test validation of empty AST."""
        validator = ASTJSONValidator()
        empty_ast = {"type": "module", "children": []}

        is_valid, errors = validator.validate(empty_ast)

        assert is_valid  # Structure is valid

        # But completeness check should warn
        is_complete, warnings = validator.validate_structure_completeness(empty_ast)
        assert not is_complete
        assert len(warnings) > 0

    def test_extract_statistics(self, sample_ast_json: dict[str, Any]) -> None:
        """Test statistics extraction."""
        validator = ASTJSONValidator()
        stats = validator.extract_statistics(sample_ast_json)

        assert stats["total_nodes"] > 0
        assert stats["functions"] == 2
        assert stats["assignments"] == 2


class TestSemanticScorer:
    """Tests for SemanticScorer."""

    def test_score_complete_ast(self, sample_ast_json: dict[str, Any]) -> None:
        """Test scoring of complete AST."""
        scorer = SemanticScorer()
        score = scorer.calculate_score(sample_ast_json)

        assert 0.0 <= score <= 1.0
        assert score >= 0.3  # Should be acceptable

    def test_score_empty_ast(self) -> None:
        """Test scoring of empty AST."""
        scorer = SemanticScorer()
        empty_ast = {"type": "module", "children": []}

        score = scorer.calculate_score(empty_ast)

        assert score < 0.3  # Should be poor

    def test_score_breakdown(self, sample_ast_json: dict[str, Any]) -> None:
        """Test detailed score breakdown."""
        scorer = SemanticScorer()
        breakdown = scorer.calculate_score_breakdown(sample_ast_json)

        assert breakdown.assignment_score > 0
        assert breakdown.function_score > 0
        assert breakdown.total_score == scorer.calculate_score(sample_ast_json)

    def test_quality_rating(self) -> None:
        """Test quality rating conversion."""
        scorer = SemanticScorer()

        assert scorer.get_quality_rating(0.9) == "excellent"
        assert scorer.get_quality_rating(0.7) == "good"
        assert scorer.get_quality_rating(0.5) == "acceptable"
        assert scorer.get_quality_rating(0.35) == "marginal"
        assert scorer.get_quality_rating(0.2) == "poor"


class TestSBTTransformer:
    """Tests for SBTTransformer."""

    def test_transform_simple_ast(self, sample_ast_node: ASTNode) -> None:
        """Test SBT transformation of simple AST."""
        transformer = SBTTransformer()
        sbt = transformer.transform(sample_ast_node)

        assert isinstance(sbt, str)
        assert "(module" in sbt
        assert ")module" in sbt
        assert "[FORK_CRITERIA]" in sbt

    def test_transform_to_tokens(self, sample_ast_node: ASTNode) -> None:
        """Test transformation to token list."""
        transformer = SBTTransformer()
        tokens = transformer.transform_to_tokens(sample_ast_node)

        assert isinstance(tokens, list)
        assert len(tokens) > 0
        assert tokens[0] == "(module"
        assert tokens[-1] == ")module"

    def test_compact_transformer(self, sample_ast_node: ASTNode) -> None:
        """Test compact SBT transformation."""
        compact = CompactSBTTransformer()
        standard = SBTTransformer()

        compact_sbt = compact.transform(sample_ast_node)
        standard_sbt = standard.transform(sample_ast_node)

        # Compact should be shorter
        assert len(compact_sbt) <= len(standard_sbt)
        # Should use abbreviations
        assert "(M" in compact_sbt or "(F" in compact_sbt


class TestCFGGenerator:
    """Tests for CFGGenerator."""

    def test_generate_simple_cfg(self, sample_ast_node: ASTNode) -> None:
        """Test CFG generation from simple AST."""
        generator = CFGGenerator()
        cfg = generator.generate(sample_ast_node)

        assert len(cfg.nodes) > 0
        assert len(cfg.edges) > 0
        assert cfg.entry_node is not None
        assert len(cfg.exit_nodes) > 0

    def test_cfg_has_entry_and_exit(self, sample_ast_node: ASTNode) -> None:
        """Test that CFG has proper entry and exit nodes."""
        generator = CFGGenerator()
        cfg = generator.generate(sample_ast_node)

        entry_nodes = [n for n in cfg.nodes if n.is_entry]
        exit_nodes = [n for n in cfg.nodes if n.is_exit]

        assert len(entry_nodes) == 1
        assert len(exit_nodes) >= 1

    def test_cfg_to_dict(self, sample_ast_node: ASTNode) -> None:
        """Test CFG dictionary conversion."""
        generator = CFGGenerator()
        cfg = generator.generate(sample_ast_node)
        cfg_dict = cfg.to_dict()

        assert "nodes" in cfg_dict
        assert "edges" in cfg_dict
        assert "entry" in cfg_dict
        assert "exits" in cfg_dict


class TestDataFlowAnalyzer:
    """Tests for DataFlowAnalyzer."""

    def test_analyze_constants(self, sample_ast_node: ASTNode) -> None:
        """Test constant detection."""
        analyzer = DataFlowAnalyzer()
        data_flow = analyzer.analyze(sample_ast_node)

        # Should detect the constant assignment
        assert "FORK_CRITERIA" in data_flow.state_writes

    def test_analyze_function_calls(self) -> None:
        """Test function call detection."""
        ast = ASTNode(
            node_type=NodeType.MODULE,
            children=(
                ASTNode(
                    node_type=NodeType.CALL,
                    name="apply_rules",
                ),
            ),
        )

        analyzer = DataFlowAnalyzer()
        data_flow = analyzer.analyze(ast)

        assert "apply_rules" in data_flow.function_calls

    def test_data_flow_to_dict(self, sample_data_flow) -> None:
        """Test DataFlowInfo dictionary conversion."""
        data_dict = sample_data_flow.to_dict()

        assert "state_reads" in data_dict
        assert "state_writes" in data_dict
        assert "constants" in data_dict
        assert isinstance(data_dict["constants"], list)
