"""Tests for the repository analysis application service."""

from pathlib import Path

from aimf.models import Repository, Technology, TechnologyCategory
from aimf.services.analysis_service import AnalysisService


class StubTechnologyDetector:
    """Technology detector used for service testing."""

    def detect(self, repository: Repository) -> list[Technology]:
        """Return a predictable technology result."""

        return [
            Technology(
                name="Java",
                category=TechnologyCategory.LANGUAGE,
                confidence=1.0,
                source="test",
            )
        ]


def test_analysis_service_creates_analysis_result() -> None:
    repository = Repository(
        name="sample",
        path=Path("/tmp/sample"),
        files=["src/main/java/Sample.java"],
        total_files=1,
    )

    service = AnalysisService(
        technology_detector=StubTechnologyDetector(),
        analyzer_version="0.1.0",
    )

    result = service.analyze(repository)

    assert result.repository is repository
    assert len(result.technologies) == 1
    assert result.technologies[0].name == "Java"
    assert result.findings == []
    assert result.recommendations == []
    assert result.completed_at is not None
    assert result.completed_at >= result.started_at
    assert result.analyzer_version == "0.1.0"