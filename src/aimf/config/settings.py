"""Application configuration loaded from a TOML file."""

import tomllib
from pathlib import Path

from pydantic import BaseModel, Field, HttpUrl


class RepositorySettings(BaseModel):
    """Configuration for the repository being analyzed."""

    url: HttpUrl
    branch: str | None = None


class WorkspaceSettings(BaseModel):
    """Configuration for the local analysis workspace."""

    directory: Path = Path(".aimf-workspace")
    clean_before_clone: bool = True


class AimfSettings(BaseModel):
    """Top-level AIMF application settings."""

    repository: RepositorySettings
    workspace: WorkspaceSettings = Field(
        default_factory=WorkspaceSettings,
    )


def load_settings(config_path: Path) -> AimfSettings:
    """Load AIMF settings from a TOML configuration file."""

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file does not exist: {config_path}"
        )

    if not config_path.is_file():
        raise ValueError(
            f"Configuration path is not a file: {config_path}"
        )

    with config_path.open("rb") as config_file:
        config_data = tomllib.load(config_file)

    return AimfSettings.model_validate(config_data)