"""Application service that orchestrates repository analysis."""

import logging
from datetime import UTC, datetime
from time import perf_counter

from aimf.models import AnalysisResult, Repository, RepositoryFacts
from aimf.services.contracts import Analyzer, RecommendationEngine, TechnologyDetector
from aimf.services.recommendation_engine import ModernizationRecommendationEngine
from aimf.services.technology_facts import technology_facts_from_detections

logger = logging.getLogger(__name__)


class AnalysisService:
    """Coordinate technology detection and repository analysis."""

    def __init__(
        self,
        technology_detector: TechnologyDetector,
        analyzer: Analyzer,
        analyzer_version: str,
        recommendation_engine: RecommendationEngine | None = None,
    ) -> None:
        self._technology_detector = technology_detector
        self._analyzer = analyzer
        self._analyzer_version = analyzer_version
        self._recommendation_engine = recommendation_engine or ModernizationRecommendationEngine()

    def analyze(self, repository: Repository) -> AnalysisResult:
        """Analyze a scanned repository and return structured results."""

        started_at = datetime.now(UTC)
        start_time = perf_counter()

        logger.info(
            "Repository analysis started",
            extra={
                "repository_name": repository.name,
                "repository_path": str(repository.path),
                "stage": "analysis",
                "file_count": len(repository.files),
            },
        )

        try:
            technologies = self._technology_detector.detect(repository)

            logger.info(
                "Technology detection completed",
                extra={
                    "repository_name": repository.name,
                    "stage": "technology_detection",
                    "technology_count": len(technologies),
                },
            )

            analyzer_result = self._analyzer.analyze(
                repository=repository,
                technologies=technologies,
            )

            facts = analyzer_result.facts.merge(
                RepositoryFacts(
                    technology=technology_facts_from_detections(technologies),
                )
            )

            recommendations = self._recommendation_engine.generate(
                facts=facts,
                findings=analyzer_result.findings,
                technologies=technologies,
            )

            completed_at = datetime.now(UTC)
            duration_ms = round((perf_counter() - start_time) * 1000, 2)

            logger.info(
                "Repository analysis completed",
                extra={
                    "repository_name": repository.name,
                    "stage": "analysis",
                    "technology_count": len(technologies),
                    "finding_count": len(analyzer_result.findings),
                    "recommendation_count": len(recommendations),
                    "duration_ms": duration_ms,
                },
            )

            return AnalysisResult(
                repository=repository,
                technologies=technologies,
                facts=facts,
                findings=analyzer_result.findings,
                recommendations=recommendations,
                started_at=started_at,
                completed_at=completed_at,
                analyzer_version=self._analyzer_version,
            )

        except Exception:
            logger.exception(
                "Repository analysis failed",
                extra={
                    "repository_name": repository.name,
                    "stage": "analysis",
                },
            )
            raise
