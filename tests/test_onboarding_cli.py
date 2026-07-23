"""Onboarding-focused CLI and configuration tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from aimf.cli import app
from aimf.cli.assess import (
    AssessmentCommandError,
    resolve_assessment_repository,
    run_assessment,
)
from aimf.config import AimfSettings, load_settings
from aimf.reporting import AssessmentMode

runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_JS = REPO_ROOT / "examples" / "sample-js-app"


def _settings(**overrides: object) -> AimfSettings:
    payload: dict[str, object] = {
        "repository": {
            "path": str(SAMPLE_JS),
        },
        "workspace": {"directory": ".aimf-workspace", "clean_before_clone": True},
        "static_analysis": {"enabled": False},
        "ai": {"bedrock": {}},
    }
    payload.update(overrides)
    return AimfSettings.model_validate(payload)


def test_resolve_assessment_repository_prefers_cli() -> None:
    settings = _settings(
        repository={
            "path": "/configured/path",
            "url": "https://github.com/example/configured.git",
        }
    )
    assert resolve_assessment_repository("/explicit/repo", settings) == "/explicit/repo"


def test_resolve_assessment_repository_prefers_path_over_url() -> None:
    settings = _settings(
        repository={
            "path": "/configured/path",
            "url": "https://github.com/example/configured.git",
        }
    )
    assert resolve_assessment_repository(None, settings) == "/configured/path"


def test_resolve_assessment_repository_falls_back_to_url() -> None:
    settings = _settings(
        repository={"url": "https://github.com/example/configured.git"},
    )
    assert (
        resolve_assessment_repository(None, settings) == "https://github.com/example/configured.git"
    )


def test_repository_settings_require_url_or_path() -> None:
    with pytest.raises(Exception, match="Configure repository"):
        AimfSettings.model_validate({"repository": {}})


def test_resolve_assessment_repository_missing_raises_actionable_error() -> None:
    settings = AimfSettings.model_validate(
        {
            "repository": {"url": "https://github.com/example/app.git"},
            "static_analysis": {"enabled": False},
        }
    )
    from aimf.cli import assess as assess_module

    original = assess_module.configured_repository_source
    try:
        assess_module.configured_repository_source = lambda _settings: None  # type: ignore[assignment]
        with pytest.raises(AssessmentCommandError, match="No repository configured"):
            resolve_assessment_repository(None, settings)
    finally:
        assess_module.configured_repository_source = original


def test_resolve_assessment_repository_empty_cli_uses_config() -> None:
    settings = _settings(repository={"path": "/from-config"})
    assert resolve_assessment_repository("   ", settings) == "/from-config"


def test_config_driven_javascript_assessment(tmp_path: Path) -> None:
    assert SAMPLE_JS.is_dir()
    output = tmp_path / "reports"
    result = run_assessment(
        repo=None,
        output_directory=output,
        mode=AssessmentMode.DETERMINISTIC,
        settings=_settings(),
        static_analysis_enabled=False,
    )
    assert result.html_report_path.is_file()
    assert result.json_report_path.is_file()
    assert result.technologies_count >= 1
    html = result.html_report_path.read_text(encoding="utf-8")
    assert "JavaScript" in html or "javascript" in html.lower() or "Node" in html
    assert "spring-petclinic" not in html.lower()
    assert ".aimf/workspace" not in str(result.run_directory)


def test_config_driven_javascript_assessment_with_fake_ai(tmp_path: Path) -> None:
    """Config-driven JS path invokes the injected AI provider once (no Bedrock)."""

    from aimf.ai.providers.base import AIModelProvider
    from aimf.ai.providers.models import (
        ModelInvocationMetadata,
        ModelInvocationOptions,
        ModelInvocationResult,
        ModelUsage,
        ModernizationModelRequest,
    )
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

    class CountingFakeProvider(AIModelProvider):
        def __init__(self) -> None:
            self.calls: list[ModernizationModelRequest] = []

        def invoke(
            self,
            request: ModernizationModelRequest,
            options: ModelInvocationOptions,
        ) -> ModelInvocationResult:
            self.calls.append(request)
            recommendation = AIRecommendationResult(
                executive_summary="Executive summary for sample JS app.",
                overall_assessment="Overall assessment for sample JS app.",
                key_risks=["Limited production evidence"],
                recommendations=[
                    AIRecommendation(
                        recommendation_id="AI-REC-001",
                        title="Keep dependencies current",
                        description="Track npm dependency updates.",
                        rationale="Sample app already uses a modern stack.",
                        priority=AIRecommendationPriority.MEDIUM,
                        effort=AIRecommendationEffort.LOW,
                        impact=AIRecommendationImpact.MEDIUM,
                        confidence=AIRecommendationConfidence.HIGH,
                        related_finding_ids=[],
                        suggested_actions=["Review package.json regularly"],
                        dependencies=[],
                    )
                ],
                modernization_phases=[
                    ModernizationPhase(
                        phase=1,
                        name="Stabilize",
                        objective="Keep the current stack healthy.",
                        recommendations=["AI-REC-001"],
                        expected_outcomes=["Predictable dependency posture"],
                    )
                ],
                evidence_coverage=EvidenceCoverage(
                    total_findings=0,
                    findings_considered=0,
                    findings_referenced=0,
                    coverage_percentage=0.0,
                ),
                limitations=["Fixture provider; no Bedrock call"],
            )
            return ModelInvocationResult(
                recommendation_result=recommendation,
                metadata=ModelInvocationMetadata(
                    provider="fake",
                    model_id=options.model_id,
                    request_id="req-js-1",
                    latency_ms=1.0,
                    usage=ModelUsage(input_tokens=1, output_tokens=1, total_tokens=2),
                    stop_reason="end_turn",
                ),
                raw_response_text="{}",
                parsed_model_response=recommendation.model_dump(mode="json"),
            )

    provider = CountingFakeProvider()
    output = tmp_path / "reports"
    result = run_assessment(
        repo=None,
        output_directory=output,
        mode=AssessmentMode.AI_ENHANCED,
        model_id="fake-model",
        settings=_settings(),
        provider=provider,
        static_analysis_enabled=False,
    )
    assert result.html_report_path.is_file()
    assert len(provider.calls) == 1
    assert "spring-petclinic" not in result.html_report_path.read_text(encoding="utf-8").lower()


def test_cli_help_mentions_canonical_workflow() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "aimf assess --config aimf.toml --output reports --with-ai" in result.output

    assess_help = runner.invoke(app, ["assess", "--help"])
    assert assess_help.exit_code == 0
    assert "--repo" in assess_help.output
    assert "--config" in assess_help.output
    assert "aimf.toml" in assess_help.output


def test_readme_documents_canonical_workflow() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "aimf assess --config aimf.toml --output reports --with-ai" in readme
    assert "spring-petclinic" not in readme.lower()
    assert "spring petclinic" not in readme.lower()
    assert ".aimf/workspace/spring-petclinic" not in readme
    assert "ModuleNotFoundError" in readme
    assert "python -m pip install -e ." in readme
    assert 'python -c "import aimf; print(aimf.__file__)"' in readme
    assert "Cloning the repository does **not** install" in readme
    assert "aws sso login --profile <profile-name>" in readme
    assert "aimf help" not in readme


def test_shipped_aimf_toml_uses_sample_js_not_petclinic() -> None:
    text = (REPO_ROOT / "aimf.toml").read_text(encoding="utf-8")
    assert "examples/sample-js-app" in text
    assert "spring-petclinic" not in text
    settings = load_settings(REPO_ROOT / "aimf.toml")
    assert settings.repository.path == "examples/sample-js-app"
    assert settings.repository.url is None


def test_cli_assess_config_path_without_repo(tmp_path: Path) -> None:
    config = tmp_path / "aimf.toml"
    config.write_text(
        f"""
[repository]
path = "{SAMPLE_JS.as_posix()}"

[static_analysis]
enabled = false
""",
        encoding="utf-8",
    )
    output = tmp_path / "out"
    result = runner.invoke(
        app,
        [
            "assess",
            "--config",
            str(config),
            "--output",
            str(output),
            "--no-static-analysis",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Modernization assessment completed" in result.output
    runs = list(output.glob("*/*"))
    assert runs
    assert (runs[0] / "report.html").is_file()


def test_cli_repo_overrides_config(tmp_path: Path) -> None:
    other = tmp_path / "other-app"
    other.mkdir()
    (other / "package.json").write_text(
        '{"name":"other-app","version":"1.0.0"}',
        encoding="utf-8",
    )
    (other / "index.js").write_text("console.log('hi')\n", encoding="utf-8")

    config = tmp_path / "aimf.toml"
    config.write_text(
        f"""
[repository]
path = "{SAMPLE_JS.as_posix()}"

[static_analysis]
enabled = false
""",
        encoding="utf-8",
    )
    output = tmp_path / "out"
    result = runner.invoke(
        app,
        [
            "assess",
            "--config",
            str(config),
            "--repo",
            str(other),
            "--output",
            str(output),
            "--no-static-analysis",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "other-app" in result.output


def test_cli_missing_repository_errors_clearly(tmp_path: Path) -> None:
    config = tmp_path / "aimf.toml"
    config.write_text(
        """
[repository]
url = "https://github.com/example/placeholder.git"

[static_analysis]
enabled = false
""",
        encoding="utf-8",
    )
    # Empty --repo should fall back to url; to force missing, omit both via patch:
    from aimf.cli import assess as assess_module

    original = assess_module.configured_repository_source

    def _none(_settings: AimfSettings) -> None:
        return None

    assess_module.configured_repository_source = _none  # type: ignore[assignment]
    try:
        result = runner.invoke(
            app,
            ["assess", "--config", str(config), "--output", str(tmp_path / "out")],
        )
    finally:
        assess_module.configured_repository_source = original

    assert result.exit_code != 0
    assert "No repository configured" in result.output
    assert "--repo" in result.output
