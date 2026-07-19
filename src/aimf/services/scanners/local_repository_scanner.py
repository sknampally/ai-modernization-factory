"""Local file-system implementation of the repository scanner."""

from collections.abc import Iterable
from pathlib import Path

from aimf.models import Repository


class LocalRepositoryScanner:
    """Scans a repository located on the local file system."""

    DEFAULT_EXCLUDED_DIRECTORIES = frozenset(
        {
            ".git",
            ".idea",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            ".tox",
            ".venv",
            ".vscode",
            "__pycache__",
            "build",
            "dist",
            "node_modules",
            "target",
        }
    )

    def __init__(
        self,
        excluded_directories: Iterable[str] | None = None,
    ) -> None:
        additional_exclusions = set(excluded_directories or [])

        self._excluded_directories = set(self.DEFAULT_EXCLUDED_DIRECTORIES) | additional_exclusions

    def scan(self, repository_path: Path) -> Repository:
        """Scan a local repository and return repository metadata."""

        resolved_path = repository_path.expanduser().resolve()

        self._validate_repository_path(resolved_path)

        files = self._collect_files(resolved_path)

        return Repository(
            name=resolved_path.name,
            path=resolved_path,
            files=files,
            total_files=len(files),
        )

    def _validate_repository_path(self, repository_path: Path) -> None:
        """Validate that the repository path exists and is a directory."""

        if not repository_path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {repository_path}")

        if not repository_path.is_dir():
            raise NotADirectoryError(f"Repository path is not a directory: {repository_path}")

    def _collect_files(self, repository_path: Path) -> list[str]:
        """Collect repository files while ignoring excluded directories."""

        files: list[str] = []

        for path in repository_path.rglob("*"):
            if self._should_exclude(path, repository_path):
                continue

            if path.is_file():
                relative_path = path.relative_to(repository_path)
                files.append(relative_path.as_posix())

        return sorted(files)

    def _should_exclude(
        self,
        path: Path,
        repository_path: Path,
    ) -> bool:
        """Return whether a path is inside an excluded directory."""

        relative_path = path.relative_to(repository_path)

        return any(part in self._excluded_directories for part in relative_path.parts)
