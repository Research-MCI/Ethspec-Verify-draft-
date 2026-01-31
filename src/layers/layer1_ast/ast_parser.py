"""LLM-based AST parser implementation.

This module implements the AST parser interface using LLM-based
AST induction from source code.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.core.entities.behavioral_model import ASTNode, NodeType
from src.core.exceptions import ASTGenerationError, JSONParsingError, ParsingError
from src.core.interfaces.ast_parser import ASTParser, ASTParserResult
from src.layers.layer1_ast.json_validator import ASTJSONValidator
from src.layers.layer1_ast.prompts.ast_generation import get_ast_generation_prompt
from src.layers.layer1_ast.semantic_scorer import SemanticScorer
from src.shared.logger import LoggerMixin
from src.shared.utils.json_utils import extract_json_from_text

if TYPE_CHECKING:
    from src.core.interfaces.llm_provider import LLMProvider


class LLMASTParser(ASTParser, LoggerMixin):
    """LLM-based AST parser implementation.

    Uses an LLM to generate AST representations from source code,
    then validates and scores the output.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        validator: ASTJSONValidator | None = None,
        scorer: SemanticScorer | None = None,
        max_retries: int = 3,
    ) -> None:
        """Initialize the AST parser.

        Args:
            llm_provider: LLM provider for AST generation
            validator: Optional custom validator
            scorer: Optional custom scorer
            max_retries: Maximum LLM call retries
        """
        self._llm = llm_provider
        self._validator = validator or ASTJSONValidator()
        self._scorer = scorer or SemanticScorer()
        self._max_retries = max_retries

    async def parse(self, source_code: str, language: str = "python") -> ASTParserResult:
        """Parse source code and return AST result.

        Args:
            source_code: The source code to parse
            language: Programming language of the source code

        Returns:
            ASTParserResult containing the parsed AST and metadata
        """
        if not source_code or not source_code.strip():
            return ASTParserResult(
                ast=None,
                raw_json={},
                semantic_score=0.0,
                is_valid=False,
                validation_errors=("Empty source code",),
            )

        self.logger.info(
            "parsing_source_code",
            language=language,
            source_length=len(source_code),
        )

        # Generate AST using LLM
        prompt = get_ast_generation_prompt(source_code, language)

        best_result: ASTParserResult | None = None
        best_score = 0.0

        for attempt in range(self._max_retries):
            try:
                response = await self._llm.generate(
                    prompt=prompt,
                    temperature=0.1 + (attempt * 0.1),  # Increase temperature on retry
                )

                # Extract JSON candidates from response
                json_candidates = extract_json_from_text(response.content)

                if not json_candidates:
                    self.logger.warning(
                        "no_json_found",
                        attempt=attempt + 1,
                        response_preview=response.content[:200],
                    )
                    continue

                # Evaluate each candidate
                for candidate in json_candidates:
                    result = self._evaluate_candidate(candidate)

                    if result.is_valid and result.semantic_score > best_score:
                        best_score = result.semantic_score
                        best_result = result

                        self.logger.info(
                            "candidate_accepted",
                            score=result.semantic_score,
                            attempt=attempt + 1,
                        )

                # If we found a good result, stop retrying
                if best_result and best_score >= 0.5:
                    break

            except Exception as e:
                self.logger.error(
                    "llm_generation_failed",
                    attempt=attempt + 1,
                    error=str(e),
                )

        if best_result:
            return best_result

        # Return failure result
        return ASTParserResult(
            ast=None,
            raw_json={},
            semantic_score=0.0,
            is_valid=False,
            validation_errors=("Failed to generate valid AST after multiple attempts",),
        )

    async def parse_file(self, file_path: str) -> ASTParserResult:
        """Parse a source file and return AST result.

        Args:
            file_path: Path to the source file

        Returns:
            ASTParserResult containing the parsed AST and metadata
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                source_code = f.read()
        except FileNotFoundError:
            return ASTParserResult(
                ast=None,
                raw_json={},
                semantic_score=0.0,
                is_valid=False,
                validation_errors=(f"File not found: {file_path}",),
            )
        except UnicodeDecodeError as e:
            return ASTParserResult(
                ast=None,
                raw_json={},
                semantic_score=0.0,
                is_valid=False,
                validation_errors=(f"Unable to decode file: {e}",),
            )

        # Detect language from extension
        language = self._detect_language(file_path)

        return await self.parse(source_code, language)

    def validate_ast(self, ast_json: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate AST JSON structure.

        Args:
            ast_json: The AST in JSON format

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        return self._validator.validate(ast_json)

    def calculate_semantic_score(self, ast_json: dict[str, Any]) -> float:
        """Calculate semantic quality score for the AST.

        Args:
            ast_json: The AST in JSON format

        Returns:
            Semantic score between 0.0 and 1.0
        """
        return self._scorer.calculate_score(ast_json)

    def _evaluate_candidate(self, ast_json: dict[str, Any]) -> ASTParserResult:
        """Evaluate an AST JSON candidate.

        Args:
            ast_json: The AST JSON to evaluate

        Returns:
            ASTParserResult with evaluation results
        """
        # Validate structure
        is_valid, validation_errors = self._validator.validate(ast_json)

        if not is_valid:
            return ASTParserResult(
                ast=None,
                raw_json=ast_json,
                semantic_score=0.0,
                is_valid=False,
                validation_errors=tuple(validation_errors),
            )

        # Check structure completeness
        is_complete, warnings = self._validator.validate_structure_completeness(ast_json)

        # Calculate semantic score
        semantic_score = self._scorer.calculate_score(ast_json)

        # Convert JSON to ASTNode
        ast_node = self._json_to_ast_node(ast_json)

        return ASTParserResult(
            ast=ast_node,
            raw_json=ast_json,
            semantic_score=semantic_score,
            is_valid=True,
            validation_errors=tuple(warnings),
            metadata={
                "statistics": self._validator.extract_statistics(ast_json),
                "quality_rating": self._scorer.get_quality_rating(semantic_score),
            },
        )

    def _json_to_ast_node(self, node_json: dict[str, Any]) -> ASTNode:
        """Convert JSON representation to ASTNode.

        Args:
            node_json: The JSON node

        Returns:
            ASTNode instance
        """
        # Map node type
        type_str = node_json.get("type", "unknown")
        try:
            node_type = NodeType(type_str)
        except ValueError:
            node_type = NodeType.UNKNOWN

        # Convert children recursively
        children_json = node_json.get("children", [])
        children = tuple(
            self._json_to_ast_node(child)
            for child in children_json
            if isinstance(child, dict)
        )

        return ASTNode(
            node_type=node_type,
            name=node_json.get("name"),
            value=node_json.get("value"),
            children=children,
            metadata=node_json.get("metadata", {}),
            line_number=node_json.get("line"),
            column=node_json.get("col"),
        )

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension.

        Args:
            file_path: Path to the file

        Returns:
            Language name
        """
        extension_map = {
            ".py": "python",
            ".pyi": "python",
            ".sol": "solidity",
            ".rs": "rust",
            ".go": "go",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
        }

        for ext, lang in extension_map.items():
            if file_path.endswith(ext):
                return lang

        return "python"  # Default to Python
