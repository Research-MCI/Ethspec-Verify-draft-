# =============================================================================
# Ethereum Protocol Specification Compliance Verifier - Dockerfile
# =============================================================================

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# Builder stage
# =============================================================================
FROM base as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# =============================================================================
# Production stage
# =============================================================================
FROM base as production

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY src/ ./src/

COPY pyproject.toml .

# Create data directories
RUN mkdir -p data/specs data/embeddings data/chromadb

# Set default command
CMD ["python", "-m", "src.integration.cli.main", "--help"]

RUN mkdir -p data/specs data/embeddings data/chromadb db results documents
# =============================================================================
# Development stage
# =============================================================================
FROM base as development

# Install development dependencies
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

# Copy application code
COPY . .

# Set default command for development
CMD ["pytest", "tests/", "-v"]

# =============================================================================
# Bot stage (for GitHub bot deployment)
# =============================================================================
FROM production as bot

# Expose port for webhook server
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the bot server
CMD ["uvicorn", "src.integration.github_bot.app:app", "--host", "0.0.0.0", "--port", "8000"]

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    CHROMA_PERSIST_DIRECTORY=/app/data/chromadb