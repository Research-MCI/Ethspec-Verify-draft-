"""Behavioral Model Extractor.

This module extracts behavioral models (preconditions, postconditions,
invariants) from analyzed code using LLM reasoning.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.layers.layer1_ast.prompts.ast_generation import get_behavioral_extraction_prompt
from src.shared.logger import LoggerMixin
from src.shared.utils.json_utils import extract_json_from_text

if TYPE_CHECKING:
    from src.core.entities.behavioral_model import ControlFlowGraph, DataFlowInfo
    from src.core.interfaces.llm_provider import LLMProvider


class BehavioralExtractor(LoggerMixin):
    """Extracts behavioral specifications from code analysis.

    Uses LLM reasoning to derive:
    - Preconditions: What must be true before execution
    - Postconditions: What will be true after execution
    - Invariants: What remains constant throughout
    """

    def __init__(self, llm_provider: LLMProvider) -> None:
        """Initialize the behavioral extractor.

        Args:
            llm_provider: LLM provider for reasoning
        """
        self._llm = llm_provider

    async def extract(
        self,
        ast: object,
        cfg: ControlFlowGraph,
        data_flow: DataFlowInfo,
    ) -> tuple[str, str, str]:
        """Extract behavioral specifications.

        Args:
            ast: The AST root node
            cfg: Control Flow Graph
            data_flow: Data flow analysis results

        Returns:
            Tuple of (precondition, postcondition, invariant)
        """
        self.logger.info("extracting_behavioral_model")

        # Generate summaries for the prompt
        ast_summary = self._summarize_ast(ast)
        cfg_summary = self._summarize_cfg(cfg)

        # Build the extraction prompt
        prompt = get_behavioral_extraction_prompt(
            ast_summary=ast_summary,
            cfg_summary=cfg_summary,
            state_reads=list(data_flow.state_reads),
            state_writes=list(data_flow.state_writes),
            constants=[str(c) for c in data_flow.constants],
            function_calls=list(data_flow.function_calls),
        )

        try:
            response = await self._llm.generate(
                prompt=prompt,
                temperature=0.2,
            )

            # Extract JSON from response
            json_results = extract_json_from_text(response.content)

            if json_results:
                result = json_results[0]
                precondition = result.get("precondition", "")
                postcondition = result.get("postcondition", "")
                invariant = result.get("invariant", "")

                self.logger.info(
                    "behavioral_model_extracted",
                    has_precondition=bool(precondition),
                    has_postcondition=bool(postcondition),
                    has_invariant=bool(invariant),
                )

                return precondition, postcondition, invariant

            # Fallback: try to extract from plain text
            return self._extract_from_text(response.content)

        except Exception as e:
            self.logger.error("behavioral_extraction_failed", error=str(e))
            return self._generate_default_behavioral_model(data_flow)

    def _summarize_ast(self, ast: object) -> str:
        """Generate a summary of the AST.

        Args:
            ast: The AST root node

        Returns:
            Summary string
        """
        summary_parts = []

        # Get basic structure info
        if hasattr(ast, "node_type"):
            summary_parts.append(f"Root type: {ast.node_type.value}")

        if hasattr(ast, "children"):
            child_types = [
                c.node_type.value for c in ast.children if hasattr(c, "node_type")
            ]
            if child_types:
                # Count by type
                type_counts: dict[str, int] = {}
                for t in child_types:
                    type_counts[t] = type_counts.get(t, 0) + 1

                summary_parts.append(
                    "Structure: " + ", ".join(f"{v} {k}(s)" for k, v in type_counts.items())
                )

        return "; ".join(summary_parts) if summary_parts else "Module with mixed content"

    def _summarize_cfg(self, cfg: ControlFlowGraph) -> str:
        """Generate a summary of the CFG.

        Args:
            cfg: Control Flow Graph

        Returns:
            Summary string
        """
        node_count = len(cfg.nodes)
        edge_count = len(cfg.edges)

        # Count node types
        type_counts: dict[str, int] = {}
        for node in cfg.nodes:
            type_counts[node.node_type] = type_counts.get(node.node_type, 0) + 1

        # Identify key control structures
        has_loops = any(
            n.node_type in ("loop_header", "loop_body") for n in cfg.nodes
        )
        has_conditions = any(n.node_type == "condition" for n in cfg.nodes)
        has_exceptions = any(
            n.node_type in ("try", "except") for n in cfg.nodes
        )

        parts = [
            f"{node_count} nodes, {edge_count} edges",
        ]

        if has_loops:
            parts.append("contains loops")
        if has_conditions:
            parts.append("contains conditionals")
        if has_exceptions:
            parts.append("has exception handling")

        return "; ".join(parts)

    def _extract_from_text(self, text: str) -> tuple[str, str, str]:
        """Extract behavioral info from plain text response.

        Args:
            text: Response text

        Returns:
            Tuple of (precondition, postcondition, invariant)
        """
        precondition = ""
        postcondition = ""
        invariant = ""

        lines = text.lower().split("\n")

        for i, line in enumerate(lines):
            if "precondition" in line:
                # Get content after colon or next line
                if ":" in line:
                    precondition = line.split(":", 1)[1].strip()
                elif i + 1 < len(lines):
                    precondition = lines[i + 1].strip()
            elif "postcondition" in line:
                if ":" in line:
                    postcondition = line.split(":", 1)[1].strip()
                elif i + 1 < len(lines):
                    postcondition = lines[i + 1].strip()
            elif "invariant" in line:
                if ":" in line:
                    invariant = line.split(":", 1)[1].strip()
                elif i + 1 < len(lines):
                    invariant = lines[i + 1].strip()

        return precondition, postcondition, invariant

    def _generate_default_behavioral_model(
        self,
        data_flow: DataFlowInfo,
    ) -> tuple[str, str, str]:
        """Generate default behavioral model from data flow.

        Args:
            data_flow: Data flow analysis results

        Returns:
            Tuple of (precondition, postcondition, invariant)
        """
        # Precondition based on imports and reads
        preconditions = []
        if data_flow.imports:
            preconditions.append(f"Modules available: {', '.join(data_flow.imports[:5])}")
        if data_flow.state_reads:
            preconditions.append(f"Variables defined: {', '.join(list(data_flow.state_reads)[:5])}")

        # Postcondition based on writes
        postconditions = []
        if data_flow.state_writes:
            postconditions.append(f"State modified: {', '.join(list(data_flow.state_writes)[:5])}")

        # Invariant based on constants
        invariants = []
        if data_flow.constants:
            const_strs = [str(c) for c in data_flow.constants[:3]]
            invariants.append(f"Constants: {', '.join(const_strs)}")

        return (
            "; ".join(preconditions) if preconditions else "No specific preconditions identified",
            "; ".join(postconditions) if postconditions else "No state modifications identified",
            "; ".join(invariants) if invariants else "No invariants identified",
        )


class RuleBasedBehavioralExtractor:
    """Rule-based behavioral extractor for simpler cases.

    Provides extraction without LLM calls for basic patterns.
    """

    def extract(
        self,
        data_flow: DataFlowInfo,
    ) -> tuple[str, str, str]:
        """Extract behavioral model using rules.

        Args:
            data_flow: Data flow analysis results

        Returns:
            Tuple of (precondition, postcondition, invariant)
        """
        # Preconditions from reads
        preconditions = []
        for var in data_flow.state_reads:
            if var.isupper():
                preconditions.append(f"Constant {var} must be defined")

        # Postconditions from writes
        postconditions = []
        for var in data_flow.state_writes:
            postconditions.append(f"Variable {var} is assigned")

        # Invariants from constants
        invariants = []
        for const in data_flow.constants:
            invariants.append(f"Value {const} remains constant")

        return (
            "; ".join(preconditions) if preconditions else "Module loaded successfully",
            "; ".join(postconditions) if postconditions else "Execution completes",
            "; ".join(invariants) if invariants else "No state invariants",
        )
