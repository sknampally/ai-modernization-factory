"""Thin Typer adapter for Enterprise Knowledge Graph commands."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from aimf.application.enterprise.errors import EnterpriseApplicationError
from aimf.application.enterprise.factory import (
    create_enterprise_knowledge_service,
    create_enterprise_query_service,
    policy_from_settings,
)
from aimf.application.enterprise.models import EnterprisePolicy
from aimf.cli.enterprise_mapping import (
    EXIT_BLOCKED,
    EXIT_ERROR,
    EXIT_SUCCESS,
    dumps_json,
    exit_code_for_error,
)
from aimf.cli.enterprise_rendering import (
    emit_build,
    emit_diff,
    emit_graph,
    emit_validation,
)
from aimf.config import AimfSettings, load_settings
from aimf.domain.enterprise.enums import EnterpriseEntityKind, EnterpriseRelationshipKind
from aimf.infrastructure.enterprise.workspace import EnterpriseWorkspaceWriter

enterprise_app = typer.Typer(
    name="enterprise",
    help=(
        "CodeStrata Enterprise Knowledge Graph (YAML workspace).\n\n"
        "Optional enterprise context above repositories. Disabled by default. "
        "`aimf assess` remains unchanged."
    ),
    no_args_is_help=True,
)


def _load_settings_or_exit(config: Path) -> AimfSettings:
    try:
        return load_settings(config)
    except (FileNotFoundError, ValueError, OSError) as error:
        typer.secho(f"Configuration error: {error}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=EXIT_ERROR) from error


def _policy_for_build(settings: AimfSettings) -> EnterprisePolicy:
    policy = policy_from_settings(settings)
    # CLI build/validate may run even when enabled=false (explicit opt-in via command).
    return policy.model_copy(
        update={
            "allow_unresolved_repositories": True,
            "require_registered_repositories": False,
        }
    )


@enterprise_app.command("init")
def init_command(
    directory: Annotated[
        Path,
        typer.Argument(help="Workspace directory to create."),
    ] = Path("enterprise"),
    examples: Annotated[
        bool,
        typer.Option("--examples", help="Seed university example manifests."),
    ] = False,
    minimal: Annotated[
        bool,
        typer.Option("--minimal", help="Create minimal workspace only."),
    ] = False,
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite generated starter files only."),
    ] = False,
) -> None:
    """Create a starter enterprise YAML workspace."""

    try:
        writer = EnterpriseWorkspaceWriter()
        created = writer.create_workspace(
            str(directory),
            examples=examples and not minimal,
            force=force,
        )
    except EnterpriseApplicationError as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=exit_code_for_error(error)) from error
    typer.echo(f"Created workspace: {directory}")
    for item in created:
        typer.echo(f"  {item}")


@enterprise_app.command("validate")
def validate_command(
    directory: Annotated[
        Path,
        typer.Argument(help="Enterprise workspace directory."),
    ] = Path("enterprise"),
    config: Annotated[
        Path,
        typer.Option("--config", "-c"),
    ] = Path("aimf.toml"),
    as_json: Annotated[bool, typer.Option("--json")] = False,
    strict: Annotated[
        bool,
        typer.Option("--strict", help="Treat unresolved repositories as errors."),
    ] = False,
) -> None:
    """Validate enterprise YAML without persisting a graph."""

    settings = _load_settings_or_exit(config)
    policy = _policy_for_build(settings)
    if strict:
        policy = policy.model_copy(
            update={
                "require_registered_repositories": True,
                "allow_unresolved_repositories": False,
            }
        )
    service = create_enterprise_knowledge_service(settings=settings, policy=policy)
    try:
        result = service.validate_workspace(str(directory))
    except EnterpriseApplicationError as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=exit_code_for_error(error)) from error
    emit_validation(result, as_json=as_json)
    raise typer.Exit(code=EXIT_SUCCESS if result.status == "passed" else EXIT_BLOCKED)


@enterprise_app.command("build")
def build_command(
    directory: Annotated[
        Path,
        typer.Argument(help="Enterprise workspace directory."),
    ] = Path("enterprise"),
    config: Annotated[
        Path,
        typer.Option("--config", "-c"),
    ] = Path("aimf.toml"),
    as_json: Annotated[bool, typer.Option("--json")] = False,
    link_assessments: Annotated[
        bool | None,
        typer.Option("--link-assessments/--no-link-assessments"),
    ] = None,
) -> None:
    """Build and persist a complete Enterprise Knowledge Graph."""

    settings = _load_settings_or_exit(config)
    policy = _policy_for_build(settings)
    service = create_enterprise_knowledge_service(settings=settings, policy=policy)
    try:
        result = service.build_graph(str(directory), link_assessments=link_assessments)
    except EnterpriseApplicationError as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=exit_code_for_error(error)) from error
    emit_build(result, as_json=as_json)


@enterprise_app.command("inspect")
def inspect_command(
    entity_id: Annotated[
        str | None,
        typer.Argument(help="Optional entity id (e.g. application:sis)."),
    ] = None,
    config: Annotated[
        Path,
        typer.Option("--config", "-c"),
    ] = Path("aimf.toml"),
    graph_id: Annotated[str | None, typer.Option("--graph-id")] = None,
    enterprise_id: Annotated[str, typer.Option("--enterprise-id")] = "enterprise:acme",
    as_json: Annotated[bool, typer.Option("--json")] = False,
    depth: Annotated[int, typer.Option("--depth")] = 1,
) -> None:
    """Inspect latest graph summary or an entity neighborhood."""

    settings = _load_settings_or_exit(config)
    queries = create_enterprise_query_service(settings=settings)
    try:
        if entity_id:
            neighborhood = queries.get_neighborhood(
                entity_id,
                depth=depth,
                graph_id=graph_id,
                enterprise_id=enterprise_id,
            )
            if as_json:
                typer.echo(dumps_json(neighborhood.model_dump(mode="json")))
            else:
                typer.echo(f"Entity: {neighborhood.entity.entity_id}")
                typer.echo(f"Name: {neighborhood.entity.name}")
                typer.echo(f"Neighbors: {len(neighborhood.neighbors)}")
                for item in neighborhood.neighbors[:30]:
                    typer.echo(f"  {item.entity_id} ({item.kind.value})")
            return
        graph = queries.get_graph(graph_id) if graph_id else queries.get_latest_graph(enterprise_id)
        emit_graph(graph, as_json=as_json)
    except EnterpriseApplicationError as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=exit_code_for_error(error)) from error


@enterprise_app.command("query")
def query_command(
    subject: Annotated[
        str,
        typer.Argument(help="applications|repositories|impact|ownership|dependencies"),
    ],
    config: Annotated[
        Path,
        typer.Option("--config", "-c"),
    ] = Path("aimf.toml"),
    domain: Annotated[str | None, typer.Option("--domain")] = None,
    application: Annotated[str | None, typer.Option("--application")] = None,
    repository: Annotated[str | None, typer.Option("--repository")] = None,
    service: Annotated[str | None, typer.Option("--service")] = None,
    enterprise_id: Annotated[str, typer.Option("--enterprise-id")] = "enterprise:acme",
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """High-level enterprise queries (no arbitrary graph language)."""

    settings = _load_settings_or_exit(config)
    queries = create_enterprise_query_service(settings=settings)
    try:
        if subject == "applications" and domain:
            domain_id = domain if domain.startswith("domain:") else f"domain:{domain}"
            items = queries.list_by_relationship(
                target_id=domain_id,
                kind=EnterpriseRelationshipKind.APPLICATION_BELONGS_TO_DOMAIN,
                enterprise_id=enterprise_id,
            )
        elif subject == "repositories" and application:
            app_id = (
                application
                if application.startswith("application:")
                else f"application:{application}"
            )
            items = queries.list_by_relationship(
                source_id=app_id,
                kind=EnterpriseRelationshipKind.APPLICATION_USES_REPOSITORY,
                enterprise_id=enterprise_id,
            )
        elif subject == "impact" and repository:
            repo_id = (
                repository if repository.startswith("repository:") else f"repository:{repository}"
            )
            summary = queries.repository_context(repo_id, enterprise_id=enterprise_id)
            if as_json:
                typer.echo(dumps_json(summary.model_dump(mode="json")))
            else:
                typer.echo(f"Source: {summary.source_entity_id}")
                for item in summary.impacted_entities:
                    typer.echo(f"  {item.entity_id}")
            return
        elif subject == "ownership" and service:
            service_id = service if service.startswith("service:") else f"service:{service}"
            items = queries.list_by_relationship(
                target_id=service_id,
                kind=EnterpriseRelationshipKind.TEAM_OWNS_SERVICE,
                enterprise_id=enterprise_id,
            )
        elif subject == "dependencies" and service:
            service_id = service if service.startswith("service:") else f"service:{service}"
            items = queries.list_by_relationship(
                source_id=service_id,
                kind=EnterpriseRelationshipKind.SERVICE_DEPENDS_ON_SERVICE,
                enterprise_id=enterprise_id,
            )
        elif subject == "applications":
            items = queries.list_entities(
                kind=EnterpriseEntityKind.APPLICATION, enterprise_id=enterprise_id
            )
        else:
            typer.secho(
                "Unsupported query; see `aimf enterprise query --help`",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=EXIT_ERROR)
        if as_json:
            typer.echo(dumps_json([item.model_dump(mode="json") for item in items]))
        else:
            for item in items:
                typer.echo(f"{item.entity_id}: {item.name}")
    except EnterpriseApplicationError as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=exit_code_for_error(error)) from error


@enterprise_app.command("explain")
def explain_command(
    relationship_id: Annotated[
        str,
        typer.Argument(help="Relationship id to explain."),
    ],
    config: Annotated[
        Path,
        typer.Option("--config", "-c"),
    ] = Path("aimf.toml"),
    enterprise_id: Annotated[str, typer.Option("--enterprise-id")] = "enterprise:acme",
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Explain a relationship's declared versus derived provenance."""

    settings = _load_settings_or_exit(config)
    queries = create_enterprise_query_service(settings=settings)
    try:
        graph = queries.get_latest_graph(enterprise_id)
        match = next(
            (rel for rel in graph.relationships if str(rel.relationship_id) == relationship_id),
            None,
        )
        if match is None:
            raise EnterpriseApplicationError(
                "Relationship not found",
                reason_code="entity_not_found",
                relationship_id=relationship_id,
            )
        payload = {
            "relationship_id": str(match.relationship_id),
            "kind": match.kind.value,
            "source": str(match.source_entity_id),
            "target": str(match.target_entity_id),
            "provenance_category": match.provenance.category.value,
            "derivation_rule": match.provenance.derivation_rule,
            "confidence": match.provenance.confidence,
            "source_ref": match.provenance.source_ref,
        }
        if as_json:
            typer.echo(dumps_json(payload))
        else:
            for key, value in payload.items():
                typer.echo(f"{key}: {value}")
    except EnterpriseApplicationError as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=exit_code_for_error(error)) from error


@enterprise_app.command("compare")
def compare_command(
    left_graph_id: Annotated[str, typer.Argument()],
    right_graph_id: Annotated[str, typer.Argument()],
    config: Annotated[
        Path,
        typer.Option("--config", "-c"),
    ] = Path("aimf.toml"),
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Compare two persisted enterprise graph versions."""

    settings = _load_settings_or_exit(config)
    service = create_enterprise_knowledge_service(settings=settings)
    try:
        diff = service.compare_graph_versions(left_graph_id, right_graph_id)
    except EnterpriseApplicationError as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=exit_code_for_error(error)) from error
    emit_diff(diff, as_json=as_json)
