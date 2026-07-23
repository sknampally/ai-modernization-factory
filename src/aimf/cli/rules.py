"""Thin CLI adapters for Shared Rule Platform (list / inspect only in 4.1)."""

from __future__ import annotations

import json
from typing import Annotated

import typer

from aimf.application.rules.errors import RuleApplicationError
from aimf.application.rules.factory import create_rule_analysis_service
from aimf.cli.rules_mapping import map_explanation, map_rule_view
from aimf.cli.rules_rendering import render_rule_detail, render_rules_table

rules_app = typer.Typer(
    name="rules",
    help=(
        "Shared Rule Platform (Phase 4.1).\n\n"
        "Lists and inspects registered production rules. Disabled by default; "
        "not wired into `aimf assess`. Fixture rules are hidden."
    ),
    no_args_is_help=True,
)


@rules_app.command("list")
def list_rules(
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit JSON."),
    ] = False,
) -> None:
    """List registered production shared rules."""

    service = create_rule_analysis_service()
    views = service.list_rules(include_non_production=False)
    rows = [map_rule_view(view) for view in views]
    if json_output:
        typer.echo(json.dumps({"rules": rows}, indent=2, ensure_ascii=False))
        return
    render_rules_table(rows)


@rules_app.command("inspect")
def inspect_rule(
    rule_id: Annotated[str, typer.Argument(help="Stable rule ID.")],
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit JSON."),
    ] = False,
) -> None:
    """Inspect one production shared rule."""

    service = create_rule_analysis_service()
    try:
        view = service.inspect_rule(rule_id)
    except RuleApplicationError as error:
        typer.echo(error.safe_message, err=True)
        raise typer.Exit(code=1) from error
    if not view.production:
        typer.echo("Rule not found", err=True)
        raise typer.Exit(code=1)
    row = map_rule_view(view)
    if json_output:
        typer.echo(json.dumps(row, indent=2, ensure_ascii=False))
        return
    render_rule_detail(row)


@rules_app.command("explain")
def explain_rule(
    rule_id: Annotated[str, typer.Argument(help="Stable rule ID.")],
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit JSON."),
    ] = False,
) -> None:
    """Explain rule metadata (deterministic; no AI)."""

    service = create_rule_analysis_service()
    try:
        view = service.inspect_rule(rule_id)
        if not view.production:
            raise RuleApplicationError(
                "Rule not found",
                reason_code="rule_not_found",
                rule_id=rule_id,
            )
        explanation = service.explain_rule_metadata(rule_id)
    except RuleApplicationError as error:
        typer.echo(error.safe_message, err=True)
        raise typer.Exit(code=1) from error
    payload = map_explanation(explanation)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    typer.echo(f"{payload['subject']}: {payload['message']}")
