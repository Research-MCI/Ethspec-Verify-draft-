# Ethereum Protocol Specification Compliance Verifier

[![CI](https://github.com/your-org/eth-spec-compliance-verifier/workflows/CI/badge.svg)](https://github.com/your-org/eth-spec-compliance-verifier/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

An automated verification framework that integrates Chain-of-Thought (CoT) reasoning with Retrieval-Augmented Generation (RAG) to systematically detect specification-implementation drift in Ethereum protocol clients.

## Overview

This framework addresses the challenge of verifying compliance between Ethereum protocol specifications and client implementations. Manual verification across multiple codebases is laborious and error-prone. This tool automates the process through a three-layer architecture:

- **Layer 1 (AST-Based Code Analysis)**: Transforms source code into structured behavioral models through LLM-based AST induction
- **Layer 2 (RAG-Enhanced Specification Ingestion)**: Builds a searchable knowledge base from Ethereum specification documents
- **Layer 3 (CoT Verification Engine)**: Implements Chain-of-Thought reasoning for systematic compliance analysis

## Features

- Automated Drift Detection: Identify discrepancies between specifications and implementations
- LLM-Powered Analysis: Leverage Large Language Models for semantic code understanding
- Confidence Scoring: Each finding includes a confidence score based on evidence strength
- CI/CD Integration: GitHub Actions workflow for automated compliance checks on PRs
- GitHub Bot: Automated PR comments with compliance findings
- CLI Tool: Command-line interface for local development and batch audits
- Human-in-the-Loop: All findings flow to human reviewers for final decisions

## Quick Start

### Prerequisites

- Python 3.10+
- Docker (optional, for Neo4j)
- Google Cloud account (for Gemini API)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/eth-spec-compliance-verifier.git
cd eth-spec-compliance-verifier

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Basic Usage

```bash
# Ingest Ethereum specifications
eth-verify ingest --source execution-specs --fork cancun

# Analyze a specification file
eth-verify analyze path/to/spec_file.py

# Verify compliance
eth-verify verify --code path/to/implementation --spec cancun

# Generate report
eth-verify report --output report.json
```

### GitHub Actions Integration

Add to your repository's `.github/workflows/compliance.yml`:

```yaml
name: Specification Compliance Check

on:
  pull_request:
    branches: [main]

jobs:
  compliance:
    uses: your-org/eth-spec-compliance-verifier/.github/workflows/compliance-check.yml@main
    with:
      fork: cancun
    secrets:
      GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Data Sources                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ Execution    │  │ Consensus    │  │   Ethereum   │               │
│  │ Specs Repo   │  │ Specs Repo   │  │     EIPs     │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Layer 1: AST-Based Code Analysis                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐     │
│  │   AST    │→ │   CFG    │→ │Data Flow │→ │   Behavioral     │     │
│  │  Parser  │  │Generator │  │ Analyzer │  │ Model Extractor  │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│               Layer 2: RAG-Enhanced Specification Ingestion          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐     │
│  │ Document │→ │ Semantic │→ │Embedding │→ │   Knowledge      │     │
│  │  Parser  │  │ Chunker  │  │Generator │  │     Graph        │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Layer 3: CoT Verification Engine                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐     │
│  │   RAG    │→ │   CoT    │→ │Req-Code  │→ │     Report       │     │
│  │Retriever │  │ Reasoner │  │Comparator│  │    Generator     │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Integration Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │     CLI      │  │ GitHub Bot   │  │GitHub Actions│               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │   Human Reviewer     │
                    │  (Final Decision)    │
                    └──────────────────────┘
```

## Configuration

Create a `.env` file with the following variables:

```env
# LLM Configuration
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

# Vector Database
CHROMADB_PATH=./data/chromadb

# Knowledge Graph (optional)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# GitHub Integration
GITHUB_APP_ID=your_app_id
GITHUB_PRIVATE_KEY_PATH=./private-key.pem
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# Logging
LOG_LEVEL=INFO
```

## Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run linting
ruff check src tests

# Run type checking
mypy src

# Format code
black src tests
isort src tests
```

## Evaluation Metrics

The framework uses the following evaluation metrics:

| Metric | Layer | Purpose |
|--------|-------|---------|
| Structural Completeness Score (SCS) | Layer 1 | Measures AST extraction quality |
| Mean Reciprocal Rank (MRR) | Layer 2 | Evaluates specification retrieval |
| Expected Calibration Error (ECE) | Layer 3 | Assesses confidence score calibration |
| Macro F1-Score | End-to-End | Overall classification performance |

## Project Structure

```
eth-spec-compliance-verifier/
├── src/
│   ├── core/                    # Domain entities, interfaces, use cases
│   ├── layers/
│   │   ├── layer1_ast/          # AST-Based Code Analysis
│   │   ├── layer2_rag/          # RAG-Enhanced Specification
│   │   └── layer3_cot/          # CoT Verification Engine
│   ├── infrastructure/          # External service integrations
│   ├── integration/             # CLI, GitHub bot, Actions
│   └── shared/                  # Utilities and configuration
├── tests/                       # Test suite
├── .github/workflows/           # CI/CD pipelines
└── docs/                        # Documentation
```

## Contributing

Contributions are welcome! Please read our Contributing Guidelines before submitting a PR.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

This project is developed by the Laboratory of Business-Enterprise (LBE), Institut Teknologi Sepuluh Nopember (ITS), Surabaya, Indonesia.

## Citation

If you use this tool in your research, please cite:

```bibtex
@software{eth_spec_compliance_verifier,
  title = {Ethereum Protocol Specification Compliance Verifier},
  author = {Sarno, Riyanarto and Sungkono, Kelly Rossa and Haryono, Agus Tri and Febryanto, Kurnia Cahya},
  year = {2025},
  url = {https://github.com/your-org/eth-spec-compliance-verifier}
}
```
