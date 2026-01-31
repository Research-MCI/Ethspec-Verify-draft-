"""Use case for generating verification reports.

This use case orchestrates report generation in various formats.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from src.core.entities.verification_result import VerificationResult
    from src.core.interfaces.report_generator import ReportFormat


class ReportGeneratorProtocol(Protocol):
    """Protocol for report generator dependency."""

    async def generate(
        self,
        result: VerificationResult,
        format: ReportFormat,
    ) -> str: ...

    async def generate_to_file(
        self,
        result: VerificationResult,
        output_path: Path,
        format: ReportFormat,
    ) -> None: ...

    async def generate_pr_comment(
        self,
        result: VerificationResult,
    ) -> str: ...

    async def generate_summary(
        self,
        result: VerificationResult,
    ) -> str: ...

    async def generate_sarif(
        self,
        result: VerificationResult,
    ) -> dict: ...


@dataclass
class GenerateReportResult:
    """Result from report generation.

    Attributes:
        content: The generated report content
        format: The report format
        output_path: Path where report was saved (if file output)
        is_success: Whether generation was successful
        error_message: Error message if generation failed
    """

    content: str | None
    format: str
    output_path: str | None
    is_success: bool
    error_message: str | None = None


class GenerateReportUseCase:
    """Use case for generating verification reports.

    This use case supports multiple output formats:
    - JSON: Structured data for programmatic consumption
    - Markdown: Human-readable reports
    - HTML: Web-viewable reports
    - SARIF: GitHub code scanning integration
    - PR Comment: GitHub pull request comments
    """

    def __init__(
        self,
        report_generator: ReportGeneratorProtocol,
    ) -> None:
        """Initialize the use case with required dependencies.

        Args:
            report_generator: Report generation implementation
        """
        self._report_generator = report_generator

    async def execute(
        self,
        result: VerificationResult,
        format: ReportFormat,
        output_path: Path | None = None,
    ) -> GenerateReportResult:
        """Execute report generation.

        Args:
            result: The verification result to report
            format: Output format for the report
            output_path: Optional path to save the report

        Returns:
            GenerateReportResult containing the report or error
        """
        try:
            # Generate the report content
            content = await self._report_generator.generate(result, format)

            # Save to file if path provided
            if output_path:
                await self._report_generator.generate_to_file(result, output_path, format)

            return GenerateReportResult(
                content=content,
                format=format.value,
                output_path=str(output_path) if output_path else None,
                is_success=True,
            )

        except Exception as e:
            return GenerateReportResult(
                content=None,
                format=format.value,
                output_path=None,
                is_success=False,
                error_message=f"Report generation failed: {e}",
            )

    async def execute_pr_comment(
        self,
        result: VerificationResult,
    ) -> GenerateReportResult:
        """Generate a GitHub PR comment.

        Args:
            result: The verification result

        Returns:
            GenerateReportResult containing the comment markdown
        """
        try:
            content = await self._report_generator.generate_pr_comment(result)

            return GenerateReportResult(
                content=content,
                format="pr_comment",
                output_path=None,
                is_success=True,
            )

        except Exception as e:
            return GenerateReportResult(
                content=None,
                format="pr_comment",
                output_path=None,
                is_success=False,
                error_message=f"PR comment generation failed: {e}",
            )

    async def execute_summary(
        self,
        result: VerificationResult,
    ) -> GenerateReportResult:
        """Generate a brief summary.

        Args:
            result: The verification result

        Returns:
            GenerateReportResult containing the summary
        """
        try:
            content = await self._report_generator.generate_summary(result)

            return GenerateReportResult(
                content=content,
                format="summary",
                output_path=None,
                is_success=True,
            )

        except Exception as e:
            return GenerateReportResult(
                content=None,
                format="summary",
                output_path=None,
                is_success=False,
                error_message=f"Summary generation failed: {e}",
            )

    async def execute_sarif(
        self,
        result: VerificationResult,
        output_path: Path | None = None,
    ) -> GenerateReportResult:
        """Generate SARIF format for GitHub code scanning.

        Args:
            result: The verification result
            output_path: Optional path to save the SARIF file

        Returns:
            GenerateReportResult containing the SARIF data
        """
        import json

        try:
            sarif_data = await self._report_generator.generate_sarif(result)
            content = json.dumps(sarif_data, indent=2)

            if output_path:
                output_path.write_text(content, encoding="utf-8")

            return GenerateReportResult(
                content=content,
                format="sarif",
                output_path=str(output_path) if output_path else None,
                is_success=True,
            )

        except Exception as e:
            return GenerateReportResult(
                content=None,
                format="sarif",
                output_path=None,
                is_success=False,
                error_message=f"SARIF generation failed: {e}",
            )
