"""Composition helpers for enterprise knowledge services."""

from __future__ import annotations

from pathlib import Path

from aimf.application.enterprise.knowledge_service import EnterpriseKnowledgeService
from aimf.application.enterprise.models import EnterprisePolicy
from aimf.application.enterprise.ports import RepositoryIdentityResolver
from aimf.application.enterprise.query_service import EnterpriseKnowledgeQueryService
from aimf.config.settings import AimfSettings
from aimf.infrastructure.enterprise.persistence import (
    FileEnterpriseGraphRepository,
    FileEnterpriseManifestSnapshotRepository,
)
from aimf.infrastructure.enterprise.yaml_loader import YamlEnterpriseManifestSource


class NullRepositoryIdentityResolver:
    def resolve(self, reference: str) -> str | None:
        return None


class PassthroughRepositoryIdentityResolver:
    """Treat canonical keys / IDs as resolved to themselves (tests / offline)."""

    def resolve(self, reference: str) -> str | None:
        compact = reference.strip()
        return compact or None


def policy_from_settings(settings: AimfSettings | None) -> EnterprisePolicy:
    if settings is None:
        return EnterprisePolicy()
    section = getattr(settings, "enterprise", None)
    if section is None:
        return EnterprisePolicy()
    return EnterprisePolicy(
        enabled=bool(section.enabled),
        workspace=str(section.workspace),
        schema_version=str(section.schema_version),
        persist_graph=bool(section.persist_graph),
        link_repository_assessments=bool(section.link_repository_assessments),
        require_registered_repositories=bool(section.require_registered_repositories),
        allow_unresolved_repositories=bool(section.allow_unresolved_repositories),
        unknown_fields=str(section.unknown_fields),
        max_manifest_files=int(section.max_manifest_files),
        max_manifest_size_bytes=int(section.max_manifest_size_bytes),
        max_yaml_depth=int(section.max_yaml_depth),
        max_graph_entities=int(section.max_graph_entities),
        max_graph_relationships=int(section.max_graph_relationships),
        max_query_results=int(section.max_query_results),
        max_traversal_depth=int(section.max_traversal_depth),
        max_dependency_paths=int(section.max_dependency_paths),
        persist_manifest_snapshot=bool(section.persist_manifest_snapshot),
    )


def create_enterprise_knowledge_service(
    *,
    settings: AimfSettings | None = None,
    policy: EnterprisePolicy | None = None,
    resolver: RepositoryIdentityResolver | None = None,
    knowledge_directory: Path | None = None,
) -> EnterpriseKnowledgeService:
    resolved_policy = policy or policy_from_settings(settings)
    if knowledge_directory is None and settings is not None:
        knowledge_directory = Path(settings.knowledge.directory)
    if knowledge_directory is None:
        knowledge_directory = Path(".aimf/knowledge")
    graph_root = knowledge_directory / "enterprise_graphs"
    snap_root = knowledge_directory / "enterprise_manifest_snapshots"
    return EnterpriseKnowledgeService(
        manifest_source=YamlEnterpriseManifestSource(policy=resolved_policy),
        graph_repository=FileEnterpriseGraphRepository(graph_root),
        snapshot_repository=FileEnterpriseManifestSnapshotRepository(snap_root),
        resolver=resolver
        if resolver is not None
        else (
            PassthroughRepositoryIdentityResolver()
            if resolved_policy.allow_unresolved_repositories
            or not resolved_policy.require_registered_repositories
            else NullRepositoryIdentityResolver()
        ),
        policy=resolved_policy,
    )


def create_enterprise_query_service(
    *,
    settings: AimfSettings | None = None,
    policy: EnterprisePolicy | None = None,
    knowledge_directory: Path | None = None,
) -> EnterpriseKnowledgeQueryService:
    resolved_policy = policy or policy_from_settings(settings)
    if knowledge_directory is None and settings is not None:
        knowledge_directory = Path(settings.knowledge.directory)
    if knowledge_directory is None:
        knowledge_directory = Path(".aimf/knowledge")
    return EnterpriseKnowledgeQueryService(
        FileEnterpriseGraphRepository(knowledge_directory / "enterprise_graphs"),
        policy=resolved_policy,
    )
