"""Tests for report path creation and retention."""

from __future__ import annotations

from pathlib import Path

import pytest

from aimf.models import AnalysisResult, Repository
from aimf.reporters.html_file_reporter import HtmlFileReporter
from aimf.reporters.json_file_reporter import JsonFileReporter
from aimf.reporters.report_paths import (
    ReportArchiveError,
    archive_excess_report_runs,
    create_report_paths,
    list_active_report_run_directories,
    retain_recent_reports,
)
from aimf.reporters.text_file_reporter import TextFileReporter


def _analysis_result(tmp_path: Path, name: str = "sample") -> AnalysisResult:
    return AnalysisResult(
        repository=Repository(
            name=name,
            path=tmp_path,
            files=[],
        ),
        technologies=[],
        findings=[],
        recommendations=[],
    )


def _create_run_directory(
    repository_directory: Path,
    timestamp: str,
) -> Path:
    run_directory = repository_directory / timestamp
    run_directory.mkdir(parents=True, exist_ok=True)
    (run_directory / "report.txt").write_text("txt", encoding="utf-8")
    (run_directory / "report.json").write_text("{}", encoding="utf-8")
    (run_directory / "report.html").write_text("<html></html>", encoding="utf-8")
    return run_directory


def test_create_report_paths_uses_timestamped_run_directories(
    tmp_path: Path,
) -> None:
    result = _analysis_result(tmp_path)

    report_paths = create_report_paths(
        result=result,
        base_directory=tmp_path / "reports",
        timestamp="20260721-153045",
        create_directory=True,
    )

    assert report_paths.directory == (tmp_path / "reports" / "sample" / "20260721-153045")
    assert report_paths.repository_name == "sample"
    assert report_paths.run_directory == report_paths.directory
    assert report_paths.run_timestamp == "20260721-153045"
    assert report_paths.text_report == report_paths.directory / "report.txt"
    assert report_paths.json_report == report_paths.directory / "report.json"
    assert report_paths.html_report == report_paths.directory / "report.html"
    assert report_paths.html_report_path == report_paths.html_report
    assert report_paths.directory.is_dir()


def test_sanitize_repository_directory_name() -> None:
    from aimf.reporters.report_paths import sanitize_repository_directory_name

    assert sanitize_repository_directory_name("Spring Petclinic!") == "spring-petclinic"
    assert sanitize_repository_directory_name("sample") == "sample"


def test_retain_recent_reports_with_fewer_than_three_runs(
    tmp_path: Path,
) -> None:
    repository_directory = tmp_path / "reports" / "sample"
    _create_run_directory(repository_directory, "20260101-010101")
    _create_run_directory(repository_directory, "20260102-020202")

    retain_recent_reports(repository_directory, keep=3)

    remaining = sorted(path.name for path in repository_directory.iterdir())
    assert remaining == [
        "20260101-010101",
        "20260102-020202",
    ]


def test_retain_recent_reports_with_exactly_three_runs(
    tmp_path: Path,
) -> None:
    repository_directory = tmp_path / "reports" / "sample"
    timestamps = [
        "20260101-010101",
        "20260102-020202",
        "20260103-030303",
    ]

    for timestamp in timestamps:
        _create_run_directory(repository_directory, timestamp)

    retain_recent_reports(repository_directory, keep=3)

    remaining = sorted(path.name for path in repository_directory.iterdir())
    assert remaining == timestamps


def test_retain_recent_reports_with_more_than_three_runs(
    tmp_path: Path,
) -> None:
    repository_directory = tmp_path / "reports" / "sample"
    timestamps = [
        "20260101-010101",
        "20260102-020202",
        "20260103-030303",
        "20260104-040404",
        "20260105-050505",
    ]

    for timestamp in timestamps:
        _create_run_directory(repository_directory, timestamp)

    (repository_directory / "notes.md").write_text("keep", encoding="utf-8")
    (repository_directory / "archive-backup").mkdir()

    retain_recent_reports(repository_directory, keep=3)

    remaining = sorted(path.name for path in repository_directory.iterdir())
    assert remaining == [
        "20260103-030303",
        "20260104-040404",
        "20260105-050505",
        "archive-backup",
        "notes.md",
    ]


def test_retain_recent_reports_is_isolated_between_repositories(
    tmp_path: Path,
) -> None:
    first_repository = tmp_path / "reports" / "first"
    second_repository = tmp_path / "reports" / "second"

    for timestamp in [
        "20260101-010101",
        "20260102-020202",
        "20260103-030303",
        "20260104-040404",
    ]:
        _create_run_directory(first_repository, timestamp)

    for timestamp in [
        "20260101-010101",
        "20260102-020202",
    ]:
        _create_run_directory(second_repository, timestamp)

    retain_recent_reports(first_repository, keep=3)

    assert sorted(path.name for path in first_repository.iterdir()) == [
        "20260102-020202",
        "20260103-030303",
        "20260104-040404",
    ]
    assert sorted(path.name for path in second_repository.iterdir()) == [
        "20260101-010101",
        "20260102-020202",
    ]


def test_cleanup_runs_only_after_successful_report_generation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _analysis_result(tmp_path, name="sample")
    repository_directory = tmp_path / "reports" / "sample"

    for timestamp in [
        "20260101-010101",
        "20260102-020202",
        "20260103-030303",
        "20260104-040404",
    ]:
        _create_run_directory(repository_directory, timestamp)

    report_paths = create_report_paths(
        result=result,
        base_directory=tmp_path / "reports",
    )

    original_json_write = JsonFileReporter.write

    def fail_json_write(
        self: JsonFileReporter,
        result: AnalysisResult,
        output_path: Path,
    ) -> None:
        del self
        del result
        del output_path
        raise RuntimeError("json write failed")

    monkeypatch.setattr(
        JsonFileReporter,
        "write",
        fail_json_write,
    )

    with pytest.raises(RuntimeError, match="json write failed"):
        TextFileReporter().write(
            result=result,
            output_path=report_paths.text_report,
        )
        JsonFileReporter().write(
            result=result,
            output_path=report_paths.json_report,
        )
        retain_recent_reports(report_paths.directory.parent)

    remaining = sorted(path.name for path in repository_directory.iterdir())
    assert "20260101-010101" in remaining
    assert len([name for name in remaining if name.startswith("2026")]) == 5

    monkeypatch.setattr(
        JsonFileReporter,
        "write",
        original_json_write,
    )

    TextFileReporter().write(
        result=result,
        output_path=report_paths.text_report,
    )
    JsonFileReporter().write(
        result=result,
        output_path=report_paths.json_report,
    )
    HtmlFileReporter().write(
        result=result,
        output_path=report_paths.html_report,
    )
    retain_recent_reports(report_paths.directory.parent)

    remaining_after_success = sorted(path.name for path in repository_directory.iterdir())
    assert "20260101-010101" not in remaining_after_success
    assert report_paths.timestamp in remaining_after_success
    assert len([name for name in remaining_after_success if name.startswith("2026")]) == 3
    assert (report_paths.directory / "report.html").is_file()


def test_archive_excess_keeps_three_active_and_moves_older(tmp_path: Path) -> None:
    repository_directory = tmp_path / "reports" / "sample"
    timestamps = [
        "20260101-010101",
        "20260102-020202",
        "20260103-030303",
        "20260104-040404",
        "20260105-050505",
    ]
    for timestamp in timestamps:
        _create_run_directory(repository_directory, timestamp)

    (repository_directory / "notes.md").write_text("keep", encoding="utf-8")
    (repository_directory / "not-a-run").mkdir()

    archived = archive_excess_report_runs(repository_directory, keep=3)

    active = [path.name for path in list_active_report_run_directories(repository_directory)]
    assert active == ["20260105-050505", "20260104-040404", "20260103-030303"]
    assert sorted(path.name for path in archived) == ["20260101-010101", "20260102-020202"]
    for name in ("20260101-010101", "20260102-020202"):
        archived_dir = repository_directory / "archive" / name
        assert archived_dir.is_dir()
        assert (archived_dir / "report.txt").read_text(encoding="utf-8") == "txt"
        assert (archived_dir / "report.html").exists()
        assert (archived_dir / "report.json").exists()
    assert (repository_directory / "notes.md").exists()
    assert (repository_directory / "not-a-run").is_dir()


def test_archive_excess_ignores_invalid_names_and_existing_archive(
    tmp_path: Path,
) -> None:
    repository_directory = tmp_path / "reports" / "sample"
    _create_run_directory(repository_directory, "20260103-030303")
    _create_run_directory(repository_directory, "20260104-040404")
    _create_run_directory(repository_directory, "20260105-050505")
    already = repository_directory / "archive" / "20260101-010101"
    already.mkdir(parents=True)
    (already / "report.json").write_text("{}", encoding="utf-8")

    archived = archive_excess_report_runs(repository_directory, keep=3)
    assert archived == []
    assert (already / "report.json").exists()
    assert sorted(
        path.name for path in repository_directory.iterdir() if path.name != "archive"
    ) == [
        "20260103-030303",
        "20260104-040404",
        "20260105-050505",
    ]


def test_archive_destination_collision_raises(tmp_path: Path) -> None:
    repository_directory = tmp_path / "reports" / "sample"
    _create_run_directory(repository_directory, "20260101-010101")
    _create_run_directory(repository_directory, "20260102-020202")
    _create_run_directory(repository_directory, "20260103-030303")
    _create_run_directory(repository_directory, "20260104-040404")
    collision = repository_directory / "archive" / "20260101-010101"
    collision.mkdir(parents=True)
    (collision / "report.json").write_text('{"kept":true}', encoding="utf-8")

    with pytest.raises(ReportArchiveError, match="destination already exists"):
        archive_excess_report_runs(repository_directory, keep=3)

    assert (collision / "report.json").read_text(encoding="utf-8") == '{"kept":true}'
    assert (repository_directory / "20260101-010101").is_dir()


def test_archive_is_isolated_between_repositories(tmp_path: Path) -> None:
    first = tmp_path / "reports" / "first"
    second = tmp_path / "reports" / "second"
    for timestamp in [
        "20260101-010101",
        "20260102-020202",
        "20260103-030303",
        "20260104-040404",
    ]:
        _create_run_directory(first, timestamp)
    for timestamp in ["20260101-010101", "20260102-020202"]:
        _create_run_directory(second, timestamp)

    archive_excess_report_runs(first, keep=3)

    assert [path.name for path in list_active_report_run_directories(first)] == [
        "20260104-040404",
        "20260103-030303",
        "20260102-020202",
    ]
    assert (first / "archive" / "20260101-010101").is_dir()
    assert sorted(path.name for path in second.iterdir()) == [
        "20260101-010101",
        "20260102-020202",
    ]
