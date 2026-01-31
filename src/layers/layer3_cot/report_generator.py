"""Report generator for verification results.

This module generates reports in various formats from verification results.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.core.interfaces.report_generator import ReportFormat, ReportGenerator
from src.shared.constants import SARIF_SCHEMA_URI, SARIF_SCHEMA_VERSION
from src.shared.logger import LoggerMixin

if TYPE_CHECKING:
    from src.core.entities.verification_result import VerificationResult


class JSONReportGenerator(ReportGenerator, LoggerMixin):
    """Generates verification reports in various formats."""

    def __init__(self) -> None:
        """Initialize the report generator."""
        pass

    async def generate(
        self,
        result: VerificationResult,
        format: ReportFormat = ReportFormat.JSON,
    ) -> str:
        """Generate a report from verification results.

        Args:
            result: The verification result
            format: Output format

        Returns:
            Report content as string
        """
        if format == ReportFormat.JSON:
            return self._generate_json(result)
        elif format == ReportFormat.MARKDOWN:
            return self._generate_markdown(result)
        elif format == ReportFormat.HTML:
            return self._generate_html(result)
        elif format == ReportFormat.SARIF:
            sarif = await self.generate_sarif(result)
            return json.dumps(sarif, indent=2)
        else:
            return self._generate_json(result)

    async def generate_to_file(
        self,
        result: VerificationResult,
        output_path: Path,
        format: ReportFormat = ReportFormat.JSON,
    ) -> None:
        """Generate and save report to file.

        Args:
            result: Verification result
            output_path: Output file path
            format: Output format
        """
        content = await self.generate(result, format)
        output_path.write_text(content, encoding="utf-8")
        self.logger.info("report_saved", path=str(output_path), format=format.value)

    async def generate_pr_comment(
        self,
        result: VerificationResult,
    ) -> str:
        """Generate GitHub PR comment.

        Args:
            result: Verification result

        Returns:
            Markdown comment
        """
        lines = []

        # Header with status
        status_emoji = self._get_status_emoji(result.summary.status.value)
        lines.append(f"## {status_emoji} Specification Compliance Check")
        lines.append("")

        # Summary
        lines.append(f"**Status**: {result.summary.status.value}")
        lines.append(f"**Confidence**: {result.summary.confidence:.0%}")
        lines.append(f"**Fork**: {result.fork}")
        lines.append("")

        if result.summary.reason:
            lines.append(f"> {result.summary.reason}")
            lines.append("")

        # Findings summary
        if result.findings:
            lines.append("### Findings")
            lines.append("")

            # Group by severity
            by_severity: dict[str, list] = {}
            for finding in result.findings[:20]:  # Limit to 20
                sev = finding.severity.value
                if sev not in by_severity:
                    by_severity[sev] = []
                by_severity[sev].append(finding)

            for severity in ["critical", "high", "medium", "low", "info"]:
                if severity in by_severity:
                    lines.append(f"#### {severity.title()} ({len(by_severity[severity])})")
                    for finding in by_severity[severity][:5]:
                        conf = f"{finding.confidence:.0%}"
                        lines.append(f"- **{finding.title}** (confidence: {conf})")
                        if finding.description:
                            lines.append(f"  - {finding.description[:200]}")
                    lines.append("")
        else:
            lines.append("### No Issues Found ")
            lines.append("")

        # Decision
        if result.decision.should_fail_ci:
            lines.append("---")
            lines.append(f" **CI Blocked**: {result.decision.blocking_reason}")
            lines.append("")

        # Footer
        lines.append("---")
        lines.append(f"*Run ID: `{result.run_id}` | Generated: {result.timestamp.isoformat()}*")

        return "\n".join(lines)

    async def generate_summary(
        self,
        result: VerificationResult,
    ) -> str:
        """Generate brief summary.

        Args:
            result: Verification result

        Returns:
            Brief summary string
        """
        status = result.summary.status.value
        confidence = result.summary.confidence
        findings_count = len(result.findings)
        blocking = len(result.blocking_findings)

        parts = [
            f"Status: {status}",
            f"Confidence: {confidence:.0%}",
            f"Findings: {findings_count}",
        ]

        if blocking > 0:
            parts.append(f"Blocking: {blocking}")

        return " | ".join(parts)

    async def generate_sarif(
        self,
        result: VerificationResult,
    ) -> dict:
        """Generate SARIF format.

        Args:
            result: Verification result

        Returns:
            SARIF dictionary
        """
        sarif: dict[str, Any] = {
            "$schema": SARIF_SCHEMA_URI,
            "version": SARIF_SCHEMA_VERSION,
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "eth-spec-compliance-verifier",
                            "version": "0.1.0",
                            "informationUri": "https://github.com/your-org/eth-spec-compliance-verifier",
                            "rules": self._generate_sarif_rules(result),
                        }
                    },
                    "results": self._generate_sarif_results(result),
                    "invocations": [
                        {
                            "executionSuccessful": True,
                            "endTimeUtc": result.timestamp.isoformat() + "Z",
                        }
                    ],
                }
            ],
        }

        return sarif

    def _generate_json(self, result: VerificationResult) -> str:
        """Generate JSON report.

        Args:
            result: Verification result

        Returns:
            JSON string
        """
        return json.dumps(result.to_dict(), indent=2, default=str)

    def _generate_markdown(self, result: VerificationResult) -> str:
        """Generate Markdown report.

        Args:
            result: Verification result

        Returns:
            Markdown string
        """
        lines = []

        lines.append("# Specification Compliance Report")
        lines.append("")
        lines.append(f"**Run ID**: `{result.run_id}`")
        lines.append(f"**Timestamp**: {result.timestamp.isoformat()}")
        lines.append(f"**Fork**: {result.fork}")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Status | {result.summary.status.value} |")
        lines.append(f"| Confidence | {result.summary.confidence:.0%} |")
        lines.append(f"| Total Requirements | {result.summary.total_requirements} |")
        lines.append(f"| Passed | {result.summary.passed_requirements} |")
        lines.append(f"| Failed | {result.summary.failed_requirements} |")
        lines.append(f"| Ambiguous | {result.summary.ambiguous_requirements} |")
        lines.append("")

        if result.summary.reason:
            lines.append(f"> {result.summary.reason}")
            lines.append("")

        # Findings
        if result.findings:
            lines.append("## Findings")
            lines.append("")

            for finding in result.findings:
                lines.append(f"### {finding.finding_id}: {finding.title}")
                lines.append("")
                lines.append(f"- **Severity**: {finding.severity.value}")
                lines.append(f"- **Category**: {finding.category.value}")
                lines.append(f"- **Confidence**: {finding.confidence:.0%}")

                if finding.code_location:
                    lines.append(f"- **Location**: `{finding.code_location}`")
                if finding.requirement_id:
                    lines.append(f"- **Requirement**: {finding.requirement_id}")

                lines.append("")
                lines.append(finding.description)
                lines.append("")

                if finding.evidence:
                    lines.append("**Evidence:**")
                    for ev in finding.evidence:
                        lines.append(f"- {ev}")
                    lines.append("")

                if finding.recommendation:
                    lines.append(f"**Recommendation**: {finding.recommendation}")
                    lines.append("")

        # Metrics
        lines.append("## Metrics")
        lines.append("")
        metrics = result.metrics
        lines.append(f"- Verification Time: {metrics.verification_time_seconds:.2f}s")
        lines.append(f"- LLM Calls: {metrics.llm_calls}")
        lines.append(f"- Tokens Used: {metrics.tokens_used}")
        lines.append("")

        # Decision
        lines.append("## Decision")
        lines.append("")
        lines.append(f"- **Should Fail CI**: {result.decision.should_fail_ci}")
        if result.decision.blocking_reason:
            lines.append(f"- **Reason**: {result.decision.blocking_reason}")
        lines.append(f"- **Requires Human Review**: {result.decision.requires_human_review}")

        return "\n".join(lines)

    def _generate_html(self, result: VerificationResult) -> str:
        """Generate HTML report.

        Args:
            result: Verification result

        Returns:
            HTML string
        """
        # Simple HTML generation - could be enhanced with templates
        md_content = self._generate_markdown(result)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Specification Compliance Report - {result.run_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #555; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
        table {{ border-collapse: collapse; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f5f5f5; }}
        pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 4px; }}
        .critical {{ color: #d9534f; }}
        .high {{ color: #f0ad4e; }}
        .medium {{ color: #5bc0de; }}
        .low {{ color: #5cb85c; }}
    </style>
</head>
<body>
<pre>{md_content}</pre>
</body>
</html>"""

        return html

    def _generate_sarif_rules(self, result: VerificationResult) -> list[dict]:
        """Generate SARIF rules from findings.

        Args:
            result: Verification result

        Returns:
            List of rule dictionaries
        """
        rules = []
        seen_categories = set()

        for finding in result.findings:
            category = finding.category.value
            if category not in seen_categories:
                seen_categories.add(category)
                rules.append({
                    "id": category,
                    "name": category.replace("_", " ").title(),
                    "shortDescription": {"text": f"Specification compliance: {category}"},
                    "defaultConfiguration": {
                        "level": self._sarif_level(finding.severity.value)
                    },
                })

        return rules

    def _generate_sarif_results(self, result: VerificationResult) -> list[dict]:
        """Generate SARIF results from findings.

        Args:
            result: Verification result

        Returns:
            List of result dictionaries
        """
        results = []

        for finding in result.findings:
            sarif_result: dict[str, Any] = {
                "ruleId": finding.category.value,
                "level": self._sarif_level(finding.severity.value),
                "message": {"text": f"{finding.title}: {finding.description}"},
            }

            if finding.code_location:
                sarif_result["locations"] = [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": finding.code_location}
                        }
                    }
                ]

            results.append(sarif_result)

        return results

    def _sarif_level(self, severity: str) -> str:
        """Convert severity to SARIF level.

        Args:
            severity: Severity string

        Returns:
            SARIF level
        """
        mapping = {
            "critical": "error",
            "high": "error",
            "medium": "warning",
            "low": "note",
            "info": "note",
        }
        return mapping.get(severity, "warning")

    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for status.

        Args:
            status: Status string

        Returns:
            Emoji character
        """
        mapping = {
            "PASS": "",
            "FAIL": "",
            "PARTIAL": "",
            "UNKNOWN": "",
            "PENDING": "",
        }
        return mapping.get(status, "")
