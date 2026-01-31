"""Use case for extracting behavioral models from source code.

This use case orchestrates Layer 1 operations to transform source code
into structured behavioral models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from src.core.entities.behavioral_model import BehavioralModel, ControlFlowGraph, DataFlowInfo


class ASTParserProtocol(Protocol):
    """Protocol for AST parser dependency."""

    async def parse(self, source_code: str, language: str = "python") -> object: ...
    async def parse_file(self, file_path: str) -> object: ...


class CFGGeneratorProtocol(Protocol):
    """Protocol for CFG generator dependency."""

    def generate(self, ast: object) -> ControlFlowGraph: ...


class DataFlowAnalyzerProtocol(Protocol):
    """Protocol for data flow analyzer dependency."""

    def analyze(self, ast: object) -> DataFlowInfo: ...


class BehavioralExtractorProtocol(Protocol):
    """Protocol for behavioral extractor dependency."""

    async def extract(
        self,
        ast: object,
        cfg: ControlFlowGraph,
        data_flow: DataFlowInfo,
    ) -> tuple[str, str, str]: ...


@dataclass
class ExtractBehavioralModelResult:
    """Result from behavioral model extraction.

    Attributes:
        behavioral_model: The extracted behavioral model (if successful)
        is_success: Whether extraction was successful
        error_message: Error message if extraction failed
        warnings: List of non-fatal warnings
    """

    behavioral_model: BehavioralModel | None
    is_success: bool
    error_message: str | None = None
    warnings: list[str] | None = None


class ExtractBehavioralModelUseCase:
    """Use case for extracting behavioral models from source code.

    This use case coordinates the Layer 1 pipeline:
    1. Parse source code into AST using LLM
    2. Validate and score the AST
    3. Generate Control Flow Graph
    4. Perform Data Flow Analysis
    5. Extract behavioral model (preconditions, postconditions, invariants)
    """

    def __init__(
        self,
        ast_parser: ASTParserProtocol,
        cfg_generator: CFGGeneratorProtocol,
        data_flow_analyzer: DataFlowAnalyzerProtocol,
        behavioral_extractor: BehavioralExtractorProtocol,
    ) -> None:
        """Initialize the use case with required dependencies.

        Args:
            ast_parser: AST parsing implementation
            cfg_generator: CFG generation implementation
            data_flow_analyzer: Data flow analysis implementation
            behavioral_extractor: Behavioral model extraction implementation
        """
        self._ast_parser = ast_parser
        self._cfg_generator = cfg_generator
        self._data_flow_analyzer = data_flow_analyzer
        self._behavioral_extractor = behavioral_extractor

    async def execute(
        self,
        source_code: str,
        source_file: str = "<unknown>",
        language: str = "python",
    ) -> ExtractBehavioralModelResult:
        """Execute behavioral model extraction.

        Args:
            source_code: The source code to analyze
            source_file: Path to the source file (for reporting)
            language: Programming language of the source

        Returns:
            ExtractBehavioralModelResult containing the model or error
        """
        from src.core.entities.behavioral_model import BehavioralModel
        from src.core.exceptions import ParsingError, SemanticValidationError

        warnings: list[str] = []

        try:
            # Step 1: Parse source code into AST
            ast_result = await self._ast_parser.parse(source_code, language)

            if not ast_result.is_valid:
                return ExtractBehavioralModelResult(
                    behavioral_model=None,
                    is_success=False,
                    error_message=f"AST parsing failed: {', '.join(ast_result.validation_errors)}",
                )

            # Check semantic score threshold
            if ast_result.semantic_score < 0.3:
                return ExtractBehavioralModelResult(
                    behavioral_model=None,
                    is_success=False,
                    error_message=(
                        f"AST semantic score too low: {ast_result.semantic_score:.2f} < 0.3"
                    ),
                )

            if ast_result.semantic_score < 0.5:
                warnings.append(
                    f"Low semantic score ({ast_result.semantic_score:.2f}), "
                    "results may be incomplete"
                )

            # Step 2: Generate Control Flow Graph
            cfg = self._cfg_generator.generate(ast_result.ast)

            # Step 3: Perform Data Flow Analysis
            data_flow = self._data_flow_analyzer.analyze(ast_result.ast)

            # Step 4: Extract behavioral model
            precondition, postcondition, invariant = await self._behavioral_extractor.extract(
                ast_result.ast,
                cfg,
                data_flow,
            )

            # Step 5: Construct SBT (Structure-Based Traversal)
            sbt = self._generate_sbt(ast_result.ast)

            # Create the behavioral model
            behavioral_model = BehavioralModel(
                source_file=source_file,
                ast=ast_result.ast,
                sbt=sbt,
                cfg=cfg,
                data_flow=data_flow,
                precondition=precondition,
                postcondition=postcondition,
                invariant=invariant,
                semantic_score=ast_result.semantic_score,
                raw_source=source_code,
            )

            return ExtractBehavioralModelResult(
                behavioral_model=behavioral_model,
                is_success=True,
                warnings=warnings if warnings else None,
            )

        except ParsingError as e:
            return ExtractBehavioralModelResult(
                behavioral_model=None,
                is_success=False,
                error_message=f"Parsing error: {e}",
            )
        except SemanticValidationError as e:
            return ExtractBehavioralModelResult(
                behavioral_model=None,
                is_success=False,
                error_message=f"Semantic validation error: {e}",
            )
        except Exception as e:
            return ExtractBehavioralModelResult(
                behavioral_model=None,
                is_success=False,
                error_message=f"Unexpected error: {e}",
            )

    async def execute_file(
        self,
        file_path: str,
        language: str = "python",
    ) -> ExtractBehavioralModelResult:
        """Execute behavioral model extraction from a file.

        Args:
            file_path: Path to the source file
            language: Programming language of the source

        Returns:
            ExtractBehavioralModelResult containing the model or error
        """
        from src.core.exceptions import SourceCodeError

        try:
            with open(file_path, encoding="utf-8") as f:
                source_code = f.read()
        except FileNotFoundError:
            return ExtractBehavioralModelResult(
                behavioral_model=None,
                is_success=False,
                error_message=f"File not found: {file_path}",
            )
        except UnicodeDecodeError as e:
            raise SourceCodeError(
                f"Unable to decode file: {e}",
                file_path=file_path,
                encoding_error=True,
            ) from e

        return await self.execute(source_code, file_path, language)

    def _generate_sbt(self, ast: object) -> str:
        """Generate Structure-Based Traversal string from AST.

        This creates a linearized representation of the AST structure
        suitable for sequence-based analysis.

        Args:
            ast: The AST root node

        Returns:
            SBT string representation
        """
        tokens: list[str] = []
        self._traverse_sbt(ast, tokens)
        return " ".join(tokens)

    def _traverse_sbt(self, node: object, tokens: list[str]) -> None:
        """Recursively traverse AST for SBT generation.

        Args:
            node: Current AST node
            tokens: List to accumulate tokens
        """
        if node is None:
            return

        # Add opening token
        node_type = getattr(node, "node_type", "unknown")
        tokens.append(f"({node_type.value if hasattr(node_type, 'value') else str(node_type)}")

        # Add name if present
        name = getattr(node, "name", None)
        if name:
            tokens.append(f"[{name}]")

        # Traverse children
        children = getattr(node, "children", [])
        for child in children:
            self._traverse_sbt(child, tokens)

        # Add closing token
        tokens.append(f"){node_type.value if hasattr(node_type, 'value') else str(node_type)}")
