"""Utilities for creating and retaining analysis report run directories."""

from __future__ import annotations

import re
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from aimf.models import AnalysisResult

_REPORT_RUN_DIRECTORY_PATTERN = re.compile(r"^\d{8}-\d{6}$")
DEFAULT_ACTIVE_REPORT_RUNS_TO_KEEP = 3
_DEFAULT_REPORTS_TO_KEEP = DEFAULT_ACTIVE_REPORT_RUNS_TO_KEEP
_UNSAFE_REPOSITORY_CHARS = re.compile(r"[^a-z0-9._-]+")
ARCHIVE_DIRECTORY_NAME = "archive"


class ReportArchiveError(RuntimeError):
    """Raised when an older report run cannot be archived safely."""


@dataclass(frozen=True)
class ReportPaths:
    """Paths for all reports generated during one analysis run."""

    directory: Path
    text_report: Path
    json_report: Path
    html_report: Path
    timestamp: str
    repository_name: str

    @property
    def run_directory(self) -> Path:
        """Alias for the timestamped run directory."""

        return self.directory

    @property
    def run_timestamp(self) -> str:
        """Alias for the shared UTC run timestamp."""

        return self.timestamp

    @property
    def html_report_path(self) -> Path:
        return self.html_report

    @property
    def json_report_path(self) -> Path:
        return self.json_report

    @property
    def text_report_path(self) -> Path:
        return self.text_report


def sanitize_repository_directory_name(repository_name: str) -> str:
    """Return a filesystem-safe repository directory name."""

    compact = repository_name.strip().lower()
    slug = _UNSAFE_REPOSITORY_CHARS.sub("-", compact).strip(".-")
    return slug or "repository"


def format_report_run_timestamp(moment: datetime | None = None) -> str:
    """Return a UTC run timestamp formatted as ``YYYYMMDD-HHMMSS``."""

    value = moment if moment is not None else datetime.now(UTC)
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    else:
        value = value.astimezone(UTC)
    return value.strftime("%Y%m%d-%H%M%S")


def create_report_paths(
    result: AnalysisResult,
    base_directory: Path,
    *,
    timestamp: str | None = None,
    clock: Callable[[], datetime] | None = None,
    create_directory: bool = True,
) -> ReportPaths:
    """Create report paths for one analysis or assessment run.

    Layout:

    ``<base_directory>/<sanitized-repository-name>/<YYYYMMDD-HHMMSS>/``

    Path fields include ``report.html``, ``report.json``, and ``report.txt`` for
    callers such as ``aimf scan``. Assessment writes only HTML and JSON.

    When ``timestamp`` is provided it is reused for the run directory. Otherwise a
    single UTC timestamp is generated from ``clock`` (or ``datetime.now(UTC)``).
    """

    if timestamp is not None:
        run_timestamp = timestamp
        if not _REPORT_RUN_DIRECTORY_PATTERN.match(run_timestamp):
            raise ValueError(f"timestamp must match YYYYMMDD-HHMMSS, got {run_timestamp!r}")
    else:
        now = clock() if clock is not None else datetime.now(UTC)
        run_timestamp = format_report_run_timestamp(now)

    repository_name = sanitize_repository_directory_name(result.repository.name)
    repository_directory = base_directory / repository_name
    run_directory = repository_directory / run_timestamp

    if create_directory:
        run_directory.mkdir(parents=True, exist_ok=True)

    return ReportPaths(
        directory=run_directory,
        text_report=run_directory / "report.txt",
        json_report=run_directory / "report.json",
        html_report=run_directory / "report.html",
        timestamp=run_timestamp,
        repository_name=repository_name,
    )


def list_active_report_run_directories(repository_directory: Path) -> list[Path]:
    """Return active timestamped run directories, newest first.

    Ignores ``archive`` and any non-matching names.
    """

    if not repository_directory.exists():
        return []

    return sorted(
        (
            path
            for path in repository_directory.iterdir()
            if path.is_dir() and _REPORT_RUN_DIRECTORY_PATTERN.match(path.name)
        ),
        key=lambda path: path.name,
        reverse=True,
    )


def archive_excess_report_runs(
    repository_directory: Path,
    *,
    keep: int = DEFAULT_ACTIVE_REPORT_RUNS_TO_KEEP,
) -> list[Path]:
    """Move older active runs under ``archive/``; keep the newest ``keep`` active.

    Historical directories are moved intact (including any legacy ``report.txt``).
    Already-archived runs are never re-archived. Destination collisions raise
    ``ReportArchiveError`` instead of overwriting.
    """

    if keep < 1:
        raise ValueError("keep must be at least 1")

    if not repository_directory.exists():
        return []

    run_directories = list_active_report_run_directories(repository_directory)
    to_archive = run_directories[keep:]
    if not to_archive:
        return []

    archive_root = repository_directory / ARCHIVE_DIRECTORY_NAME
    archive_root.mkdir(parents=True, exist_ok=True)

    archived: list[Path] = []
    for outdated_directory in to_archive:
        destination = archive_root / outdated_directory.name
        if destination.exists():
            raise ReportArchiveError(
                f"Cannot archive report run {outdated_directory.name!r}: "
                f"destination already exists at {destination}"
            )
        shutil.move(str(outdated_directory), str(destination))
        archived.append(destination)
    return archived


def retain_recent_reports(
    repository_directory: Path,
    keep: int = _DEFAULT_REPORTS_TO_KEEP,
) -> None:
    """Keep only the newest timestamped report-run directories for one repository.

    Cleanup considers only direct child directories whose names match
    ``YYYYMMDD-HHMMSS``. Non-directory files and unrelated directories are ignored.

    This delete-based retention is used by ``aimf scan``. Assessment runs use
    ``archive_excess_report_runs`` instead.
    """

    if keep < 1:
        raise ValueError("keep must be at least 1")

    if not repository_directory.exists():
        return

    run_directories = list_active_report_run_directories(repository_directory)

    for outdated_directory in run_directories[keep:]:
        shutil.rmtree(outdated_directory)
