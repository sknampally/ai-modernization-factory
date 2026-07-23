"""Compose concrete knowledge-store implementations for application callers."""

from __future__ import annotations

from pathlib import Path

from aimf.config.settings import AimfSettings, KnowledgeSettings
from aimf.infrastructure.knowledge_store.defaults import DEFAULT_KNOWLEDGE_DIRECTORY
from aimf.infrastructure.knowledge_store.sqlite.store import SqliteKnowledgeStore


def knowledge_directory_from_settings(settings: AimfSettings | None) -> Path:
    """Resolve the knowledge directory from settings or the default path."""

    if settings is None:
        return DEFAULT_KNOWLEDGE_DIRECTORY
    knowledge: KnowledgeSettings = settings.knowledge
    return Path(knowledge.directory)


def create_knowledge_store(
    directory: Path | None = None,
    *,
    settings: AimfSettings | None = None,
) -> SqliteKnowledgeStore:
    """Create an unopened SQLite knowledge store for application use."""

    resolved = directory if directory is not None else knowledge_directory_from_settings(settings)
    return SqliteKnowledgeStore(resolved)
