"""MCP enterprise tool registration tests."""

from __future__ import annotations

import asyncio
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from aimf.application.enterprise.factory import (
    PassthroughRepositoryIdentityResolver,
    create_enterprise_knowledge_service,
    create_enterprise_query_service,
)
from aimf.application.enterprise.models import EnterprisePolicy
from aimf.infrastructure.enterprise.workspace import EnterpriseWorkspaceWriter
from aimf.interfaces.mcp.tools.enterprise import register_enterprise_tools


def test_enterprise_tools_registered(tmp_path: Path) -> None:
    workspace = tmp_path / "enterprise"
    EnterpriseWorkspaceWriter().create_workspace(str(workspace), examples=True)
    policy = EnterprisePolicy(
        require_registered_repositories=False,
        allow_unresolved_repositories=True,
    )
    knowledge = create_enterprise_knowledge_service(
        policy=policy,
        resolver=PassthroughRepositoryIdentityResolver(),
        knowledge_directory=tmp_path / "knowledge",
    )
    queries = create_enterprise_query_service(
        policy=policy, knowledge_directory=tmp_path / "knowledge"
    )
    knowledge.build_graph(str(workspace))
    server = FastMCP(name="test")
    register_enterprise_tools(
        server, knowledge_service=knowledge, query_service=queries
    )

    async def _check() -> None:
        tools = {tool.name for tool in await server.list_tools()}
        assert "validate_enterprise_workspace" in tools
        assert "build_enterprise_knowledge_graph" in tools
        assert "get_enterprise_graph" in tools
        assert "compare_enterprise_graph_versions" in tools

    asyncio.run(_check())
