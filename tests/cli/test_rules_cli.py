"""CLI tests for aimf rules (Phase 4.1)."""

from __future__ import annotations

from typer.testing import CliRunner

from aimf.cli import app

runner = CliRunner()


def test_rules_help() -> None:
    result = runner.invoke(app, ["rules", "--help"])
    assert result.exit_code == 0
    assert "list" in result.stdout
    assert "inspect" in result.stdout


def test_rules_list_empty_production() -> None:
    result = runner.invoke(app, ["rules", "list", "--json"])
    assert result.exit_code == 0
    assert '"rules": []' in result.stdout or '"rules":[]' in result.stdout.replace(" ", "")


def test_rules_inspect_unknown() -> None:
    result = runner.invoke(app, ["rules", "inspect", "fixture.always-match"])
    assert result.exit_code == 1


def test_assess_still_present() -> None:
    result = runner.invoke(app, ["assess", "--help"])
    assert result.exit_code == 0
    assert "Assess a repository" in result.stdout
