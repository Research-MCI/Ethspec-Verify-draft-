"""Use case for ingesting specification documents.

This use case orchestrates Layer 2 operations to parse, chunk, embed,
and store specification documents in the knowledge base.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from src.core.entities.specification import (
        NormalizedSpecification,
        SpecificationChunk,
        SpecificationDocument,
        SpecificationMetadata,
    )


class DocumentParserProtocol(Protocol):
    """Protocol for document parser dependency."""

    async def parse(
        self,
        content: str,
        metadata: SpecificationMetadata,
    ) -> SpecificationDocument: ...

    async def parse_file(
        self,
        file_path: str,
        metadata: SpecificationMetadata,
    ) -> SpecificationDocument: ...


class SemanticChunkerProtocol(Protocol):
    """Protocol for semantic chunker dependency."""

    def chunk(
        self,
        document: SpecificationDocument,
    ) -> list[SpecificationChunk]: ...


class EmbeddingGeneratorProtocol(Protocol):
    """Protocol for embedding generator dependency."""

    async def generate_batch(
        self,
        texts: list[str],
        batch_size: int = 100,
    ) -> list[tuple[float, ...]]: ...


class VectorStoreProtocol(Protocol):
    """Protocol for vector store dependency."""

    async def add_batch(
        self,
        chunk_ids: list[str],
        contents: list[str],
        embeddings: list[tuple[float, ...]],
        metadatas: list[dict] | None = None,
    ) -> None: ...


class KnowledgeGraphProtocol(Protocol):
    """Protocol for knowledge graph dependency."""

    async def add_node(self, node: object) -> None: ...
    async def add_relation(self, relation: object) -> None: ...


class SpecNormalizerProtocol(Protocol):
    """Protocol for specification normalizer dependency."""

    async def normalize(
        self,
        document: SpecificationDocument,
        chunks: list[SpecificationChunk],
    ) -> NormalizedSpecification: ...


@dataclass
class IngestSpecificationResult:
    """Result from specification ingestion.

    Attributes:
        document: The ingested document (if successful)
        normalized_spec: The normalized specification (if successful)
        chunks_count: Number of chunks created
        is_success: Whether ingestion was successful
        error_message: Error message if ingestion failed
    """

    document: SpecificationDocument | None
    normalized_spec: NormalizedSpecification | None
    chunks_count: int
    is_success: bool
    error_message: str | None = None


class IngestSpecificationUseCase:
    """Use case for ingesting specification documents.

    This use case coordinates the Layer 2 pipeline:
    1. Parse specification documents
    2. Perform semantic chunking
    3. Generate vector embeddings
    4. Store in vector database
    5. Build knowledge graph relationships
    6. Normalize specifications
    """

    def __init__(
        self,
        document_parser: DocumentParserProtocol,
        semantic_chunker: SemanticChunkerProtocol,
        embedding_generator: EmbeddingGeneratorProtocol,
        vector_store: VectorStoreProtocol,
        knowledge_graph: KnowledgeGraphProtocol,
        spec_normalizer: SpecNormalizerProtocol,
    ) -> None:
        """Initialize the use case with required dependencies.

        Args:
            document_parser: Document parsing implementation
            semantic_chunker: Semantic chunking implementation
            embedding_generator: Embedding generation implementation
            vector_store: Vector storage implementation
            knowledge_graph: Knowledge graph implementation
            spec_normalizer: Specification normalization implementation
        """
        self._document_parser = document_parser
        self._semantic_chunker = semantic_chunker
        self._embedding_generator = embedding_generator
        self._vector_store = vector_store
        self._knowledge_graph = knowledge_graph
        self._spec_normalizer = spec_normalizer

    async def execute(
        self,
        content: str,
        metadata: SpecificationMetadata,
    ) -> IngestSpecificationResult:
        """Execute specification ingestion.

        Args:
            content: The specification content to ingest
            metadata: Metadata about the specification

        Returns:
            IngestSpecificationResult containing the result or error
        """
        try:
            # Step 1: Parse the document
            document = await self._document_parser.parse(content, metadata)

            # Step 2: Perform semantic chunking
            chunks = self._semantic_chunker.chunk(document)

            if not chunks:
                return IngestSpecificationResult(
                    document=document,
                    normalized_spec=None,
                    chunks_count=0,
                    is_success=False,
                    error_message="No chunks extracted from document",
                )

            # Step 3: Generate embeddings
            chunk_contents = [chunk.content for chunk in chunks]
            embeddings = await self._embedding_generator.generate_batch(chunk_contents)

            # Step 4: Store in vector database
            chunk_ids = [chunk.chunk_id for chunk in chunks]
            metadatas = [chunk.metadata.to_dict() for chunk in chunks]

            await self._vector_store.add_batch(
                chunk_ids=chunk_ids,
                contents=chunk_contents,
                embeddings=embeddings,
                metadatas=metadatas,
            )

            # Step 5: Build knowledge graph
            await self._build_knowledge_graph(document, chunks)

            # Step 6: Normalize specification
            normalized_spec = await self._spec_normalizer.normalize(document, chunks)

            return IngestSpecificationResult(
                document=document,
                normalized_spec=normalized_spec,
                chunks_count=len(chunks),
                is_success=True,
            )

        except Exception as e:
            return IngestSpecificationResult(
                document=None,
                normalized_spec=None,
                chunks_count=0,
                is_success=False,
                error_message=f"Ingestion failed: {e}",
            )

    async def execute_file(
        self,
        file_path: str,
        metadata: SpecificationMetadata,
    ) -> IngestSpecificationResult:
        """Execute specification ingestion from a file.

        Args:
            file_path: Path to the specification file
            metadata: Metadata about the specification

        Returns:
            IngestSpecificationResult containing the result or error
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            return IngestSpecificationResult(
                document=None,
                normalized_spec=None,
                chunks_count=0,
                is_success=False,
                error_message=f"File not found: {file_path}",
            )
        except UnicodeDecodeError as e:
            return IngestSpecificationResult(
                document=None,
                normalized_spec=None,
                chunks_count=0,
                is_success=False,
                error_message=f"Unable to decode file: {e}",
            )

        return await self.execute(content, metadata)

    async def _build_knowledge_graph(
        self,
        document: SpecificationDocument,
        chunks: list[SpecificationChunk],
    ) -> None:
        """Build knowledge graph nodes and relationships.

        Args:
            document: The parsed document
            chunks: The document chunks
        """
        from src.core.interfaces.knowledge_graph import (
            KnowledgeNode,
            KnowledgeRelation,
            NodeType,
            RelationType,
        )

        # Create document node
        doc_node = KnowledgeNode(
            node_id=document.doc_id,
            node_type=NodeType.SPECIFICATION,
            label=document.title,
            properties={
                "fork_version": document.metadata.fork_version,
                "category": document.metadata.category.value,
            },
        )
        await self._knowledge_graph.add_node(doc_node)

        # Create chunk nodes and relationships
        for chunk in chunks:
            chunk_node = KnowledgeNode(
                node_id=chunk.chunk_id,
                node_type=NodeType.REQUIREMENT,
                label=chunk.content[:50] + "..." if len(chunk.content) > 50 else chunk.content,
                properties={
                    "requirement_type": chunk.requirement_type.value,
                    "parent_section": chunk.parent_section,
                },
            )
            await self._knowledge_graph.add_node(chunk_node)

            # Link chunk to document
            relation = KnowledgeRelation(
                relation_id=f"{document.doc_id}_contains_{chunk.chunk_id}",
                source_id=document.doc_id,
                target_id=chunk.chunk_id,
                relation_type=RelationType.CONTAINS,
            )
            await self._knowledge_graph.add_relation(relation)

            # Link related chunks
            for related_id in chunk.related_chunks:
                related_relation = KnowledgeRelation(
                    relation_id=f"{chunk.chunk_id}_related_{related_id}",
                    source_id=chunk.chunk_id,
                    target_id=related_id,
                    relation_type=RelationType.RELATED_TO,
                )
                await self._knowledge_graph.add_relation(related_relation)
