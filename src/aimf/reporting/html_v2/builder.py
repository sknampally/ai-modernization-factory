"""Build HtmlReportViewModel from validated report input and Phase 3 artifacts."""

from __future__ import annotations

import re
from collections import Counter

from aimf.domain.ai_enrichment import AiEnrichmentResult
from aimf.domain.findings import Finding as Phase3Finding
from aimf.domain.findings import RuleEvaluationResult
from aimf.domain.recommendations import Recommendation as Phase3Recommendation
from aimf.domain.recommendations import RecommendationResult
from aimf.models import AnalysisResult
from aimf.models import Finding as Phase1Finding
from aimf.models import Recommendation as Phase1Recommendation
from aimf.reporting.ai_status import (
    ai_execution_status_label,
    assessment_mode_display_label,
)
from aimf.reporting.html_v2.models import (
    AiEnrichmentView,
    AiNextStepView,
    AiPriorityView,
    AiRiskView,
    AiThemeView,
    ArtifactRefView,
    AssessmentMetadataView,
    AssessmentSummaryView,
    DashboardMetrics,
    EvidenceView,
    FindingView,
    HtmlReportViewModel,
    RecommendationActionView,
    RecommendationView,
    ReportSummary,
    RepositoryProfileView,
    TechnologyItemView,
    VersionHighlightView,
    priority_rank,
    severity_rank,
)
from aimf.reporting.modernization_models import (
    AIExecutionStatus,
    AssessmentMode,
    HighlightedVersionInput,
    ModernizationReportInput,
    ReportArtifactInput,
)
from aimf.reporting.modernization_view import repository_identifier, sanitize_display_path
from aimf.security.redaction import redact_secrets

_AWS_KEY_PATTERN = re.compile(r"AKIA[0-9A-Z]{16}")
_AWS_SECRET_PATTERN = re.compile(r"(?i)(aws_secret_access_key\s*[=:]\s*)(\S+)")


def build_html_report_view_model(report_input: ModernizationReportInput) -> HtmlReportViewModel:
    """Assemble a presentation view-model. No analysis re-run."""

    analysis = report_input.analysis_result
    findings = _build_findings(report_input)
    recommendations = _build_recommendations(report_input)
    ai_view = _build_ai_enrichment(report_input.ai_enrichment)
    findings_by_severity = _count_sorted(
        [item.severity for item in findings],
        key_rank=severity_rank,
    )
    recommendations_by_priority = _count_sorted(
        [item.priority for item in recommendations],
        key_rank=priority_rank,
    )
    highest_priority = recommendations[0].priority if recommendations else None
    technologies = _technology_items(analysis)
    version_highlights = tuple(
        VersionHighlightView(
            label=item.label,
            value=item.value,
            kind=item.kind,
            detail=item.detail,
        )
        for item in report_input.highlighted_versions
    )
    artifacts = tuple(
        ArtifactRefView(label=item.label, relative_path=_safe_relative(item.relative_path))
        for item in report_input.report_artifacts
    )
    repo_name = repository_identifier(report_input)
    ai_status_label = _ai_enrichment_status(report_input, ai_view is not None)
    highest_severity = _highest_finding_severity(findings)
    metrics = _dashboard_metrics(
        analysis=analysis,
        technology_count=len(technologies),
        findings_count=len(findings),
        recommendations_count=len(recommendations),
        highest_finding_severity=highest_severity,
    )
    summary = ReportSummary(
        repository_name=repo_name,
        assessment_mode=report_input.assessment_mode.value,
        assessment_mode_label=assessment_mode_display_label(report_input),
        technologies=tuple(item.name for item in technologies),
        total_findings=len(findings),
        findings_by_severity=findings_by_severity,
        total_recommendations=len(recommendations),
        highest_recommendation_priority=highest_priority,
        ai_enrichment_status=ai_status_label,
        ai_enrichment_available=ai_view is not None,
        metrics=metrics,
        highest_finding_severity=highest_severity,
    )
    repository = RepositoryProfileView(
        name=analysis.repository.name,
        reference=_safe_optional_text(report_input.repository_reference),
        source_type="github" if analysis.repository.source_url else "local",
        file_count=analysis.repository.total_files or len(analysis.repository.files),
        default_branch=analysis.repository.default_branch,
    )
    rules_evaluated = 0
    if report_input.assessment_rule_evaluation is not None:
        rules_evaluated = len(report_input.assessment_rule_evaluation.rules_evaluated)
    assessment_summary = AssessmentSummaryView(
        rules_evaluated=rules_evaluated,
        findings_count=len(findings),
        recommendations_count=len(recommendations),
        findings_by_severity=findings_by_severity,
        recommendations_by_priority=recommendations_by_priority,
        summary_text=_assessment_summary_text(
            findings_count=len(findings),
            recommendations_count=len(recommendations),
            ai_available=ai_view is not None,
        ),
    )
    timing = report_input.timing
    metadata = AssessmentMetadataView(
        generated_at_utc=report_input.generated_at_utc.isoformat().replace("+00:00", "Z"),
        report_title=report_input.report_title,
        organization_name=report_input.organization_name,
        warnings=tuple(_safe_text(item) for item in report_input.warnings),
        timing_total_ms=timing.total_ms if timing else None,
        timing_scan_ms=timing.scan_ms if timing else None,
        timing_analysis_ms=timing.analysis_ms if timing else None,
        timing_ai_ms=timing.ai_ms if timing else None,
        timing_report_ms=timing.report_ms if timing else None,
        ai_status=report_input.ai_status.value,
        model_id=(
            report_input.ai_attempt.model_id
            if report_input.ai_attempt is not None
            else (
                report_input.assessment_result.model_metadata.model_id
                if report_input.assessment_result is not None
                else None
            )
        ),
        confidentiality_notice=_safe_optional_text(report_input.confidentiality_notice),
    )
    return HtmlReportViewModel(
        summary=summary,
        repository=repository,
        technologies=technologies,
        version_highlights=version_highlights,
        assessment_summary=assessment_summary,
        findings=findings,
        recommendations=recommendations,
        ai_enrichment=ai_view,
        architecture_report=report_input.architecture_report,
        technical_debt_report=report_input.technical_debt_report,
        artifacts=artifacts,
        metadata=metadata,
    )


def default_report_artifacts(
    *,
    include_ai_enrichment: bool,
    include_ai_execution: bool,
    include_architecture_assessment: bool = False,
) -> tuple[ReportArtifactInput, ...]:
    """Stable relative artifact list for Graph and Artifact References."""

    items = [
        ReportArtifactInput(label="Findings", relative_path="findings.json"),
        ReportArtifactInput(label="Recommendations", relative_path="recommendations.json"),
        ReportArtifactInput(label="Assessment JSON", relative_path="report.json"),
        ReportArtifactInput(
            label="Repository Graph",
            relative_path="graphs/repository-graph.json",
        ),
        ReportArtifactInput(
            label="Assessment Graph",
            relative_path="graphs/assessment-graph.json",
        ),
        ReportArtifactInput(
            label="Graph Summary",
            relative_path="graphs/graph-summary.json",
        ),
    ]
    if include_architecture_assessment:
        items.append(
            ReportArtifactInput(
                label="Architecture Assessment",
                relative_path="architecture-assessment.json",
            )
        )
    if include_ai_enrichment:
        items.append(ReportArtifactInput(label="AI Enrichment", relative_path="ai-enrichment.json"))
    if include_ai_execution:
        items.append(ReportArtifactInput(label="AI Execution", relative_path="ai-execution.json"))
    return tuple(items)

def _build_findings(report_input: ModernizationReportInput) -> tuple[FindingView, ...]:
    evaluation = report_input.assessment_rule_evaluation
    if evaluation is not None:
        return tuple(_phase3_finding_view(item) for item in _sorted_phase3_findings(evaluation))
    return tuple(
        _phase1_finding_view(item) for item in _sorted_phase1_findings(report_input.analysis_result)
    )


def _build_recommendations(
    report_input: ModernizationReportInput,
) -> tuple[RecommendationView, ...]:
    result = report_input.assessment_recommendation_result
    if result is not None:
        return tuple(
            _phase3_recommendation_view(item) for item in _sorted_phase3_recommendations(result)
        )
    return tuple(
        _phase1_recommendation_view(item)
        for item in sorted(
            report_input.analysis_result.recommendations,
            key=lambda item: (
                priority_rank(str(getattr(item.priority, "value", item.priority))),
                item.title.lower(),
                str(item.id),
            ),
        )
    )


def _sorted_phase3_findings(evaluation: RuleEvaluationResult) -> tuple[Phase3Finding, ...]:
    return tuple(
        sorted(
            evaluation.findings,
            key=lambda item: (
                severity_rank(item.severity.value),
                item.category.value,
                item.title.lower(),
                item.id,
            ),
        )
    )


def _sorted_phase3_recommendations(
    result: RecommendationResult,
) -> tuple[Phase3Recommendation, ...]:
    return tuple(
        sorted(
            result.recommendations,
            key=lambda item: (
                priority_rank(item.priority.value),
                item.category.value,
                item.title.lower(),
                item.id,
            ),
        )
    )


def _sorted_phase1_findings(analysis: AnalysisResult) -> tuple[Phase1Finding, ...]:
    return tuple(
        sorted(
            analysis.findings,
            key=lambda item: (
                severity_rank(str(getattr(item.severity, "value", item.severity))),
                str(getattr(item.category, "value", item.category)).lower(),
                item.title.lower(),
                str(item.id),
            ),
        )
    )


def _phase3_finding_view(finding: Phase3Finding) -> FindingView:
    return FindingView(
        finding_id=finding.id,
        rule_id=finding.rule_id,
        title=_safe_text(finding.title),
        description=_safe_text(finding.description),
        severity=finding.severity.value,
        category=finding.category.value,
        affected_nodes=tuple(str(node.root) for node in finding.affected_assessment_node_ids),
        evidence=tuple(
            EvidenceView(
                evidence_type=item.evidence_type,
                source_id=item.source_id,
                path=_safe_path(item.path),
                excerpt=_safe_optional_text(item.excerpt),
                node_id=str(item.node_id.root) if item.node_id is not None else None,
            )
            for item in finding.evidence
        ),
    )


def _phase1_finding_view(finding: Phase1Finding) -> FindingView:
    return FindingView(
        finding_id=str(finding.id),
        rule_id=finding.rule_id or "unknown",
        title=_safe_text(finding.title),
        description=_safe_text(finding.description),
        severity=str(getattr(finding.severity, "value", finding.severity)),
        category=str(getattr(finding.category, "value", finding.category)),
        affected_nodes=(),
        evidence=tuple(
            EvidenceView(
                evidence_type="file",
                source_id=item.file_path,
                path=_safe_path(item.file_path),
                excerpt=_safe_optional_text(item.snippet or item.description),
                node_id=None,
            )
            for item in finding.evidence
        ),
    )


def _phase3_recommendation_view(item: Phase3Recommendation) -> RecommendationView:
    return RecommendationView(
        recommendation_id=item.id,
        title=_safe_text(item.title),
        summary=_safe_text(item.summary),
        rationale=_safe_text(item.rationale),
        priority=item.priority.value,
        category=item.category.value,
        related_finding_ids=tuple(item.related_finding_ids),
        affected_nodes=tuple(str(node.root) for node in item.affected_node_ids),
        actions=tuple(
            RecommendationActionView(
                order=action.order,
                title=_safe_text(action.title),
                description=_safe_text(action.description),
                command=_safe_optional_text(action.command),
            )
            for action in sorted(item.actions, key=lambda row: (row.order, row.title))
        ),
        evidence=tuple(
            EvidenceView(
                evidence_type=ev.evidence_type,
                source_id=ev.source_id,
                path=_safe_path(ev.path),
                excerpt=_safe_optional_text(ev.excerpt),
                node_id=str(ev.node_id.root) if ev.node_id is not None else None,
            )
            for ev in item.evidence
        ),
    )


def _phase1_recommendation_view(item: Phase1Recommendation) -> RecommendationView:
    return RecommendationView(
        recommendation_id=str(item.id),
        title=_safe_text(item.title),
        summary=_safe_text(item.description),
        rationale=_safe_text(item.rationale or item.description),
        priority=str(getattr(item.priority, "value", item.priority)),
        category=str(getattr(item.category, "value", item.category)),
        related_finding_ids=tuple(str(fid) for fid in item.related_finding_ids),
        affected_nodes=(),
        actions=tuple(
            RecommendationActionView(
                order=index,
                title=_safe_text(action),
                description=_safe_text(action),
                command=None,
            )
            for index, action in enumerate(item.actions or (), start=1)
        ),
        evidence=tuple(
            EvidenceView(
                evidence_type="file",
                source_id=ev.file_path,
                path=_safe_path(ev.file_path),
                excerpt=_safe_optional_text(ev.snippet or ev.description),
                node_id=None,
            )
            for ev in item.evidence
        ),
    )


def _build_ai_enrichment(result: AiEnrichmentResult | None) -> AiEnrichmentView | None:
    if result is None:
        return None
    return AiEnrichmentView(
        headline=_safe_text(result.executive_summary.headline),
        narrative=_safe_text(result.executive_summary.narrative),
        posture=_safe_optional_text(result.executive_summary.posture),
        themes=tuple(
            AiThemeView(
                title=_safe_text(theme.title),
                summary=_safe_text(theme.summary),
                related_finding_ids=tuple(theme.related_finding_ids),
                related_recommendation_ids=tuple(theme.related_recommendation_ids),
            )
            for theme in result.themes
        ),
        priorities=tuple(
            AiPriorityView(
                title=_safe_text(item.title),
                rationale=_safe_text(item.rationale),
                priority=item.priority.value,
                related_finding_ids=tuple(item.related_finding_ids),
                related_recommendation_ids=tuple(item.related_recommendation_ids),
            )
            for item in result.priorities
        ),
        risks=tuple(
            AiRiskView(
                title=_safe_text(item.title),
                summary=_safe_text(item.summary),
                severity=item.severity.value,
                related_finding_ids=tuple(item.related_finding_ids),
                related_recommendation_ids=tuple(item.related_recommendation_ids),
            )
            for item in result.risks
        ),
        suggested_next_steps=tuple(
            AiNextStepView(
                order=item.order,
                title=_safe_text(item.title),
                summary=_safe_text(item.summary),
                related_finding_ids=tuple(item.related_finding_ids),
                related_recommendation_ids=tuple(item.related_recommendation_ids),
            )
            for item in sorted(result.suggested_next_steps, key=lambda row: row.order)
        ),
        referenced_finding_ids=tuple(result.referenced_finding_ids),
        referenced_recommendation_ids=tuple(result.referenced_recommendation_ids),
        provider=_safe_text(result.provider_metadata.provider),
        model_id=_safe_text(result.provider_metadata.model_id),
        request_id=_safe_optional_text(result.provider_metadata.request_id),
        latency_ms=result.provider_metadata.latency_ms,
        input_tokens=result.provider_metadata.input_tokens,
        output_tokens=result.provider_metadata.output_tokens,
        limitations=tuple(_safe_text(item) for item in result.limitations),
    )


def _technology_items(analysis: AnalysisResult) -> tuple[TechnologyItemView, ...]:
    items = [
        TechnologyItemView(
            name=tech.name,
            category=str(getattr(tech.category, "value", tech.category))
            if tech.category is not None
            else None,
            version=tech.version,
        )
        for tech in sorted(
            analysis.technologies,
            key=lambda tech: (
                str(getattr(tech.category, "value", tech.category) or "").lower(),
                tech.name.lower(),
            ),
        )
    ]
    return tuple(items)


def _count_sorted(
    values: list[str] | tuple[str, ...],
    *,
    key_rank: object,
) -> tuple[tuple[str, int], ...]:
    counter: Counter[str] = Counter(values)
    return tuple(
        sorted(
            counter.items(),
            key=lambda pair: (key_rank(pair[0]), pair[0]),  # type: ignore[operator]
        )
    )


def _ai_enrichment_status(
    report_input: ModernizationReportInput,
    available: bool,
) -> str:
    if available:
        return "Available"
    if report_input.assessment_mode == AssessmentMode.DETERMINISTIC:
        return "Not requested"
    if report_input.ai_status == AIExecutionStatus.SUCCEEDED:
        return "Succeeded (artifact unavailable)"
    if report_input.ai_status == AIExecutionStatus.NOT_REQUESTED:
        return "Not requested"
    return ai_execution_status_label(report_input.ai_status)


def _assessment_summary_text(
    *,
    findings_count: int,
    recommendations_count: int,
    ai_available: bool,
) -> str:
    base = (
        f"{findings_count} deterministic finding(s) and "
        f"{recommendations_count} deterministic recommendation(s)."
    )
    if ai_available:
        return base + " AI executive summary is included separately."
    return base


def _dashboard_metrics(
    *,
    analysis: AnalysisResult,
    technology_count: int,
    findings_count: int,
    recommendations_count: int,
    highest_finding_severity: str,
) -> DashboardMetrics:
    file_count = analysis.repository.total_files or len(analysis.repository.files)
    structure = analysis.facts.structure if analysis.facts is not None else None
    cicd = analysis.facts.cicd if analysis.facts is not None else None
    cloud = analysis.facts.cloud if analysis.facts is not None else None
    test_file_count = structure.test_file_count if structure is not None else None
    has_tests = structure.has_tests if structure is not None else None
    if has_tests is None and test_file_count is not None:
        has_tests = test_file_count > 0
    cicd_present: bool | None = None
    if cicd is not None:
        cicd_present = bool(cicd.has_ci) if cicd.has_ci is not None else bool(cicd.pipeline_count)
    cloud_count, cloud_primary, cloud_status = _cloud_enablement_signals(cloud)
    return DashboardMetrics(
        file_count=file_count,
        technology_count=technology_count,
        findings_count=findings_count,
        recommendations_count=recommendations_count,
        test_file_count=test_file_count,
        has_tests=has_tests,
        test_files_label=_test_files_label(
            test_file_count=test_file_count,
            has_tests=has_tests,
            structure_available=structure is not None,
        ),
        cicd_present=cicd_present,
        cicd_label=_cicd_label(cicd_present),
        cloud_signal_count=cloud_count,
        cloud_signals_primary=cloud_primary,
        cloud_signals_status=cloud_status,
        highest_finding_severity=highest_finding_severity,
        repository_size_label=f"{file_count} files",
    )


def _highest_finding_severity(findings: tuple[FindingView, ...]) -> str:
    """Return the highest severity among report findings, or None Detected."""

    if not findings:
        return "None Detected"
    order = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
        "informational": 4,
        "info": 4,
    }
    labels = {
        "critical": "Critical",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
        "informational": "Informational",
        "info": "Informational",
    }
    best_key = min(
        (item.severity.lower() for item in findings),
        key=lambda key: order.get(key, 99),
    )
    return labels.get(best_key, "Unknown")


def _cloud_enablement_signals(cloud: object | None) -> tuple[int | None, str, str]:
    """Return (count, primary label, status) for the seven cloud enablement signals."""

    if cloud is None:
        return None, "Unknown", "Unknown"
    raw = (
        getattr(cloud, "has_docker", None),
        getattr(cloud, "has_kubernetes", None),
        getattr(cloud, "has_helm", None),
        getattr(cloud, "has_terraform", None),
        getattr(cloud, "has_cloudformation", None),
        getattr(cloud, "has_serverless", None),
        getattr(cloud, "has_docker_compose", None),
    )
    if all(value is None for value in raw):
        return None, "Unknown", "Unknown"
    count = sum(1 for value in raw if value is True)
    primary = f"{count} of 7"
    if count >= 2:
        status = "Established"
    elif count == 1:
        status = "Partial"
    else:
        status = "Not detected"
    return count, primary, status


def _cicd_label(present: bool | None) -> str:
    if present is True:
        return "Detected"
    if present is False:
        return "Not detected"
    return "Unknown"


def _test_files_label(
    *,
    test_file_count: int | None,
    has_tests: bool | None,
    structure_available: bool,
) -> str:
    if not structure_available:
        return "Unknown"
    if test_file_count is not None:
        return str(test_file_count)
    if has_tests is True:
        return "Detected"
    if has_tests is False:
        return "Not detected"
    return "Unknown"


def _safe_text(value: str) -> str:
    text = redact_secrets(value.replace("\x00", ""))
    text = _AWS_KEY_PATTERN.sub("[REDACTED]", text)
    text = _AWS_SECRET_PATTERN.sub(r"\1[REDACTED]", text)
    return text


def _safe_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    compact = value.strip()
    if not compact:
        return None
    return _safe_text(compact)


def _safe_path(value: str | None) -> str | None:
    if value is None:
        return None
    compact = value.strip()
    if not compact:
        return None
    return _safe_text(sanitize_display_path(compact))


def _safe_relative(path: str) -> str:
    compact = path.replace("\\", "/").strip().lstrip("/")
    if compact.startswith("..") or ":/" in compact or compact.startswith("/"):
        return _safe_text(sanitize_display_path(compact))
    return _safe_text(compact)


__all__ = [
    "HighlightedVersionInput",
    "ReportArtifactInput",
    "build_html_report_view_model",
    "default_report_artifacts",
]
