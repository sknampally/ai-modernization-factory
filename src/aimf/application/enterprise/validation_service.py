"""Deterministic enterprise manifest validation."""

from __future__ import annotations

from collections import defaultdict

from aimf.application.enterprise.models import (
    EnterpriseManifestValidationResult,
    EnterprisePolicy,
    EnterpriseValidationIssue,
    EnterpriseValidationSeverity,
)
from aimf.application.enterprise.ports import RepositoryIdentityResolver
from aimf.domain.enterprise.enums import (
    EnterpriseEntityKind,
    EnterpriseProvenanceCategory,
    EnterpriseRelationshipKind,
)
from aimf.domain.enterprise.errors import (
    EnterpriseHierarchyCycleError,
    EnterpriseIdentityError,
    EnterpriseRelationshipConstraintError,
)
from aimf.domain.enterprise.identifiers import (
    build_entity_id,
    build_relationship_id,
    normalize_local_id,
)
from aimf.domain.enterprise.manifests import (
    SUPPORTED_API_VERSION,
    EnterpriseManifestCollection,
)
from aimf.domain.enterprise.relationships import (
    HIERARCHY_RELATIONSHIPS,
    validate_relationship_kinds,
)

_SUSPICIOUS_KEYS = frozenset(
    {
        "password",
        "secret",
        "token",
        "privatekey",
        "private_key",
        "accesskey",
        "access_key",
        "clientsecret",
        "client_secret",
        "connectionstring",
        "connection_string",
    }
)

_KIND_MAP: dict[str, EnterpriseEntityKind] = {
    item.value: item for item in EnterpriseEntityKind if not item.value.startswith("Codestrata")
}
_KIND_MAP["Relationships"] = EnterpriseEntityKind.ENTERPRISE  # collection marker handled separately

_REF_FIELDS: dict[str, EnterpriseEntityKind] = {
    "parentOrganization": EnterpriseEntityKind.ORGANIZATION,
    "parentDomain": EnterpriseEntityKind.BUSINESS_DOMAIN,
    "parentCapability": EnterpriseEntityKind.BUSINESS_CAPABILITY,
    "parentTeam": EnterpriseEntityKind.TEAM,
    "owningOrganization": EnterpriseEntityKind.ORGANIZATION,
    "owningTeam": EnterpriseEntityKind.TEAM,
    "businessOwner": EnterpriseEntityKind.PERSON,
    "technicalOwner": EnterpriseEntityKind.PERSON,
    "defaultOrganization": EnterpriseEntityKind.ORGANIZATION,
}


class EnterpriseManifestValidationService:
    def validate(
        self,
        collection: EnterpriseManifestCollection,
        *,
        policy: EnterprisePolicy,
        resolver: RepositoryIdentityResolver | None = None,
    ) -> EnterpriseManifestValidationResult:
        errors: list[EnterpriseValidationIssue] = []
        warnings: list[EnterpriseValidationIssue] = []
        entity_ids: dict[str, str] = {}
        entity_kinds: dict[str, EnterpriseEntityKind] = {}
        relationship_ids: set[str] = set()
        hierarchy_edges: list[tuple[str, str, str]] = []
        unresolved_repos: list[str] = []
        entities_checked = 0
        relationships_checked = 0

        relationship_docs: list[tuple[str, list[object]]] = []

        for doc in collection.documents:
            if (
                doc.api_version != policy.schema_version
                and doc.api_version != SUPPORTED_API_VERSION
            ):
                errors.append(
                    _issue(
                        "unsupported_api_version",
                        f"Unsupported apiVersion {doc.api_version}",
                        manifest_path=doc.source_relative_path,
                        field_path="apiVersion",
                    )
                )
                continue
            kind_raw = str(doc.kind)
            if kind_raw == "Relationships":
                entries = doc.spec.get("relationships", [])
                if not isinstance(entries, list):
                    errors.append(
                        _issue(
                            "invalid_relationships",
                            "Relationships.spec.relationships must be a list",
                            manifest_path=doc.source_relative_path,
                        )
                    )
                    continue
                relationship_docs.append((doc.source_relative_path, list(entries)))
                continue

            try:
                kind = EnterpriseEntityKind(kind_raw)
            except ValueError:
                errors.append(
                    _issue(
                        "unsupported_kind",
                        f"Unsupported kind {kind_raw}",
                        manifest_path=doc.source_relative_path,
                        field_path="kind",
                    )
                )
                continue

            entities_checked += 1
            try:
                local_id = normalize_local_id(doc.metadata.id)
                entity_id = build_entity_id(kind, local_id)
            except EnterpriseIdentityError as error:
                errors.append(
                    _issue(
                        error.reason_code,
                        str(error),
                        manifest_path=doc.source_relative_path,
                        field_path="metadata.id",
                    )
                )
                continue

            if entity_id in entity_ids:
                errors.append(
                    _issue(
                        "duplicate_entity_id",
                        f"Duplicate entity id {entity_id}",
                        manifest_path=doc.source_relative_path,
                        entity_id=entity_id,
                    )
                )
            else:
                entity_ids[entity_id] = doc.source_relative_path
                entity_kinds[entity_id] = kind

            self._scan_secrets(doc.spec, doc.source_relative_path, errors)
            self._scan_credential_urls(doc.spec, doc.source_relative_path, errors)

            if kind is EnterpriseEntityKind.REPOSITORY_REFERENCE:
                ref = str(doc.spec.get("canonicalKey") or doc.spec.get("remoteUrl") or local_id)
                if resolver is not None:
                    resolved = resolver.resolve(ref)
                    if resolved is None:
                        unresolved_repos.append(entity_id)
                        if (
                            policy.require_registered_repositories
                            and not policy.allow_unresolved_repositories
                        ):
                            errors.append(
                                _issue(
                                    "unresolved_repository",
                                    f"Repository reference {entity_id} could not be resolved",
                                    manifest_path=doc.source_relative_path,
                                    entity_id=entity_id,
                                )
                            )
                        else:
                            warnings.append(
                                _issue(
                                    "unresolved_repository",
                                    f"Repository reference {entity_id} is unresolved",
                                    manifest_path=doc.source_relative_path,
                                    entity_id=entity_id,
                                    severity=EnterpriseValidationSeverity.WARNING,
                                    blocking=False,
                                )
                            )

            for field, _target_kind in (
                ("businessDomains", EnterpriseEntityKind.BUSINESS_DOMAIN),
                ("capabilities", EnterpriseEntityKind.BUSINESS_CAPABILITY),
                ("repositories", EnterpriseEntityKind.REPOSITORY_REFERENCE),
                ("services", EnterpriseEntityKind.SERVICE),
                ("apis", EnterpriseEntityKind.API),
                ("dataStores", EnterpriseEntityKind.DATA_STORE),
                ("environments", EnterpriseEntityKind.ENVIRONMENT),
                ("applications", EnterpriseEntityKind.APPLICATION),
            ):
                values = doc.spec.get(field, [])
                if values and not isinstance(values, list):
                    errors.append(
                        _issue(
                            "invalid_reference_list",
                            f"{field} must be a list",
                            manifest_path=doc.source_relative_path,
                            field_path=f"spec.{field}",
                            entity_id=entity_id,
                        )
                    )

            for field, target_kind in _REF_FIELDS.items():
                if field in doc.spec and doc.spec[field]:
                    try:
                        build_entity_id(target_kind, str(doc.spec[field]))
                    except EnterpriseIdentityError as error:
                        errors.append(
                            _issue(
                                error.reason_code,
                                str(error),
                                manifest_path=doc.source_relative_path,
                                field_path=f"spec.{field}",
                                entity_id=entity_id,
                            )
                        )

        # Second pass: relationships after all entities are indexed.
        for path, entries in relationship_docs:
            for entry in entries:
                relationships_checked += 1
                self._validate_relationship_entry(
                    entry,
                    path,
                    entity_kinds,
                    relationship_ids,
                    hierarchy_edges,
                    errors,
                )

        # Second pass: resolve pending scalar refs and list refs from specs.
        pending_refs: list[tuple[str, str, str, str]] = []
        for doc in collection.documents:
            kind_raw = str(doc.kind)
            if kind_raw == "Relationships":
                continue
            try:
                kind = EnterpriseEntityKind(kind_raw)
                entity_id = build_entity_id(kind, doc.metadata.id)
            except (ValueError, EnterpriseIdentityError):
                continue
            for field, target_kind in _REF_FIELDS.items():
                value = doc.spec.get(field)
                if not value:
                    continue
                try:
                    target_id = build_entity_id(target_kind, str(value))
                except EnterpriseIdentityError:
                    continue
                pending_refs.append((entity_id, target_id, field, doc.source_relative_path))
            for field, target_kind, rel_kind in (
                (
                    "businessDomains",
                    EnterpriseEntityKind.BUSINESS_DOMAIN,
                    EnterpriseRelationshipKind.APPLICATION_BELONGS_TO_DOMAIN,
                ),
                (
                    "capabilities",
                    EnterpriseEntityKind.BUSINESS_CAPABILITY,
                    EnterpriseRelationshipKind.APPLICATION_SUPPORTS_CAPABILITY,
                ),
                (
                    "repositories",
                    EnterpriseEntityKind.REPOSITORY_REFERENCE,
                    EnterpriseRelationshipKind.APPLICATION_USES_REPOSITORY,
                ),
                (
                    "services",
                    EnterpriseEntityKind.SERVICE,
                    EnterpriseRelationshipKind.APPLICATION_CONTAINS_SERVICE,
                ),
            ):
                values = doc.spec.get(field, [])
                if not isinstance(values, list):
                    continue
                for item in values:
                    try:
                        target_id = build_entity_id(target_kind, str(item))
                    except EnterpriseIdentityError as error:
                        errors.append(
                            _issue(
                                error.reason_code,
                                str(error),
                                manifest_path=doc.source_relative_path,
                                field_path=f"spec.{field}",
                                entity_id=entity_id,
                            )
                        )
                        continue
                    pending_refs.append((entity_id, target_id, field, doc.source_relative_path))
                    if kind is EnterpriseEntityKind.APPLICATION and field in {
                        "businessDomains",
                        "capabilities",
                        "repositories",
                        "services",
                    }:
                        try:
                            validate_relationship_kinds(rel_kind, kind, target_kind)
                        except EnterpriseRelationshipConstraintError:
                            pass

        for source_id, target_id, field, path in pending_refs:
            if target_id not in entity_kinds:
                errors.append(
                    _issue(
                        "unknown_reference",
                        f"Unknown reference {target_id} in {field}",
                        manifest_path=path,
                        field_path=f"spec.{field}",
                        entity_id=source_id,
                    )
                )

        # Hierarchy cycles from explicit relationship entries.
        try:
            cycles = _detect_cycles(hierarchy_edges)
        except EnterpriseHierarchyCycleError as error:
            cycles = (str(error),)
        for cycle in cycles:
            errors.append(
                _issue(
                    "hierarchy_cycle",
                    f"Hierarchy cycle detected: {cycle}",
                    blocking=True,
                )
            )

        status = "passed" if not errors else "failed"
        return EnterpriseManifestValidationResult(
            status=status,
            manifests_checked=len(collection.documents),
            entities_checked=entities_checked,
            relationships_checked=relationships_checked,
            errors=tuple(errors),
            warnings=tuple(warnings),
            unresolved_repository_references=tuple(sorted(set(unresolved_repos))),
            duplicate_ids=tuple(
                sorted(
                    {
                        issue.entity_id
                        for issue in errors
                        if issue.code == "duplicate_entity_id" and issue.entity_id
                    }
                )
            ),
            cycles=tuple(cycles) if isinstance(cycles, tuple) else tuple(cycles),
            source_fingerprint=collection.source_fingerprint,
        )

    def _validate_relationship_entry(
        self,
        entry: object,
        path: str,
        entity_kinds: dict[str, EnterpriseEntityKind],
        relationship_ids: set[str],
        hierarchy_edges: list[tuple[str, str, str]],
        errors: list[EnterpriseValidationIssue],
    ) -> None:
        if not isinstance(entry, dict):
            errors.append(
                _issue(
                    "invalid_relationship",
                    "Relationship entry must be a mapping",
                    manifest_path=path,
                )
            )
            return
        kind_raw = str(entry.get("kind", ""))
        source = str(entry.get("source", ""))
        target = str(entry.get("target", ""))
        try:
            kind = EnterpriseRelationshipKind(kind_raw)
        except ValueError:
            errors.append(
                _issue(
                    "unsupported_relationship_kind",
                    f"Unsupported relationship kind {kind_raw}",
                    manifest_path=path,
                )
            )
            return
        if source not in entity_kinds or target not in entity_kinds:
            # May be validated after full load; warn if missing.
            if source and source not in entity_kinds:
                errors.append(
                    _issue(
                        "unknown_reference",
                        f"Unknown relationship source {source}",
                        manifest_path=path,
                        entity_id=source,
                    )
                )
            if target and target not in entity_kinds:
                errors.append(
                    _issue(
                        "unknown_reference",
                        f"Unknown relationship target {target}",
                        manifest_path=path,
                        entity_id=target,
                    )
                )
            return
        try:
            validate_relationship_kinds(kind, entity_kinds[source], entity_kinds[target])
        except EnterpriseRelationshipConstraintError as error:
            errors.append(
                _issue(
                    error.reason_code,
                    str(error),
                    manifest_path=path,
                    relationship_id=None,
                )
            )
            return
        rel_id = build_relationship_id(
            kind,
            source,
            target,
            discriminator=str(entry["discriminator"]) if entry.get("discriminator") else None,
        )
        if rel_id in relationship_ids:
            errors.append(
                _issue(
                    "duplicate_relationship",
                    f"Duplicate relationship {rel_id}",
                    manifest_path=path,
                    relationship_id=rel_id,
                )
            )
        relationship_ids.add(rel_id)
        if kind in HIERARCHY_RELATIONSHIPS:
            hierarchy_edges.append((source, target, kind.value))

    def _scan_secrets(
        self,
        payload: object,
        path: str,
        errors: list[EnterpriseValidationIssue],
    ) -> None:
        if isinstance(payload, dict):
            for key, value in payload.items():
                key_l = str(key).lower().replace("-", "_")
                if key_l in _SUSPICIOUS_KEYS or key_l.replace("_", "") in {
                    item.replace("_", "") for item in _SUSPICIOUS_KEYS
                }:
                    errors.append(
                        _issue(
                            "suspicious_secret_field",
                            f"Suspicious secret-like field '{key}' is not allowed",
                            manifest_path=path,
                            field_path=str(key),
                        )
                    )
                    continue
                self._scan_secrets(value, path, errors)
        elif isinstance(payload, list):
            for item in payload:
                self._scan_secrets(item, path, errors)

    def _scan_credential_urls(
        self,
        payload: object,
        path: str,
        errors: list[EnterpriseValidationIssue],
    ) -> None:
        if isinstance(payload, dict):
            for key, value in payload.items():
                if (
                    isinstance(value, str)
                    and "://" in value
                    and "@" in value.split("://", 1)[-1].split("/", 1)[0]
                ):
                    errors.append(
                        _issue(
                            "credential_bearing_url",
                            f"Credential-bearing URL rejected in field '{key}'",
                            manifest_path=path,
                            field_path=str(key),
                        )
                    )
                else:
                    self._scan_credential_urls(value, path, errors)
        elif isinstance(payload, list):
            for item in payload:
                self._scan_credential_urls(item, path, errors)


def _issue(
    code: str,
    message: str,
    *,
    manifest_path: str | None = None,
    field_path: str | None = None,
    entity_id: str | None = None,
    relationship_id: str | None = None,
    severity: EnterpriseValidationSeverity = EnterpriseValidationSeverity.ERROR,
    blocking: bool = True,
) -> EnterpriseValidationIssue:
    return EnterpriseValidationIssue(
        code=code,
        severity=severity,
        safe_message=message,
        manifest_path=manifest_path,
        field_path=field_path,
        entity_id=entity_id,
        relationship_id=relationship_id,
        blocking=blocking,
    )


def _detect_cycles(edges: list[tuple[str, str, str]]) -> tuple[str, ...]:
    graph: dict[str, list[str]] = defaultdict(list)
    for source, target, _kind in edges:
        graph[source].append(target)
    cycles: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def dfs(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            if node in stack:
                idx = stack.index(node)
                cycles.append(" -> ".join(stack[idx:] + [node]))
            return
        visiting.add(node)
        stack.append(node)
        for nxt in graph.get(node, []):
            dfs(nxt)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in sorted(graph):
        dfs(node)
    return tuple(sorted(set(cycles)))


# Silence unused import warning for provenance category in this module.
_ = EnterpriseProvenanceCategory
