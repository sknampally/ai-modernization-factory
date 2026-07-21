"""Tests for PMD command construction."""

from pathlib import Path

from aimf.static_analysis.providers.pmd_command import PmdCommandBuilder


def test_analyze_command_is_argument_list_without_shell() -> None:
    command = PmdCommandBuilder("pmd").analyze_command(
        source_roots=[Path("/tmp/my repo/src/main/java")],
        rulesets=["category/java/bestpractices.xml"],
        report_file=Path("/tmp/report.xml"),
        minimum_priority=5,
    )

    assert command.args[0] == "pmd"
    assert "check" in command.args
    assert "--dir" in command.args
    assert "/tmp/my repo/src/main/java" in command.args
    assert "--rulesets" in command.args
    assert "category/java/bestpractices.xml" in command.args
    assert "--minimum-priority" in command.args
    assert "5" in command.args
    assert all(";" not in arg for arg in command.args)


def test_version_command() -> None:
    command = PmdCommandBuilder("/opt/pmd/bin/pmd").version_command()
    assert command.args == ["/opt/pmd/bin/pmd", "--version"]
