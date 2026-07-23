"""Additive MCP tools for Shared Rule Platform (Phase 4.1)."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from aimf.application.rules.analysis_service import RuleAnalysisService
from aimf.application.rules.errors import RuleApplicationError
from aimf.cli.rules_mapping import map_explanation, map_rule_view
from aimf.interfaces.mcp.tools._common import require_nonblank, run_bounded


def register_rules_tools(
    server: FastMCP,
    *,
    rule_analysis_service: RuleAnalysisService | None,
) -> None:
    @server.tool(name="list_shared_rules", structured_output=True)
    def list_shared_rules() -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if rule_analysis_service is None:
                raise RuleApplicationError(
                    "Rule analysis service is not configured",
                    reason_code="rules_service_missing",
                )
            views = rule_analysis_service.list_rules(include_non_production=False)
            return {"rules": [map_rule_view(view) for view in views]}

        return run_bounded("list_shared_rules", _run)

    @server.tool(name="get_shared_rule", structured_output=True)
    def get_shared_rule(rule_id: str) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if rule_analysis_service is None:
                raise RuleApplicationError(
                    "Rule analysis service is not configured",
                    reason_code="rules_service_missing",
                )
            view = rule_analysis_service.inspect_rule(
                require_nonblank(rule_id, label="rule_id")
            )
            if not view.production:
                raise RuleApplicationError(
                    "Rule not found",
                    reason_code="rule_not_found",
                    rule_id=rule_id,
                )
            return map_rule_view(view)

        return run_bounded("get_shared_rule", _run)

    @server.tool(name="explain_shared_rule_metadata", structured_output=True)
    def explain_shared_rule_metadata(rule_id: str) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if rule_analysis_service is None:
                raise RuleApplicationError(
                    "Rule analysis service is not configured",
                    reason_code="rules_service_missing",
                )
            view = rule_analysis_service.inspect_rule(
                require_nonblank(rule_id, label="rule_id")
            )
            if not view.production:
                raise RuleApplicationError(
                    "Rule not found",
                    reason_code="rule_not_found",
                    rule_id=rule_id,
                )
            return map_explanation(rule_analysis_service.explain_rule_metadata(rule_id))

        return run_bounded("explain_shared_rule_metadata", _run)

    @server.tool(name="get_shared_rule_platform_summary", structured_output=True)
    def get_shared_rule_platform_summary() -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if rule_analysis_service is None:
                raise RuleApplicationError(
                    "Rule analysis service is not configured",
                    reason_code="rules_service_missing",
                )
            views = rule_analysis_service.list_rules(include_non_production=False)
            return {
                "enabled_by_default": False,
                "production_rule_count": len(views),
                "wired_into_assess": False,
                "phase": "4.1",
                "note": "Shared Rule Platform infrastructure only; packs deferred to 4.2+",
            }

        return run_bounded("get_shared_rule_platform_summary", _run)
