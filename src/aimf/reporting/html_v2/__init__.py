"""HTML Report v2: view-model and self-contained renderer."""

from aimf.reporting.html_v2.builder import (
    build_html_report_view_model,
    default_report_artifacts,
)
from aimf.reporting.html_v2.models import (
    AiEnrichmentView,
    FindingView,
    HtmlReportViewModel,
    RecommendationView,
    ReportSummary,
)
from aimf.reporting.html_v2.renderer import CONTENT_SECURITY_POLICY, HtmlReportRenderer
from aimf.reporting.html_v2.versions import build_highlighted_versions
from aimf.reporting.modernization_models import HighlightedVersionInput, ReportArtifactInput

__all__ = [
    "CONTENT_SECURITY_POLICY",
    "AiEnrichmentView",
    "FindingView",
    "HighlightedVersionInput",
    "HtmlReportRenderer",
    "HtmlReportViewModel",
    "RecommendationView",
    "ReportArtifactInput",
    "ReportSummary",
    "build_highlighted_versions",
    "build_html_report_view_model",
    "default_report_artifacts",
]
