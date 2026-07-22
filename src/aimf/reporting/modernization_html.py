"""Self-contained HTML renderer for modernization assessment reports."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from aimf.ai.agents.models import AGENT_VERSION
from aimf.ai.contracts.models import LLM_CONTRACT_SCHEMA_VERSION
from aimf.ai.recommendations.enums import (
    AIRecommendationConfidence,
    AIRecommendationEffort,
    AIRecommendationImpact,
    AIRecommendationPriority,
)
from aimf.ai.recommendations.models import (
    AI_RECOMMENDATION_SCHEMA_VERSION,
    AIRecommendation,
    ModernizationPhase,
)
from aimf.models import Finding, Severity
from aimf.models.evidence import Evidence
from aimf.reporters.evidence_location import (
    REPOSITORY_LEVEL_EVIDENCE_LABEL,
    format_evidence_location,
)
from aimf.reporters.html_rendering import (
    COLLECTION_COLLAPSE_THRESHOLD,
    escape_and_wrap,
    escape_html,
    render_collection,
    wrap_table,
)
from aimf.reporting.deterministic_content import (
    render_comparison_section,
    render_deterministic_executive_summary,
    render_deterministic_recommendations,
    render_repository_system_intelligence,
    render_static_analysis_providers,
)
from aimf.reporting.modernization_models import AssessmentMode, ModernizationReportInput
from aimf.reporting.modernization_view import (
    assessment_mode_label,
    finding_anchor_id,
    finding_anchor_map,
    repository_identifier,
    sanitize_display_path,
    sorted_findings,
    validate_modernization_report_input,
)
from aimf.static_analysis.models import StaticAnalysisStatus

AI_NOT_EXECUTED_MESSAGE = (
    "AI interpretation was not executed for this assessment. "
    "The report contains AIMF deterministic system intelligence only."
)

CONTENT_SECURITY_POLICY = (
    "default-src 'none'; "
    "base-uri 'none'; "
    "form-action 'none'; "
    "frame-ancestors 'none'; "
    "img-src 'none'; "
    "font-src 'none'; "
    "connect-src 'none'; "
    "object-src 'none'; "
    "script-src 'none'; "
    "style-src 'unsafe-inline'"
)


class ModernizationHTMLReportRenderer:
    """Render a polished, deterministic modernization assessment HTML report."""

    collection_collapse_threshold = COLLECTION_COLLAPSE_THRESHOLD

    def render(self, report_input: ModernizationReportInput) -> str:
        """Return a complete self-contained HTML document."""

        validated = validate_modernization_report_input(report_input)
        analysis = validated.analysis_result
        repo_name = repository_identifier(validated)
        return (
            "<!DOCTYPE html>\n"
            '<html lang="en">\n'
            "<head>\n"
            '<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<meta http-equiv="Content-Security-Policy" '
            f'content="{escape_html(CONTENT_SECURITY_POLICY)}">\n'
            f"<title>{escape_html(f'AIMF Assessment — {repo_name}')}</title>\n"
            f"<style>{_css()}</style>\n"
            "</head>\n"
            "<body>\n"
            '<div class="page">\n'
            f"{self._render_cover(validated)}"
            f"{self._render_toc(validated)}"
            f"{render_deterministic_executive_summary(analysis)}"
            f"{render_repository_system_intelligence(analysis)}"
            f"{render_static_analysis_providers(analysis)}"
            f"{self._render_findings(validated)}"
            f"{render_deterministic_recommendations(analysis)}"
            f"{render_comparison_section(analysis)}"
            f"{self._render_ai_interpretation(validated)}"
            f"{self._render_analysis_coverage(validated)}"
            f"{self._render_coverage_and_limitations(validated)}"
            f"{self._render_execution_details(validated)}"
            f"{self._render_methodology(validated)}"
            f"{self._render_footer(validated)}"
            "</div>\n"
            "</body>\n"
            "</html>\n"
        )

    def _render_cover(self, report_input: ModernizationReportInput) -> str:
        analysis = report_input.analysis_result
        context = report_input.analysis_context
        source_type = (
            context.repository.source_type
            if context is not None
            else ("github" if analysis.repository.source_url else "local")
        )
        org = report_input.organization_name
        notice = report_input.confidentiality_notice
        generated = _format_timestamp(report_input.generated_at_utc)
        mode_label = assessment_mode_label(report_input.assessment_mode)
        technologies = ", ".join(tech.name for tech in analysis.technologies) or ("None detected")
        build_systems = (
            ", ".join(analysis.facts.build.build_systems)
            if analysis.facts.build is not None and analysis.facts.build.build_systems
            else "None detected"
        )
        dependency_count = "Unknown"
        if analysis.facts.dependencies is not None:
            deps = analysis.facts.dependencies
            count = deps.dependency_count or deps.direct_dependency_count
            if count is not None:
                dependency_count = str(count)
        org_row = (
            f"<dt>Organization</dt><dd>{escape_and_wrap(org)}</dd>\n" if org and org.strip() else ""
        )
        notice_block = (
            f'<p class="confidentiality">{escape_and_wrap(notice)}</p>\n'
            if notice and notice.strip()
            else ""
        )
        warning_block = ""
        if report_input.warnings:
            items = "".join(f"<li>{escape_and_wrap(item)}</li>" for item in report_input.warnings)
            warning_block = (
                '<div class="warning" role="status">\n'
                "<strong>Assessment warnings</strong>\n"
                f"<ul>{items}</ul>\n"
                "</div>\n"
            )
        schema_rows = ""
        if report_input.ai_executed:
            schema_rows = (
                "<dt>Context schema</dt>"
                f"<dd>{escape_html(LLM_CONTRACT_SCHEMA_VERSION)}</dd>\n"
                "<dt>Recommendation schema</dt>"
                f"<dd>{escape_html(AI_RECOMMENDATION_SCHEMA_VERSION)}</dd>\n"
                f"<dt>Agent version</dt><dd>{escape_html(AGENT_VERSION)}</dd>\n"
            )
        legend = (
            '<p class="legend">'
            '<span class="chip deterministic">Deterministic evidence</span> '
            + (
                '<span class="chip ai">AI-generated interpretation</span>'
                if report_input.ai_executed
                else '<span class="chip">AI interpretation not executed</span>'
            )
            + "</p>\n"
        )
        subtitle = (
            "AI-enhanced modernization assessment"
            if report_input.ai_executed
            else "Deterministic modernization assessment"
        )
        return (
            '<header id="cover" class="report-header cover">\n'
            "<h1>AI Modernization Factory</h1>\n"
            f'<p class="subtitle">{escape_html(subtitle)}</p>\n'
            f"{notice_block}"
            f"{warning_block}"
            '<dl class="meta-grid">\n'
            f"<dt>Repository</dt><dd>{escape_and_wrap(repository_identifier(report_input))}</dd>\n"
            f"{org_row}"
            f"<dt>Assessment mode</dt><dd>{escape_html(mode_label)}</dd>\n"
            f"<dt>Generated (UTC)</dt><dd>{escape_and_wrap(generated)}</dd>\n"
            f"<dt>Source type</dt><dd>{escape_and_wrap(source_type)}</dd>\n"
            f"<dt>Files scanned</dt><dd>{len(analysis.repository.files)}</dd>\n"
            f"<dt>Detected technologies</dt><dd>{escape_and_wrap(technologies)}</dd>\n"
            f"<dt>Build systems</dt><dd>{escape_and_wrap(build_systems)}</dd>\n"
            f"<dt>Dependency count</dt><dd>{escape_and_wrap(dependency_count)}</dd>\n"
            f"{schema_rows}"
            "</dl>\n"
            f"{legend}"
            "</header>\n"
        )

    def _render_toc(self, report_input: ModernizationReportInput) -> str:
        items = [
            ("executive-summary", "Executive Summary"),
            ("repository-intelligence", "Repository System Intelligence"),
            ("static-analysis", "Static Analysis"),
            ("findings", "Deterministic Findings"),
            ("deterministic-recommendations", "Deterministic Recommendations"),
        ]
        if (
            report_input.analysis_result.comparison is not None
            and report_input.analysis_result.comparison.baseline_available
        ):
            items.append(("comparison", "Changes Since Previous Assessment"))
        items.extend(
            [
                ("ai-interpretation", "AI Interpretation"),
                ("analysis-coverage", "Analysis Coverage"),
                ("coverage", "Evidence Coverage and Limitations"),
                ("execution", "Assessment Execution Details"),
                ("methodology", "Methodology"),
            ]
        )
        links = "".join(
            f'<li><a href="#{anchor}">{escape_html(label)}</a></li>\n' for anchor, label in items
        )
        return (
            '<nav id="contents" class="section toc" aria-label="Table of contents">\n'
            "<h2>Contents</h2>\n"
            f"<ol>\n{links}</ol>\n"
            "</nav>\n"
        )

    def _render_ai_interpretation(self, report_input: ModernizationReportInput) -> str:
        if report_input.ai_status.value == "failed":
            detail = report_input.ai_failure_message or "AI assessment failed."
            return (
                '<section id="ai-interpretation" class="section ai-section page-break">\n'
                "<h2>AI Interpretation</h2>\n"
                '<p class="ai-label">AI interpretation</p>\n'
                '<p class="warning" role="status">'
                "<strong>AI status:</strong> failed. Deterministic evidence above remains valid. "
                f"{escape_and_wrap(detail)}"
                "</p>\n"
                "</section>\n"
            )
        if not report_input.ai_executed:
            return (
                '<section id="ai-interpretation" class="section ai-section page-break">\n'
                "<h2>AI Interpretation</h2>\n"
                '<p class="ai-label">AI interpretation</p>\n'
                f'<p class="ai-not-executed">{escape_and_wrap(AI_NOT_EXECUTED_MESSAGE)}</p>\n'
                "</section>\n"
            )

        return (
            '<section id="ai-interpretation" class="section ai-section page-break">\n'
            "<h2>AI Interpretation</h2>\n"
            '<p class="ai-label">AI-generated interpretation based on deterministic evidence</p>\n'
            f"{self._render_ai_executive_body(report_input)}"
            f"{self._render_key_risks_body(report_input)}"
            f"{self._render_ai_recommendations_body(report_input)}"
            f"{self._render_ai_roadmap_body(report_input)}"
            f"{self._render_ai_limitations_body(report_input)}"
            f"{self._render_ai_metadata_body(report_input)}"
            "</section>\n"
        )

    def _render_ai_executive_body(self, report_input: ModernizationReportInput) -> str:
        assert report_input.assessment_result is not None
        assert report_input.analysis_context is not None
        recommendation = report_input.assessment_result.recommendation_result
        coverage = recommendation.evidence_coverage
        truncation = report_input.analysis_context.findings_truncation
        warning = ""
        if truncation.truncated or coverage.input_truncated:
            warning = (
                '<p class="warning" role="status">'
                "<strong>Context truncation warning:</strong> "
                "Source evidence provided to the assessment may be incomplete. "
                f"Findings included: {truncation.included_count} of "
                f"{truncation.original_count}."
                "</p>\n"
            )
        return (
            "<h3>Executive Interpretation</h3>\n"
            f"<p>{escape_and_wrap(recommendation.executive_summary)}</p>\n"
            f"<p>{escape_and_wrap(recommendation.overall_assessment)}</p>\n"
            '<dl class="meta-grid">\n'
            "<dt>Evidence coverage</dt>"
            f"<dd>{coverage.coverage_percentage:.2f}%</dd>\n"
            "<dt>Findings referenced</dt>"
            f"<dd>{coverage.findings_referenced} / {coverage.total_findings}</dd>\n"
            "</dl>\n"
            f"{warning}"
        )

    def _render_key_risks_body(self, report_input: ModernizationReportInput) -> str:
        assert report_input.assessment_result is not None
        recommendation = report_input.assessment_result.recommendation_result
        risks = recommendation.key_risks
        priority_risks = [
            item
            for item in recommendation.recommendations
            if item.priority in {AIRecommendationPriority.CRITICAL, AIRecommendationPriority.HIGH}
        ][:5]
        anchors = finding_anchor_map(report_input.analysis_result.findings)

        cards: list[str] = []
        if priority_risks:
            for item in priority_risks:
                cards.append(self._risk_card_from_recommendation(item, anchors))
        elif risks:
            for index, risk in enumerate(risks[:5], start=1):
                cards.append(
                    '<article class="card risk-card ai-card">\n'
                    '<div class="card-header">\n'
                    '<span class="badge ai-badge">AI</span>\n'
                    f"<h3>{escape_and_wrap(f'Risk {index}')}</h3>\n"
                    "</div>\n"
                    f"<p>{escape_and_wrap(risk)}</p>\n"
                    "</article>\n"
                )
        else:
            cards.append('<p class="empty">No key risks were identified.</p>\n')

        return "<h3>Key Modernization Risks</h3>\n" + "".join(cards)

    def _risk_card_from_recommendation(
        self,
        recommendation: AIRecommendation,
        anchors: dict[str, str],
    ) -> str:
        related = self._finding_links(recommendation.related_finding_ids, anchors)
        return (
            '<article class="card risk-card ai-card">\n'
            '<div class="card-header">\n'
            f"{_priority_badge(recommendation.priority)}"
            f"{_confidence_badge(recommendation.confidence)}"
            f'<span class="rule-id">{escape_html(recommendation.recommendation_id)}</span>\n'
            f"<h3>{escape_and_wrap(recommendation.title)}</h3>\n"
            "</div>\n"
            f"<p>{escape_and_wrap(recommendation.description)}</p>\n"
            f"<p><strong>Related findings:</strong> {related}</p>\n"
            "</article>\n"
        )

    def _render_ai_recommendations_body(self, report_input: ModernizationReportInput) -> str:
        assert report_input.assessment_result is not None
        recommendations = report_input.assessment_result.recommendation_result.recommendations
        anchors = finding_anchor_map(report_input.analysis_result.findings)
        if not recommendations:
            body = '<p class="empty">No AI recommendations were generated.</p>\n'
        else:
            body = "".join(self._recommendation_card(item, anchors) for item in recommendations)
        return f"<h3>AI Recommendations ({len(recommendations)})</h3>\n{body}"

    def _recommendation_card(
        self,
        recommendation: AIRecommendation,
        anchors: dict[str, str],
    ) -> str:
        actions = (
            "<ul>"
            + "".join(
                f"<li>{escape_and_wrap(action)}</li>" for action in recommendation.suggested_actions
            )
            + "</ul>"
            if recommendation.suggested_actions
            else "<p>None</p>"
        )
        dependencies = (
            ", ".join(escape_html(item) for item in recommendation.dependencies)
            if recommendation.dependencies
            else escape_html("None")
        )
        related = self._finding_links(recommendation.related_finding_ids, anchors)
        return (
            f'<article id="recommendation-{escape_html(_slug(recommendation.recommendation_id))}" '
            'class="card recommendation-card ai-card">\n'
            '<div class="card-header">\n'
            f"{_priority_badge(recommendation.priority)}"
            f"{_effort_badge(recommendation.effort)}"
            f"{_impact_badge(recommendation.impact)}"
            f"{_confidence_badge(recommendation.confidence)}"
            f'<span class="rule-id">{escape_html(recommendation.recommendation_id)}</span>\n'
            f"<h3>{escape_and_wrap(recommendation.title)}</h3>\n"
            "</div>\n"
            f"<p>{escape_and_wrap(recommendation.description)}</p>\n"
            f"<p><strong>Rationale:</strong> {escape_and_wrap(recommendation.rationale)}</p>\n"
            f"<div><strong>Actions:</strong>{actions}</div>\n"
            f"<p><strong>Dependencies:</strong> {dependencies}</p>\n"
            f"<p><strong>Related findings:</strong> {related}</p>\n"
            "</article>\n"
        )

    def _render_ai_roadmap_body(self, report_input: ModernizationReportInput) -> str:
        assert report_input.assessment_result is not None
        phases = report_input.assessment_result.recommendation_result.modernization_phases
        if not phases:
            body = '<p class="empty">No modernization phases were defined.</p>\n'
        else:
            body = "".join(self._phase_card(phase) for phase in phases)
        return f"<h3>Modernization Roadmap</h3>\n{body}"

    def _render_ai_limitations_body(self, report_input: ModernizationReportInput) -> str:
        assert report_input.assessment_result is not None
        limitations = report_input.assessment_result.recommendation_result.limitations
        if not limitations:
            body = '<p class="empty">No AI limitations were recorded.</p>\n'
        else:
            body = (
                "<ul>"
                + "".join(f"<li>{escape_and_wrap(item)}</li>" for item in limitations)
                + "</ul>\n"
            )
        return "<h3>AI Limitations</h3>\n" + body

    def _render_ai_metadata_body(self, report_input: ModernizationReportInput) -> str:
        assert report_input.assessment_result is not None
        metadata = report_input.assessment_result.model_metadata
        usage = metadata.usage
        budget = (
            report_input.analysis_context.budget
            if report_input.analysis_context is not None
            else None
        )
        rows = [
            ("Provider", metadata.provider or "—"),
            ("Model", metadata.model_id or "—"),
            (
                "Input tokens",
                str(usage.input_tokens) if usage.input_tokens is not None else "—",
            ),
            (
                "Output tokens",
                str(usage.output_tokens) if usage.output_tokens is not None else "—",
            ),
            (
                "Latency (ms)",
                f"{metadata.latency_ms:.2f}" if metadata.latency_ms is not None else "—",
            ),
        ]
        if budget is not None:
            rows.extend(
                [
                    ("Candidate findings", str(budget.candidate_finding_count)),
                    ("Included findings", str(budget.included_finding_count)),
                    ("Omitted informational", str(budget.omitted_informational_count)),
                    ("Estimated input tokens", str(budget.estimated_input_tokens)),
                    ("Static-analysis profile", budget.static_analysis_profile or "—"),
                ]
            )
        details = "".join(
            f"<dt>{escape_html(label)}</dt><dd>{escape_and_wrap(value)}</dd>\n"
            for label, value in rows
        )
        return f'<h3>AI Execution Metadata</h3>\n<dl class="meta-grid">\n{details}</dl>\n'

    def _phase_card(self, phase: ModernizationPhase) -> str:
        recommendations = (
            ", ".join(
                f'<a href="#recommendation-{escape_html(_slug(item))}">{escape_html(item)}</a>'
                for item in phase.recommendations
            )
            if phase.recommendations
            else escape_html("None")
        )
        outcomes = (
            "<ul>"
            + "".join(f"<li>{escape_and_wrap(item)}</li>" for item in phase.expected_outcomes)
            + "</ul>"
            if phase.expected_outcomes
            else "<p>None</p>"
        )
        return (
            '<article class="card phase-card ai-card">\n'
            f"<h3>Phase {phase.phase}: {escape_and_wrap(phase.name)}</h3>\n"
            f"<p><strong>Objective:</strong> {escape_and_wrap(phase.objective)}</p>\n"
            f"<p><strong>Recommendations:</strong> {recommendations}</p>\n"
            f"<div><strong>Expected outcomes:</strong>{outcomes}</div>\n"
            "</article>\n"
        )

    def _render_findings(self, report_input: ModernizationReportInput) -> str:
        all_findings = sorted_findings(report_input.analysis_result.findings)
        primary_supporting = [
            finding
            for finding in all_findings
            if str(finding.metadata.get("customer_visibility") or "primary")
            in {"primary", "supporting"}
            or finding.source.value != "external_static_analysis"
        ]
        informational = [
            finding
            for finding in all_findings
            if finding.source.value == "external_static_analysis"
            and finding.metadata.get("customer_visibility") == "informational"
        ]

        if not primary_supporting and not informational:
            return (
                '<section id="findings" class="section deterministic-section page-break">\n'
                "<h2>Deterministic Findings</h2>\n"
                '<p class="deterministic-label">Deterministic analysis evidence</p>\n'
                '<p class="empty">No deterministic findings were detected.</p>\n'
                "</section>\n"
            )

        blocks = self._finding_category_blocks(primary_supporting)
        appendix = self._informational_appendix(informational)
        disclosure = ""
        results = report_input.analysis_result.static_analysis_results
        if any(item.suppressed_from_html_count > 0 for item in results):
            disclosure = (
                '<p class="static-analysis-disclosure">'
                "Some low-value or repetitive static-analysis observations are retained "
                "in the JSON assessment but summarized or omitted from the "
                "customer-facing HTML."
                "</p>\n"
            )

        visible_count = len(primary_supporting) + len(informational)
        return (
            '<section id="findings" class="section deterministic-section page-break">\n'
            f"<h2>Deterministic Findings ({visible_count})</h2>\n"
            '<p class="deterministic-label">Deterministic analysis evidence</p>\n'
            + disclosure
            + "".join(blocks)
            + appendix
            + "</section>\n"
        )

    def _finding_category_blocks(self, findings: list[Finding]) -> list[str]:
        grouped: dict[tuple[str, str], list[Finding]] = defaultdict(list)
        occurrence: dict[str, int] = {}
        for finding in findings:
            severity = str(getattr(finding.severity, "value", finding.severity)).lower()
            category = str(getattr(finding.category, "value", finding.category)).lower()
            grouped[(severity, category)].append(finding)

        blocks: list[str] = []
        for (severity, category), group in grouped.items():
            cards: list[str] = []
            for finding in group:
                rule_id = finding.rule_id or ""
                index = occurrence.get(rule_id, 0)
                occurrence[rule_id] = index + 1
                anchor = finding_anchor_id(
                    rule_id or str(finding.id),
                    index=index,
                )
                cards.append(self._finding_card(finding, anchor))
            blocks.append(
                f'<div class="category-group">\n'
                f"<h3>{escape_html(severity.title())} / {escape_html(category.title())}</h3>\n"
                + "".join(cards)
                + "</div>\n"
            )
        return blocks

    def _informational_appendix(self, findings: list[Finding]) -> str:
        if not findings:
            return ""
        row_parts: list[str] = []
        for finding in findings:
            occurrence = finding.metadata.get("occurrence_count") or 1
            file_count = finding.metadata.get("affected_file_count")
            if file_count is None:
                file_count = len(finding.evidence)
            severity = str(getattr(finding.severity, "value", finding.severity))
            row_parts.append(
                "<tr>"
                f'<td class="technical-value">{escape_and_wrap(finding.rule_id or "—")}</td>'
                f"<td>{escape_and_wrap(finding.title)}</td>"
                f"<td>{escape_html(str(occurrence))}</td>"
                f"<td>{escape_html(str(file_count))}</td>"
                f"<td>{escape_html(severity)}</td>"
                "</tr>\n"
            )
        rows = "".join(row_parts)
        table = wrap_table(
            '<table class="facts informational-appendix">\n'
            "<thead><tr><th>Rule</th><th>Title</th><th>Occurrences</th>"
            "<th>Files</th><th>Severity</th></tr></thead>\n"
            f"<tbody>{rows}</tbody>\n"
            "</table>\n",
            css_class="table-wrapper informational-appendix-wrapper",
        )
        return (
            '<div class="informational-appendix category-group">\n'
            "<h3>Informational static-analysis groups</h3>\n"
            "<p>Compact appendix of lower-value or repetitive PMD patterns.</p>\n"
            f"{table}"
            "</div>\n"
        )

    def _finding_card(self, finding: Finding, anchor: str) -> str:
        technologies = (
            render_collection(
                finding.affected_technologies,
                presentation="badges",
                threshold=self.collection_collapse_threshold,
            )
            if finding.affected_technologies
            else escape_html("None")
        )
        provider_badges = _provider_badges(finding)
        occurrence = finding.metadata.get("occurrence_count")
        occurrence_html = ""
        if isinstance(occurrence, int) and occurrence > 1:
            files = finding.metadata.get("affected_file_count") or len(finding.evidence)
            occurrence_html = (
                f'<p class="grouped-occurrence"><strong>Occurrences:</strong> '
                f"{occurrence} across {files} file"
                f"{'s' if files != 1 else ''}</p>\n"
            )
        return (
            f'<article id="{escape_html(anchor)}" class="card finding-card deterministic-card">\n'
            '<div class="card-header">\n'
            f"{_severity_badge(finding.severity)}"
            f"{provider_badges}"
            f'<span class="rule-id">{escape_html(finding.rule_id or "No rule ID")}</span>\n'
            f"<h4>{escape_and_wrap(finding.title)}</h4>\n"
            "</div>\n"
            f"<p>{escape_and_wrap(finding.description)}</p>\n"
            f"{occurrence_html}"
            '<div class="affected-technologies">\n'
            "<strong>Affected technologies:</strong>\n"
            f"{technologies}\n"
            "</div>\n"
            f"{self._evidence_list(finding.evidence)}"
            "</article>\n"
        )

    def _evidence_list(self, evidence_items: list[Evidence]) -> str:
        if not evidence_items:
            return "<p><strong>Evidence:</strong> None provided.</p>\n"

        items: list[str] = []
        for item in evidence_items:
            path = sanitize_display_path(item.file_path)
            location = format_evidence_location(
                path if path else item.file_path,
                item.line_number,
                item.column_number,
            )
            if path in {".", "./"} or item.file_path.strip() in {".", "./"}:
                location = REPOSITORY_LEVEL_EVIDENCE_LABEL
                parts = [
                    f'<span class="technical-value evidence-location">'
                    f"{escape_html(location)}</span>"
                ]
            else:
                parts = [
                    f'<span class="technical-value evidence-location">'
                    f"{escape_and_wrap(location)}</span>"
                ]
            if item.description:
                parts.append(f" — {escape_and_wrap(item.description)}")
            items.append(f"<li>{''.join(parts)}</li>")
        return (
            f'<p><strong>Evidence:</strong></p>\n<ul class="evidence-list">{"".join(items)}</ul>\n'
        )

    def _render_analysis_coverage(self, report_input: ModernizationReportInput) -> str:
        results = report_input.analysis_result.static_analysis_results
        if not results:
            static_status = "disabled"
            static_detail = "Static analysis was not configured for this assessment."
            static_meta = ""
        else:
            primary = results[0]
            static_status = primary.status.value
            if primary.status == StaticAnalysisStatus.UNAVAILABLE:
                static_detail = (
                    f"{primary.provider_name} static analysis was unavailable for this "
                    "assessment. Repository scanning, technology detection, and the "
                    "remaining deterministic analyzers completed successfully."
                )
            elif primary.status == StaticAnalysisStatus.DISABLED:
                static_detail = (
                    f"{primary.provider_name} static analysis was disabled for this assessment."
                )
            elif primary.status == StaticAnalysisStatus.FAILED:
                static_detail = (
                    f"{primary.provider_name} static analysis failed. "
                    "Remaining deterministic analyzers completed successfully."
                )
            elif primary.status == StaticAnalysisStatus.SKIPPED:
                static_detail = (
                    f"{primary.provider_name} static analysis was skipped "
                    "(not applicable for this repository)."
                )
            else:
                finding_count = sum(len(item.findings) for item in results)
                version = primary.provider_version or "unknown"
                static_detail = (
                    f"{primary.provider_name} {version} completed with {finding_count} finding(s)."
                )
            duration = f"{primary.duration_ms:.2f}" if primary.duration_ms is not None else "—"
            static_meta = (
                '<dl class="meta-grid">\n'
                f"<dt>Provider</dt><dd>{escape_html(primary.provider_name)}</dd>\n"
                "<dt>Provider version</dt>"
                f"<dd>{escape_html(primary.provider_version or '—')}</dd>\n"
                f"<dt>Duration (ms)</dt><dd>{duration}</dd>\n"
                "<dt>Findings</dt>"
                f"<dd>{sum(len(item.findings) for item in results)}</dd>\n"
                "</dl>\n"
            )

        if report_input.ai_status.value == "failed":
            ai_status = "failed"
        elif report_input.ai_executed:
            ai_status = "executed"
        else:
            ai_status = "not_executed"
        timing_rows = ""
        if report_input.timing is not None:
            timing = report_input.timing
            timing_rows = (
                "<h3>Execution Timing</h3>\n"
                '<dl class="meta-grid">\n'
                f"<dt>Total (ms)</dt><dd>{timing.total_ms:.2f}</dd>\n"
                f"<dt>Scan (ms)</dt><dd>{_optional_float(timing.scan_ms)}</dd>\n"
                f"<dt>Analysis (ms)</dt><dd>{_optional_float(timing.analysis_ms)}</dd>\n"
                "<dt>Static analysis (ms)</dt>"
                f"<dd>{_optional_float(timing.static_analysis_ms)}</dd>\n"
                f"<dt>AI (ms)</dt><dd>{_optional_float(timing.ai_ms)}</dd>\n"
                f"<dt>Report (ms)</dt><dd>{_optional_float(timing.report_ms)}</dd>\n"
                "</dl>\n"
            )

        return (
            '<section id="analysis-coverage" class="section deterministic-section page-break">\n'
            "<h2>Analysis Coverage</h2>\n"
            '<p class="deterministic-label">Execution coverage for this assessment</p>\n'
            '<dl class="meta-grid">\n'
            "<dt>Deterministic analysis</dt><dd>completed</dd>\n"
            f"<dt>Static analysis</dt><dd>{escape_html(static_status)}</dd>\n"
            f"<dt>AI interpretation</dt><dd>{escape_html(ai_status)}</dd>\n"
            "</dl>\n"
            f"<p>{escape_and_wrap(static_detail)}</p>\n"
            f"{static_meta}"
            f"{timing_rows}"
            "</section>\n"
        )

    def _render_coverage_and_limitations(
        self,
        report_input: ModernizationReportInput,
    ) -> str:
        if not report_input.ai_executed:
            findings = report_input.analysis_result.findings
            with_evidence = sum(1 for item in findings if item.evidence)
            return (
                '<section id="coverage" class="section page-break">\n'
                "<h2>Evidence Coverage and Limitations</h2>\n"
                '<dl class="meta-grid">\n'
                f"<dt>Total findings</dt><dd>{len(findings)}</dd>\n"
                f"<dt>Findings with evidence</dt><dd>{with_evidence}</dd>\n"
                "<dt>AI coverage</dt><dd>Not applicable</dd>\n"
                "</dl>\n"
                '<p class="validation-note">'
                "This report contains deterministic repository evidence only. "
                "Enable AI-enhanced assessment when modernization recommendations "
                "and roadmap interpretation are required."
                "</p>\n"
                "</section>\n"
            )
        assessment = report_input.assessment_result
        context = report_input.analysis_context
        assert assessment is not None
        assert context is not None
        recommendation = assessment.recommendation_result
        coverage = recommendation.evidence_coverage
        truncation = context.findings_truncation
        context_findings = context.findings
        with_evidence = sum(1 for item in context_findings if item.evidence)
        limitations = recommendation.limitations
        limitation_items = (
            "".join(f"<li>{escape_and_wrap(item)}</li>" for item in limitations)
            if limitations
            else "<li>None recorded.</li>"
        )
        excluded = max(0, truncation.original_count - truncation.included_count)
        return (
            '<section id="coverage" class="section page-break">\n'
            "<h2>Evidence Coverage and Limitations</h2>\n"
            '<dl class="meta-grid">\n'
            f"<dt>Total findings</dt><dd>{coverage.total_findings}</dd>\n"
            f"<dt>Findings considered</dt><dd>{coverage.findings_considered}</dd>\n"
            f"<dt>Findings referenced</dt><dd>{coverage.findings_referenced}</dd>\n"
            f"<dt>Coverage</dt><dd>{coverage.coverage_percentage:.2f}%</dd>\n"
            f"<dt>Findings included in context</dt><dd>{truncation.included_count}</dd>\n"
            f"<dt>Findings excluded by truncation</dt><dd>{excluded}</dd>\n"
            f"<dt>Context truncated</dt><dd>{'Yes' if truncation.truncated else 'No'}</dd>\n"
            f"<dt>Findings with evidence</dt><dd>{with_evidence}</dd>\n"
            "</dl>\n"
            "<h3>AI Limitations</h3>\n"
            f"<ul>{limitation_items}</ul>\n"
            '<p class="validation-note">'
            "Recommendations require engineering validation before implementation. "
            "AI interpretation must not replace code review, testing, or security assessment."
            "</p>\n"
            "</section>\n"
        )

    def _render_execution_details(self, report_input: ModernizationReportInput) -> str:
        mode_label = assessment_mode_label(report_input.assessment_mode)
        if not report_input.ai_executed:
            return (
                '<section id="execution" class="section page-break">\n'
                "<h2>Assessment Execution Details</h2>\n"
                '<dl class="meta-grid">\n'
                f"<dt>Assessment mode</dt><dd>{escape_html(mode_label)}</dd>\n"
                "<dt>AI executed</dt><dd>No</dd>\n"
                "<dt>Provider</dt><dd>Not applicable</dd>\n"
                "<dt>Model ID</dt><dd>Not applicable</dd>\n"
                "<dt>Latency (ms)</dt><dd>Not applicable</dd>\n"
                "<dt>Input tokens</dt><dd>Not applicable</dd>\n"
                "<dt>Output tokens</dt><dd>Not applicable</dd>\n"
                "<dt>Total tokens</dt><dd>Not applicable</dd>\n"
                "</dl>\n"
                "</section>\n"
            )
        assert report_input.assessment_result is not None
        assessment = report_input.assessment_result
        metadata = assessment.model_metadata
        trace = assessment.trace
        usage = metadata.usage
        input_tokens = _optional_int(usage.input_tokens)
        output_tokens = _optional_int(usage.output_tokens)
        total_tokens = _optional_int(usage.total_tokens)
        return (
            '<section id="execution" class="section page-break">\n'
            "<h2>Assessment Execution Details</h2>\n"
            '<dl class="meta-grid">\n'
            f"<dt>Assessment mode</dt><dd>{escape_html(mode_label)}</dd>\n"
            "<dt>AI executed</dt><dd>Yes</dd>\n"
            f"<dt>Provider</dt><dd>{escape_html(metadata.provider)}</dd>\n"
            f"<dt>Model ID</dt><dd>{escape_html(metadata.model_id)}</dd>\n"
            f"<dt>Latency (ms)</dt><dd>{metadata.latency_ms:.2f}</dd>\n"
            f"<dt>Input tokens</dt><dd>{input_tokens}</dd>\n"
            f"<dt>Output tokens</dt><dd>{output_tokens}</dd>\n"
            f"<dt>Total tokens</dt><dd>{total_tokens}</dd>\n"
            f"<dt>Agent version</dt><dd>{escape_html(trace.agent_version)}</dd>\n"
            f"<dt>Tool-call count</dt><dd>{trace.tool_call_count}</dd>\n"
            f"<dt>Model-call count</dt><dd>{trace.model_call_count}</dd>\n"
            "</dl>\n"
            "</section>\n"
        )

    def _render_methodology(self, report_input: ModernizationReportInput) -> str:
        if report_input.assessment_mode == AssessmentMode.DETERMINISTIC:
            steps = (
                "<li>Deterministic repository analysis produces findings, technologies, "
                "and metrics without generative invention.</li>\n"
                "<li>Evidence is rendered into a customer-facing HTML report without "
                "invoking an AI provider.</li>\n"
                "<li>AI interpretation, recommendations, and roadmap phases are omitted "
                "until an AI-enhanced assessment is requested.</li>\n"
                "<li>This report separates deterministic evidence from AI interpretation "
                "and does not invent modernization guidance.</li>\n"
            )
        else:
            steps = (
                "<li>Deterministic repository analysis produces findings, technologies, "
                "and metrics without generative invention.</li>\n"
                "<li>Analysis evidence is normalized into a structured LLM analysis "
                "contract with explicit truncation metadata.</li>\n"
                "<li>AI interpretation produces modernization recommendations only from "
                "that structured evidence.</li>\n"
                "<li>Recommendations are validated so finding, dependency, and phase "
                "references resolve against known identifiers.</li>\n"
                "<li>This report separates deterministic evidence from AI interpretation "
                "and requires engineering validation before action.</li>\n"
            )
        return (
            '<section id="methodology" class="section page-break">\n'
            "<h2>Methodology</h2>\n"
            f"<ol>\n{steps}</ol>\n"
            "</section>\n"
        )

    def _render_footer(self, report_input: ModernizationReportInput) -> str:
        generated = _format_timestamp(report_input.generated_at_utc)
        return (
            '<footer class="report-footer">\n'
            f"<p>Generated by AIMF at {escape_and_wrap(generated)}.</p>\n"
            '<p class="print-meta">Print or save as PDF for offline distribution.</p>\n'
            "</footer>\n"
        )

    def _finding_links(self, finding_ids: list[str], anchors: dict[str, str]) -> str:
        if not finding_ids:
            return escape_html("None")
        parts: list[str] = []
        for finding_id in finding_ids:
            anchor = anchors.get(finding_id)
            label = escape_html(finding_id)
            if anchor:
                parts.append(f'<a href="#{escape_html(anchor)}">{label}</a>')
            else:
                parts.append(label)
        return ", ".join(parts)


def _optional_int(value: int | None) -> str:
    return str(value) if value is not None else "—"


def _optional_float(value: float | None) -> str:
    return f"{value:.2f}" if value is not None else "—"


def _provider_badges(finding: Finding) -> str:
    provider_name = finding.metadata.get("provider_name")
    if not isinstance(provider_name, str) or not provider_name:
        return ""
    badges = [f'<span class="badge provider">{escape_and_wrap(provider_name)}</span>']
    priority = finding.metadata.get("original_priority")
    if priority is not None:
        badges.append(
            f'<span class="badge category">{escape_and_wrap(provider_name)} priority '
            f"{escape_html(str(priority))}</span>"
        )
    ruleset = finding.metadata.get("ruleset")
    if isinstance(ruleset, str) and ruleset:
        label = ruleset.rsplit("/", maxsplit=1)[-1].removesuffix(".xml")
        badges.append(f'<span class="badge category">{escape_and_wrap(label)}</span>')
    return "".join(badges)


def _severity_badge(severity: Severity | str) -> str:
    value = str(getattr(severity, "value", severity)).lower()
    return f'<span class="badge severity-{escape_html(value)}">{escape_html(value.upper())}</span>'


def _priority_badge(priority: AIRecommendationPriority | str) -> str:
    value = str(getattr(priority, "value", priority)).lower()
    return f'<span class="badge priority-{escape_html(value)}">{escape_html(value.upper())}</span>'


def _effort_badge(effort: AIRecommendationEffort | str) -> str:
    value = str(getattr(effort, "value", effort)).lower()
    return (
        f'<span class="badge effort-{escape_html(value)}">'
        f"EFFORT {escape_html(value.replace('_', ' ').upper())}</span>"
    )


def _impact_badge(impact: AIRecommendationImpact | str) -> str:
    value = str(getattr(impact, "value", impact)).lower()
    return (
        f'<span class="badge impact-{escape_html(value)}">'
        f"IMPACT {escape_html(value.upper())}</span>"
    )


def _confidence_badge(confidence: AIRecommendationConfidence | str) -> str:
    value = str(getattr(confidence, "value", confidence)).lower()
    return (
        f'<span class="badge confidence-{escape_html(value)}">'
        f"CONFIDENCE {escape_html(value.upper())}</span>"
    )


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(tz=value.tzinfo).isoformat().replace("+00:00", "Z")


def _slug(value: str) -> str:
    cleaned = []
    for char in value.strip():
        if char.isalnum() or char in {"-", "_"}:
            cleaned.append(char.lower())
        else:
            cleaned.append("-")
    slug = "".join(cleaned).strip("-")
    return slug or "item"


def _css() -> str:
    return """
:root {
  --bg: #f5f7fa;
  --surface: #ffffff;
  --text: #1f2933;
  --muted: #52606d;
  --border: #d9e2ec;
  --accent: #243b53;
  --ai: #3d4f5f;
  --deterministic: #0b6e4f;
  --critical: #9b1c1c;
  --high: #b44d12;
  --medium: #8a6d3b;
  --low: #0c6b58;
  --info: #334e68;
  --warn-bg: #fff6e8;
  --warn-border: #f0d2a8;
}
* { box-sizing: border-box; }
html, body {
  margin: 0;
  max-width: 100%;
  overflow-x: hidden;
}
body {
  color: var(--text);
  background: var(--bg);
  font-family: "IBM Plex Sans", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.5;
}
.page {
  max-width: 1080px;
  width: 100%;
  margin: 0 auto;
  padding: 1.5rem;
  min-width: 0;
  overflow-wrap: anywhere;
  word-break: break-word;
}
.report-header, .section, .summary-card, .fact-group, .roadmap-group, .card,
.provider-summary-section, .comparison-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  min-width: 0;
  max-width: 100%;
}
.report-header, .section {
  padding: 1.25rem 1.5rem;
  margin-bottom: 1rem;
}
.cover h1 { margin-bottom: 0.35rem; }
.subtitle, .empty, .report-footer, .ai-label, .deterministic-label { color: var(--muted); }
.ai-label, .deterministic-label {
  font-size: 0.92rem;
  font-weight: 600;
  margin-top: 0;
}
.ai-section { border-left: 4px solid var(--ai); }
.deterministic-section { border-left: 4px solid var(--deterministic); }
.ai-card { border-left: 3px solid var(--ai); }
.deterministic-card { border-left: 3px solid var(--deterministic); }
.legend { margin-top: 1rem; }
.chip {
  display: inline-block;
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0.15rem 0.65rem;
  font-size: 0.85rem;
  margin-right: 0.35rem;
}
.chip.deterministic { color: var(--deterministic); }
.chip.ai { color: var(--ai); }
.summary-grid, .fact-groups, .roadmap-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(min(240px, 100%), 1fr));
  min-width: 0;
  max-width: 100%;
}
.summary-card, .fact-group, .roadmap-group {
  padding: 1rem;
  min-width: 0;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
}
.metric {
  font-size: 2rem;
  font-weight: 700;
  margin: 0.25rem 0 0.75rem;
}
.summary-signals { margin-top: 1rem; }
.change-list { margin: 0.25rem 0 0 1.1rem; padding: 0; }
.badge.provider, .badge.category { background: #e8eef3; color: var(--ai); }
.badge.change-new, .badge.change-worsened { background: #feecdc; color: var(--high); }
.badge.change-resolved, .badge.change-improved { background: #e1f5f0; color: var(--low); }
.badge.change-changed { background: #e6eff8; color: var(--info); }
.confidentiality {
  border: 1px solid var(--warn-border);
  background: var(--warn-bg);
  padding: 0.75rem 1rem;
  border-radius: 6px;
}
.warning {
  border: 1px solid var(--warn-border);
  background: var(--warn-bg);
  padding: 0.75rem 1rem;
  border-radius: 6px;
}
.validation-note {
  border-top: 1px solid var(--border);
  padding-top: 0.75rem;
  color: var(--muted);
}
h1, h2, h3, h4 { margin-top: 0; color: var(--accent); }
.meta-grid {
  display: grid;
  grid-template-columns: max-content minmax(0, 1fr);
  gap: 0.45rem 1rem;
}
.meta-grid dt { font-weight: 600; }
.meta-grid dd { margin: 0; }
.toc ol { margin: 0; padding-left: 1.25rem; }
.toc a { color: var(--accent); text-decoration: none; }
.toc a:hover, .toc a:focus { text-decoration: underline; }
.card {
  padding: 1rem 1.1rem;
  margin: 0.85rem 0;
}
.card-header {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem 0.55rem;
  align-items: center;
  margin-bottom: 0.5rem;
}
.card-header h3, .card-header h4 { margin: 0; flex: 1 1 100%; }
.rule-id {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  color: var(--muted);
}
.badge {
  display: inline-block;
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0.1rem 0.55rem;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}
.severity-critical, .priority-critical { background: #fde8e8; color: var(--critical); }
.severity-high, .priority-high { background: #feecdc; color: var(--high); }
.severity-medium, .priority-medium { background: #fbf1de; color: var(--medium); }
.severity-low, .priority-low, .effort-small, .impact-low, .confidence-low {
  background: #e1f5f0; color: var(--low);
}
.severity-info, .effort-medium, .impact-medium, .confidence-medium {
  background: #e6eff8; color: var(--info);
}
.effort-large, .effort-extra_large, .impact-high, .confidence-high, .priority-high {
  background: #feecdc; color: var(--high);
}
.ai-badge { background: #e8eef3; color: var(--ai); }
.table-wrapper { max-width: 100%; overflow-x: auto; }
table.facts, table.counts {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}
table.facts th, table.facts td, table.counts th, table.counts td {
  text-align: left;
  padding: 0.4rem 0.25rem;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
}
.evidence-list { margin: 0.25rem 0 0 1.1rem; padding: 0; }
.affected-technologies { margin: 0.5rem 0; }
.value-badges, .badge { max-width: 100%; }
.technical-value {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.page-break { break-before: page; page-break-before: always; }
#cover, #contents { break-before: auto; page-break-before: auto; }
.print-meta { display: none; }
@media (max-width: 768px) {
  .page { padding: 1rem; }
  .meta-grid { grid-template-columns: 1fr; }
}
@media print {
  body { background: #fff; color: #000; }
  .page { max-width: none; margin: 0; padding: 0; }
  .report-header, .section, .card {
    border-color: #999;
    box-shadow: none;
  }
  .section.page-break { break-before: page; page-break-before: always; }
  .card { break-inside: avoid; page-break-inside: avoid; }
  .print-meta { display: block; }
  a { color: inherit; text-decoration: none; }
  .toc a::after { content: ""; }
}
""".strip()
