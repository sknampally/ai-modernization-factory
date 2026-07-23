"""Optional AI artifact MCP tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from aimf.application.knowledge.queries import KnowledgeQueryService
from aimf.interfaces.mcp.mapping import to_mcp_dict, to_mcp_payload
from aimf.interfaces.mcp.models import AbsentArtifactResponse
from aimf.interfaces.mcp.security import require_nonblank
from aimf.interfaces.mcp.tools._common import run_bounded


def register_artifact_tools(server: FastMCP, queries: KnowledgeQueryService) -> None:
    @server.tool(name="get_ai_execution", structured_output=True)
    def get_ai_execution(run_id: str) -> dict[str, Any]:
        """Return AI execution metadata when present for a run."""

        def _run() -> dict[str, Any]:
            payload = queries.get_ai_execution(require_nonblank(run_id, label="run_id"))
            if payload is None:
                return to_mcp_dict(
                    AbsentArtifactResponse(
                        present=False,
                        artifact="ai_execution",
                        message="AI execution artifact was not persisted for this run",
                    )
                )
            return {
                "present": True,
                "artifact": "ai_execution",
                "data": to_mcp_payload(payload),
            }

        return run_bounded("get_ai_execution", _run)

    @server.tool(name="get_ai_enrichment", structured_output=True)
    def get_ai_enrichment(run_id: str) -> dict[str, Any]:
        """Return AI enrichment narrative when present for a run."""

        def _run() -> dict[str, Any]:
            payload = queries.get_ai_enrichment(require_nonblank(run_id, label="run_id"))
            if payload is None:
                return to_mcp_dict(
                    AbsentArtifactResponse(
                        present=False,
                        artifact="ai_enrichment",
                        message="AI enrichment artifact was not persisted for this run",
                    )
                )
            return {
                "present": True,
                "artifact": "ai_enrichment",
                "data": to_mcp_payload(payload),
            }

        return run_bounded("get_ai_enrichment", _run)
