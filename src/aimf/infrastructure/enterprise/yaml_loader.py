"""Safe YAML enterprise manifest loader (infrastructure boundary)."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import yaml

from aimf.application.enterprise.errors import (
    EnterpriseManifestLoadError,
    EnterpriseManifestParseError,
    EnterpriseSchemaVersionError,
    EnterpriseSecurityError,
    EnterpriseWorkspaceNotFoundError,
)
from aimf.application.enterprise.models import EnterprisePolicy
from aimf.domain.enterprise.manifests import (
    SUPPORTED_API_VERSION,
    EnterpriseManifestCollection,
    EnterpriseManifestDocument,
    ManifestMetadata,
)

logger = logging.getLogger(__name__)


class YamlEnterpriseManifestSource:
    """Load enterprise YAML manifests with hard security bounds."""

    def __init__(self, *, policy: EnterprisePolicy | None = None) -> None:
        self._policy = policy or EnterprisePolicy()

    def load(self, workspace_root: str) -> EnterpriseManifestCollection:
        root = Path(workspace_root)
        if not root.is_dir():
            raise EnterpriseWorkspaceNotFoundError(
                "Enterprise workspace directory was not found",
                reason_code="workspace_not_found",
                manifest_path=_safe_rel(root),
            )
        resolved_root = root.resolve()
        files = sorted(
            [
                path
                for path in resolved_root.rglob("*")
                if path.is_file() and path.suffix.lower() in {".yaml", ".yml"}
            ],
            key=lambda item: str(item.relative_to(resolved_root)).replace("\\", "/"),
        )
        if len(files) > self._policy.max_manifest_files:
            raise EnterpriseSecurityError(
                "Enterprise workspace exceeds max_manifest_files",
                reason_code="too_many_manifests",
            )
        documents: list[EnterpriseManifestDocument] = []
        fingerprints: list[str] = []
        for path in files:
            rel = str(path.relative_to(resolved_root)).replace("\\", "/")
            if path.is_symlink():
                target = path.resolve()
                try:
                    target.relative_to(resolved_root)
                except ValueError as error:
                    raise EnterpriseSecurityError(
                        "Symlink escapes enterprise workspace",
                        reason_code="symlink_escape",
                        manifest_path=rel,
                    ) from error
            size = path.stat().st_size
            if size > self._policy.max_manifest_size_bytes:
                raise EnterpriseSecurityError(
                    "Manifest exceeds max_manifest_size_bytes",
                    reason_code="manifest_too_large",
                    manifest_path=rel,
                )
            text = path.read_text(encoding="utf-8")
            try:
                # SafeLoader only — no custom constructors.
                payload = yaml.safe_load(text)
            except yaml.YAMLError as error:
                raise EnterpriseManifestParseError(
                    "Failed to parse enterprise YAML",
                    reason_code="yaml_parse_error",
                    manifest_path=rel,
                ) from error
            if payload is None:
                continue
            if not isinstance(payload, dict):
                raise EnterpriseManifestParseError(
                    "Enterprise YAML root must be a mapping",
                    reason_code="yaml_root_not_mapping",
                    manifest_path=rel,
                )
            _assert_depth(payload, self._policy.max_yaml_depth, rel)
            doc = self._to_document(payload, rel)
            documents.append(doc)
            fingerprints.append(doc.content_fingerprint)

        source_fp = hashlib.sha256(
            json.dumps(fingerprints, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        logger.info(
            "enterprise.manifests_loaded",
            extra={
                "manifest_count": len(documents),
                "source_fingerprint": source_fp,
            },
        )
        return EnterpriseManifestCollection(
            workspace_relative_root=_safe_rel(resolved_root),
            documents=tuple(documents),
            source_fingerprint=source_fp,
        )

    def _to_document(
        self, payload: dict[str, Any], relative_path: str
    ) -> EnterpriseManifestDocument:
        api_version = str(payload.get("apiVersion", "")).strip()
        if not api_version:
            raise EnterpriseSchemaVersionError(
                "apiVersion is required",
                reason_code="missing_api_version",
                manifest_path=relative_path,
                field_path="apiVersion",
            )
        if api_version != self._policy.schema_version and api_version != SUPPORTED_API_VERSION:
            raise EnterpriseSchemaVersionError(
                f"Unsupported apiVersion {api_version}",
                reason_code="unsupported_api_version",
                manifest_path=relative_path,
                field_path="apiVersion",
            )
        kind = payload.get("kind")
        metadata_raw = payload.get("metadata")
        if not isinstance(metadata_raw, dict):
            raise EnterpriseManifestLoadError(
                "metadata is required",
                reason_code="missing_metadata",
                manifest_path=relative_path,
                field_path="metadata",
            )
        spec = payload.get("spec") or {}
        if not isinstance(spec, dict):
            raise EnterpriseManifestLoadError(
                "spec must be a mapping",
                reason_code="invalid_spec",
                manifest_path=relative_path,
                field_path="spec",
            )
        metadata = ManifestMetadata(
            id=str(metadata_raw.get("id", "")),
            name=str(metadata_raw.get("name", "")),
            description=(
                str(metadata_raw["description"])
                if metadata_raw.get("description") is not None
                else None
            ),
            labels={
                str(key): str(value)
                for key, value in dict(metadata_raw.get("labels") or {}).items()
            },
            annotations={
                str(key): str(value)
                for key, value in dict(metadata_raw.get("annotations") or {}).items()
            },
            external_ids={
                str(key): str(value)
                for key, value in dict(metadata_raw.get("externalIds") or {}).items()
            },
        )
        canonical = {
            "apiVersion": api_version,
            "kind": kind,
            "metadata": metadata.model_dump(mode="json"),
            "spec": spec,
        }
        digest = hashlib.sha256(
            json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return EnterpriseManifestDocument(
            api_version=api_version,
            kind=str(kind),
            metadata=metadata,
            spec=dict(spec),
            source_relative_path=relative_path,
            content_fingerprint=digest,
        )


def _assert_depth(value: object, max_depth: int, path: str, depth: int = 0) -> None:
    if depth > max_depth:
        raise EnterpriseSecurityError(
            "YAML nesting exceeds max_yaml_depth",
            reason_code="yaml_too_deep",
            manifest_path=path,
        )
    if isinstance(value, dict):
        for item in value.values():
            _assert_depth(item, max_depth, path, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _assert_depth(item, max_depth, path, depth + 1)


def _safe_rel(path: Path) -> str:
    # Prefer basename-style relative label; never invent absolute exposure in messages.
    return path.name if path.name else "enterprise"
