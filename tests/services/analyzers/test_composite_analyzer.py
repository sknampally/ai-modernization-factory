"""Tests for the composite repository analyzer."""

from collections.abc import Sequence
from pathlib import Path

from aimf.models import (
    Finding,
    FindingCategory,
    FindingSource,
    Repository,
    Severity,
    Technology,
)
from aimf.services.analyzers import CompositeAnalyzer


class StubAnalyzer:
    """Analyzer that returns one configured finding."""

    def __init__(self, rule_id: str) -> None:
        self._rule_id = rule_id

    def analyze(
        self,
        repository: Repository,
        technologies: Sequence[Technology],
    ) -> list[Finding]:
        """Return one finding."""

        return [
            Finding(
                rule_id=self._rule_id,
                title="Test finding",
                description=f"Finding for {repository.name}.",
                category=FindingCategory.OTHER,
                severity=Severity.INFO,
                source=FindingSource.DETERMINISTIC,
            )
        ]


def test_composite_analyzer_combines_findings() -> None:
    repository = Repository(
        name="sample",
        path=Path("/tmp/sample"),
    )

    analyzer = CompositeAnalyzer(
        analyzers=[
            StubAnalyzer("test.first"),
            StubAnalyzer("test.second"),
        ]
    )

    findings = analyzer.analyze(
        repository=repository,
        technologies=[],
    )

    assert [finding.rule_id for finding in findings] == [
        "test.first",
        "test.second",
    ]


def test_composite_analyzer_returns_empty_list_when_no_analyzers_exist() -> None:
    repository = Repository(
        name="sample",
        path=Path("/tmp/sample"),
    )

    analyzer = CompositeAnalyzer(analyzers=[])

    findings = analyzer.analyze(
        repository=repository,
        technologies=[],
    )

    assert findings == []
