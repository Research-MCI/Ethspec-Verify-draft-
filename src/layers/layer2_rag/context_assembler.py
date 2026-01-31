"""Context assembler for LLM prompts.

This module assembles context from specifications and implementation
artifacts for LLM processing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.entities.behavioral_model import BehavioralModel
    from src.core.interfaces.vector_store import SearchResult


@dataclass
class AssembledContext:
    """Assembled context for LLM processing.

    Attributes:
        specification_context: Formatted specification excerpts
        implementation_context: Formatted implementation details
        combined_context: Full combined context
        token_estimate: Estimated token count
        sources: List of source references
    """

    specification_context: str
    implementation_context: str
    combined_context: str
    token_estimate: int
    sources: list[str]


class ContextAssembler:
    """Assembles context from multiple sources for LLM processing.

    Combines:
    - Retrieved specification chunks
    - Behavioral model information
    - Knowledge graph relationships
    """

    def __init__(
        self,
        max_context_tokens: int = 4000,
        chars_per_token: float = 4.0,
    ) -> None:
        """Initialize the context assembler.

        Args:
            max_context_tokens: Maximum tokens for context
            chars_per_token: Estimated characters per token
        """
        self.max_context_tokens = max_context_tokens
        self.chars_per_token = chars_per_token
        self.max_context_chars = int(max_context_tokens * chars_per_token)

    def assemble(
        self,
        search_results: list[SearchResult],
        behavioral_model: BehavioralModel | None = None,
    ) -> AssembledContext:
        """Assemble context from search results and behavioral model.

        Args:
            search_results: Retrieved specification chunks
            behavioral_model: Optional behavioral model from code

        Returns:
            AssembledContext
        """
        spec_parts: list[str] = []
        sources: list[str] = []
        current_chars = 0

        # Add specification context
        for i, result in enumerate(search_results):
            chunk_text = self._format_spec_chunk(result, i + 1)
            chunk_chars = len(chunk_text)

            if current_chars + chunk_chars > self.max_context_chars * 0.7:
                break

            spec_parts.append(chunk_text)
            sources.append(result.chunk_id)
            current_chars += chunk_chars

        specification_context = "\n\n".join(spec_parts)

        # Add implementation context
        impl_parts: list[str] = []
        if behavioral_model:
            impl_context = self._format_behavioral_model(behavioral_model)
            impl_chars = len(impl_context)

            if current_chars + impl_chars <= self.max_context_chars:
                impl_parts.append(impl_context)
                current_chars += impl_chars

        implementation_context = "\n\n".join(impl_parts)

        # Combine context
        combined_parts = []
        if specification_context:
            combined_parts.append("## Relevant Specifications\n" + specification_context)
        if implementation_context:
            combined_parts.append("## Implementation Details\n" + implementation_context)

        combined_context = "\n\n---\n\n".join(combined_parts)

        return AssembledContext(
            specification_context=specification_context,
            implementation_context=implementation_context,
            combined_context=combined_context,
            token_estimate=int(current_chars / self.chars_per_token),
            sources=sources,
        )

    def _format_spec_chunk(self, result: SearchResult, index: int) -> str:
        """Format a specification chunk for context.

        Args:
            result: Search result
            index: Result index

        Returns:
            Formatted string
        """
        parts = [f"### Specification Excerpt {index}"]

        # Add metadata if available
        metadata = result.metadata
        if metadata:
            meta_parts = []
            if "fork_version" in metadata:
                meta_parts.append(f"Fork: {metadata['fork_version']}")
            if "category" in metadata:
                meta_parts.append(f"Category: {metadata['category']}")
            if meta_parts:
                parts.append(f"*{' | '.join(meta_parts)}*")

        # Add relevance score
        parts.append(f"Relevance: {result.score:.2f}")

        # Add content
        parts.append("")
        parts.append(result.content)

        return "\n".join(parts)

    def _format_behavioral_model(self, model: BehavioralModel) -> str:
        """Format behavioral model for context.

        Args:
            model: Behavioral model

        Returns:
            Formatted string
        """
        parts = ["### Code Behavioral Model"]

        parts.append(f"**Source**: `{model.source_file}`")
        parts.append(f"**Semantic Score**: {model.semantic_score:.2f}")

        # Behavioral aspects
        if model.precondition:
            parts.append(f"\n**Precondition**: {model.precondition}")
        if model.postcondition:
            parts.append(f"**Postcondition**: {model.postcondition}")
        if model.invariant:
            parts.append(f"**Invariant**: {model.invariant}")

        # Data flow summary
        df = model.data_flow
        if df.state_writes:
            parts.append(f"\n**State Modifications**: {', '.join(df.state_writes[:10])}")
        if df.constants:
            const_strs = [str(c) for c in df.constants[:5]]
            parts.append(f"**Constants**: {', '.join(const_strs)}")
        if df.function_calls:
            parts.append(f"**Function Calls**: {', '.join(list(df.function_calls)[:10])}")

        return "\n".join(parts)

    def assemble_for_verification(
        self,
        search_results: list[SearchResult],
        behavioral_model: BehavioralModel,
        requirement_description: str,
    ) -> str:
        """Assemble context specifically for verification prompts.

        Args:
            search_results: Retrieved specifications
            behavioral_model: Code behavioral model
            requirement_description: The requirement being verified

        Returns:
            Formatted context string
        """
        parts = []

        # Requirement being verified
        parts.append("## Requirement Under Verification")
        parts.append(requirement_description)

        # Relevant specifications
        parts.append("\n## Supporting Specification Excerpts")
        for i, result in enumerate(search_results[:5]):  # Limit to top 5
            parts.append(f"\n### Excerpt {i + 1} (relevance: {result.score:.2f})")
            parts.append(result.content)

        # Implementation details
        parts.append("\n## Implementation Under Analysis")
        parts.append(f"**File**: `{behavioral_model.source_file}`")

        if behavioral_model.precondition:
            parts.append(f"**Precondition**: {behavioral_model.precondition}")
        if behavioral_model.postcondition:
            parts.append(f"**Postcondition**: {behavioral_model.postcondition}")

        # Key data flow
        df = behavioral_model.data_flow
        if df.state_writes:
            parts.append(f"**Modified State**: {', '.join(df.state_writes[:5])}")
        if df.constants:
            parts.append(f"**Constants Used**: {', '.join(str(c) for c in df.constants[:5])}")

        return "\n".join(parts)
