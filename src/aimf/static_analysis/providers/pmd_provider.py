"""PMD static-analysis provider."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path
from time import perf_counter

from aimf.models.repository import Repository
from aimf.models.technology import Technology
from aimf.static_analysis.models import (
    StaticAnalysisContext,
    StaticAnalysisResult,
    StaticAnalysisStatus,
)
from aimf.static_analysis.providers.pmd_command import PmdCommandBuilder
from aimf.static_analysis.providers.pmd_parser import PmdParser

_JAVA_SOURCE_ROOTS = (
    "src/main/java",
    "src/test/java",
)

_EXCLUDED_DIRECTORY_NAMES = frozenset(
    {
        ".git",
        ".aimf",
        ".idea",
        ".venv",
        "venv",
        "build",
        "target",
        "generated",
        "node_modules",
        "vendor",
        "reports",
        "dist",
        "__pycache__",
    }
)


class PmdProvider:
    """Run PMD against Java repositories and normalize findings."""

    def __init__(
        self,
        *,
        executable: str = "pmd",
        rulesets: Sequence[str] | None = None,
        minimum_priority: int = 5,
        timeout_seconds: int = 120,
        enabled: bool = True,
        command_builder: PmdCommandBuilder | None = None,
        parser: PmdParser | None = None,
        process_runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    ) -> None:
        self._executable = executable
        self._rulesets = list(
            rulesets
            or (
                "category/java/bestpractices.xml",
                "category/java/errorprone.xml",
                "category/java/design.xml",
            )
        )
        self._minimum_priority = minimum_priority
        self._timeout_seconds = timeout_seconds
        self._enabled = enabled
        self._command_builder = command_builder or PmdCommandBuilder(executable)
        self._parser = parser or PmdParser()
        self._process_runner = process_runner or subprocess.run
        self._cached_version: str | None | bool = False

    @property
    def provider_id(self) -> str:
        return "pmd"

    @property
    def display_name(self) -> str:
        return "PMD"

    @property
    def supported_languages(self) -> frozenset[str]:
        return frozenset({"Java"})

    def is_available(self) -> bool:
        if self._cached_version is False:
            self._cached_version = self._resolve_version()
        return self._cached_version is not None

    def is_applicable(self, context: StaticAnalysisContext) -> bool:
        if not self._enabled:
            return False
        return self._repository_has_java(
            repository=context.repository,
            technologies=context.detected_technologies,
        )

    def analyze(self, context: StaticAnalysisContext) -> StaticAnalysisResult:
        started = perf_counter()
        version = self._resolve_version()
        if version is None:
            return StaticAnalysisResult(
                provider_id=self.provider_id,
                provider_name=self.display_name,
                status=StaticAnalysisStatus.UNAVAILABLE,
                error_message="PMD executable was not found.",
                warnings=["PMD executable was not found."],
            )

        repository_path = Path(context.repository_path)
        source_roots = self._resolve_source_roots(
            repository=context.repository,
            repository_path=repository_path,
        )
        if not source_roots:
            return StaticAnalysisResult(
                provider_id=self.provider_id,
                provider_name=self.display_name,
                provider_version=version,
                status=StaticAnalysisStatus.SKIPPED,
                warnings=["No Java source roots were found for PMD analysis."],
                duration_ms=round((perf_counter() - started) * 1000, 2),
            )

        with tempfile.TemporaryDirectory(prefix="aimf-pmd-") as temp_directory:
            report_file = Path(temp_directory) / "pmd-report.xml"
            command = self._command_builder.analyze_command(
                source_roots=source_roots,
                rulesets=self._rulesets,
                report_file=report_file,
                minimum_priority=self._minimum_priority,
            )

            try:
                completed = self._run_process(command.args)
            except subprocess.TimeoutExpired:
                return StaticAnalysisResult(
                    provider_id=self.provider_id,
                    provider_name=self.display_name,
                    provider_version=version,
                    status=StaticAnalysisStatus.FAILED,
                    duration_ms=round((perf_counter() - started) * 1000, 2),
                    command_metadata=self._sanitize_command_metadata(command.metadata),
                    error_message="PMD analysis timed out.",
                    warnings=["PMD analysis timed out."],
                )

            if completed.returncode not in {0, 4} and not report_file.exists():
                # Retry once with legacy CLI if the modern command is unrecognized.
                legacy = self._command_builder.legacy_analyze_command(
                    source_roots=source_roots,
                    rulesets=self._rulesets,
                    report_file=report_file,
                    minimum_priority=self._minimum_priority,
                )
                try:
                    completed = self._run_process(legacy.args)
                except subprocess.TimeoutExpired:
                    return StaticAnalysisResult(
                        provider_id=self.provider_id,
                        provider_name=self.display_name,
                        provider_version=version,
                        status=StaticAnalysisStatus.FAILED,
                        duration_ms=round((perf_counter() - started) * 1000, 2),
                        command_metadata=self._sanitize_command_metadata(legacy.metadata),
                        error_message="PMD analysis timed out.",
                        warnings=["PMD analysis timed out."],
                    )
                command = legacy

            if completed.returncode not in {0, 4} and not report_file.exists():
                return StaticAnalysisResult(
                    provider_id=self.provider_id,
                    provider_name=self.display_name,
                    provider_version=version,
                    status=StaticAnalysisStatus.FAILED,
                    duration_ms=round((perf_counter() - started) * 1000, 2),
                    command_metadata=self._sanitize_command_metadata(command.metadata),
                    error_message=self._sanitize_error(
                        completed.stderr or completed.stdout or "PMD failed"
                    ),
                    warnings=["PMD analysis failed."],
                )

            report_xml = ""
            if report_file.exists():
                report_xml = report_file.read_text(encoding="utf-8", errors="replace")
            elif completed.stdout:
                report_xml = completed.stdout

            try:
                findings = self._parser.parse(
                    report_xml,
                    repository_path=repository_path,
                    provider_version=version,
                )
            except ValueError as exc:
                return StaticAnalysisResult(
                    provider_id=self.provider_id,
                    provider_name=self.display_name,
                    provider_version=version,
                    status=StaticAnalysisStatus.FAILED,
                    duration_ms=round((perf_counter() - started) * 1000, 2),
                    command_metadata=self._sanitize_command_metadata(command.metadata),
                    error_message=str(exc),
                    warnings=[str(exc)],
                )

            files_analyzed = len(
                {finding.evidence[0].file_path for finding in findings if finding.evidence}
            )
            return StaticAnalysisResult(
                provider_id=self.provider_id,
                provider_name=self.display_name,
                provider_version=version,
                status=StaticAnalysisStatus.COMPLETED,
                findings=findings,
                files_analyzed=files_analyzed,
                duration_ms=round((perf_counter() - started) * 1000, 2),
                command_metadata=self._sanitize_command_metadata(command.metadata),
            )

    def _resolve_version(self) -> str | None:
        executable = shutil.which(self._executable) or self._executable
        command = self._command_builder.version_command()
        command_args = [executable, *command.args[1:]]
        try:
            completed = self._run_process(command_args, timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            return None

        output = (completed.stdout or "") + "\n" + (completed.stderr or "")
        match = re.search(r"(\d+\.\d+(?:\.\d+)?)", output)
        if match is None:
            return None if completed.returncode != 0 else "unknown"
        return match.group(1)

    def _run_process(
        self,
        args: list[str],
        *,
        timeout: int | None = None,
    ) -> subprocess.CompletedProcess[str]:
        completed = self._process_runner(
            args,
            capture_output=True,
            text=True,
            check=False,
            shell=False,
            timeout=timeout or self._timeout_seconds,
        )
        if not isinstance(completed, subprocess.CompletedProcess):
            raise TypeError("process runner must return CompletedProcess")
        return completed

    def _resolve_source_roots(
        self,
        *,
        repository: Repository,
        repository_path: Path,
    ) -> list[Path]:
        roots: list[Path] = []
        for relative in _JAVA_SOURCE_ROOTS:
            candidate = repository_path / relative
            if candidate.is_dir():
                roots.append(candidate)

        if roots:
            return roots

        java_files = [
            Path(path)
            for path in repository.files
            if path.replace("\\", "/").endswith(".java") and not self._is_excluded(path)
        ]
        if not java_files:
            return []

        # Fallback: unique parent directories of Java files under the repository.
        parents = sorted({(repository_path / path).parent for path in java_files})
        return parents[:20]

    def _repository_has_java(
        self,
        *,
        repository: Repository,
        technologies: Sequence[Technology],
    ) -> bool:
        if any(technology.name == "Java" for technology in technologies):
            return True
        return any(path.replace("\\", "/").endswith(".java") for path in repository.files)

    @staticmethod
    def _is_excluded(relative_path: str) -> bool:
        parts = set(Path(relative_path.replace("\\", "/")).parts)
        return bool(parts & _EXCLUDED_DIRECTORY_NAMES)

    @staticmethod
    def _sanitize_command_metadata(metadata: dict[str, object]) -> dict[str, object]:
        sanitized = dict(metadata)
        sanitized.pop("args", None)
        sanitized.pop("command", None)
        sanitized.pop("executable_path", None)
        return sanitized

    @staticmethod
    def _sanitize_error(message: str) -> str:
        compact = " ".join(message.split())
        if len(compact) > 300:
            return compact[:297] + "..."
        return compact
