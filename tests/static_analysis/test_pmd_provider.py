"""Tests for PMD provider execution semantics with mocked processes."""

from __future__ import annotations

import subprocess
from pathlib import Path

from aimf.models import Repository, Technology
from aimf.models.enums import TechnologyCategory
from aimf.static_analysis.models import StaticAnalysisContext, StaticAnalysisStatus
from aimf.static_analysis.providers.pmd_provider import PmdProvider


class _FakeRunner:
    def __init__(self, responses: list[subprocess.CompletedProcess[str]]) -> None:
        self.responses = list(responses)
        self.calls: list[list[str]] = []

    def __call__(self, args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        del kwargs
        self.calls.append(list(args))
        if not self.responses:
            raise AssertionError("unexpected process call")
        return self.responses.pop(0)


def _context(tmp_path: Path) -> StaticAnalysisContext:
    java = tmp_path / "src/main/java/example/Foo.java"
    java.parent.mkdir(parents=True)
    java.write_text("class Foo {}", encoding="utf-8")
    repository = Repository(
        name="sample",
        path=tmp_path,
        files=["src/main/java/example/Foo.java"],
    )
    return StaticAnalysisContext(
        repository=repository,
        repository_path=str(tmp_path),
        detected_technologies=[
            Technology(name="Java", category=TechnologyCategory.LANGUAGE, confidence=1.0)
        ],
    )


def test_pmd_unavailable() -> None:
    runner = _FakeRunner(
        [
            subprocess.CompletedProcess(
                args=["pmd", "--version"],
                returncode=127,
                stdout="",
                stderr="not found",
            )
        ]
    )
    provider = PmdProvider(process_runner=runner)
    assert provider.is_available() is False


def test_nonzero_exit_with_valid_violations_is_completed(tmp_path: Path) -> None:
    source = tmp_path / "src/main/java/example/Foo.java"
    xml = f"""<?xml version="1.0"?>
    <pmd>
      <file name="{source}">
        <violation beginline="1" rule="UnusedPrivateField"
          ruleset="Best Practices" priority="5">unused</violation>
      </file>
    </pmd>
    """

    def runner(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        del kwargs
        if "--version" in args:
            return subprocess.CompletedProcess(args, 0, stdout="PMD 7.1.0", stderr="")
        report_file = Path(args[args.index("--report-file") + 1])
        report_file.write_text(xml, encoding="utf-8")
        return subprocess.CompletedProcess(args, 4, stdout="", stderr="")

    provider = PmdProvider(process_runner=runner)
    result = provider.analyze(_context(tmp_path))
    assert result.status == StaticAnalysisStatus.COMPLETED
    assert len(result.findings) == 1
    assert result.findings[0].evidence[0].file_path.startswith("src/")


def test_applicability_requires_java(tmp_path: Path) -> None:
    provider = PmdProvider(
        process_runner=lambda *args, **kwargs: subprocess.CompletedProcess(
            args=["pmd"], returncode=0, stdout="7.0.0", stderr=""
        )
    )
    context = StaticAnalysisContext(
        repository=Repository(name="js", path=tmp_path, files=["index.js"]),
        repository_path=str(tmp_path),
        detected_technologies=[],
    )
    assert provider.is_applicable(context) is False
