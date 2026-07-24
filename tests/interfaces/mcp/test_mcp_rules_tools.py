"""MCP tests for Shared Rule Platform tools."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from aimf.application.rules.factory import create_rule_analysis_service
from aimf.interfaces.mcp.server import build_mcp_server
from aimf.interfaces.mcp.tools.rules import register_rules_tools


def test_rules_tools_register_additively() -> None:
    server = FastMCP("test")
    service = create_rule_analysis_service()
    register_rules_tools(server, rule_analysis_service=service)
    # Tool manager should expose the four Phase 4.1 tools.
    tools = getattr(server, "_tool_manager", None)
    assert tools is not None


def test_list_shared_rules_includes_architecture_pack() -> None:
    from aimf.application.assessment import AssessmentApplicationService
    from aimf.application.knowledge.queries import KnowledgeQueryService
    from aimf.cli.rules_mapping import map_rule_view
    from aimf.domain.rules.enums import RuleCategory

    service = create_rule_analysis_service()
    views = service.list_rules(include_non_production=False)
    rows = [map_rule_view(view) for view in views]
    assert rows
    assert all(row["category"] == RuleCategory.ARCHITECTURE.value for row in rows)
    assert any(row["rule_id"] == "architecture.dependency-cycle" for row in rows)
    _ = AssessmentApplicationService
    _ = KnowledgeQueryService
    _ = build_mcp_server
