"""Tests for the AI Modernization Factory command-line interface."""

from typer.testing import CliRunner

from aimf.cli import app

runner = CliRunner()


def test_version_command() -> None:
    """The version command should display the application version."""
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "AI Modernization Factory 0.1.0" in result.stdout


def test_cli_help() -> None:
    """The CLI help should display the application description."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Analyze and modernize legacy enterprise applications" in result.stdout
    assert "version" in result.stdout


def test_scan_help_shows_output_option() -> None:
    result = runner.invoke(app, ["scan", "--help"])

    assert result.exit_code == 0
    assert "--output" in result.stdout
    assert "text" in result.stdout
    assert "json" in result.stdout
