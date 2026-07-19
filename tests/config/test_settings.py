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

    assert str(settings.repository.url) == (
        "https://github.com/example/sample-java-app.git"
    )
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


def test_load_settings_rejects_missing_file(
    tmp_path: Path,
) -> None:
    """Configuration loader should reject nonexistent files."""

    missing_file = tmp_path / "missing.toml"

    with pytest.raises(FileNotFoundError):
        load_settings(missing_file)