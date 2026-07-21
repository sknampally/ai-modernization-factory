"""Render AIMF analysis results as readable console reports."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aimf.models import AnalysisResult, Finding


class ConsoleReporter:
    """Render an AnalysisResult using Rich console components."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def render(self, result: AnalysisResult) -> None:
        """Render the complete analysis report.

        This method is retained for backward compatibility.
        """

        self.render_detailed(result)

    def render_detailed(self, result: AnalysisResult) -> None:
        """Render the complete analysis report."""

        self._render_header()
        self._render_repository(result)
        self._render_technologies(result)
        self._render_build_facts(result)
        self._render_dependency_facts(result)
        self._render_findings(result)
        self._render_summary(result)

    def render_summary(
        self,
        result: AnalysisResult,
        text_report_path: Path | None = None,
        json_report_path: Path | None = None,
    ) -> None:
        """Render a concise analysis summary."""

        self._render_header()
        self._render_repository_summary(result)
        self._render_technology_summary(result)
        self._render_summary(result)

        if text_report_path is not None or json_report_path is not None:
            self._render_report_locations(
                text_report_path=text_report_path,
                json_report_path=json_report_path,
            )

    def _render_header(self) -> None:
        title = Text("AI Modernization Factory", style="bold")
        subtitle = Text(
            "Deterministic repository analysis",
            style="dim",
        )

        self.console.print(
            Panel.fit(
                Text.assemble(title, "\n", subtitle),
                border_style="blue",
            )
        )

    def _render_repository(self, result: AnalysisResult) -> None:
        repository = result.repository

        table = Table(
            title="Repository",
            show_header=False,
            box=None,
        )
        table.add_column("Field", style="bold")
        table.add_column("Value")

        table.add_row("Name", repository.name)
        table.add_row("Path", str(repository.path))
        table.add_row("Files scanned", str(len(repository.files)))

        self.console.print(table)
        self.console.print()

    def _render_repository_summary(
        self,
        result: AnalysisResult,
    ) -> None:
        repository = result.repository

        table = Table(
            title="Repository",
            show_header=False,
            box=None,
        )
        table.add_column("Field", style="bold")
        table.add_column("Value")

        table.add_row("Name", repository.name)
        table.add_row("Files scanned", str(len(repository.files)))

        build = result.facts.build

        if build is not None:
            table.add_row(
                "Build systems",
                self._join_or_default(build.build_systems),
            )

        dependencies = result.facts.dependencies

        if dependencies is not None:
            table.add_row(
                "Dependencies",
                str(dependencies.direct_dependency_count),
            )

        self.console.print(table)
        self.console.print()

    def _render_technologies(self, result: AnalysisResult) -> None:
        table = Table(title="Technologies")
        table.add_column("Technology", style="bold")
        table.add_column("Category")
        table.add_column("Confidence", justify="right")

        for technology in result.technologies:
            table.add_row(
                technology.name,
                self._display_value(technology.category),
                f"{technology.confidence:.0%}",
            )

        if result.technologies:
            self.console.print(table)
        else:
            self.console.print(
                Panel(
                    "No technologies detected.",
                    title="Technologies",
                )
            )

        self.console.print()

    def _render_technology_summary(
        self,
        result: AnalysisResult,
    ) -> None:
        if not result.technologies:
            self.console.print(
                Panel(
                    "No technologies detected.",
                    title="Technologies",
                )
            )
            self.console.print()
            return

        technologies = ", ".join(
            technology.name
            for technology in result.technologies
        )

        self.console.print(
            Panel(
                technologies,
                title="Technologies",
            )
        )
        self.console.print()

    def _render_build_facts(self, result: AnalysisResult) -> None:
        build = result.facts.build

        if build is None:
            return

        table = Table(
            title="Build",
            show_header=False,
            box=None,
        )
        table.add_column("Field", style="bold")
        table.add_column("Value")

        table.add_row(
            "Build systems",
            self._join_or_default(build.build_systems),
        )
        table.add_row(
            "Build files",
            self._join_or_default(build.build_files),
        )
        table.add_row(
            "Packaging",
            self._join_or_default(build.packaging_types),
        )
        table.add_row(
            "Modules",
            str(len(build.modules)),
        )
        table.add_row(
            "Multi-module",
            "Yes" if build.multi_module else "No",
        )

        java_versions = list(
            dict.fromkeys(
                [
                    *build.java_source_versions,
                    *build.java_target_versions,
                ]
            )
        )

        table.add_row(
            "Java versions",
            self._join_or_default(java_versions),
        )
        table.add_row(
            "Commands",
            self._join_or_default(build.inferred_commands),
        )

        self.console.print(table)
        self.console.print()

    def _render_dependency_facts(
        self,
        result: AnalysisResult,
    ) -> None:
        dependencies = result.facts.dependencies

        if dependencies is None:
            return

        table = Table(
            title="Dependencies",
            show_header=False,
            box=None,
        )
        table.add_column("Field", style="bold")
        table.add_column("Value")

        table.add_row(
            "Manifests",
            str(
                sum(
                    not manifest.lockfile
                    for manifest in dependencies.manifests
                )
            ),
        )
        table.add_row(
            "Lockfiles",
            str(
                sum(
                    manifest.lockfile
                    for manifest in dependencies.manifests
                )
            ),
        )
        table.add_row(
            "Direct dependencies",
            str(dependencies.direct_dependency_count),
        )
        table.add_row(
            "Development dependencies",
            str(dependencies.development_dependency_count),
        )
        table.add_row(
            "Test dependencies",
            str(dependencies.test_dependency_count),
        )
        table.add_row(
            "Frameworks",
            self._join_or_default(
                dependencies.framework_dependencies
            ),
        )
        table.add_row(
            "Database libraries",
            self._join_or_default(
                dependencies.database_drivers
            ),
        )
        table.add_row(
            "Cloud SDKs",
            self._join_or_default(dependencies.cloud_sdks),
        )
        table.add_row(
            "Testing libraries",
            self._join_or_default(
                dependencies.testing_libraries
            ),
        )

        self.console.print(table)
        self.console.print()

    def _render_findings(self, result: AnalysisResult) -> None:
        if not result.findings:
            self.console.print(
                Panel(
                    "[green]No deterministic findings detected.[/green]",
                    title="Findings",
                    border_style="green",
                )
            )
            self.console.print()
            return

        table = Table(title="Findings")
        table.add_column("Severity", style="bold")
        table.add_column("Rule")
        table.add_column("Finding")
        table.add_column("Evidence")

        sorted_findings = sorted(
            result.findings,
            key=self._finding_sort_key,
        )

        for finding in sorted_findings:
            severity = self._display_value(finding.severity)

            table.add_row(
                self._severity_text(severity),
                finding.rule_id or "",
                finding.title,
                self._format_evidence(finding),
            )

        self.console.print(table)
        self.console.print()

    def _format_evidence(
        self,
        finding: Finding,
        maximum_items: int = 5,
    ) -> str:
        if not finding.evidence:
            return finding.description

        rendered: list[str] = []

        for item in finding.evidence[:maximum_items]:
            if item.detected_value:
                rendered.append(
                    f"{item.file_path}: {item.detected_value}"
                )
            elif item.description:
                rendered.append(
                    f"{item.file_path}: {item.description}"
                )
            else:
                rendered.append(item.file_path)

        remaining = len(finding.evidence) - maximum_items

        if remaining > 0:
            rendered.append(f"... and {remaining} more")

        return "\n".join(rendered)

    def _render_summary(self, result: AnalysisResult) -> None:
        severity_counts = Counter(
            self._display_value(finding.severity)
            for finding in result.findings
        )

        table = Table(
            title="Summary",
            show_header=False,
            box=None,
        )
        table.add_column("Severity", style="bold")
        table.add_column("Count", justify="right")

        for severity in (
            "critical",
            "high",
            "medium",
            "low",
            "info",
        ):
            table.add_row(
                self._severity_text(severity),
                str(severity_counts.get(severity, 0)),
            )

        table.add_row("Total", str(len(result.findings)))

        self.console.print(table)
        self.console.print()

    def _render_report_locations(
        self,
        text_report_path: Path | None,
        json_report_path: Path | None,
    ) -> None:
        table = Table(
            title="Generated Reports",
            show_header=False,
            box=None,
        )
        table.add_column("Format", style="bold")
        table.add_column("Path")

        if text_report_path is not None:
            table.add_row(
                "Text",
                str(text_report_path),
            )

        if json_report_path is not None:
            table.add_row(
                "JSON",
                str(json_report_path),
            )

        self.console.print(table)

    def _finding_sort_key(
        self,
        finding: Finding,
    ) -> tuple[int, str]:
        severity_order = {
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 3,
            "info": 4,
        }

        severity = self._display_value(finding.severity)

        return (
            severity_order.get(severity, 99),
            finding.rule_id or "",
        )

    def _severity_text(self, severity: str) -> Text:
        styles = {
            "critical": "bold red",
            "high": "red",
            "medium": "yellow",
            "low": "cyan",
            "info": "blue",
        }

        return Text(
            severity.upper(),
            style=styles.get(severity, "white"),
        )

    def _display_value(self, value: Any) -> str:
        raw_value = getattr(value, "value", value)
        return str(raw_value).lower()

    def _join_or_default(
        self,
        values: list[str],
        default: str = "None detected",
    ) -> str:
        if not values:
            return default

        return ", ".join(values)