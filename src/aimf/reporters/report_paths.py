"""Utilities for creating analysis report output paths."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from aimf.models import AnalysisResult


@dataclass(frozen=True)
class ReportPaths:
    """Paths for all reports generated during one analysis run."""

    directory: Path
    text_report: Path
    json_report: Path


def create_report_paths(
    result: AnalysisResult,
    base_directory: Path,
) -> ReportPaths:
    """Create a unique report directory for an analysis run."""

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    report_directory = (
        base_directory
        / result.repository.name
        / timestamp
    )

    report_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return ReportPaths(
        directory=report_directory,
        text_report=report_directory / "report.txt",
        json_report=report_directory / "report.json",
    )