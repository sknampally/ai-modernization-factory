"""Human-readable enterprise CLI rendering."""

from __future__ import annotations

import typer

from aimf.application.enterprise.models import (
    EnterpriseBuildResult,
    EnterpriseGraphDiff,
    EnterpriseManifestValidationResult,
)
from aimf.cli.enterprise_mapping import (
    build_to_dict,
    diff_to_dict,
    dumps_json,
    graph_summary_to_dict,
    validation_to_dict,
)
from aimf.domain.enterprise.entities import EnterpriseKnowledgeGraph


def emit_validation(result: EnterpriseManifestValidationResult, *, as_json: bool) -> None:
    if as_json:
        typer.echo(dumps_json(validation_to_dict(result)))
        return
    typer.echo(f"Status: {result.status}")
    typer.echo(f"Manifests: {result.manifests_checked}")
    typer.echo(f"Entities: {result.entities_checked}")
    typer.echo(f"Relationships: {result.relationships_checked}")
    if result.errors:
        typer.echo("Errors:")
        for issue in result.errors[:50]:
            loc = issue.manifest_path or "-"
            typer.echo(f"  [{issue.code}] {loc}: {issue.safe_message}")
    if result.warnings:
        typer.echo("Warnings:")
        for issue in result.warnings[:50]:
            typer.echo(f"  [{issue.code}] {issue.safe_message}")
    if result.unresolved_repository_references:
        typer.echo(
            "Unresolved repositories: " + ", ".join(result.unresolved_repository_references[:20])
        )


def emit_build(result: EnterpriseBuildResult, *, as_json: bool) -> None:
    if as_json:
        typer.echo(dumps_json(build_to_dict(result)))
        return
    typer.echo(f"Graph ID: {result.graph.graph_id}")
    typer.echo(f"Enterprise: {result.graph.enterprise_id}")
    typer.echo(f"Entities: {len(result.graph.entities)}")
    typer.echo(f"Relationships: {len(result.graph.relationships)}")
    typer.echo(f"Repository links: {result.linked_repository_count}")
    typer.echo(f"Validation: {result.validation.status}")
    typer.echo(f"Duration ms: {result.duration_ms}")


def emit_graph(graph: EnterpriseKnowledgeGraph, *, as_json: bool) -> None:
    if as_json:
        typer.echo(dumps_json(graph_summary_to_dict(graph)))
        return
    typer.echo(f"Graph ID: {graph.graph_id}")
    typer.echo(f"Enterprise: {graph.enterprise_id}")
    typer.echo(f"Entities: {len(graph.entities)}")
    typer.echo(f"Relationships: {len(graph.relationships)}")
    typer.echo(f"Fingerprint: {graph.graph_fingerprint}")


def emit_diff(diff: EnterpriseGraphDiff, *, as_json: bool) -> None:
    if as_json:
        typer.echo(dumps_json(diff_to_dict(diff)))
        return
    typer.echo(f"Left: {diff.left_graph_id}")
    typer.echo(f"Right: {diff.right_graph_id}")
    typer.echo(f"Entities added: {len(diff.entities_added)}")
    typer.echo(f"Entities removed: {len(diff.entities_removed)}")
    typer.echo(f"Entities modified: {len(diff.entities_modified)}")
    typer.echo(f"Relationships added: {len(diff.relationships_added)}")
    typer.echo(f"Relationships removed: {len(diff.relationships_removed)}")
