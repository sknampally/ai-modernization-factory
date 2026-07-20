"""Service contracts for the AI Modernization Factory workflow."""

from collections.abc import Sequence
from typing import Protocol

from aimf.models import AnalyzerResult, Repository, Technology


class TechnologyDetector(Protocol):
    """Detects languages, frameworks, build tools, and other technologies."""

    def detect(self, repository: Repository) -> list[Technology]:
        """Detect technologies used by the repository."""
        ...


class Analyzer(Protocol):
    """Performs deterministic analysis of a repository."""

    def analyze(
        self,
        repository: Repository,
        technologies: Sequence[Technology],
    ) -> AnalyzerResult:
        """Analyze the repository and return structured findings."""
        ...
