"""Application service that orchestrates repository analysis."""

from datetime import UTC, datetime
from pathlib import Path

from aimf.models import AnalysisResult
from aimf.services.contracts import (
    AnalyzerEngine,
    RecommendationEngine,
    RepositoryScanner,
    TechnologyDetector,
)


class AnalysisService:
    """Coordinates the complete repository analysis workflow."""

    def __init__(
        self,
        repository_scanner: RepositoryScanner,
        technology_detector: TechnologyDetector,
        analyzer_engine: AnalyzerEngine,
        recommendation_engine: RecommendationEngine,
        analyzer_version: str | None = None,
    ) -> None:
        self._repository_scanner = repository_scanner
        self._technology_detector = technology_detector
        self._analyzer_engine = analyzer_engine
        self._recommendation_engine = recommendation_engine
        self._analyzer_version = analyzer_version

    def analyze(self, repository_path: Path) -> AnalysisResult:
        """Run the complete modernization analysis workflow."""

        started_at = datetime.now(UTC)

        repository = self._repository_scanner.scan(repository_path)

        technologies = self._technology_detector.detect(repository)

        repository.technologies = technologies

        findings = self._analyzer_engine.analyze(
            repository=repository,
            technologies=technologies,
        )

        recommendations = self._recommendation_engine.generate(
            repository=repository,
            technologies=technologies,
            findings=findings,
        )

        completed_at = datetime.now(UTC)

        return AnalysisResult(
            repository=repository,
            technologies=technologies,
            findings=findings,
            recommendations=recommendations,
            started_at=started_at,
            completed_at=completed_at,
            analyzer_version=self._analyzer_version,
        )