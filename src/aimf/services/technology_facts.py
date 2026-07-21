"""Helpers for deriving technology facts from detections."""

from __future__ import annotations

from collections.abc import Sequence

from aimf.models.enums import TechnologyCategory
from aimf.models.normalized_facts import TechnologyFacts
from aimf.models.technology import Technology


def technology_facts_from_detections(
    technologies: Sequence[Technology],
) -> TechnologyFacts:
    """Normalize detected technologies into structured technology facts."""

    programming_languages: list[str] = []
    frameworks: list[str] = []
    build_tools: list[str] = []
    test_frameworks: list[str] = []
    detected_technologies: list[str] = []

    for technology in technologies:
        name = technology.name
        detected_technologies.append(name)

        if technology.category == TechnologyCategory.LANGUAGE:
            programming_languages.append(name)
        elif technology.category == TechnologyCategory.FRAMEWORK:
            frameworks.append(name)
        elif technology.category == TechnologyCategory.BUILD_TOOL:
            build_tools.append(name)
        elif technology.category == TechnologyCategory.TESTING:
            test_frameworks.append(name)

    return TechnologyFacts(
        programming_languages=list(dict.fromkeys(programming_languages)),
        frameworks=list(dict.fromkeys(frameworks)),
        build_tools=list(dict.fromkeys(build_tools)),
        test_frameworks=list(dict.fromkeys(test_frameworks)),
        detected_technologies=list(dict.fromkeys(detected_technologies)),
    )
