"""Configuration management using Pydantic Settings.

This module provides centralized configuration management with validation
and environment variable support.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """LLM provider configuration."""

    model_config = SettingsConfigDict(env_prefix="GEMINI_")

    api_key: str = Field(default="", description="Gemini API key")
    model: str = Field(default="gemini-2.5-flash", description="Gemini model name")
    embedding_model: str = Field(
        default="text-embedding-004",
        description="Embedding model name",
    )
    temperature: float = Field(default=0.1, ge=0.0, le=1.0)
    max_tokens: int = Field(default=8192, ge=1)


class VectorStoreSettings(BaseSettings):
    """Vector store configuration."""

    model_config = SettingsConfigDict(env_prefix="CHROMADB_")

    path: str = Field(default="./data/chromadb", description="ChromaDB storage path")
    collection_name: str = Field(
        default="eth_specifications",
        description="Default collection name",
    )


class KnowledgeGraphSettings(BaseSettings):
    """Knowledge graph (Neo4j) configuration."""

    model_config = SettingsConfigDict(env_prefix="NEO4J_")

    uri: str = Field(default="bolt://localhost:7687", description="Neo4j URI")
    user: str = Field(default="neo4j", description="Neo4j username")
    password: str = Field(default="", description="Neo4j password")
    database: str = Field(default="neo4j", description="Neo4j database name")


class GitHubSettings(BaseSettings):
    """GitHub integration configuration."""

    model_config = SettingsConfigDict(env_prefix="GITHUB_")

    app_id: str = Field(default="", description="GitHub App ID")
    private_key_path: str = Field(
        default="./private-key.pem",
        description="Path to GitHub App private key",
    )
    webhook_secret: str = Field(default="", description="GitHub webhook secret")
    token: str = Field(default="", description="GitHub personal access token")


class EthereumSettings(BaseSettings):
    """Ethereum specification configuration."""

    execution_specs_repo: str = Field(
        default="ethereum/execution-specs",
        description="Execution specs repository",
    )
    consensus_specs_repo: str = Field(
        default="ethereum/consensus-specs",
        description="Consensus specs repository",
    )
    default_fork: str = Field(default="cancun", description="Default fork version")


class Settings(BaseSettings):
    """Main application settings.

    Loads configuration from environment variables with the following precedence:
    1. Environment variables
    2. .env file
    3. Default values
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application settings
    debug: bool = Field(default=False, description="Debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    log_format: Literal["json", "console"] = Field(
        default="console",
        description="Log output format",
    )

    # Cache settings
    cache_enabled: bool = Field(default=True, description="Enable caching")
    cache_ttl_seconds: int = Field(default=3600, ge=0, description="Cache TTL")

    # Verification settings
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Confidence threshold for findings",
    )
    max_findings_per_run: int = Field(
        default=100,
        ge=1,
        description="Maximum findings per verification run",
    )

    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    workers: int = Field(default=4, ge=1, description="Number of workers")

    # Nested settings
    llm: LLMSettings = Field(default_factory=LLMSettings)
    vector_store: VectorStoreSettings = Field(default_factory=VectorStoreSettings)
    knowledge_graph: KnowledgeGraphSettings = Field(default_factory=KnowledgeGraphSettings)
    github: GitHubSettings = Field(default_factory=GitHubSettings)
    ethereum: EthereumSettings = Field(default_factory=EthereumSettings)

    @field_validator("log_level", mode="before")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate and normalize log level."""
        return v.upper()

    @property
    def data_dir(self) -> Path:
        """Get the data directory path."""
        return Path("./data")

    @property
    def specs_dir(self) -> Path:
        """Get the specifications directory path."""
        return self.data_dir / "specs"

    @property
    def embeddings_dir(self) -> Path:
        """Get the embeddings directory path."""
        return self.data_dir / "embeddings"

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.specs_dir.mkdir(parents=True, exist_ok=True)
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
        Path(self.vector_store.path).mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings instance (cached)
    """
    return Settings()


def reload_settings() -> Settings:
    """Reload settings (clear cache and create new instance).

    Returns:
        Fresh Settings instance
    """
    get_settings.cache_clear()
    return get_settings()
