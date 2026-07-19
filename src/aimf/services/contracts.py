"""Service contracts for the AI Modernization Factory workflow."""

from typing import Protocol

from aimf.models import Repository, Technology


class TechnologyDetector(Protocol):
    """Detects languages, frameworks, build tools, and other technologies."""

    def detect(self, repository: Repository) -> list[Technology]:
        """Detect technologies used by the repository."""
        ...