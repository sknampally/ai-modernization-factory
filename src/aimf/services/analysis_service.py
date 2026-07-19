"""Application service that orchestrates repository analysis."""

from datetime import UTC, datetime

from aimf.models import AnalysisResult, Repository
from aimf.services.contracts import TechnologyDetector


class AnalysisService:
    """Coordinates deterministic analysis of a scanned repository."""

    def __init__(
        self,
        technology_detector: TechnologyDetector,
        analyzer_version: str | None = None,
    ) -> None:
        self._technology_detector = technology_detector
        self._analyzer_version = analyzer_version

    def analyze(self, repository: Repository) -> AnalysisResult:
        """Analyze a scanned repository and return structured results."""

        started_at = datetime.now(UTC)

        technologies = self._technology_detector.detect(repository)

        completed_at = datetime.now(UTC)

        return AnalysisResult(
            repository=repository,
            technologies=technologies,
            findings=[],
            recommendations=[],
            started_at=started_at,
            completed_at=completed_at,
            analyzer_version=self._analyzer_version,
        )