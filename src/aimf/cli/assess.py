"""Thin CLI adapter for modernization assessment."""

from __future__ import annotations

import traceback
from pathlib import Path
from typing import Annotated

import typer

from aimf.ai.providers.parsing import sanitize_provider_text
from aimf.application.assessment import (
    AIMF_BEDROCK_MODEL_ID_ENV,
    DEFAULT_ASSESS_MAX_OUTPUT_TOKENS,
    DEFAULT_ASSESS_OUTPUT_DIRECTORY,
    DEFAULT_ASSESS_REPORT_TITLE,
    DEFAULT_ASSESS_TEMPERATURE,
    AssessmentApplicationService,
    AssessmentCommandError,
    AssessmentCommandResult,
    is_github_repository_source,
    modernization_json_report_filename,
    modernization_report_basename,
    modernization_report_filename,
    resolve_assessment_repository,
    resolve_bedrock_model_id,
    run_assessment,
)
from aimf.logging_config import configure_logging
from aimf.reporting import AssessmentMode
from aimf.static_analysis.providers.pmd_discovery import AIMF_PMD_PATH_ENV

__all__ = [
    "AIMF_BEDROCK_MODEL_ID_ENV",
    "AIMF_PMD_PATH_ENV",
    "DEFAULT_ASSESS_MAX_OUTPUT_TOKENS",
    "DEFAULT_ASSESS_OUTPUT_DIRECTORY",
    "DEFAULT_ASSESS_REPORT_TITLE",
    "DEFAULT_ASSESS_TEMPERATURE",
    "AssessmentApplicationService",
    "AssessmentCommandError",
    "AssessmentCommandResult",
    "is_github_repository_source",
    "modernization_json_report_filename",
    "modernization_report_basename",
    "modernization_report_filename",
    "register_assess_command",
    "resolve_assessment_repository",
    "resolve_bedrock_model_id",
    "run_assessment",
]


def register_assess_command(app: typer.Typer) -> None:
    """Register the assess command on the AIMF Typer application."""

    @app.command("assess")
    def assess(
        repo: Annotated[
            str | None,
            typer.Option(
                "--repo",
                "-r",
                help=(
                    "Local repository path or GitHub URL. Overrides "
                    "repository.path / repository.url from --config. "
                    "Required when neither is set in configuration."
                ),
            ),
        ] = None,
        output: Annotated[
            Path,
            typer.Option(
                "--output",
                "-o",
                help="Directory where timestamped assessment reports are written.",
            ),
        ] = DEFAULT_ASSESS_OUTPUT_DIRECTORY,
        with_ai: Annotated[
            bool,
            typer.Option(
                "--with-ai/--no-ai",
                help=(
                    "Enable AI-enhanced assessment. Default is --no-ai "
                    "(deterministic evidence only; no cloud provider required)."
                ),
            ),
        ] = False,
        model_id: Annotated[
            str | None,
            typer.Option(
                "--model-id",
                help=(
                    "Bedrock model ID for --with-ai. Resolution order: this flag, "
                    "AIMF_BEDROCK_MODEL_ID, ai.bedrock.model_id, then "
                    "amazon.nova-lite-v1:0."
                ),
            ),
        ] = None,
        pmd_path: Annotated[
            str | None,
            typer.Option(
                "--pmd-path",
                help=(
                    "Optional path or command name for the PMD executable. "
                    f"Overrides {AIMF_PMD_PATH_ENV} and configuration."
                ),
            ),
        ] = None,
        pmd_profile: Annotated[
            str | None,
            typer.Option(
                "--pmd-profile",
                help=(
                    "PMD analysis profile: focused, standard, or comprehensive. "
                    "Overrides static_analysis.pmd.profile from configuration."
                ),
            ),
        ] = None,
        static_analysis: Annotated[
            bool,
            typer.Option(
                "--static-analysis/--no-static-analysis",
                help="Enable or disable external static analysis for this run.",
            ),
        ] = True,
        branch: Annotated[
            str | None,
            typer.Option(
                "--branch",
                help="Git branch for GitHub repositories.",
            ),
        ] = None,
        report_title: Annotated[
            str,
            typer.Option(
                "--report-title",
                help="Title shown in the HTML assessment report.",
            ),
        ] = DEFAULT_ASSESS_REPORT_TITLE,
        organization_name: Annotated[
            str | None,
            typer.Option(
                "--organization-name",
                help="Optional organization name for the HTML report header.",
            ),
        ] = None,
        max_output_tokens: Annotated[
            int,
            typer.Option(
                "--max-output-tokens",
                help="Maximum model output tokens (AI-enhanced mode only).",
            ),
        ] = DEFAULT_ASSESS_MAX_OUTPUT_TOKENS,
        temperature: Annotated[
            float,
            typer.Option(
                "--temperature",
                help="Model temperature (AI-enhanced mode only; default 0.0).",
            ),
        ] = DEFAULT_ASSESS_TEMPERATURE,
        max_context_characters: Annotated[
            int | None,
            typer.Option(
                "--max-context-characters",
                help="Maximum LLM analysis context JSON size in characters.",
            ),
        ] = None,
        config: Annotated[
            Path,
            typer.Option(
                "--config",
                "-c",
                help="Path to the AIMF TOML configuration file.",
            ),
        ] = Path("aimf.toml"),
        verbose: Annotated[
            bool,
            typer.Option(
                "--verbose",
                "-v",
                help="Enable diagnostic logging and display stack traces for failures.",
            ),
        ] = False,
    ) -> None:
        """Assess a repository and write HTML + JSON reports.

        Canonical workflow:

            aimf assess --config aimf.toml --output reports --with-ai

        Repository selection: --repo, then repository.path, then
        repository.url from the config file.
        """

        configure_logging(level="DEBUG" if verbose else "WARNING")

        if model_id and model_id.strip() and not with_ai:
            typer.secho(
                "--model-id requires --with-ai.\n\n"
                "Fix: add --with-ai, or omit --model-id for deterministic assessment.",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=2)

        mode = AssessmentMode.AI_ENHANCED if with_ai else AssessmentMode.DETERMINISTIC
        # Typer defaults --static-analysis to True; treat as "follow config" unless
        # the user explicitly disabled with --no-static-analysis.
        static_override: bool | None = False if not static_analysis else None

        try:
            run_assessment(
                repo=repo,
                output_directory=output,
                mode=mode,
                model_id=model_id,
                branch=branch,
                report_title=report_title,
                organization_name=organization_name,
                max_output_tokens=max_output_tokens,
                temperature=temperature,
                max_context_characters=max_context_characters,
                pmd_path=pmd_path,
                pmd_profile=pmd_profile,
                static_analysis_enabled=static_override,
                config_path=config,
                verbose=verbose,
            )
        except AssessmentCommandError as error:
            typer.secho(str(error), fg=typer.colors.RED, err=True)
            if verbose:
                typer.secho(traceback.format_exc(), fg=typer.colors.RED, err=True)
            raise typer.Exit(code=error.exit_code) from error
        except Exception as error:  # noqa: BLE001 - CLI boundary
            typer.secho(
                sanitize_provider_text(str(error)),
                fg=typer.colors.RED,
                err=True,
            )
            if verbose:
                typer.secho(traceback.format_exc(), fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1) from error
