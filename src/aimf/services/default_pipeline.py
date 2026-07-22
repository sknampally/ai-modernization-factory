"""Shared default analysis pipeline construction for CLI commands."""

from __future__ import annotations

from aimf import __version__
from aimf.config.settings import AimfSettings
from aimf.services.analysis_service import AnalysisService
from aimf.services.analyzers import (
    ArchitectureAnalyzer,
    BuildDiscoveryAnalyzer,
    BuildMetadataAnalyzer,
    CicdDiscoveryAnalyzer,
    CloudReadinessAnalyzer,
    CompositeAnalyzer,
    DependencyDiscoveryAnalyzer,
    DependencyHealthAnalyzer,
    DependencyMetadataAnalyzer,
    RepositoryMetricsAnalyzer,
    SecurityAnalyzer,
)
from aimf.services.detectors.composite_technology_detector import (
    CompositeTechnologyDetector,
)
from aimf.services.detectors.java_technology_detector import JavaTechnologyDetector
from aimf.services.detectors.javascript_technology_detector import (
    JavaScriptTechnologyDetector,
)
from aimf.services.detectors.php_technology_detector import PhpTechnologyDetector
from aimf.static_analysis.providers import PmdProvider
from aimf.static_analysis.service import StaticAnalysisService


def create_default_analysis_service(
    settings: AimfSettings,
    *,
    pmd_executable: str | None = None,
    static_analysis_enabled: bool | None = None,
    pmd_profile: str | None = None,
) -> AnalysisService:
    """Create the standard AIMF analysis service from application settings."""

    technology_detector = CompositeTechnologyDetector(
        detectors=[
            JavaTechnologyDetector(),
            JavaScriptTechnologyDetector(),
            PhpTechnologyDetector(),
        ]
    )

    static_analysis_settings = settings.static_analysis
    enabled = (
        static_analysis_settings.enabled
        if static_analysis_enabled is None
        else static_analysis_enabled
    )
    providers = []
    if static_analysis_settings.pmd.enabled:
        profile = pmd_profile or static_analysis_settings.pmd.profile
        providers.append(
            PmdProvider(
                executable=pmd_executable or static_analysis_settings.pmd.executable,
                profile=profile,
                rulesets=static_analysis_settings.pmd.rulesets,
                timeout_seconds=static_analysis_settings.pmd.timeout_seconds,
                enabled=True,
            )
        )

    static_analysis_service = StaticAnalysisService(
        providers=providers,
        enabled=enabled,
        fail_on_provider_error=static_analysis_settings.fail_on_provider_error,
    )

    return AnalysisService(
        technology_detector=technology_detector,
        analyzer=CompositeAnalyzer(
            analyzers=[
                RepositoryMetricsAnalyzer(),
                BuildDiscoveryAnalyzer(),
                BuildMetadataAnalyzer(),
                DependencyDiscoveryAnalyzer(),
                DependencyMetadataAnalyzer(),
                DependencyHealthAnalyzer(),
                CicdDiscoveryAnalyzer(),
                SecurityAnalyzer(),
                ArchitectureAnalyzer(),
                CloudReadinessAnalyzer(),
            ]
        ),
        analyzer_version=__version__,
        static_analysis_service=static_analysis_service,
    )
