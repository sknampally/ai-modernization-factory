"""Application configuration loaded from a TOML file."""

from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator

from aimf.config.dotenv import load_dotenv
from aimf.repository_auth.exceptions import UnsupportedRepositoryUrlError
from aimf.repository_auth.github_urls import parse_github_repository_url
from aimf.repository_auth.models import RepositoryAuthenticationConfig


class RepositorySettings(BaseModel):
    """Configuration for the repository being analyzed.

    Provide at least one of:

    * ``url`` — GitHub HTTPS/SSH URL (required for ``aimf scan``)
    * ``path`` — local filesystem path (supported by ``aimf assess``)
    """

    url: str | None = None
    path: str | None = None
    branch: str | None = None
    authentication: RepositoryAuthenticationConfig | None = None

    @field_validator("url")
    @classmethod
    def validate_repository_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        compact = value.strip()
        if not compact:
            raise ValueError("repository.url must be a nonempty GitHub URL")
        # Validate shape at configuration load time; do not resolve credentials.
        parse_github_repository_url(compact)
        return compact

    @field_validator("path")
    @classmethod
    def validate_repository_path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        compact = value.strip()
        if not compact:
            raise ValueError("repository.path must be a nonempty local path")
        if "://" in compact:
            raise ValueError(
                "repository.path must be a local filesystem path, not a URL. "
                "Use repository.url for GitHub repositories."
            )
        return compact

    @model_validator(mode="after")
    def require_url_or_path(self) -> RepositorySettings:
        if self.url is None and self.path is None:
            raise ValueError(
                "Configure repository.url (GitHub) or repository.path (local). "
                'Example: path = "examples/sample-js-app" or '
                'url = "https://github.com/org/repo"'
            )
        return self


class WorkspaceSettings(BaseModel):
    """Configuration for the local analysis workspace."""

    directory: Path = Path(".aimf-workspace")
    clean_before_clone: bool = True


class PmdSettings(BaseModel):
    """Configuration for the PMD static-analysis provider."""

    enabled: bool = True
    executable: str = "pmd"
    profile: str = "standard"
    rulesets: list[str] = Field(
        default_factory=lambda: [
            "category/java/bestpractices.xml",
            "category/java/errorprone.xml",
            "category/java/design.xml",
        ]
    )
    minimum_priority: int = 5
    timeout_seconds: int = 120

    @field_validator("executable")
    @classmethod
    def validate_executable(cls, value: str) -> str:
        compact = value.strip()
        if not compact:
            raise ValueError("PMD executable must be a nonempty string")
        if any(character in compact for character in [";", "|", "&", "`", "$", "\n"]):
            raise ValueError("PMD executable must not contain shell metacharacters")
        return compact

    @field_validator("profile")
    @classmethod
    def validate_profile(cls, value: str) -> str:
        from aimf.static_analysis.providers.pmd_profiles import parse_pmd_profile

        return parse_pmd_profile(value).value

    @field_validator("rulesets")
    @classmethod
    def validate_rulesets(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("PMD rulesets must not be empty")
        cleaned: list[str] = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("PMD rulesets must be nonempty strings")
            cleaned.append(item.strip())
        return cleaned

    @field_validator("minimum_priority")
    @classmethod
    def validate_priority(cls, value: int) -> int:
        if value < 1 or value > 5:
            raise ValueError("PMD minimum_priority must be between 1 and 5")
        return value

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("PMD timeout_seconds must be a positive integer")
        return value


class StaticAnalysisProviderSettings(BaseModel):
    """Provider-specific static-analysis settings."""

    pmd: PmdSettings = Field(default_factory=PmdSettings)


class StaticAnalysisSettings(BaseModel):
    """Top-level static-analysis subsystem settings."""

    enabled: bool = False
    fail_on_provider_error: bool = False
    pmd: PmdSettings = Field(default_factory=PmdSettings)

    @model_validator(mode="before")
    @classmethod
    def coerce_nested_pmd(cls, value: object) -> object:
        """Allow both [static_analysis.pmd] nesting styles from TOML."""

        if not isinstance(value, dict):
            return value
        # tomllib may provide pmd as nested table already.
        return value


class AwsSettings(BaseModel):
    """Optional AWS session settings for Bedrock and related services.

    Prefer configuring profile/region here so users do not need to export
    ``AWS_PROFILE`` or ``AWS_REGION`` before running ``aimf assess --with-ai``.
    """

    profile: str | None = None
    region: str | None = None

    @field_validator("profile", "region")
    @classmethod
    def validate_optional_nonempty(cls, value: str | None) -> str | None:
        if value is None:
            return None
        compact = value.strip()
        return compact or None


class BedrockSettings(BaseModel):
    """Optional AWS Bedrock settings for modernization assessment."""

    model_id: str | None = None
    region: str | None = None

    @field_validator("model_id", "region")
    @classmethod
    def validate_optional_nonempty(cls, value: str | None) -> str | None:
        if value is None:
            return None
        compact = value.strip()
        return compact or None


DEFAULT_BEDROCK_MODEL_ID = "amazon.nova-lite-v1:0"
DEFAULT_BEDROCK_PROVIDER = "bedrock"


class AiSettings(BaseModel):
    """Optional AI subsystem settings."""

    provider: str = "bedrock"
    bedrock: BedrockSettings = Field(default_factory=BedrockSettings)

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        compact = value.strip().lower()
        if not compact:
            raise ValueError("ai.provider must be a nonempty string")
        return compact


class KnowledgeSettings(BaseModel):
    """Local engineering knowledge store settings.

    The knowledge store is independent of report retention under ``reports/``.
    Assessment does not open this store automatically until a later increment.
    """

    directory: Path = Path(".aimf/knowledge")


class AimfSettings(BaseModel):
    """Top-level AIMF application settings."""

    repository: RepositorySettings
    workspace: WorkspaceSettings = Field(
        default_factory=WorkspaceSettings,
    )
    knowledge: KnowledgeSettings = Field(
        default_factory=KnowledgeSettings,
    )
    static_analysis: StaticAnalysisSettings = Field(
        default_factory=StaticAnalysisSettings,
    )
    aws: AwsSettings = Field(default_factory=AwsSettings)
    ai: AiSettings = Field(default_factory=AiSettings)


def load_settings(config_path: Path) -> AimfSettings:
    """Load AIMF settings from a TOML configuration file.

    Automatically loads a nearby ``.env`` file (if present) before reading
    configuration so environment-variable references such as
    ``AIMF_GITHUB_TOKEN`` resolve without requiring ``source .env``.
    """

    resolved_config = config_path.expanduser()
    load_dotenv(start_directory=resolved_config.parent)
    load_dotenv(start_directory=Path.cwd())

    if not resolved_config.exists():
        raise FileNotFoundError(
            f"Configuration file does not exist: {resolved_config}\n\n"
            "Fix: create aimf.toml in the project root (see README), or pass "
            "--config /path/to/aimf.toml"
        )

    if not resolved_config.is_file():
        raise ValueError(f"Configuration path is not a file: {resolved_config}")

    with resolved_config.open("rb") as config_file:
        config_data = tomllib.load(config_file)

    try:
        return AimfSettings.model_validate(config_data)
    except Exception as error:
        raise ValueError(
            f"Invalid configuration in {resolved_config}: {error}\n\n"
            "Fix: check [repository] url/path and other settings against the README."
        ) from error


def configured_repository_source(settings: AimfSettings) -> str | None:
    """Return the configured assess/scan repository source, if any.

    Preference for configuration-only resolution: local ``path``, then ``url``.
    """

    if settings.repository.path:
        return settings.repository.path
    if settings.repository.url:
        return settings.repository.url
    return None


def is_github_repository_source(source: str) -> bool:
    """Return whether ``source`` is a GitHub repository URL."""

    try:
        parse_github_repository_url(source)
    except UnsupportedRepositoryUrlError:
        return False
    return True
