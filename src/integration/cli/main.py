"""Main CLI entry point using Typer.

This module provides the command-line interface for the
Ethereum Specification Compliance Verifier.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from src.shared.config import get_settings
from src.shared.constants import DEFAULT_FORK, SUPPORTED_FORKS
from src.shared.logger import setup_logging

app = typer.Typer(
    name="eth-verify",
    help="Ethereum Protocol Specification Compliance Verifier",
    add_completion=False,
)

console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        from src import __version__

        console.print(f"eth-verify version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug mode",
    ),
) -> None:
    """Ethereum Protocol Specification Compliance Verifier.

    An automated verification framework that integrates Chain-of-Thought (CoT)
    reasoning with Retrieval-Augmented Generation (RAG) to detect
    specification-implementation drift in Ethereum protocol clients.
    """
    settings = get_settings()
    log_level = "DEBUG" if debug else settings.log_level
    setup_logging(level=log_level, format=settings.log_format)


@app.command()
def ingest(
    source: str = typer.Argument(
        ...,
        help="Source repository (execution-specs or consensus-specs) or path",
    ),
    fork: str = typer.Option(
        DEFAULT_FORK,
        "--fork",
        "-f",
        help=f"Fork version ({', '.join(SUPPORTED_FORKS[-5:])})",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for embeddings",
    ),
) -> None:
    """Ingest Ethereum specifications into the knowledge base.

    Examples:
        eth-verify ingest execution-specs --fork cancun
        eth-verify ingest ./path/to/specs --fork prague
    """
    import asyncio

    from src.shared.utils.validation import validate_fork_version

    validate_fork_version(fork)

    console.print(f"[bold blue]Ingesting specifications from {source}...[/bold blue]")
    console.print(f"Fork: {fork}")

    async def run_ingest() -> None:
        # This would be the full implementation
        console.print("[yellow]Ingestion not yet fully implemented[/yellow]")
        console.print("Would ingest from:", source)

    asyncio.run(run_ingest())


@app.command()
def analyze(
    path: Path = typer.Argument(
        ...,
        help="Path to source file or directory to analyze",
        exists=True,
    ),
    language: str = typer.Option(
        "python",
        "--language",
        "-l",
        help="Programming language",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file for behavioral model (JSON)",
    ),
) -> None:
    """Analyze source code and extract behavioral model.

    Examples:
        eth-verify analyze ./src/fork.py
        eth-verify analyze ./src/ --output model.json
    """
    import asyncio

    console.print(f"[bold blue]Analyzing {path}...[/bold blue]")

    async def run_analyze() -> None:
        settings = get_settings()

        if not settings.llm.api_key:
            console.print("[red]Error: GEMINI_API_KEY not configured[/red]")
            raise typer.Exit(1)

        from src.infrastructure.llm.gemini_provider import GeminiProvider
        from src.layers.layer1_ast import (
            BehavioralExtractor,
            CFGGenerator,
            DataFlowAnalyzer,
            LLMASTParser,
        )

        # Initialize components
        llm = GeminiProvider(
            api_key=settings.llm.api_key,
            model_name=settings.llm.model,
        )
        ast_parser = LLMASTParser(llm)
        cfg_generator = CFGGenerator()
        data_flow_analyzer = DataFlowAnalyzer()
        behavioral_extractor = BehavioralExtractor(llm)

        if path.is_file():
            files = [path]
        else:
            files = list(path.glob("**/*.py"))

        for file_path in files[:5]:  # Limit for demo
            console.print(f"\nAnalyzing: {file_path}")

            try:
                with open(file_path, encoding="utf-8") as f:
                    source_code = f.read()

                # Parse AST
                result = await ast_parser.parse(source_code, language)

                if result.is_valid and result.ast:
                    console.print(f"  [green]AST Score: {result.semantic_score:.2f}[/green]")

                    # Generate CFG
                    cfg = cfg_generator.generate(result.ast)
                    console.print(f"  CFG: {len(cfg.nodes)} nodes, {len(cfg.edges)} edges")

                    # Analyze data flow
                    data_flow = data_flow_analyzer.analyze(result.ast)
                    console.print(f"  State writes: {len(data_flow.state_writes)}")
                    console.print(f"  Constants: {len(data_flow.constants)}")

                else:
                    console.print(f"  [red]Failed: {result.validation_errors}[/red]")

            except Exception as e:
                console.print(f"  [red]Error: {e}[/red]")

    asyncio.run(run_analyze())


@app.command()
def verify(
    code: Path = typer.Argument(
        ...,
        help="Path to code file or directory",
        exists=True,
    ),
    fork: str = typer.Option(
        DEFAULT_FORK,
        "--fork",
        "-f",
        help="Fork version to verify against",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file for verification report",
    ),
    format: str = typer.Option(
        "json",
        "--format",
        help="Output format (json, markdown, sarif)",
    ),
) -> None:
    """Verify code compliance against specifications.

    Examples:
        eth-verify verify ./implementation.py --fork cancun
        eth-verify verify ./src/ --output report.json
    """
    import asyncio

    from src.shared.utils.validation import validate_fork_version

    validate_fork_version(fork)

    console.print(f"[bold blue]Verifying compliance for {code}...[/bold blue]")
    console.print(f"Fork: {fork}")

    async def run_verify() -> None:
        console.print("[yellow]Full verification pipeline not yet implemented[/yellow]")
        console.print("Would verify:", code)
        console.print("Against fork:", fork)

    asyncio.run(run_verify())


@app.command()
def report(
    input_file: Path = typer.Argument(
        ...,
        help="Input verification result JSON",
        exists=True,
    ),
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        help="Output report file",
    ),
    format: str = typer.Option(
        "markdown",
        "--format",
        help="Output format (json, markdown, html, sarif)",
    ),
) -> None:
    """Generate report from verification results.

    Examples:
        eth-verify report results.json --output report.md --format markdown
    """
    import asyncio
    import json

    console.print(f"[bold blue]Generating {format} report...[/bold blue]")

    async def run_report() -> None:
        from datetime import datetime

        from src.core.entities.verification_result import (
            ComplianceStatus,
            Metrics,
            VerificationDecision,
            VerificationResult,
            VerificationSummary,
        )
        from src.core.interfaces.report_generator import ReportFormat
        from src.layers.layer3_cot.report_generator import JSONReportGenerator

        # Load input
        with open(input_file, encoding="utf-8") as f:
            data = json.load(f)

        # Create result from data (simplified)
        result = VerificationResult(
            run_id=data.get("run_id", "unknown"),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat())),
            fork=data.get("fork", "unknown"),
            summary=VerificationSummary(
                status=ComplianceStatus(data.get("summary", {}).get("status", "UNKNOWN")),
                confidence=data.get("summary", {}).get("confidence", 0.0),
                reason=data.get("summary", {}).get("reason", ""),
            ),
            findings=tuple(),
            metrics=Metrics(),
            decision=VerificationDecision(should_fail_ci=False),
        )

        # Generate report
        generator = JSONReportGenerator()
        format_enum = ReportFormat(format)
        content = await generator.generate(result, format_enum)

        output.write_text(content, encoding="utf-8")
        console.print(f"[green]Report saved to {output}[/green]")

    asyncio.run(run_report())


@app.command()
def status() -> None:
    """Show current configuration and status."""
    settings = get_settings()

    table = Table(title="Configuration Status")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Status", style="yellow")

    # LLM Configuration
    api_key = settings.llm.api_key
    table.add_row(
        "Gemini API Key",
        "***" + api_key[-4:] if api_key else "Not set",
        "" if api_key else "",
    )
    table.add_row("LLM Model", settings.llm.model, "")

    # Vector Store
    table.add_row("ChromaDB Path", settings.vector_store.path, "")

    # GitHub
    github_token = settings.github.token
    table.add_row(
        "GitHub Token",
        "***" + github_token[-4:] if github_token else "Not set",
        "" if github_token else "",
    )

    # General
    table.add_row("Log Level", settings.log_level, "")
    table.add_row("Default Fork", settings.ethereum.default_fork, "")

    console.print(table)


if __name__ == "__main__":
    app()
