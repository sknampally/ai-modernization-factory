"""Render AIMF analysis results as readable console reports."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aimf.models import AnalysisResult, Finding, Priority, Recommendation


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
        """Render the complete detailed analysis report."""

        self._render_header()
        self._render_repository(result)
        self._render_technologies(result)
        self._render_repository_facts(result)
        self._render_build_facts(result)
        self._render_dependency_facts(result)
        self._render_findings(result)
        self._render_recommendations(result)
        self._render_prioritized_roadmap(result)
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
        self._render_recommendation_summary(result)
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
        table.add_column("Value", overflow="fold")

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
        table.add_column("Value", overflow="fold")

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
        table.add_column("Technology", style="bold", overflow="fold")
        table.add_column("Category", overflow="fold")
        table.add_column("Confidence", justify="right")

        for technology in result.technologies:
            confidence = (
                f"{technology.confidence:.0%}" if technology.confidence is not None else "Unknown"
            )

            table.add_row(
                technology.name,
                self._display_value(technology.category),
                confidence,
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

        technologies = ", ".join(technology.name for technology in result.technologies)

        self.console.print(
            Panel(
                technologies,
                title="Technologies",
            )
        )
        self.console.print()

    def _render_repository_facts(self, result: AnalysisResult) -> None:
        """Render a concise normalized repository facts section."""

        facts = result.facts
        rows: list[tuple[str, str]] = []

        structure = facts.structure
        if structure is not None:
            if structure.file_count is not None:
                rows.append(("File count", str(structure.file_count)))
            if structure.source_file_count is not None:
                rows.append(("Source files", str(structure.source_file_count)))
            if structure.test_file_count is not None:
                rows.append(("Test files", str(structure.test_file_count)))
            if structure.application_count is not None:
                rows.append(("Applications", str(structure.application_count)))
            if structure.has_tests is not None:
                rows.append(("Has tests", "Yes" if structure.has_tests else "No"))
            if structure.architecture_layers:
                rows.append(
                    (
                        "Architecture layers",
                        self._join_or_default(structure.architecture_layers),
                    )
                )

        technology = facts.technology
        if technology is not None:
            if technology.programming_languages:
                rows.append(
                    (
                        "Languages",
                        self._join_or_default(technology.programming_languages),
                    )
                )
            if technology.frameworks:
                rows.append(
                    (
                        "Frameworks",
                        self._join_or_default(technology.frameworks),
                    )
                )
            if technology.build_tools:
                rows.append(
                    (
                        "Build tools",
                        self._join_or_default(technology.build_tools),
                    )
                )
            if technology.test_frameworks:
                rows.append(
                    (
                        "Test frameworks",
                        self._join_or_default(technology.test_frameworks),
                    )
                )

        dependencies = facts.dependencies
        if dependencies is not None:
            rows.append(
                (
                    "Dependency count",
                    str(dependencies.dependency_count or dependencies.direct_dependency_count),
                )
            )
            if dependencies.outdated_dependencies:
                rows.append(
                    (
                        "Outdated dependencies",
                        self._join_or_default(dependencies.outdated_dependencies),
                    )
                )

        cicd = facts.cicd
        if cicd is not None:
            platforms = cicd.ci_platforms or cicd.providers
            if platforms:
                rows.append(("CI platforms", self._join_or_default(platforms)))
            rows.append(("Has CI", "Yes" if cicd.has_ci else "No"))
            rows.append(
                (
                    "Deployment workflow",
                    "Yes" if cicd.has_deployment_workflow else "No",
                )
            )

        security = facts.security
        if security is not None:
            if security.sensitive_file_count is not None:
                rows.append(
                    (
                        "Sensitive files",
                        str(security.sensitive_file_count),
                    )
                )
            if security.secret_finding_count is not None:
                rows.append(
                    (
                        "Secret findings",
                        str(security.secret_finding_count),
                    )
                )
            if security.weak_crypto_count is not None:
                rows.append(
                    (
                        "Weak crypto findings",
                        str(security.weak_crypto_count),
                    )
                )
            if security.dangerous_execution_count is not None:
                rows.append(
                    (
                        "Dangerous execution findings",
                        str(security.dangerous_execution_count),
                    )
                )

        cloud = facts.cloud
        if cloud is not None:
            if cloud.cloud_capabilities:
                rows.append(
                    (
                        "Cloud capabilities",
                        self._join_or_default(cloud.cloud_capabilities),
                    )
                )
            for label, flag in (
                ("Docker", cloud.has_docker),
                ("Docker Compose", cloud.has_docker_compose),
                ("Kubernetes", cloud.has_kubernetes),
                ("Helm", cloud.has_helm),
                ("Terraform", cloud.has_terraform),
                ("CloudFormation", cloud.has_cloudformation),
                ("Serverless", cloud.has_serverless),
            ):
                if flag is not None:
                    rows.append((label, "Yes" if flag else "No"))

        architecture = facts.architecture
        if architecture is not None:
            for label, flag in (
                ("API layer", architecture.has_api_layer),
                ("Service layer", architecture.has_service_layer),
                ("Persistence layer", architecture.has_persistence_layer),
                ("Domain layer", architecture.has_domain_layer),
                ("Multi-application", architecture.is_multi_application),
            ):
                if flag is not None:
                    rows.append((label, "Yes" if flag else "No"))

        if not rows:
            return

        table = Table(
            title="Repository Facts",
            show_header=False,
            box=None,
        )
        table.add_column("Field", style="bold")
        table.add_column("Value", overflow="fold")

        for field_name, field_value in rows:
            table.add_row(field_name, field_value)

        self.console.print(table)
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
        table.add_column("Value", overflow="fold")

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
        table.add_column("Value", overflow="fold")

        table.add_row(
            "Manifests",
            str(sum(not manifest.lockfile for manifest in dependencies.manifests)),
        )
        table.add_row(
            "Lockfiles",
            str(sum(manifest.lockfile for manifest in dependencies.manifests)),
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
            self._join_or_default(dependencies.framework_dependencies),
        )
        table.add_row(
            "Database libraries",
            self._join_or_default(dependencies.database_drivers),
        )
        table.add_row(
            "Cloud SDKs",
            self._join_or_default(dependencies.cloud_sdks),
        )
        table.add_row(
            "Testing libraries",
            self._join_or_default(dependencies.testing_libraries),
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

        self.console.print(
            Text(
                f"Findings ({len(result.findings)})",
                style="bold",
            )
        )
        self.console.print()

        sorted_findings = sorted(
            result.findings,
            key=self._finding_sort_key,
        )

        for finding in sorted_findings:
            self._render_finding(finding)

    def _render_finding(self, finding: Finding) -> None:
        severity = self._display_value(finding.severity)

        heading = Text()
        heading.append_text(self._severity_text(severity))
        heading.append("  ")
        heading.append(
            finding.rule_id or "No rule ID",
            style="bold",
        )
        heading.append("  ")
        heading.append(
            finding.title,
            style="bold",
        )

        details: list[Text] = []

        if finding.description:
            description = Text()
            description.append("Description: ", style="bold")
            description.append(finding.description)
            details.append(description)

        category = Text()
        category.append("Category: ", style="bold")
        category.append(self._display_value(finding.category))
        details.append(category)

        source = Text()
        source.append("Source: ", style="bold")
        source.append(self._display_value(finding.source))
        details.append(source)

        if finding.affected_technologies:
            technologies = Text()
            technologies.append(
                "Affected technologies: ",
                style="bold",
            )
            technologies.append(", ".join(finding.affected_technologies))
            details.append(technologies)

        evidence_renderables = self._finding_evidence(finding)

        panel_content = Group(
            *details,
            Text(),
            *evidence_renderables,
        )

        self.console.print(
            Panel(
                panel_content,
                title=heading,
                title_align="left",
                border_style=self._severity_style(severity),
                expand=True,
            )
        )

    def _finding_evidence(
        self,
        finding: Finding,
    ) -> list[Text]:
        if not finding.evidence:
            no_evidence = Text()
            no_evidence.append("Evidence: ", style="bold")
            no_evidence.append("No structured evidence provided.")
            return [no_evidence]

        rendered: list[Text] = [
            Text("Evidence:", style="bold"),
        ]

        for index, item in enumerate(
            finding.evidence,
            start=1,
        ):
            evidence = Text()
            evidence.append(f"  {index}. ", style="dim")
            evidence.append(item.file_path, style="bold")

            if item.line_number is not None:
                evidence.append(f":{item.line_number}")

                if item.end_line_number is not None and item.end_line_number != item.line_number:
                    evidence.append(f"-{item.end_line_number}")

            rendered.append(evidence)

            if item.detected_value:
                detected_value = Text()
                detected_value.append(
                    "     Detected value: ",
                    style="bold",
                )
                detected_value.append(item.detected_value)
                rendered.append(detected_value)

            if item.description:
                description = Text()
                description.append(
                    "     Description: ",
                    style="bold",
                )
                description.append(item.description)
                rendered.append(description)

            if item.snippet:
                snippet = Text()
                snippet.append(
                    "     Snippet: ",
                    style="bold",
                )
                snippet.append(item.snippet)
                rendered.append(snippet)

        return rendered

    def _render_summary(self, result: AnalysisResult) -> None:
        severity_counts = Counter(
            self._display_value(finding.severity) for finding in result.findings
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

    def _render_recommendation_summary(
        self,
        result: AnalysisResult,
    ) -> None:
        recommendations = result.recommendations

        priority_counts = Counter(
            self._display_value(recommendation.priority) for recommendation in recommendations
        )

        counts_table = Table(
            title="Recommendations by Priority",
            show_header=False,
            box=None,
        )
        counts_table.add_column("Priority", style="bold")
        counts_table.add_column("Count", justify="right")

        for priority in ("critical", "high", "medium", "low"):
            counts_table.add_row(
                priority.upper(),
                str(priority_counts.get(priority, 0)),
            )

        counts_table.add_row("Total", str(len(recommendations)))
        self.console.print(counts_table)
        self.console.print()

        if not recommendations:
            return

        top_recommendations = recommendations[:5]

        self.console.print(
            Text(
                f"Top Recommendations ({len(top_recommendations)})",
                style="bold",
            )
        )
        self.console.print()

        for recommendation in top_recommendations:
            self._render_recommendation(recommendation, compact=True)

    def _render_recommendations(self, result: AnalysisResult) -> None:
        recommendations = result.recommendations

        if not recommendations:
            self.console.print(
                Panel(
                    "[green]No modernization recommendations generated.[/green]",
                    title="Modernization Recommendations",
                    border_style="green",
                )
            )
            self.console.print()
            return

        self.console.print(
            Text(
                f"Modernization Recommendations ({len(recommendations)})",
                style="bold",
            )
        )
        self.console.print()

        for recommendation in recommendations:
            self._render_recommendation(recommendation, compact=False)

    def _render_prioritized_roadmap(self, result: AnalysisResult) -> None:
        recommendations = result.recommendations

        groups = {
            "Immediate": [
                recommendation
                for recommendation in recommendations
                if recommendation.priority in {Priority.CRITICAL, Priority.HIGH}
            ],
            "Near term": [
                recommendation
                for recommendation in recommendations
                if recommendation.priority == Priority.MEDIUM
            ],
            "Later": [
                recommendation
                for recommendation in recommendations
                if recommendation.priority == Priority.LOW
            ],
        }

        self.console.print(Text("Prioritized Roadmap", style="bold"))
        self.console.print()

        for group_name, group_recommendations in groups.items():
            if not group_recommendations:
                self.console.print(
                    Panel(
                        "None",
                        title=group_name,
                        border_style="dim",
                    )
                )
                self.console.print()
                continue

            lines = [
                f"{self._display_value(recommendation.priority).upper()}: {recommendation.title}"
                for recommendation in group_recommendations
            ]

            self.console.print(
                Panel(
                    "\n".join(lines),
                    title=group_name,
                    border_style="blue",
                )
            )
            self.console.print()

    def _render_recommendation(
        self,
        recommendation: Recommendation,
        *,
        compact: bool,
    ) -> None:
        priority = self._display_value(recommendation.priority)

        heading = Text()
        heading.append(priority.upper(), style=self._priority_style(priority))
        heading.append("  ")
        heading.append(recommendation.rule_id, style="bold")
        heading.append("  ")
        heading.append(recommendation.title, style="bold")

        details: list[Text] = []

        rationale = Text()
        rationale.append("Rationale: ", style="bold")
        rationale.append(recommendation.rationale)
        details.append(rationale)

        action = Text()
        action.append("Proposed action: ", style="bold")
        action.append(recommendation.description)
        details.append(action)

        if not compact:
            effort = Text()
            effort.append("Effort: ", style="bold")
            effort.append(self._display_value(recommendation.effort))
            details.append(effort)

            risk = Text()
            risk.append("Risk: ", style="bold")
            risk.append(self._display_value(recommendation.risk))
            details.append(risk)

            category = Text()
            category.append("Category: ", style="bold")
            category.append(self._display_value(recommendation.category))
            details.append(category)

            evidence_lines = self._recommendation_evidence(recommendation)
            panel_content = Group(*details, Text(), *evidence_lines)
        else:
            effort = Text()
            effort.append("Effort: ", style="bold")
            effort.append(self._display_value(recommendation.effort))
            details.append(effort)

            risk = Text()
            risk.append("Risk: ", style="bold")
            risk.append(self._display_value(recommendation.risk))
            details.append(risk)

            panel_content = Group(*details)

        self.console.print(
            Panel(
                panel_content,
                title=heading,
                title_align="left",
                border_style=self._priority_style(priority),
                expand=True,
            )
        )

    def _recommendation_evidence(
        self,
        recommendation: Recommendation,
    ) -> list[Text]:
        if not recommendation.evidence:
            no_evidence = Text()
            no_evidence.append("Evidence: ", style="bold")
            no_evidence.append("No structured evidence provided.")
            return [no_evidence]

        rendered: list[Text] = [Text("Evidence:", style="bold")]

        for index, item in enumerate(recommendation.evidence, start=1):
            evidence = Text()
            evidence.append(f"  {index}. ", style="dim")
            evidence.append(item.file_path, style="bold")

            if item.description:
                evidence.append(f" — {item.description}")

            rendered.append(evidence)

        return rendered

    def _priority_style(self, priority: str) -> str:
        styles = {
            "critical": "bold red",
            "high": "red",
            "medium": "yellow",
            "low": "cyan",
        }

        return styles.get(priority, "white")

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
        table.add_column("Path", overflow="fold")

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
        return Text(
            severity.upper(),
            style=self._severity_style(severity),
        )

    def _severity_style(self, severity: str) -> str:
        styles = {
            "critical": "bold red",
            "high": "red",
            "medium": "yellow",
            "low": "cyan",
            "info": "blue",
        }

        return styles.get(severity, "white")

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
