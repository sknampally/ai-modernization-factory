"""Tests for the modernization assessment HTML report."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from aimf.ai.agents.models import (
    AGENT_VERSION,
    AgentExecutionStatus,
    AgentExecutionTrace,
    ModernizationAssessmentResult,
)
from aimf.ai.contracts.models import (
    LLMAnalysisContext,
    LLMEvidenceLocation,
    LLMFindingEvidence,
    LLMMetricsContext,
    LLMRepositoryContext,
    LLMSectionTruncation,
    LLMTechnologyEvidence,
    LLM_CONTRACT_SCHEMA_VERSION,
)
from aimf.ai.providers.models import ModelInvocationMetadata, ModelUsage
from aimf.ai.recommendations import (
    AIRecommendation,
    AIRecommendationConfidence,
    AIRecommendationEffort,
    AIRecommendationImpact,
    AIRecommendationPriority,
    AIRecommendationResult,
    EvidenceCoverage,
    ModernizationPhase,
)
from aimf.models import (
    AnalysisResult,
    Evidence,
    Finding,
    FindingCategory,
    FindingSource,
    Repository,
    RepositoryFacts,
    Severity,
    StructureFacts,
    Technology,
    TechnologyCategory,
)
from aimf.reporting import (
    CONTENT_SECURITY_POLICY,
    ModernizationHTMLReportRenderer,
    ModernizationReportInput,
    ModernizationReportValidationError,
    modernization_report_input_from_json,
    modernization_report_input_to_json,
    sanitize_display_path,
    write_modernization_html_report,
)


def _truncation(
    count: int = 0, *, truncated: bool = False, original: int | None = None
) -> LLMSectionTruncation:
    return LLMSectionTruncation(
        truncated=truncated,
        original_count=original if original is not None else count,
        included_count=count,
    )


def _analysis_result(tmp_path: Path, *, repo_name: str = "sample-app") -> AnalysisResult:
    return AnalysisResult(
        repository=Repository(
            name=repo_name,
            path=tmp_path / "workspace" / repo_name,
            source_url="https://github.com/example/sample-app.git",
            default_branch="main",
            files=["src/App.java", "pom.xml"],
            total_files=2,
        ),
        technologies=[
            Technology(
                name="Java",
                category=TechnologyCategory.LANGUAGE,
                version="17",
                confidence=1.0,
                source="test",
            ),
            Technology(
                name="Maven",
                category=TechnologyCategory.BUILD_TOOL,
                confidence=1.0,
                source="test",
            ),
        ],
        facts=RepositoryFacts(
            structure=StructureFacts(
                file_count=2,
                source_file_count=1,
                test_file_count=0,
            )
        ),
        findings=[
            Finding(
                rule_id="SEC001",
                title="Critical finding",
                description="Secret exposure risk",
                category=FindingCategory.SECURITY,
                severity=Severity.CRITICAL,
                source=FindingSource.DETERMINISTIC,
                evidence=[
                    Evidence(file_path=".", description="Whole repository"),
                    Evidence(file_path="src/App.java", line_number=10),
                ],
                affected_technologies=["Java"],
            ),
            Finding(
                rule_id="SEC002",
                title="Medium finding",
                description="Dependency hygiene",
                category=FindingCategory.SECURITY,
                severity=Severity.MEDIUM,
                source=FindingSource.DETERMINISTIC,
                evidence=[Evidence(file_path="pom.xml", line_number=4)],
                affected_technologies=["Maven"],
            ),
        ],
    )


def _context(*, repo_name: str = "sample-app", truncated: bool = False) -> LLMAnalysisContext:
    findings = [
        LLMFindingEvidence(
            rule_id="SEC001",
            title="Critical finding",
            category="security",
            severity="critical",
            summary="Secret exposure risk",
            evidence=[LLMEvidenceLocation(path=".")],
            evidence_truncation=_truncation(1),
        ),
        LLMFindingEvidence(
            rule_id="SEC002",
            title="Medium finding",
            category="security",
            severity="medium",
            summary="Dependency hygiene",
            evidence_truncation=_truncation(),
        ),
    ]
    return LLMAnalysisContext(
        repository=LLMRepositoryContext(
            name=repo_name,
            source_type="github",
            default_branch="main",
            commit_sha="abc1234",
            file_count=2,
        ),
        technologies=[
            LLMTechnologyEvidence(name="Java", category="language", version="17"),
            LLMTechnologyEvidence(name="Maven", category="build_tool"),
        ],
        metrics=LLMMetricsContext(
            file_count=2,
            source_file_count=1,
            test_file_count=0,
            finding_count=2,
            technology_count=2,
        ),
        findings=findings,
        findings_truncation=_truncation(
            count=2,
            truncated=truncated,
            original=5 if truncated else 2,
        ),
    )


def _recommendation(
    recommendation_id: str,
    *,
    related: list[str] | None = None,
    dependencies: list[str] | None = None,
    priority: AIRecommendationPriority = AIRecommendationPriority.HIGH,
) -> AIRecommendation:
    return AIRecommendation(
        recommendation_id=recommendation_id,
        title=f"Title {recommendation_id}",
        description=f"Description {recommendation_id}",
        rationale=f"Rationale {recommendation_id}",
        priority=priority,
        effort=AIRecommendationEffort.MEDIUM,
        impact=AIRecommendationImpact.HIGH,
        confidence=AIRecommendationConfidence.MEDIUM,
        related_finding_ids=related or [],
        suggested_actions=["Implement control"],
        dependencies=dependencies or [],
    )


def _assessment(
    *,
    related_ok: bool = True,
    raw_response: str | None = '<script>alert("x")</script>',
) -> ModernizationAssessmentResult:
    related_one = ["SEC001"] if related_ok else ["MISSING"]
    result = AIRecommendationResult(
        executive_summary="Executive summary of modernization opportunities.",
        overall_assessment="The application is moderately ready for modernization.",
        key_risks=["Secret exposure", "Weak dependency controls"],
        recommendations=[
            _recommendation("REC-001", related=related_one),
            _recommendation(
                "REC-002",
                related=["SEC002"] if related_ok else [],
                dependencies=["REC-001"],
                priority=AIRecommendationPriority.MEDIUM,
            ),
        ],
        modernization_phases=[
            ModernizationPhase(
                phase=1,
                name="Stabilize",
                objective="Reduce critical risk",
                recommendations=["REC-001"],
                expected_outcomes=["Lower exposure"],
            ),
            ModernizationPhase(
                phase=2,
                name="Hardening",
                objective="Improve dependency hygiene",
                recommendations=["REC-002"],
                expected_outcomes=["Safer builds"],
            ),
        ],
        evidence_coverage=EvidenceCoverage(
            total_findings=2,
            findings_considered=2,
            findings_referenced=2,
            coverage_percentage=100.0,
            input_truncated=False,
        ),
        limitations=["No runtime profiling data was available."],
    )
    return ModernizationAssessmentResult(
        recommendation_result=result,
        model_metadata=ModelInvocationMetadata(
            provider="fake",
            model_id="test-model",
            request_id="req-1",
            latency_ms=42.5,
            usage=ModelUsage(input_tokens=11, output_tokens=22, total_tokens=33),
            stop_reason="end_turn",
        ),
        trace=AgentExecutionTrace(
            trace_id="trace-1",
            started_at_utc=datetime(2026, 7, 21, 12, 0, tzinfo=UTC),
            completed_at_utc=datetime(2026, 7, 21, 12, 1, tzinfo=UTC),
            total_latency_ms=1000.0,
            status=AgentExecutionStatus.COMPLETED,
            steps=(),
            tool_call_count=5,
            model_call_count=1,
            input_tokens=11,
            output_tokens=22,
            total_tokens=33,
        ),
        raw_model_response=raw_response,
    )


def _report_input(
    tmp_path: Path,
    *,
    truncated: bool = False,
    organization_name: str | None = "Example Org",
    confidentiality_notice: str | None = "Internal use only",
    assessment: ModernizationAssessmentResult | None = None,
    analysis: AnalysisResult | None = None,
    context: LLMAnalysisContext | None = None,
) -> ModernizationReportInput:
    return ModernizationReportInput(
        analysis_result=analysis or _analysis_result(tmp_path),
        analysis_context=context or _context(truncated=truncated),
        assessment_result=assessment or _assessment(),
        generated_at_utc=datetime(2026, 7, 21, 15, 30, tzinfo=UTC),
        organization_name=organization_name,
        confidentiality_notice=confidentiality_notice,
    )


def test_complete_report_rendering(tmp_path: Path) -> None:
    html = ModernizationHTMLReportRenderer().render(_report_input(tmp_path, truncated=True))
    assert "<!DOCTYPE html>" in html
    assert "Modernization Assessment" in html
    assert "sample-app" in html
    assert "Example Org" in html
    assert "Internal use only" in html
    assert "Executive summary of modernization opportunities." in html
    assert "Repository Overview" in html
    assert "Key Risks" in html
    assert "Recommendations" in html
    assert "Modernization Roadmap" in html
    assert "Deterministic Findings" in html
    assert "Evidence Coverage and Limitations" in html
    assert "Assessment Execution Details" in html
    assert "Methodology" in html
    assert "Context truncation warning" in html
    assert AGENT_VERSION in html
    assert LLM_CONTRACT_SCHEMA_VERSION in html


def test_minimal_valid_report(tmp_path: Path) -> None:
    assessment = _assessment()
    minimal = ModernizationReportInput(
        analysis_result=_analysis_result(tmp_path),
        analysis_context=_context(),
        assessment_result=assessment,
        generated_at_utc=datetime(2026, 7, 21, 15, 30, tzinfo=UTC),
    )
    html = ModernizationHTMLReportRenderer().render(minimal)
    assert "Modernization Assessment" in html
    assert "sample-app" in html


def test_deterministic_output(tmp_path: Path) -> None:
    report_input = _report_input(tmp_path)
    renderer = ModernizationHTMLReportRenderer()
    assert renderer.render(report_input) == renderer.render(report_input)


def test_executive_summary_and_ai_label(tmp_path: Path) -> None:
    html = ModernizationHTMLReportRenderer().render(_report_input(tmp_path))
    assert "AI-generated interpretation based on deterministic evidence" in html
    assert "100.00%" in html


def test_repository_overview_technology_and_metrics(tmp_path: Path) -> None:
    html = ModernizationHTMLReportRenderer().render(_report_input(tmp_path))
    assert "Java" in html
    assert "Maven" in html
    assert "Files analyzed" in html
    assert "Findings (analysis)" in html


def test_risks_recommendations_and_phases(tmp_path: Path) -> None:
    html = ModernizationHTMLReportRenderer().render(_report_input(tmp_path))
    assert "REC-001" in html
    assert "Title REC-001" in html
    assert "Phase 1: Stabilize" in html
    assert "Reduce critical risk" in html
    assert "EFFORT MEDIUM" in html
    assert "IMPACT HIGH" in html
    assert "CONFIDENCE MEDIUM" in html


def test_deterministic_findings_and_anchors(tmp_path: Path) -> None:
    html = ModernizationHTMLReportRenderer().render(_report_input(tmp_path))
    assert 'id="finding-sec001"' in html
    assert 'href="#finding-sec001"' in html
    assert "Repository-level analysis" in html
    assert "src/App.java:10" in html
    assert "Deterministic analysis evidence" in html


def test_evidence_coverage_limitations_and_validation_note(tmp_path: Path) -> None:
    html = ModernizationHTMLReportRenderer().render(_report_input(tmp_path, truncated=True))
    assert "Findings excluded by truncation" in html
    assert "No runtime profiling data was available." in html
    assert "Recommendations require engineering validation" in html


def test_execution_metadata(tmp_path: Path) -> None:
    html = ModernizationHTMLReportRenderer().render(_report_input(tmp_path))
    assert "fake" in html
    assert "test-model" in html
    assert "42.50" in html
    assert "Tool-call count" in html
    assert ">5<" in html or ">5</dd>" in html
    assert "Model-call count" in html


def test_methodology_toc_print_css_and_csp(tmp_path: Path) -> None:
    html = ModernizationHTMLReportRenderer().render(_report_input(tmp_path))
    assert 'id="contents"' in html
    assert 'href="#executive-summary"' in html
    assert "@media print" in html
    assert "page-break-before: always" in html
    assert "Content-Security-Policy" in html
    assert CONTENT_SECURITY_POLICY.split(";")[0] in html
    assert "script-src 'none'" in html
    assert "Deterministic repository analysis" in html


def test_html_escaping_and_injection_prevention(tmp_path: Path) -> None:
    poisoned = _assessment()
    poisoned = ModernizationAssessmentResult(
        recommendation_result=AIRecommendationResult(
            executive_summary='<script>alert("xss")</script>',
            overall_assessment='<img src=x onerror=alert(1)>',
            key_risks=['<b>bold</b>'],
            recommendations=[
                _recommendation("REC-001", related=["SEC001"]),
            ],
            modernization_phases=[],
            evidence_coverage=EvidenceCoverage(
                total_findings=1,
                findings_considered=1,
                findings_referenced=1,
                coverage_percentage=100.0,
            ),
            limitations=['<iframe src="http://evil"></iframe>'],
        ),
        model_metadata=poisoned.model_metadata,
        trace=poisoned.trace,
        raw_model_response='{"prompt":"SYSTEM INSTRUCTIONS","secret":"AKIAIOSFODNN7EXAMPLE"}',
    )
    html = ModernizationHTMLReportRenderer().render(
        _report_input(
            tmp_path,
            assessment=poisoned,
            organization_name='<script>org</script>',
            confidentiality_notice='<svg onload=alert(1)>',
        )
    )
    assert "<script>alert" not in html
    assert "&lt;script&gt;alert" in html
    assert "<img src=x" not in html
    assert "<iframe" not in html
    assert "onload=" not in html


def test_absence_of_raw_response_prompts_excerpts_credentials(tmp_path: Path) -> None:
    assessment = _assessment(
        raw_response=(
            "SYSTEM INSTRUCTIONS Developer instructions "
            "AKIAIOSFODNN7EXAMPLE excerpt=class App {}"
        )
    )
    html = ModernizationHTMLReportRenderer().render(
        _report_input(tmp_path, assessment=assessment)
    )
    assert "AKIAIOSFODNN7EXAMPLE" not in html
    assert "SYSTEM INSTRUCTIONS" not in html
    assert "Developer instructions" not in html
    assert "excerpt=class App {}" not in html
    assert assessment.raw_model_response not in html
    assert str(tmp_path / "workspace" / "sample-app") not in html


def test_repository_path_sanitization() -> None:
    assert sanitize_display_path("/var/tmp/project/src/App.java") == "App.java"
    assert sanitize_display_path("src/App.java") == "src/App.java"
    assert sanitize_display_path(".") == "."


def test_inconsistent_repository_rejection(tmp_path: Path) -> None:
    with pytest.raises(ModernizationReportValidationError, match="Inconsistent repository"):
        ModernizationHTMLReportRenderer().render(
            _report_input(
                tmp_path,
                analysis=_analysis_result(tmp_path, repo_name="alpha"),
                context=_context(repo_name="beta"),
            )
        )


def test_invalid_recommendation_reference_rejection(tmp_path: Path) -> None:
    with pytest.raises(ModernizationReportValidationError, match="related_finding_ids|resolve"):
        ModernizationHTMLReportRenderer().render(
            _report_input(tmp_path, assessment=_assessment(related_ok=False))
        )


def test_invalid_phase_reference_rejection(tmp_path: Path) -> None:
    base = _assessment()
    broken = AIRecommendationResult.model_construct(
        schema_version=base.recommendation_result.schema_version,
        executive_summary=base.recommendation_result.executive_summary,
        overall_assessment=base.recommendation_result.overall_assessment,
        key_risks=base.recommendation_result.key_risks,
        recommendations=base.recommendation_result.recommendations,
        modernization_phases=[
            ModernizationPhase.model_construct(
                phase=1,
                name="Broken",
                objective="Objective",
                recommendations=["REC-999"],
                expected_outcomes=[],
            )
        ],
        evidence_coverage=base.recommendation_result.evidence_coverage,
        limitations=base.recommendation_result.limitations,
    )
    assessment = ModernizationAssessmentResult(
        recommendation_result=broken,
        model_metadata=base.model_metadata,
        trace=base.trace,
        raw_model_response=None,
    )
    with pytest.raises(ModernizationReportValidationError, match="Phase recommendation"):
        ModernizationHTMLReportRenderer().render(
            _report_input(tmp_path, assessment=assessment)
        )


def test_json_round_trip(tmp_path: Path) -> None:
    report_input = _report_input(tmp_path)
    restored = modernization_report_input_from_json(
        modernization_report_input_to_json(report_input)
    )
    assert restored.report_title == report_input.report_title
    assert restored.analysis_context.repository.name == "sample-app"
    assert restored.assessment_result.model_metadata.model_id == "test-model"


def test_file_writing(tmp_path: Path) -> None:
    output = tmp_path / "out" / "modernization.html"
    path = write_modernization_html_report(_report_input(tmp_path), output)
    assert path == output
    content = output.read_text(encoding="utf-8")
    assert "Modernization Assessment" in content


def test_no_external_assets_or_scripts(tmp_path: Path) -> None:
    html = ModernizationHTMLReportRenderer().render(_report_input(tmp_path))
    assert "<script" not in html.lower()
    assert "onclick=" not in html.lower()
    assert "http://" not in html or "https://github.com/example/sample-app.git" not in html
    assert "https://" not in html.replace("https://github.com/example/sample-app.git", "")
    assert "cdn." not in html.lower()
    assert "@import" not in html.lower()
    assert "<link " not in html.lower()


def test_frozen_input_contract(tmp_path: Path) -> None:
    report_input = _report_input(tmp_path)
    with pytest.raises(ValidationError):
        report_input.report_title = "Changed"
    with pytest.raises(ValidationError):
        ModernizationReportInput(
            analysis_result=_analysis_result(tmp_path),
            analysis_context=_context(),
            assessment_result=_assessment(),
            generated_at_utc=datetime(2026, 7, 21, 15, 30, tzinfo=UTC),
            unexpected=True,  # type: ignore[call-arg]
        )
