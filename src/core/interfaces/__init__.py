"""Core interfaces defining contracts for implementations."""

from src.core.interfaces.ast_parser import ASTParser, ASTParserResult
from src.core.interfaces.embedding_generator import EmbeddingGenerator
from src.core.interfaces.knowledge_graph import KnowledgeGraph, KnowledgeNode, KnowledgeRelation
from src.core.interfaces.llm_provider import LLMProvider, LLMResponse
from src.core.interfaces.report_generator import ReportFormat, ReportGenerator
from src.core.interfaces.vector_store import SearchResult, VectorStore

__all__ = [
    # AST Parser
    "ASTParser",
    "ASTParserResult",
    # Embedding Generator
    "EmbeddingGenerator",
    # Knowledge Graph
    "KnowledgeGraph",
    "KnowledgeNode",
    "KnowledgeRelation",
    # LLM Provider
    "LLMProvider",
    "LLMResponse",
    # Report Generator
    "ReportFormat",
    "ReportGenerator",
    # Vector Store
    "SearchResult",
    "VectorStore",
]
