"""Composition helpers for the CodeStrata FastMCP server."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from mcp.server.fastmcp import FastMCP

from aimf.application.assessment import AssessmentApplicationService
from aimf.application.knowledge.ports import KnowledgeStore
from aimf.application.knowledge.queries import KnowledgeQueryService
from aimf.config import AimfSettings, load_settings
from aimf.infrastructure.knowledge_store.factory import (
    create_knowledge_query_service,
    create_knowledge_store,
)
from aimf.interfaces.mcp.server import build_mcp_server


def create_mcp_server(
    *,
    query_service: KnowledgeQueryService | None = None,
    assessment_service: AssessmentApplicationService | None = None,
    settings: AimfSettings | None = None,
    config_path: Path | None = None,
    knowledge_store: KnowledgeStore | None = None,
) -> FastMCP:
    """Create a CodeStrata FastMCP server with injectable application services.

    Importing this module has no side effects. Store/Bedrock connections occur
    only when services are constructed here or when tools execute.
    """

    resolved_settings = settings
    if resolved_settings is None and config_path is not None:
        resolved_settings = load_settings(config_path)

    queries = query_service
    if queries is None:
        if knowledge_store is not None:
            queries = KnowledgeQueryService(knowledge_store)
        else:
            queries = create_knowledge_query_service(settings=resolved_settings)

    assess = assessment_service or AssessmentApplicationService()
    return build_mcp_server(
        queries=queries,
        assessment_service=assess,
        settings=resolved_settings,
    )


def open_default_knowledge_store(settings: AimfSettings) -> KnowledgeStore:
    """Open the configured SQLite knowledge store for MCP composition."""

    store = create_knowledge_store(settings=settings)
    store.open()
    return cast(KnowledgeStore, store)
