"""Service contracts for the AI Modernization Factory analysis workflow."""

from pathlib import Path
from typing import Protocol

from aimf.models import (
    Finding,
    Recommendation,
    Repository,
    Technology,
)


class RepositoryScanner(Protocol):
    """Scans a source repository and collects repository information."""

    def scan(self, repository_path: Path) -> Repository:
        """Scan a repository and return its structured representation."""
        ...


class TechnologyDetector(Protocol):
    """Detects languages, frameworks, build tools, and other technologies."""

    def detect(self, repository: Repository) -> list[Technology]:
        """Detect technologies used by the repository."""
        ...


class AnalyzerEngine(Protocol):
    """Runs deterministic analyzers against a repository."""

    def analyze(
        self,
        repository: Repository,
        technologies: list[Technology],
    ) -> list[Finding]:
        """Analyze the repository and return structured findings."""
        ...


class RecommendationEngine(Protocol):
    """Generates modernization recommendations from analysis findings."""

    def generate(
        self,
        repository: Repository,
        technologies: list[Technology],
        findings: list[Finding],
    ) -> list[Recommendation]:
        """Generate recommendations from repository findings."""
        ...