"""Scanner for public and private GitHub repositories."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from aimf.models import Repository
from aimf.repository_auth.exceptions import (
    RepositoryAccessCategory,
    RepositoryAccessError,
)
from aimf.repository_auth.git_runner import run_git, verify_remote_origin_url
from aimf.repository_auth.models import RepositoryAuthenticationConfig
from aimf.repository_auth.service import RepositoryAuthenticationService
from aimf.security.redaction import Redactor
from aimf.services.scanners.local_repository_scanner import (
    LocalRepositoryScanner,
)

logger = logging.getLogger(__name__)


class GitHubRepositoryScanner:
    """Clone and scan a GitHub repository with optional authentication."""

    def __init__(
        self,
        workspace_directory: Path,
        branch: str | None = None,
        clean_before_clone: bool = True,
        local_scanner: LocalRepositoryScanner | None = None,
        authentication: RepositoryAuthenticationConfig | None = None,
        authentication_service: RepositoryAuthenticationService | None = None,
        clone_timeout_seconds: float = 300,
    ) -> None:
        self._workspace_directory = workspace_directory
        self._branch = branch
        self._clean_before_clone = clean_before_clone
        self._local_scanner = local_scanner or LocalRepositoryScanner()
        self._authentication = authentication
        self._authentication_service = authentication_service or RepositoryAuthenticationService()
        self._clone_timeout_seconds = clone_timeout_seconds

    def scan(self, repository_url: str) -> Repository:
        """Clone a GitHub repository and scan its files."""

        parsed = self._authentication_service.validate_compatibility(
            repository_url,
            self._authentication,
        )
        clone_url = parsed.credential_free_url
        repository_name = parsed.repository_name
        clone_directory = self._workspace_directory / repository_name

        self._workspace_directory.mkdir(parents=True, exist_ok=True)

        if clone_directory.exists():
            if self._clean_before_clone:
                shutil.rmtree(clone_directory)
            else:
                raise FileExistsError(f"Repository workspace already exists: {clone_directory}")

        logger.info(
            "Cloning GitHub repository %s/%s via %s",
            parsed.owner,
            parsed.repository,
            parsed.transport,
        )

        try:
            with self._authentication_service.git_execution_context(
                clone_url,
                self._authentication,
            ) as auth_context:
                provider_id = auth_context.provider_id
                logger.info(
                    "Using authentication provider %s for clone",
                    provider_id,
                )
                self._clone_repository(
                    clone_url=clone_url,
                    clone_directory=clone_directory,
                    environment=auth_context.environment,
                    redactor=auth_context.redactor,
                )
                verify_remote_origin_url(
                    clone_directory,
                    expected_credential_free_url=clone_url,
                    redactor=auth_context.redactor,
                )
        except RepositoryAccessError:
            self._cleanup_partial_clone(clone_directory)
            raise
        except Exception:
            self._cleanup_partial_clone(clone_directory)
            raise

        repository = self._local_scanner.scan(clone_directory)
        return repository.model_copy(
            update={
                "source_url": clone_url,
                "default_branch": self._branch,
            }
        )

    def _clone_repository(
        self,
        *,
        clone_url: str,
        clone_directory: Path,
        environment: dict[str, str],
        redactor: Redactor,
    ) -> None:
        arguments = [
            "clone",
            "--depth",
            "1",
        ]
        if self._branch:
            arguments.extend(
                [
                    "--branch",
                    self._branch,
                    "--single-branch",
                ]
            )
        arguments.extend([clone_url, str(clone_directory)])

        run_git(
            arguments,
            timeout_seconds=self._clone_timeout_seconds,
            environment=environment,
            redactor=redactor,
        )

    def _cleanup_partial_clone(self, clone_directory: Path) -> None:
        if not clone_directory.exists():
            return
        try:
            shutil.rmtree(clone_directory)
        except OSError as error:
            raise RepositoryAccessError(
                "Failed to clean up a partial repository clone.",
                category=RepositoryAccessCategory.WORKSPACE_CLEANUP_FAILED,
            ) from error
