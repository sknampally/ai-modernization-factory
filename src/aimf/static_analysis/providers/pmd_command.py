"""PMD CLI command construction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PmdCommand:
    """Argument list and metadata for a PMD invocation."""

    args: list[str]
    metadata: dict[str, object]


class PmdCommandBuilder:
    """Build PMD CLI invocations without shell interpolation."""

    def __init__(self, executable: str = "pmd") -> None:
        self._executable = executable

    def version_command(self) -> PmdCommand:
        """Build a command that reports the PMD version."""

        return PmdCommand(
            args=[self._executable, "--version"],
            metadata={"purpose": "version"},
        )

    def analyze_command(
        self,
        *,
        source_roots: list[Path],
        rulesets: list[str],
        report_file: Path,
        minimum_priority: int,
        format_name: str = "xml",
    ) -> PmdCommand:
        """Build a PMD analysis command using an argument list."""

        # Prefer PMD 7 `check` syntax; fall back callers may retry with legacy.
        args = [
            self._executable,
            "check",
            "--no-cache",
            "--format",
            format_name,
            "--report-file",
            str(report_file),
            "--rulesets",
            ",".join(rulesets),
            "--minimum-priority",
            str(minimum_priority),
        ]
        for source_root in source_roots:
            args.extend(["--dir", str(source_root)])

        return PmdCommand(
            args=args,
            metadata={
                "purpose": "analyze",
                "format": format_name,
                "ruleset_count": len(rulesets),
                "source_root_count": len(source_roots),
                "minimum_priority": minimum_priority,
                "cli_style": "pmd7-check",
            },
        )

    def legacy_analyze_command(
        self,
        *,
        source_roots: list[Path],
        rulesets: list[str],
        report_file: Path,
        minimum_priority: int,
        format_name: str = "xml",
    ) -> PmdCommand:
        """Build a legacy PMD 6-style analysis command."""

        args = [
            self._executable,
            "-d",
            str(source_roots[0]),
            "-R",
            ",".join(rulesets),
            "-f",
            format_name,
            "-r",
            str(report_file),
            "-minimumpriority",
            str(minimum_priority),
        ]
        return PmdCommand(
            args=args,
            metadata={
                "purpose": "analyze",
                "format": format_name,
                "ruleset_count": len(rulesets),
                "source_root_count": len(source_roots),
                "minimum_priority": minimum_priority,
                "cli_style": "pmd6-legacy",
            },
        )
