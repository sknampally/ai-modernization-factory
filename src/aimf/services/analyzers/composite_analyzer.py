"""Composite analyzer that executes multiple repository analyzers."""

from collections.abc import Sequence

from aimf.models import Finding, Repository, Technology
from aimf.services.contracts import Analyzer


class CompositeAnalyzer:
    """Executes configured analyzers and combines their findings."""

    def __init__(self, analyzers: Sequence[Analyzer]) -> None:
        self._analyzers = tuple(analyzers)

    def analyze(
        self,
        repository: Repository,
        technologies: Sequence[Technology],
    ) -> list[Finding]:
        """Execute all analyzers and return their findings."""

        findings: list[Finding] = []

        for analyzer in self._analyzers:
            findings.extend(
                analyzer.analyze(
                    repository=repository,
                    technologies=technologies,
                )
            )

        return findings
