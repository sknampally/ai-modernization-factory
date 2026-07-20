"""Composite analyzer that executes multiple repository analyzers."""

from collections.abc import Sequence

from aimf.models import AnalyzerResult, Repository, RepositoryFacts, Technology
from aimf.services.contracts import Analyzer


class CompositeAnalyzer:
    """Executes configured analyzers and combines their results."""

    def __init__(self, analyzers: Sequence[Analyzer]) -> None:
        self._analyzers = tuple(analyzers)

    def analyze(
        self,
        repository: Repository,
        technologies: Sequence[Technology],
    ) -> AnalyzerResult:
        """Execute all analyzers and combine their findings and facts."""

        findings = []
        facts = RepositoryFacts()

        for analyzer in self._analyzers:
            result = analyzer.analyze(
                repository=repository,
                technologies=technologies,
            )

            findings.extend(result.findings)
            facts = facts.merge(result.facts)

        return AnalyzerResult(
            findings=findings,
            facts=facts,
        )
