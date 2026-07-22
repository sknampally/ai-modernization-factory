"""Built-in AIMF Engineering Knowledge Catalog access.

The seed catalog is deliberately small: enough to prove catalog contracts and
support upcoming Knowledge Pipeline work without attempting to model the entire
engineering industry. It is not loaded at import time.
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from aimf.domain.engineering_knowledge import EngineeringKnowledgeGraph
from aimf.services.engineering_knowledge.loader import EngineeringKnowledgeCatalogLoader

BUILTIN_CATALOG_ID = "aimf-core"
BUILTIN_CATALOG_VERSION = "1.0.0"
_BUILTIN_RESOURCE = "aimf-core-v1.yaml"


def builtin_engineering_knowledge_catalog_path() -> Path:
    """Return the filesystem path of the packaged AIMF core catalog."""

    resource = files("aimf.resources.engineering_knowledge").joinpath(_BUILTIN_RESOURCE)
    return Path(str(resource))


def load_builtin_engineering_knowledge_catalog() -> EngineeringKnowledgeGraph:
    """Load and validate the packaged AIMF core Engineering Knowledge Catalog."""

    return EngineeringKnowledgeCatalogLoader().load_path(
        builtin_engineering_knowledge_catalog_path()
    )
