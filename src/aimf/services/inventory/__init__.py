"""Repository inventory builder pipeline.

Converts scanner-discovered relative paths into a validated
``RepositoryManifest``. Stages are deterministic and scanner-agnostic: the
builder never depends on how files were discovered (local, GitHub, archive).
"""

from __future__ import annotations

from aimf.services.inventory.builder import RepositoryInventoryBuilder
from aimf.services.inventory.classification import RepositoryFileKindClassifier
from aimf.services.inventory.content_reader import (
    FileContent,
    LocalFilesystemContentReader,
    RepositoryContentReader,
)
from aimf.services.inventory.hashing import ContentHashingService
from aimf.services.inventory.language import FilenameLanguageDetector

__all__ = [
    "ContentHashingService",
    "FileContent",
    "FilenameLanguageDetector",
    "LocalFilesystemContentReader",
    "RepositoryContentReader",
    "RepositoryFileKindClassifier",
    "RepositoryInventoryBuilder",
]
