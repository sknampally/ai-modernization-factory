"""Utilities for creating and retaining analysis report run directories."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from aimf.models import AnalysisResult

_REPORT_RUN_DIRECTORY_PATTERN = re.compile(r"^\d{8}-\d{6}$")
_DEFAULT_REPORTS_TO_KEEP = 3


@dataclass(frozen=True)
class ReportPaths:
    """Paths for all reports generated during one analysis run."""

    directory: Path
    text_report: Path
    json_report: Path
    timestamp: str


def create_report_paths(
    result: AnalysisResult,
    base_directory: Path,
) -> ReportPaths:
    """Create report paths for one analysis run.

    Layout:

    ``<base_directory>/<repository-name>/<YYYYMMDD-HHMMSS>/report.txt``
    ``<base_directory>/<repository-name>/<YYYYMMDD-HHMMSS>/report.json``
    """

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    repository_directory = base_directory / result.repository.name
    run_directory = repository_directory / timestamp

    run_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return ReportPaths(
        directory=run_directory,
        text_report=run_directory / "report.txt",
        json_report=run_directory / "report.json",
        timestamp=timestamp,
    )


def retain_recent_reports(
    repository_directory: Path,
    keep: int = _DEFAULT_REPORTS_TO_KEEP,
) -> None:
    """Keep only the newest timestamped report-run directories for one repository.

    Cleanup considers only direct child directories whose names match
    ``YYYYMMDD-HHMMSS``. Non-directory files and unrelated directories are ignored.
    """

    if keep < 1:
        raise ValueError("keep must be at least 1")

    if not repository_directory.exists():
        return

    run_directories = sorted(
        (
            path
            for path in repository_directory.iterdir()
            if path.is_dir() and _REPORT_RUN_DIRECTORY_PATTERN.match(path.name)
        ),
        key=lambda path: path.name,
        reverse=True,
    )

    for outdated_directory in run_directories[keep:]:
        shutil.rmtree(outdated_directory)
