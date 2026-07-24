"""Tests for AIMF configuration loading."""

from pathlib import Path

import pytest

from aimf.config import load_settings


def test_load_settings_reads_repository_configuration(
    tmp_path: Path,
) -> None:
    """Configuration loader should parse repository settings."""

    config_file = tmp_path / "aimf.toml"

    config_file.write_text(
        """
        [repository]
        url = "https://github.com/example/sample-java-app.git"
        branch = "main"

        [workspace]
        directory = ".aimf-workspace"
        clean_before_clone = true
        """,
        encoding="utf-8",
    )

    settings = load_settings(config_file)

    assert str(settings.repository.url) == ("https://github.com/example/sample-java-app.git")
    assert settings.repository.branch == "main"
    assert settings.workspace.directory == Path(".aimf-workspace")
    assert settings.workspace.clean_before_clone is True


def test_load_settings_uses_workspace_defaults(
    tmp_path: Path,
) -> None:
    """Workspace settings should be optional."""

    config_file = tmp_path / "aimf.toml"

    config_file.write_text(
        """
        [repository]
        url = "https://github.com/example/sample-php-app.git"
        """,
        encoding="utf-8",
    )

    settings = load_settings(config_file)

    assert settings.repository.branch is None
    assert settings.workspace.directory == Path(".aimf-workspace")
    assert settings.workspace.clean_before_clone is True


def test_load_settings_reads_static_analysis_configuration(
    tmp_path: Path,
) -> None:
    config_file = tmp_path / "aimf.toml"
    config_file.write_text(
        """
        [repository]
        url = "https://github.com/example/sample-java-app.git"

        [static_analysis]
        enabled = true
        fail_on_provider_error = false

        [static_analysis.pmd]
        enabled = true
        executable = "pmd"
        minimum_priority = 4
        timeout_seconds = 60
        """,
        encoding="utf-8",
    )

    settings = load_settings(config_file)

    assert settings.static_analysis.enabled is True
    assert settings.static_analysis.pmd.minimum_priority == 4
    assert settings.static_analysis.pmd.timeout_seconds == 60


def test_load_settings_accepts_local_repository_path(tmp_path: Path) -> None:
    config_file = tmp_path / "aimf.toml"
    config_file.write_text(
        """
        [repository]
        path = "examples/sample-js-app"
        """,
        encoding="utf-8",
    )
    settings = load_settings(config_file)
    assert settings.repository.path == "examples/sample-js-app"
    assert settings.repository.url is None


def test_load_settings_rejects_empty_repository_section(tmp_path: Path) -> None:
    config_file = tmp_path / "aimf.toml"
    config_file.write_text(
        """
        [repository]
        branch = "main"
        """,
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Configure repository"):
        load_settings(config_file)


def test_load_settings_uses_knowledge_defaults(tmp_path: Path) -> None:
    config_file = tmp_path / "aimf.toml"
    config_file.write_text(
        """
        [repository]
        url = "https://github.com/example/sample-php-app.git"
        """,
        encoding="utf-8",
    )
    settings = load_settings(config_file)
    assert settings.knowledge.directory == Path(".aimf/knowledge")


def test_load_settings_reads_knowledge_directory(tmp_path: Path) -> None:
    config_file = tmp_path / "aimf.toml"
    config_file.write_text(
        """
        [repository]
        path = "examples/sample-js-app"

        [knowledge]
        directory = ".aimf/custom-knowledge"
        """,
        encoding="utf-8",
    )
    settings = load_settings(config_file)
    assert settings.knowledge.directory == Path(".aimf/custom-knowledge")


def test_load_settings_reads_mcp_defaults(tmp_path: Path) -> None:
    config_file = tmp_path / "aimf.toml"
    config_file.write_text(
        """
        [repository]
        path = "examples/sample-js-app"
        """,
        encoding="utf-8",
    )
    settings = load_settings(config_file)
    assert settings.mcp.enabled is True
    assert settings.mcp.transport == "stdio"


def test_load_settings_reads_mcp_section(tmp_path: Path) -> None:
    config_file = tmp_path / "aimf.toml"
    config_file.write_text(
        """
        [repository]
        path = "examples/sample-js-app"

        [mcp]
        enabled = true
        transport = "stdio"
        log_level = "DEBUG"
        """,
        encoding="utf-8",
    )
    settings = load_settings(config_file)
    assert settings.mcp.log_level == "DEBUG"


def test_language_evidence_pipeline_disabled_by_default(tmp_path: Path) -> None:
    config_file = tmp_path / "aimf.toml"
    config_file.write_text(
        """
        [repository]
        path = "."
        """,
        encoding="utf-8",
    )
    settings = load_settings(config_file)
    assert settings.evidence.language.enabled is False
    assert settings.evidence.language.providers.auto_detect is True
    assert settings.evidence.language.python.enabled is True


def test_complexity_evidence_enabled_by_default(tmp_path: Path) -> None:
    config_file = tmp_path / "aimf.toml"
    config_file.write_text(
        """
        [repository]
        path = "."
        """,
        encoding="utf-8",
    )
    settings = load_settings(config_file)
    assert settings.evidence.complexity.enabled is True
    assert settings.evidence.complexity.python.enabled is True
    assert settings.evidence.complexity.java.enabled is True
    assert "/.aimf/" in settings.evidence.complexity.ignore_path_markers


def test_architecture_conclusions_disabled_by_default(tmp_path: Path) -> None:
    config_file = tmp_path / "aimf.toml"
    config_file.write_text(
        """
        [repository]
        path = "."
        """,
        encoding="utf-8",
    )
    settings = load_settings(config_file)
    assert settings.analysis.architecture_conclusions.enabled is False
    assert settings.analysis.architecture_conclusions.policies.positive_boundary_conformance is False


def test_architecture_assessment_section_disabled_by_default(tmp_path: Path) -> None:
    config_file = tmp_path / "aimf.toml"
    config_file.write_text(
        """
        [repository]
        path = "."
        """,
        encoding="utf-8",
    )
    settings = load_settings(config_file)
    assert settings.assessment.sections.architecture.enabled is False
    assert settings.assessment.sections.architecture.include_findings is True
    assert settings.assessment.sections.architecture.include_conclusions is True


def test_architecture_report_section_disabled_by_default(tmp_path: Path) -> None:
    config_file = tmp_path / "aimf.toml"
    config_file.write_text(
        """
        [repository]
        path = "."
        """,
        encoding="utf-8",
    )
    settings = load_settings(config_file)
    assert settings.report.sections.architecture.enabled is False
    assert settings.report.sections.architecture.include_executive_summary is True


def test_technical_debt_gates_disabled_by_default(tmp_path: Path) -> None:
    config_file = tmp_path / "aimf.toml"
    config_file.write_text(
        """
        [repository]
        path = "."
        """,
        encoding="utf-8",
    )
    settings = load_settings(config_file)
    assert settings.rules.technical_debt.enabled is False
    assert settings.assessment.sections.technical_debt.enabled is False
    assert settings.assessment.sections.technical_debt.include_findings is True
    assert settings.report.sections.technical_debt.enabled is False
    assert settings.report.sections.technical_debt.include_executive_summary is True


def test_technical_debt_report_section_can_be_enabled(tmp_path: Path) -> None:
    config_file = tmp_path / "aimf.toml"
    config_file.write_text(
        """
        [repository]
        path = "."

        [report.sections.technical_debt]
        enabled = true
        include_hotspots = false
        """,
        encoding="utf-8",
    )
    settings = load_settings(config_file)
    assert settings.report.sections.technical_debt.enabled is True
    assert settings.report.sections.technical_debt.include_hotspots is False
    assert settings.report.sections.technical_debt.include_themes is True
