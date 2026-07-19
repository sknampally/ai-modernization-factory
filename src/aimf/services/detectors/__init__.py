"""Technology detector implementations."""

from aimf.services.detectors.composite_technology_detector import (
    CompositeTechnologyDetector,
)
from aimf.services.detectors.java_technology_detector import (
    JavaTechnologyDetector,
)
from aimf.services.detectors.javascript_technology_detector import (
    JavaScriptTechnologyDetector,
)
from aimf.services.detectors.php_technology_detector import (
    PhpTechnologyDetector,
)

__all__ = [
    "CompositeTechnologyDetector",
    "JavaScriptTechnologyDetector",
    "JavaTechnologyDetector",
    "PhpTechnologyDetector",
]