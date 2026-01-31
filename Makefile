.PHONY: install install-dev test test-cov lint format typecheck clean docker-build docker-run run-cli run-bot ingest-specs help

# Default target
help:
	@echo "Ethereum Protocol Specification Compliance Verifier"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Development:"
	@echo "  install       Install production dependencies"
	@echo "  install-dev   Install development dependencies"
	@echo "  test          Run tests"
	@echo "  test-cov      Run tests with coverage"
	@echo "  lint          Run linters (ruff)"
	@echo "  format        Format code (black, isort)"
	@echo "  typecheck     Run type checking (mypy)"
	@echo "  clean         Clean build artifacts"
	@echo ""
	@echo "Running:"
	@echo "  run-cli       Run CLI tool"
	@echo "  run-bot       Run GitHub bot server"
	@echo "  ingest-specs  Ingest Ethereum specifications"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build  Build Docker image"
	@echo "  docker-run    Run in Docker"
	@echo "  docker-up     Start all services with docker-compose"
	@echo "  docker-down   Stop all services"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt
	pre-commit install

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v -m integration

# Code Quality
lint:
	ruff check src tests

lint-fix:
	ruff check src tests --fix

format:
	black src tests
	isort src tests

typecheck:
	mypy src

check: lint typecheck test
	@echo "All checks passed!"

# Cleaning
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Running
run-cli:
	python -m src.integration.cli.main

run-bot:
	uvicorn src.integration.github_bot.app:app --host 0.0.0.0 --port 8000 --reload

ingest-specs:
	python scripts/ingest_specs.py

# Docker
docker-build:
	docker build -t eth-spec-verifier .

docker-run:
	docker run --rm -it --env-file .env eth-spec-verifier

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

# Development shortcuts
dev: install-dev
	@echo "Development environment ready!"

setup: install-dev
	mkdir -p data/specs/execution-specs
	mkdir -p data/specs/consensus-specs
	mkdir -p data/embeddings
	mkdir -p data/chromadb
	cp .env.example .env
	@echo "Setup complete! Edit .env with your configuration."
