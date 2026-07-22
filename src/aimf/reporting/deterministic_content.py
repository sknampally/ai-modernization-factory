"""HTML fragment builders for deterministic AnalysisResult content.

Ported from HtmlFileReporter presentation logic so ModernizationHTMLReportRenderer
can reuse the same field coverage without becoming a third full-document renderer.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from aimf.models import AnalysisResult, Priority, Recommendation, Severity
from aimf.models.evidence import Evidence
from aimf.reporters.evidence_location import format_evidence_item_location
from aimf.reporters.html_rendering import (
    COLLECTION_COLLAPSE_THRESHOLD,
    escape_and_wrap,
    escape_html,
    render_collection,
    wrap_table,
)


def display_enum(value: Any) -> str:
    """Return a lowercase display string for enum or plain values."""

    raw_value = getattr(value, "value", value)
    return str(raw_value).lower()


def _ruleset_label(item: Any) -> str:
    rulesets = item.command_metadata.get("rulesets") if item.command_metadata else None
    if isinstance(rulesets, list) and rulesets:
        return ", ".join(str(ruleset) for ruleset in rulesets)
    return "—"


def render_deterministic_executive_summary(result: AnalysisResult) -> str:
    """Render the deterministic executive summary section."""

    severity_counts = Counter(finding.severity for finding in result.findings)
    priority_counts = Counter(recommendation.priority for recommendation in result.recommendations)

    severity_rows = "".join(
        (
            "<tr>"
            f"<td>{_severity_badge(severity)}</td>"
            f"<td>{severity_counts.get(severity, 0)}</td>"
            "</tr>"
        )
        for severity in (
            Severity.CRITICAL,
            Severity.HIGH,
            Severity.MEDIUM,
            Severity.LOW,
            Severity.INFO,
        )
    )
    priority_rows = "".join(
        (
            "<tr>"
            f"<td>{_priority_badge(priority)}</td>"
            f"<td>{priority_counts.get(priority, 0)}</td>"
            "</tr>"
        )
        for priority in (
            Priority.CRITICAL,
            Priority.HIGH,
            Priority.MEDIUM,
            Priority.LOW,
        )
    )

    findings_table = wrap_table(
        '<table class="counts">\n'
        "<thead><tr><th>Severity</th><th>Count</th></tr></thead>\n"
        f"<tbody>{severity_rows}</tbody>\n"
        "</table>\n"
    )
    recommendations_table = wrap_table(
        '<table class="counts">\n'
        "<thead><tr><th>Priority</th><th>Count</th></tr></thead>\n"
        f"<tbody>{priority_rows}</tbody>\n"
        "</table>\n"
    )

    return (
        '<section id="executive-summary" '
        'class="section deterministic-section">\n'
        "<h2>Executive Summary</h2>\n"
        '<p class="deterministic-label">Deterministic analysis evidence</p>\n'
        f'<p class="summary-text">{escape_and_wrap(_executive_summary_text(result))}</p>\n'
        f"{_executive_summary_signals(result)}"
        '<div class="summary-grid">\n'
        '<div class="summary-card">\n'
        "<h3>Findings</h3>\n"
        f'<p class="metric">{len(result.findings)}</p>\n'
        f"{findings_table}"
        "</div>\n"
        '<div class="summary-card">\n'
        "<h3>Recommendations</h3>\n"
        f'<p class="metric">{len(result.recommendations)}</p>\n'
        f"{recommendations_table}"
        "</div>\n"
        "</div>\n"
        "</section>\n"
    )


def render_repository_system_intelligence(result: AnalysisResult) -> str:
    """Render repository fact groups as system intelligence."""

    groups = [
        ("Structure", _structure_fact_rows(result)),
        ("Technology", _technology_fact_rows(result)),
        ("Build and Dependencies", _build_dependency_fact_rows(result)),
        ("CI/CD", _cicd_fact_rows(result)),
        ("Security", _security_fact_rows(result)),
        ("Architecture", _architecture_fact_rows(result)),
        ("Cloud Readiness", _cloud_fact_rows(result)),
    ]

    group_html: list[str] = []
    for title, rows in groups:
        if not rows:
            continue
        row_html = "".join(
            f"<tr><th>{escape_html(label)}</th><td>{value}</td></tr>\n" for label, value in rows
        )
        group_html.append(
            f'<div class="fact-group">\n'
            f"<h3>{escape_html(title)}</h3>\n"
            f"{_fact_table(row_html)}"
            f"</div>\n"
        )

    if not group_html:
        body = '<p class="empty">No repository facts were populated.</p>\n'
    else:
        body = '<div class="fact-groups">\n' + "".join(group_html) + "</div>\n"

    return (
        '<section id="repository-intelligence" '
        'class="section deterministic-section">\n'
        "<h2>Repository System Intelligence</h2>\n"
        '<p class="deterministic-label">Deterministic analysis evidence</p>\n'
        f"{body}</section>\n"
    )


def render_static_analysis_providers(result: AnalysisResult) -> str:
    """Render the static analysis provider summary table."""

    if not result.static_analysis_results:
        return (
            '<section id="static-analysis" '
            'class="section deterministic-section provider-summary-section">\n'
            "<h2>Static Analysis</h2>\n"
            '<p class="deterministic-label">Deterministic analysis evidence</p>\n'
            '<p class="empty">Static analysis was not configured or produced no '
            "provider results.</p>\n"
            "</section>\n"
        )

    rows = "".join(_static_analysis_summary_rows(result.static_analysis_results))
    provider_table = wrap_table(
        '<table class="facts provider-summary">\n'
        "<thead><tr>"
        "<th>Provider</th><th>Status</th><th>Profile</th><th>Version</th>"
        "<th>Eligible</th><th>Analyzed</th><th>Raw</th><th>Grouped</th>"
        "<th>Primary</th><th>Supporting</th><th>Info</th><th>HTML summarized</th>"
        "<th>Ruleset</th><th>Duration (ms)</th><th>Notes</th>"
        "</tr></thead>\n"
        f"<tbody>{rows}</tbody>\n"
        "</table>\n",
        css_class="table-wrapper provider-summary-wrapper",
    )

    disclosure = ""
    if any(item.suppressed_from_html_count > 0 for item in result.static_analysis_results):
        disclosure = (
            '<p class="static-analysis-disclosure">'
            "Some low-value or repetitive static-analysis observations are retained "
            "in the JSON assessment but summarized or omitted from the customer-facing "
            "HTML."
            "</p>\n"
        )

    return (
        '<section id="static-analysis" '
        'class="section deterministic-section provider-summary-section">\n'
        "<h2>Static Analysis</h2>\n"
        '<p class="deterministic-label">Deterministic analysis evidence</p>\n'
        f"{provider_table}"
        f"{disclosure}"
        "</section>\n"
    )


def _static_analysis_summary_rows(results: list[Any]) -> list[str]:
    rows: list[str] = []
    for item in results:
        rows.append(
            "<tr>"
            f'<td class="technical-value">{escape_and_wrap(item.provider_name)}</td>'
            f"<td>{escape_html(item.status.value)}</td>"
            f'<td class="technical-value">'
            f"{escape_and_wrap(item.profile or item.command_metadata.get('profile') or '—')}"
            "</td>"
            f'<td class="technical-value">'
            f"{escape_and_wrap(item.provider_version or '—')}"
            "</td>"
            f"<td>{item.eligible_file_count}</td>"
            f"<td>{item.files_analyzed}</td>"
            f"<td>{item.raw_observation_count}</td>"
            f"<td>{item.grouped_finding_count}</td>"
            f"<td>{item.primary_count}</td>"
            f"<td>{item.supporting_count}</td>"
            f"<td>{item.informational_count}</td>"
            f"<td>{item.suppressed_from_html_count}</td>"
            f'<td class="technical-value">'
            f"{escape_and_wrap(_ruleset_label(item))}"
            "</td>"
            f"<td>"
            f"{escape_html(str(item.duration_ms) if item.duration_ms is not None else '—')}"
            f"</td>"
            f'<td class="technical-value">'
            f"{escape_and_wrap(item.error_message or '; '.join(item.warnings) or '—')}"
            "</td>"
            "</tr>\n"
        )
    return rows


def render_deterministic_recommendations(result: AnalysisResult) -> str:
    """Render recommendation cards and a priority plan.

    Related recommendations are grouped by category for executive readability
    while preserving every deterministic recommendation in JSON.
    """

    if not result.recommendations:
        cards = '<p class="empty">No deterministic recommendations were generated.</p>\n'
    else:
        by_category: dict[str, list[Recommendation]] = {}
        for recommendation in result.recommendations:
            category = str(getattr(recommendation.category, "value", recommendation.category))
            by_category.setdefault(category, []).append(recommendation)
        sections: list[str] = []
        for category in sorted(by_category.keys(), key=str.lower):
            group = by_category[category]
            label = escape_and_wrap(category.replace("_", " ").title())
            heading = f'<h3 class="recommendation-group">{label} ({len(group)})</h3>\n'
            group_cards = "".join(_recommendation_card(item) for item in group)
            sections.append(heading + group_cards)
        cards = "".join(sections)

    return (
        '<section id="deterministic-recommendations" '
        'class="section deterministic-section">\n'
        f"<h2>Deterministic Recommendations ({len(result.recommendations)})</h2>\n"
        '<p class="deterministic-label">Deterministic analysis evidence</p>\n'
        '<p class="hint">Grouped by category for readability. AI recommendations appear later '
        "and synthesize across these items.</p>\n"
        f"{cards}"
        f"{_priority_plan(result)}"
        "</section>\n"
    )


def render_comparison_section(result: AnalysisResult) -> str:
    """Render comparison details when a baseline assessment is available."""

    comparison = result.comparison

    if comparison is None or not comparison.baseline_available:
        return ""

    summary = comparison.summary
    summary_rows = [
        ("New findings", str(summary.new_findings)),
        ("Resolved findings", str(summary.resolved_findings)),
        ("Worsened findings", str(summary.worsened_findings)),
        ("Improved findings", str(summary.improved_findings)),
        ("New recommendations", str(summary.new_recommendations)),
        ("Resolved recommendations", str(summary.resolved_recommendations)),
        ("Worsened priorities", str(summary.worsened_priorities)),
        ("Improved priorities", str(summary.improved_priorities)),
        ("Fact changes", str(summary.fact_changes)),
    ]
    summary_html = "".join(
        f"<tr><th>{escape_html(label)}</th><td>{escape_and_wrap(value)}</td></tr>\n"
        for label, value in summary_rows
    )

    version_rows = ""
    if (
        comparison.baseline_analyzer_version
        or comparison.current_analyzer_version
        or comparison.baseline_ruleset_version
        or comparison.current_ruleset_version
    ):
        version_rows = (
            "<dt>Baseline analyzer</dt>"
            f"<dd>{escape_and_wrap(comparison.baseline_analyzer_version or 'Unknown')}</dd>\n"
            "<dt>Current analyzer</dt>"
            f"<dd>{escape_and_wrap(comparison.current_analyzer_version or 'Unknown')}</dd>\n"
            "<dt>Baseline ruleset</dt>"
            f"<dd>{escape_and_wrap(comparison.baseline_ruleset_version or 'Unknown')}</dd>\n"
            "<dt>Current ruleset</dt>"
            f"<dd>{escape_and_wrap(comparison.current_ruleset_version or 'Unknown')}</dd>\n"
        )

    notes_html = ""
    if comparison.notes:
        notes_items = "".join(
            f'<li class="technical-value">{escape_and_wrap(note)}</li>' for note in comparison.notes
        )
        notes_html = f'<h3>Notes</h3>\n<ul class="change-list">{notes_items}</ul>\n'

    return (
        '<section id="comparison" '
        'class="section deterministic-section comparison-section">\n'
        "<h2>Changes Since Previous Assessment</h2>\n"
        '<p class="deterministic-label">Deterministic analysis evidence</p>\n'
        '<dl class="meta-grid">\n'
        "<dt>Baseline timestamp</dt>"
        f"<dd>{escape_and_wrap(comparison.baseline_timestamp or 'Unknown')}</dd>\n"
        "<dt>Current timestamp</dt>"
        f"<dd>{escape_and_wrap(comparison.current_timestamp or 'Unknown')}</dd>\n"
        f"{version_rows}"
        "</dl>\n"
        f"{notes_html}"
        "<h3>Summary</h3>\n"
        + _fact_table(summary_html)
        + _comparison_finding_list(
            "New Findings",
            comparison.new_findings,
            "new",
        )
        + _comparison_finding_list(
            "Resolved Findings",
            comparison.resolved_findings,
            "resolved",
        )
        + _severity_change_list(comparison.severity_changes)
        + _comparison_recommendation_list(
            "New Recommendations",
            comparison.new_recommendations,
            "new",
        )
        + _comparison_recommendation_list(
            "Resolved Recommendations",
            comparison.resolved_recommendations,
            "resolved",
        )
        + _priority_change_list(comparison.priority_changes)
        + _fact_change_list(comparison.fact_changes)
        + "</section>\n"
    )


def _executive_summary_text(result: AnalysisResult) -> str:
    finding_count = len(result.findings)
    recommendation_count = len(result.recommendations)
    critical_findings = sum(finding.severity == Severity.CRITICAL for finding in result.findings)
    high_recommendations = sum(
        recommendation.priority in {Priority.CRITICAL, Priority.HIGH}
        for recommendation in result.recommendations
    )

    parts = [
        (
            f"Analyzed repository '{result.repository.name}' with "
            f"{len(result.repository.files)} scanned file(s)."
        ),
        (
            f"Detected {finding_count} finding(s) "
            f"({critical_findings} critical) and "
            f"{recommendation_count} recommendation(s) "
            f"({high_recommendations} critical/high priority)."
        ),
    ]

    structure = result.facts.structure
    if structure is not None and structure.has_tests is not None:
        parts.append(
            "Automated tests were detected."
            if structure.has_tests
            else "No automated tests were detected."
        )

    cicd = result.facts.cicd
    if cicd is not None:
        parts.append("CI was detected." if cicd.has_ci else "No CI pipeline was detected.")

    cloud = result.facts.cloud
    if cloud is not None and cloud.cloud_capabilities:
        parts.append("Cloud capabilities detected: " + ", ".join(cloud.cloud_capabilities) + ".")

    return " ".join(parts)


def _executive_summary_signals(result: AnalysisResult) -> str:
    technologies = ", ".join(technology.name for technology in result.technologies) or (
        "None detected"
    )
    critical_high = sum(
        finding.severity in {Severity.CRITICAL, Severity.HIGH} for finding in result.findings
    )

    structure = result.facts.structure
    if structure is None or structure.has_tests is None:
        tests_detected = "Unknown"
    elif structure.has_tests:
        tests_detected = "Yes"
    else:
        tests_detected = "No"

    cicd = result.facts.cicd
    if cicd is None:
        ci_detected = "Unknown"
    elif cicd.has_ci:
        ci_detected = "Yes"
    else:
        ci_detected = "No"

    cloud = result.facts.cloud
    if cloud is None or not cloud.cloud_capabilities:
        cloud_signals = "None detected"
    else:
        cloud_signals = ", ".join(cloud.cloud_capabilities)

    return (
        '<dl class="meta-grid">\n'
        "<dt>Files analyzed</dt>"
        f"<dd>{len(result.repository.files)}</dd>\n"
        "<dt>Technologies detected</dt>"
        f"<dd>{escape_and_wrap(technologies)}</dd>\n"
        "<dt>Critical/high risk count</dt>"
        f"<dd>{critical_high}</dd>\n"
        "<dt>Tests detected</dt>"
        f"<dd>{escape_html(tests_detected)}</dd>\n"
        "<dt>CI detected</dt>"
        f"<dd>{escape_html(ci_detected)}</dd>\n"
        "<dt>Cloud-readiness signals</dt>"
        f"<dd>{escape_and_wrap(cloud_signals)}</dd>\n"
        "</dl>\n"
    )


def _structure_fact_rows(
    result: AnalysisResult,
) -> list[tuple[str, str]]:
    structure = result.facts.structure
    if structure is None:
        return []

    rows: list[tuple[str, str]] = []
    _add_int_row(rows, "File count", structure.file_count)
    _add_int_row(rows, "Source files", structure.source_file_count)
    _add_int_row(rows, "Test files", structure.test_file_count)
    _add_int_row(rows, "Applications", structure.application_count)
    _add_bool_row(rows, "Has tests", structure.has_tests)
    _add_list_row(
        rows,
        "Architecture layers",
        structure.architecture_layers,
        presentation="badges",
    )
    return rows


def _technology_fact_rows(
    result: AnalysisResult,
) -> list[tuple[str, str]]:
    technology = result.facts.technology
    if technology is None:
        return []

    rows: list[tuple[str, str]] = []
    _add_list_row(
        rows,
        "Languages",
        technology.programming_languages,
        presentation="badges",
    )
    _add_list_row(
        rows,
        "Frameworks",
        technology.frameworks,
        presentation="badges",
    )
    _add_list_row(
        rows,
        "Build tools",
        technology.build_tools,
        presentation="badges",
    )
    _add_list_row(
        rows,
        "Test frameworks",
        technology.test_frameworks,
        presentation="badges",
    )
    _add_list_row(
        rows,
        "Detected technologies",
        technology.detected_technologies,
        presentation="badges",
    )
    return rows


def _build_dependency_fact_rows(
    result: AnalysisResult,
) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    build = result.facts.build
    if build is not None:
        _add_list_row(
            rows,
            "Build systems",
            build.build_systems,
            presentation="badges",
        )
        _add_list_row(rows, "Build files", build.build_files)
        _add_list_row(rows, "Wrapper files", build.wrapper_files)
        _add_list_row(rows, "Lock files", build.lock_files)
        _add_list_row(
            rows,
            "Packaging types",
            build.packaging_types,
            presentation="badges",
        )
        _add_bool_row(rows, "Multi-module", build.multi_module)
        _add_list_row(rows, "Modules", build.modules)
        _add_list_row(rows, "Build plugins", build.plugins)
        _add_list_row(rows, "Inferred commands", build.inferred_commands)

    dependencies = result.facts.dependencies
    if dependencies is not None:
        count = dependencies.dependency_count or dependencies.direct_dependency_count
        rows.append(("Dependency count", escape_html(str(count))))
        _add_int_row(
            rows,
            "Direct dependencies",
            dependencies.direct_dependency_count,
        )
        _add_list_row(
            rows,
            "Framework dependencies",
            dependencies.framework_dependencies,
        )
        _add_list_row(
            rows,
            "Database libraries",
            dependencies.database_drivers,
        )
        _add_list_row(
            rows,
            "Cloud SDKs",
            dependencies.cloud_sdks,
        )
        _add_list_row(
            rows,
            "Testing libraries",
            dependencies.testing_libraries,
        )
        _add_list_row(
            rows,
            "Outdated dependencies",
            dependencies.outdated_dependencies,
        )
    return rows


def _cicd_fact_rows(
    result: AnalysisResult,
) -> list[tuple[str, str]]:
    cicd = result.facts.cicd
    if cicd is None:
        return []

    rows: list[tuple[str, str]] = []
    platforms = cicd.ci_platforms or cicd.providers
    _add_list_row(rows, "CI platforms", platforms, presentation="badges")
    _add_bool_row(rows, "Has CI", cicd.has_ci)
    _add_bool_row(rows, "Has deployment workflow", cicd.has_deployment_workflow)
    _add_int_row(rows, "Pipeline count", cicd.pipeline_count)
    _add_list_row(rows, "Pipeline files", cicd.pipeline_files)

    workflow_actions = _pipeline_metadata_values(cicd.pipelines, "actions")
    _add_list_row(rows, "Workflow actions", workflow_actions)

    build_commands = _pipeline_command_values(cicd.pipelines, "build_commands")
    test_commands = _pipeline_command_values(cicd.pipelines, "test_commands")
    deployment_commands = _pipeline_command_values(
        cicd.pipelines,
        "deployment_commands",
    )
    _add_list_row(rows, "Build commands", build_commands)
    _add_list_row(rows, "Test commands", test_commands)
    _add_list_row(rows, "Deployment commands", deployment_commands)
    return rows


def _security_fact_rows(
    result: AnalysisResult,
) -> list[tuple[str, str]]:
    security = result.facts.security
    if security is None:
        return []

    rows: list[tuple[str, str]] = []
    _add_int_row(rows, "Sensitive files", security.sensitive_file_count)
    _add_int_row(rows, "Secret findings", security.secret_finding_count)
    _add_int_row(rows, "Weak crypto findings", security.weak_crypto_count)
    _add_int_row(
        rows,
        "Dangerous execution findings",
        security.dangerous_execution_count,
    )
    return rows


def _architecture_fact_rows(
    result: AnalysisResult,
) -> list[tuple[str, str]]:
    architecture = result.facts.architecture
    if architecture is None:
        return []

    rows: list[tuple[str, str]] = []
    _add_bool_row(rows, "API layer", architecture.has_api_layer)
    _add_bool_row(rows, "Service layer", architecture.has_service_layer)
    _add_bool_row(
        rows,
        "Persistence layer",
        architecture.has_persistence_layer,
    )
    _add_bool_row(rows, "Domain layer", architecture.has_domain_layer)
    _add_bool_row(
        rows,
        "Multi-application",
        architecture.is_multi_application,
    )
    return rows


def _cloud_fact_rows(
    result: AnalysisResult,
) -> list[tuple[str, str]]:
    cloud = result.facts.cloud
    if cloud is None:
        return []

    rows: list[tuple[str, str]] = []
    _add_list_row(
        rows,
        "Cloud capabilities",
        cloud.cloud_capabilities,
        presentation="badges",
    )
    _add_bool_row(rows, "Docker", cloud.has_docker)
    _add_bool_row(rows, "Dev Container", cloud.has_devcontainer)
    _add_bool_row(rows, "Docker Compose", cloud.has_docker_compose)
    _add_bool_row(rows, "Kubernetes", cloud.has_kubernetes)
    _add_bool_row(rows, "Helm", cloud.has_helm)
    _add_bool_row(rows, "Terraform", cloud.has_terraform)
    _add_bool_row(rows, "CloudFormation", cloud.has_cloudformation)
    _add_bool_row(rows, "Serverless", cloud.has_serverless)
    return rows


def _recommendation_card(recommendation: Recommendation) -> str:
    actions = recommendation.actions or [recommendation.description]
    actions_html = (
        "<ul>"
        + "".join(
            f'<li class="technical-value">{escape_and_wrap(action)}</li>' for action in actions
        )
        + "</ul>"
    )
    related = (
        ", ".join(escape_and_wrap(item) for item in recommendation.related_finding_ids)
        if recommendation.related_finding_ids
        else escape_html("None")
    )

    return (
        '<article class="card recommendation-card deterministic-card">\n'
        '<div class="card-header">\n'
        f"{_priority_badge(recommendation.priority)}"
        f'<span class="badge category">'
        f"{escape_html(display_enum(recommendation.category))}"
        "</span>\n"
        f'<span class="rule-id technical-value">'
        f"{escape_and_wrap(recommendation.rule_id)}"
        "</span>\n"
        f"<h4>{escape_and_wrap(recommendation.title)}</h4>\n"
        "</div>\n"
        f"<p><strong>Rationale:</strong> {escape_and_wrap(recommendation.rationale)}</p>\n"
        f"<div><strong>Proposed actions:</strong>{actions_html}</div>\n"
        "<p>"
        f"<strong>Effort:</strong> {escape_html(display_enum(recommendation.effort))} &nbsp; "
        f"<strong>Risk:</strong> {escape_html(display_enum(recommendation.risk))}"
        "</p>\n"
        f"<p><strong>Related finding IDs:</strong> {related}</p>\n"
        f'<div class="evidence">{_evidence_list(recommendation.evidence)}</div>\n'
        "</article>\n"
    )


def _priority_plan(result: AnalysisResult) -> str:
    groups = {
        "Immediate": [
            recommendation
            for recommendation in result.recommendations
            if recommendation.priority in {Priority.CRITICAL, Priority.HIGH}
        ],
        "Near Term": [
            recommendation
            for recommendation in result.recommendations
            if recommendation.priority == Priority.MEDIUM
        ],
        "Later": [
            recommendation
            for recommendation in result.recommendations
            if recommendation.priority == Priority.LOW
        ],
    }

    group_blocks: list[str] = []
    for title, recommendations in groups.items():
        if not recommendations:
            items = '<li class="empty-item">None</li>'
        else:
            items = "".join(
                (
                    "<li>"
                    f"{_priority_badge(recommendation.priority)}"
                    f" {escape_html(recommendation.title)}"
                    "</li>"
                )
                for recommendation in recommendations
            )
        group_blocks.append(
            f'<div class="roadmap-group">\n'
            f"<h3>{escape_html(title)}</h3>\n"
            f"<ul>{items}</ul>\n"
            f"</div>\n"
        )

    return (
        "<h3>Deterministic Priority Plan</h3>\n"
        '<div class="roadmap-grid">\n' + "".join(group_blocks) + "</div>\n"
    )


def _comparison_finding_list(
    title: str,
    findings: list[Any],
    label: str,
) -> str:
    if not findings:
        return f'<h3>{escape_html(title)}</h3>\n<p class="empty">None</p>\n'

    items: list[str] = []
    for finding in findings:
        items.append(
            "<li>"
            f'<span class="badge change-{label}">{escape_html(label.title())}</span> '
            f'<span class="technical-value">'
            f"{escape_and_wrap(finding.rule_id or 'No rule ID')}"
            "</span>"
            " — "
            f"{escape_and_wrap(finding.title)} "
            f"({escape_html(finding.severity)})"
            "</li>"
        )
    return f'<h3>{escape_html(title)}</h3>\n<ul class="change-list">{"".join(items)}</ul>\n'


def _comparison_recommendation_list(
    title: str,
    recommendations: list[Any],
    label: str,
) -> str:
    if not recommendations:
        return f'<h3>{escape_html(title)}</h3>\n<p class="empty">None</p>\n'

    items: list[str] = []
    for recommendation in recommendations:
        items.append(
            "<li>"
            f'<span class="badge change-{label}">{escape_html(label.title())}</span> '
            f'<span class="technical-value">{escape_and_wrap(recommendation.rule_id)}</span>'
            " — "
            f"{escape_and_wrap(recommendation.title)} "
            f"({escape_html(recommendation.priority)})"
            "</li>"
        )
    return f'<h3>{escape_html(title)}</h3>\n<ul class="change-list">{"".join(items)}</ul>\n'


def _severity_change_list(changes: list[Any]) -> str:
    if not changes:
        return '<h3>Severity Changes</h3>\n<p class="empty">None</p>\n'

    items: list[str] = []
    for change in changes:
        if change.direction == "increased":
            badge_class = "worsened"
            badge_label = "Worsened"
        else:
            badge_class = "improved"
            badge_label = "Improved"
        items.append(
            "<li>"
            f'<span class="badge change-{badge_class}">{escape_html(badge_label)}</span> '
            f'<span class="technical-value">'
            f"{escape_and_wrap(change.rule_id or 'No rule ID')}</span>"
            " — "
            f"{escape_and_wrap(change.title)}: "
            f"{escape_html(change.previous_severity)} → "
            f"{escape_html(change.current_severity)}"
            "</li>"
        )
    return f'<h3>Severity Changes</h3>\n<ul class="change-list">{"".join(items)}</ul>\n'


def _priority_change_list(changes: list[Any]) -> str:
    if not changes:
        return '<h3>Priority Changes</h3>\n<p class="empty">None</p>\n'

    items: list[str] = []
    for change in changes:
        if change.direction == "increased":
            badge_class = "worsened"
            badge_label = "Worsened"
        else:
            badge_class = "improved"
            badge_label = "Improved"
        items.append(
            "<li>"
            f'<span class="badge change-{badge_class}">{escape_html(badge_label)}</span> '
            f'<span class="technical-value">{escape_and_wrap(change.rule_id)}</span>'
            " — "
            f"{escape_and_wrap(change.title)}: "
            f"{escape_html(change.previous_priority)} → "
            f"{escape_html(change.current_priority)}"
            "</li>"
        )
    return f'<h3>Priority Changes</h3>\n<ul class="change-list">{"".join(items)}</ul>\n'


def _fact_change_list(changes: list[Any]) -> str:
    if not changes:
        return '<h3>Repository Fact Changes</h3>\n<p class="empty">None</p>\n'

    items: list[str] = []
    for change in changes:
        items.append(
            "<li>"
            '<span class="badge change-changed">Changed</span> '
            f'<span class="technical-value">{escape_and_wrap(change.display_text())}</span>'
            "</li>"
        )

    return f'<h3>Repository Fact Changes</h3>\n<ul class="change-list">{"".join(items)}</ul>\n'


def _evidence_list(evidence_items: list[Evidence]) -> str:
    if not evidence_items:
        return "<p><strong>Evidence:</strong> None provided.</p>"

    items: list[str] = []
    for item in evidence_items:
        location = format_evidence_item_location(item)
        parts = [
            f'<span class="technical-value evidence-location">{escape_and_wrap(location)}</span>'
        ]
        if item.description:
            parts.append(f" — {escape_and_wrap(item.description)}")
        if item.detected_value:
            parts.append(
                f' (detected: <span class="technical-value">'
                f"{escape_and_wrap(item.detected_value)}"
                "</span>)"
            )
        items.append(f"<li>{''.join(parts)}</li>")

    return f'<p><strong>Evidence:</strong></p><ul class="evidence-list">{"".join(items)}</ul>'


def _pipeline_metadata_values(
    pipelines: list[Any],
    key: str,
) -> list[str]:
    values: list[str] = []
    for pipeline in pipelines:
        metadata = getattr(pipeline, "metadata", {}) or {}
        raw = metadata.get(key)
        if isinstance(raw, list):
            values.extend(str(item) for item in raw if item)
        elif isinstance(raw, str) and raw:
            values.append(raw)
    return list(dict.fromkeys(values))


def _pipeline_command_values(
    pipelines: list[Any],
    attribute: str,
) -> list[str]:
    values: list[str] = []
    for pipeline in pipelines:
        commands = getattr(pipeline, attribute, None) or []
        values.extend(str(command) for command in commands if command)
    return list(dict.fromkeys(values))


def _fact_table(row_html: str) -> str:
    return wrap_table(
        f'<table class="facts fact-table">\n{row_html}</table>\n',
    )


def _add_int_row(
    rows: list[tuple[str, str]],
    label: str,
    value: int | None,
) -> None:
    if value is None:
        return
    rows.append((label, escape_html(str(value))))


def _add_bool_row(
    rows: list[tuple[str, str]],
    label: str,
    value: bool | None,
) -> None:
    if value is None:
        return
    rows.append((label, _bool_label(value)))


def _add_list_row(
    rows: list[tuple[str, str]],
    label: str,
    values: list[str] | None,
    *,
    presentation: str = "list",
) -> None:
    if not values:
        return
    rows.append(
        (
            label,
            render_collection(
                values,
                presentation=presentation,
                threshold=COLLECTION_COLLAPSE_THRESHOLD,
            ),
        )
    )


def _bool_label(value: bool | None) -> str:
    if value is None:
        return escape_html("Unknown")
    return escape_html("Yes" if value else "No")


def _severity_badge(severity: Severity) -> str:
    value = display_enum(severity)
    return f'<span class="badge severity-{escape_html(value)}">{escape_html(value.upper())}</span>'


def _priority_badge(priority: Priority) -> str:
    value = display_enum(priority)
    return f'<span class="badge priority-{escape_html(value)}">{escape_html(value.upper())}</span>'
