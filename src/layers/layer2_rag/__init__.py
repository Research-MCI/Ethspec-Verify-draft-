"""Layer 2: RAG-Enhanced Specification Ingestion.

This layer builds a searchable knowledge base from Ethereum specification
documents through parsing, chunking, embedding, and graph construction.
"""

from src.layers.layer2_rag.context_assembler import ContextAssembler
from src.layers.layer2_rag.document_parser import DocumentParser
from src.layers.layer2_rag.embedding_generator import GeminiEmbeddingGenerator
from src.layers.layer2_rag.knowledge_graph import InMemoryKnowledgeGraph
from src.layers.layer2_rag.semantic_chunker import SemanticChunker
from src.layers.layer2_rag.spec_normalizer import SpecificationNormalizer
from src.layers.layer2_rag.vector_database import ChromaDBVectorStore

__all__ = [
    "ChromaDBVectorStore",
    "ContextAssembler",
    "DocumentParser",
    "GeminiEmbeddingGenerator",
    "InMemoryKnowledgeGraph",
    "SemanticChunker",
    "SpecificationNormalizer",
]
