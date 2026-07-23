"""Infrastructure adapters for enterprise YAML and graph persistence."""

from __future__ import annotations

__all__ = [
    "EnterpriseWorkspaceWriter",
    "FileEnterpriseGraphRepository",
    "FileEnterpriseManifestSnapshotRepository",
    "YamlEnterpriseManifestSource",
]


def __getattr__(name: str) -> object:
    if name in {
        "FileEnterpriseGraphRepository",
        "FileEnterpriseManifestSnapshotRepository",
    }:
        from aimf.infrastructure.enterprise import persistence as _persistence

        return getattr(_persistence, name)
    if name == "EnterpriseWorkspaceWriter":
        from aimf.infrastructure.enterprise.workspace import EnterpriseWorkspaceWriter

        return EnterpriseWorkspaceWriter
    if name == "YamlEnterpriseManifestSource":
        from aimf.infrastructure.enterprise.yaml_loader import YamlEnterpriseManifestSource

        return YamlEnterpriseManifestSource
    raise AttributeError(name)
