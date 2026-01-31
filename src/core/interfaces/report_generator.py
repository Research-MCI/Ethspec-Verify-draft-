"""Report generator interface for verification output.

This module defines the abstract interface for generating verification reports.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from src.core.entities.verification_result import VerificationResult


class ReportFormat(str, Enum):
    """Supported report formats."""

    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    SARIF = "sarif"  # Static Analysis Results Interchange Format


class ReportGenerator(ABC):
    """Abstract interface for report generation implementations.

    Implementations should handle generating verification reports in
    various formats for different consumers (CI/CD, humans, tools).
    """

    @abstractmethod
    async def generate(
        self,
        result: VerificationResult,
        format: ReportFormat = ReportFormat.JSON,
    ) -> str:
        """Generate a report from verification results.

        Args:
            result: The verification result to report
            format: Output format for the report

        Returns:
            Report content as string
        """
        ...

    @abstractmethod
    async def generate_to_file(
        self,
        result: VerificationResult,
        output_path: Path,
        format: ReportFormat = ReportFormat.JSON,
    ) -> None:
        """Generate a report and save to file.

        Args:
            result: The verification result to report
            output_path: Path to save the report
            format: Output format for the report
        """
        ...

    @abstractmethod
    async def generate_pr_comment(
        self,
        result: VerificationResult,
    ) -> str:
        """Generate a GitHub PR comment from verification results.

        Args:
            result: The verification result

        Returns:
            Markdown formatted comment for GitHub PR
        """
        ...

    @abstractmethod
    async def generate_summary(
        self,
        result: VerificationResult,
    ) -> str:
        """Generate a brief summary of verification results.

        Args:
            result: The verification result

        Returns:
            Brief summary string
        """
        ...

    @abstractmethod
    async def generate_sarif(
        self,
        result: VerificationResult,
    ) -> dict:
        """Generate SARIF format for GitHub code scanning.

        Args:
            result: The verification result

        Returns:
            SARIF-formatted dictionary
        """
        ...
