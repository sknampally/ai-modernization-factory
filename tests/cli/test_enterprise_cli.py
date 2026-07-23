"""CLI tests for aimf enterprise."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from aimf.cli import app

runner = CliRunner()


def test_enterprise_help() -> None:
    result = runner.invoke(app, ["enterprise", "--help"])
    assert result.exit_code == 0
    assert "init" in result.stdout
    assert "validate" in result.stdout
    assert "build" in result.stdout


def test_enterprise_init_and_validate(tmp_path: Path) -> None:
    workspace = tmp_path / "enterprise"
    config = tmp_path / "aimf.toml"
    config.write_text(
        f"""
        [repository]
        path = "examples/sample-js-app"
        [knowledge]
        directory = "{tmp_path / "knowledge"}"
        [enterprise]
        enabled = false
        """,
        encoding="utf-8",
    )
    init = runner.invoke(
        app,
        ["enterprise", "init", str(workspace), "--examples"],
    )
    assert init.exit_code == 0
    validate = runner.invoke(
        app,
        ["enterprise", "validate", str(workspace), "--config", str(config)],
    )
    assert validate.exit_code == 0
    build = runner.invoke(
        app,
        ["enterprise", "build", str(workspace), "--config", str(config), "--json"],
    )
    assert build.exit_code == 0
    assert "graph_id" in build.stdout
