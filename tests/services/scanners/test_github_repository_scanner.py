"""Tests for the public GitHub repository scanner."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from aimf.models import Repository
from aimf.services.scanners import GitHubRepositoryScanner


def test_github_scanner_clones_and_scans_repository(
    tmp_path: Path,
) -> None:
    """GitHub scanner should clone and delegate local scanning."""

    local_scanner = Mock()

    local_scanner.scan.return_value = Repository(
        name="sample-app",
        path=tmp_path / "workspace" / "sample-app",
        files=["pom.xml"],
        total_files=1,
    )

    scanner = GitHubRepositoryScanner(
        workspace_directory=tmp_path / "workspace",
        branch="main",
        local_scanner=local_scanner,
    )

    repository_url = (
        "https://github.com/example/sample-app.git"
    )

    with patch("subprocess.run") as run_mock:
        repository = scanner.scan(repository_url)

    run_mock.assert_called_once_with(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "--branch",
            "main",
            "--single-branch",
            repository_url,
            str(tmp_path / "workspace" / "sample-app"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    local_scanner.scan.assert_called_once_with(
        tmp_path / "workspace" / "sample-app"
    )

    assert repository.name == "sample-app"
    assert repository.source_url == repository_url
    assert repository.default_branch == "main"


def test_github_scanner_rejects_non_github_url(
    tmp_path: Path,
) -> None:
    """Scanner should reject unsupported repository hosts."""

    scanner = GitHubRepositoryScanner(
        workspace_directory=tmp_path,
    )

    with pytest.raises(
        ValueError,
        match="Only public GitHub repositories",
    ):
        scanner.scan(
            "https://gitlab.com/example/sample-app.git"
        )


def test_github_scanner_rejects_invalid_github_path(
    tmp_path: Path,
) -> None:
    """Scanner should require an owner and repository name."""

    scanner = GitHubRepositoryScanner(
        workspace_directory=tmp_path,
    )

    with pytest.raises(
        ValueError,
        match="owner and repository name",
    ):
        scanner.scan("https://github.com/example")


def test_github_scanner_reports_clone_failure(
    tmp_path: Path,
) -> None:
    """Scanner should convert Git failures into readable errors."""

    scanner = GitHubRepositoryScanner(
        workspace_directory=tmp_path,
    )

    clone_error = subprocess.CalledProcessError(
        returncode=128,
        cmd=["git", "clone"],
        stderr="Repository not found",
    )

    with (
        patch(
            "subprocess.run",
            side_effect=clone_error,
        ),
        pytest.raises(
            RuntimeError,
            match="Repository not found",
        ),
    ):
        scanner.scan(
            "https://github.com/example/missing-app.git"
        )