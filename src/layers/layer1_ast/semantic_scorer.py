"""Semantic scoring for AST quality assessment.

This module provides scoring functions to evaluate the quality
and completeness of LLM-generated AST representations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SemanticScoreBreakdown:
    """Breakdown of semantic score components.

    Attributes:
        import_score: Score for import statements
        assignment_score: Score for assignments/constants
        type_score: Score for type definitions
        function_score: Score for function definitions
        control_flow_score: Score for control flow structures
        total_score: Overall score
    """

    import_score: float
    assignment_score: float
    type_score: float
    function_score: float
    control_flow_score: float
    total_score: float


class SemanticScorer:
    """Scores AST semantic quality based on content analysis.

    The semantic score evaluates how well the AST captures the
    meaningful structure of the source code.
    """

    # Weights for different components
    WEIGHTS = {
        "imports": 0.15,
        "assignments": 0.25,
        "types": 0.15,
        "functions": 0.25,
        "control_flow": 0.20,
    }

    # Thresholds for scoring
    THRESHOLDS = {
        "imports": {"min": 1, "good": 3},
        "assignments": {"min": 1, "good": 5},
        "types": {"min": 0, "good": 2},
        "functions": {"min": 1, "good": 3},
        "control_flow": {"min": 0, "good": 2},
    }

    def calculate_score(self, ast_json: dict[str, Any]) -> float:
        """Calculate the semantic score for an AST.

        Args:
            ast_json: The AST JSON to score

        Returns:
            Semantic score between 0.0 and 1.0
        """
        breakdown = self.calculate_score_breakdown(ast_json)
        return breakdown.total_score

    def calculate_score_breakdown(
        self,
        ast_json: dict[str, Any],
    ) -> SemanticScoreBreakdown:
        """Calculate detailed semantic score breakdown.

        Args:
            ast_json: The AST JSON to score

        Returns:
            SemanticScoreBreakdown with component scores
        """
        # Collect elements from AST
        elements = self._collect_elements(ast_json)

        # Calculate individual scores
        import_score = self._score_component(
            len(elements["imports"]),
            self.THRESHOLDS["imports"],
        )
        assignment_score = self._score_component(
            len(elements["assignments"]) + len(elements["constants"]),
            self.THRESHOLDS["assignments"],
        )
        type_score = self._score_component(
            len(elements["types"]),
            self.THRESHOLDS["types"],
        )
        function_score = self._score_component(
            len(elements["functions"]) + len(elements["classes"]),
            self.THRESHOLDS["functions"],
        )
        control_flow_score = self._score_component(
            len(elements["control_flow"]),
            self.THRESHOLDS["control_flow"],
        )

        # Calculate weighted total
        total_score = (
            import_score * self.WEIGHTS["imports"]
            + assignment_score * self.WEIGHTS["assignments"]
            + type_score * self.WEIGHTS["types"]
            + function_score * self.WEIGHTS["functions"]
            + control_flow_score * self.WEIGHTS["control_flow"]
        )

        return SemanticScoreBreakdown(
            import_score=import_score,
            assignment_score=assignment_score,
            type_score=type_score,
            function_score=function_score,
            control_flow_score=control_flow_score,
            total_score=total_score,
        )

    def _score_component(
        self,
        count: int,
        thresholds: dict[str, int],
    ) -> float:
        """Score a component based on count and thresholds.

        Args:
            count: Number of elements found
            thresholds: Dict with 'min' and 'good' threshold values

        Returns:
            Score between 0.0 and 1.0
        """
        if count == 0:
            return 0.0
        elif count < thresholds["min"]:
            return 0.3
        elif count < thresholds["good"]:
            # Linear interpolation between min and good
            progress = (count - thresholds["min"]) / (
                thresholds["good"] - thresholds["min"]
            )
            return 0.3 + 0.5 * progress
        else:
            # Above good threshold
            return min(1.0, 0.8 + 0.2 * (count / (thresholds["good"] * 2)))

    def _collect_elements(self, ast_json: dict[str, Any]) -> dict[str, list[Any]]:
        """Collect categorized elements from the AST.

        Args:
            ast_json: The AST JSON

        Returns:
            Dictionary of element lists by category
        """
        elements: dict[str, list[Any]] = {
            "imports": [],
            "assignments": [],
            "constants": [],
            "types": [],
            "functions": [],
            "classes": [],
            "control_flow": [],
        }

        self._traverse_and_collect(ast_json, elements)
        return elements

    def _traverse_and_collect(
        self,
        node: dict[str, Any],
        elements: dict[str, list[Any]],
    ) -> None:
        """Recursively traverse and collect elements.

        Args:
            node: The current node
            elements: Dictionary to accumulate elements
        """
        node_type = node.get("type", "")

        # Categorize by type
        if node_type == "import":
            elements["imports"].append(node)
        elif node_type == "assignment":
            elements["assignments"].append(node)
            # Check if it's a constant (uppercase name)
            name = node.get("name", "")
            if name and name.isupper():
                elements["constants"].append(node)
        elif node_type == "constant":
            elements["constants"].append(node)
        elif node_type == "function":
            elements["functions"].append(node)
        elif node_type == "class":
            elements["classes"].append(node)
        elif node_type in ("if", "for", "while", "try", "with"):
            elements["control_flow"].append(node)

        # Check for type annotations in metadata
        metadata = node.get("metadata", {})
        if metadata.get("type_annotation") or metadata.get("return_type"):
            elements["types"].append(node)

        # Traverse children
        for child in node.get("children", []):
            if isinstance(child, dict):
                self._traverse_and_collect(child, elements)

    def is_acceptable(
        self,
        score: float,
        threshold: float = 0.3,
    ) -> bool:
        """Check if a score is acceptable.

        Args:
            score: The semantic score
            threshold: Minimum acceptable score

        Returns:
            True if score meets threshold
        """
        return score >= threshold

    def get_quality_rating(self, score: float) -> str:
        """Get a human-readable quality rating.

        Args:
            score: The semantic score

        Returns:
            Quality rating string
        """
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "acceptable"
        elif score >= 0.3:
            return "marginal"
        else:
            return "poor"
