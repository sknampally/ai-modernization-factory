"""Scanner for public GitHub repositories."""

import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from aimf.models import Repository
from aimf.services.scanners.local_repository_scanner import (
    LocalRepositoryScanner,
)


class GitHubRepositoryScanner:
    """Clone and scan a public GitHub repository."""

    def __init__(
        self,
        workspace_directory: Path,
        branch: str | None = None,
        clean_before_clone: bool = True,
        local_scanner: LocalRepositoryScanner | None = None,
    ) -> None:
        self._workspace_directory = workspace_directory
        self._branch = branch
        self._clean_before_clone = clean_before_clone
        self._local_scanner = local_scanner or LocalRepositoryScanner()

    def scan(self, repository_url: str) -> Repository:
        """Clone a public GitHub repository and scan its files."""

        self._validate_repository_url(repository_url)

        repository_name = self._extract_repository_name(repository_url)
        clone_directory = self._workspace_directory / repository_name

        self._workspace_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        if clone_directory.exists():
            if self._clean_before_clone:
                shutil.rmtree(clone_directory)
            else:
                raise FileExistsError(
                    "Repository workspace already exists: "
                    f"{clone_directory}"
                )

        clone_command = [
            "git",
            "clone",
            "--depth",
            "1",
        ]

        if self._branch:
            clone_command.extend(
                [
                    "--branch",
                    self._branch,
                    "--single-branch",
                ]
            )

        clone_command.extend(
            [
                repository_url,
                str(clone_directory),
            ]
        )

        try:
            subprocess.run(
                clone_command,
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as error:
            raise RuntimeError(
                "Git is not installed or is not available on PATH."
            ) from error
        except subprocess.CalledProcessError as error:
            error_message = error.stderr.strip() or error.stdout.strip()

            raise RuntimeError(
                "Unable to clone GitHub repository"
                + (
                    f": {error_message}"
                    if error_message
                    else "."
                )
            ) from error

        repository = self._local_scanner.scan(clone_directory)

        return repository.model_copy(
            update={
                "source_url": repository_url,
                "default_branch": self._branch,
            }
        )

    def _validate_repository_url(
        self,
        repository_url: str,
    ) -> None:
        """Validate that the URL points to a public GitHub repository."""

        parsed_url = urlparse(repository_url)

        if parsed_url.scheme not in {"http", "https"}:
            raise ValueError(
                "Repository URL must use HTTP or HTTPS."
            )

        if parsed_url.hostname not in {
            "github.com",
            "www.github.com",
        }:
            raise ValueError(
                "Only public GitHub repositories are supported."
            )

        path_parts = [
            part
            for part in parsed_url.path.split("/")
            if part
        ]

        if len(path_parts) < 2:
            raise ValueError(
                "GitHub URL must contain an owner and repository name."
            )

    def _extract_repository_name(
        self,
        repository_url: str,
    ) -> str:
        """Extract the repository name from its GitHub URL."""

        parsed_url = urlparse(repository_url)
        repository_name = Path(parsed_url.path).name

        if repository_name.endswith(".git"):
            repository_name = repository_name[:-4]

        if not repository_name:
            raise ValueError(
                "Unable to determine repository name from URL."
            )

        return repository_name