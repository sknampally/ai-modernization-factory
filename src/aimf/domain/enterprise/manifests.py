"""Typed enterprise manifest envelopes (YAML-independent)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from aimf.domain.enterprise.enums import EnterpriseEntityKind

SUPPORTED_API_VERSION = "codestrata.io/v1alpha1"


class ManifestMetadata(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str | None = None
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)
    external_ids: dict[str, str] = Field(default_factory=dict)


class EnterpriseManifestDocument(BaseModel):
    """One YAML document after safe parse and envelope validation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    api_version: str
    kind: EnterpriseEntityKind | str
    metadata: ManifestMetadata
    spec: dict[str, Any] = Field(default_factory=dict)
    source_relative_path: str
    content_fingerprint: str


class EnterpriseManifestCollection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workspace_relative_root: str
    documents: tuple[EnterpriseManifestDocument, ...] = ()
    source_fingerprint: str


class RelationshipManifestEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: str
    source: str
    target: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    discriminator: str | None = None
