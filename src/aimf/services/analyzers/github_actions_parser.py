"""Parse GitHub Actions workflow files."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from aimf.models import CicdPipeline


class GitHubActionsParser:
    """Parse GitHub Actions YAML workflow configurations."""

    _BUILD_KEYWORDS = (
        "build",
        "compile",
        "package",
        "assemble",
        "mvn package",
        "mvn install",
        "gradle build",
        "./gradlew build",
        "npm run build",
        "yarn build",
        "pnpm build",
    )

    _TEST_KEYWORDS = (
        "test",
        "pytest",
        "jest",
        "vitest",
        "mocha",
        "mvn test",
        "gradle test",
        "./gradlew test",
        "npm test",
        "yarn test",
        "pnpm test",
    )

    _DEPLOYMENT_KEYWORDS = (
        "deploy",
        "release",
        "publish",
        "kubectl",
        "helm",
        "terraform apply",
        "aws cloudformation deploy",
        "aws ecs update-service",
        "serverless deploy",
    )

    _SECURITY_KEYWORDS = (
        "security",
        "codeql",
        "dependabot",
        "snyk",
        "trivy",
        "sonarqube",
        "sonarcloud",
        "semgrep",
        "gitleaks",
        "dependency-check",
        "npm audit",
        "mvn dependency-check",
        "bandit",
    )

    _CACHE_ACTIONS = (
        "actions/cache",
        "setup-java",
        "setup-node",
        "setup-python",
        "setup-go",
    )

    _ARTIFACT_ACTIONS = (
        "actions/upload-artifact",
        "actions/download-artifact",
    )

    def parse(
        self,
        workflow_path: Path,
        relative_path: str,
    ) -> CicdPipeline:
        """Parse a GitHub Actions workflow file."""

        workflow_data = self._load_workflow(workflow_path)

        workflow_name = self._optional_string(workflow_data.get("name"))

        triggers = self._parse_triggers(workflow_data.get("on"))

        jobs_data = workflow_data.get("jobs")
        jobs = jobs_data if isinstance(jobs_data, Mapping) else {}

        job_names: list[str] = []
        build_commands: list[str] = []
        test_commands: list[str] = []
        deployment_commands: list[str] = []
        security_commands: list[str] = []

        uses_containers = False
        uses_matrix_builds = False
        uses_caching = False
        uses_artifacts = False

        for job_name, job_value in jobs.items():
            if not isinstance(job_name, str):
                continue

            if not isinstance(job_value, Mapping):
                continue

            job_names.append(job_name)

            uses_containers = uses_containers or self._job_uses_container(job_value)
            uses_matrix_builds = uses_matrix_builds or self._job_uses_matrix(job_value)

            steps = job_value.get("steps")

            if not isinstance(steps, list):
                continue

            for step in steps:
                if not isinstance(step, Mapping):
                    continue

                command = self._step_description(step)

                if command is not None:
                    self._classify_command(
                        command=command,
                        build_commands=build_commands,
                        test_commands=test_commands,
                        deployment_commands=deployment_commands,
                        security_commands=security_commands,
                    )

                action = self._optional_string(step.get("uses"))

                if action is None:
                    continue

                normalized_action = action.lower()

                uses_caching = (
                    uses_caching
                    or any(
                        cache_action in normalized_action for cache_action in self._CACHE_ACTIONS
                    )
                    and self._step_enables_cache(
                        step=step,
                        action=normalized_action,
                    )
                )

                uses_artifacts = uses_artifacts or any(
                    artifact_action in normalized_action
                    for artifact_action in self._ARTIFACT_ACTIONS
                )

                self._classify_command(
                    command=action,
                    build_commands=build_commands,
                    test_commands=test_commands,
                    deployment_commands=deployment_commands,
                    security_commands=security_commands,
                )

        return CicdPipeline(
            provider="github-actions",
            path=relative_path,
            pipeline_name=(workflow_name or self._pipeline_name(relative_path)),
            triggers=triggers,
            jobs=job_names,
            build_commands=self._unique(build_commands),
            test_commands=self._unique(test_commands),
            deployment_commands=self._unique(deployment_commands),
            security_commands=self._unique(security_commands),
            uses_containers=uses_containers,
            uses_matrix_builds=uses_matrix_builds,
            uses_caching=uses_caching,
            uses_artifacts=uses_artifacts,
            metadata={
                "job_count": len(job_names),
            },
        )

    def _load_workflow(
        self,
        workflow_path: Path,
    ) -> dict[str, Any]:
        """Load a workflow YAML file safely."""

        if not workflow_path.is_file():
            return {}

        try:
            raw_data = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        except (
            OSError,
            UnicodeDecodeError,
            yaml.YAMLError,
        ):
            return {}

        if not isinstance(raw_data, dict):
            return {}

        return {str(key): value for key, value in raw_data.items()}

    def _parse_triggers(
        self,
        trigger_value: object,
    ) -> list[str]:
        """Extract workflow trigger names."""

        if isinstance(trigger_value, str):
            return [trigger_value]

        if isinstance(trigger_value, list):
            return [value for value in trigger_value if isinstance(value, str)]

        if isinstance(trigger_value, Mapping):
            return [str(key) for key in trigger_value]

        return []

    def _job_uses_container(
        self,
        job: Mapping[object, object],
    ) -> bool:
        """Determine whether a job uses containers or services."""

        return job.get("container") is not None or job.get("services") is not None

    def _job_uses_matrix(
        self,
        job: Mapping[object, object],
    ) -> bool:
        """Determine whether a job uses a matrix strategy."""

        strategy = job.get("strategy")

        return isinstance(strategy, Mapping) and strategy.get("matrix") is not None

    def _step_description(
        self,
        step: Mapping[object, object],
    ) -> str | None:
        """Return the most useful description of a workflow step."""

        run_command = self._optional_string(step.get("run"))

        if run_command is not None:
            return run_command

        action = self._optional_string(step.get("uses"))

        if action is not None:
            return action

        return self._optional_string(step.get("name"))

    def _classify_command(
        self,
        command: str,
        build_commands: list[str],
        test_commands: list[str],
        deployment_commands: list[str],
        security_commands: list[str],
    ) -> None:
        """Classify a workflow command by its purpose."""

        normalized_command = command.lower()

        if self._contains_keyword(
            normalized_command,
            self._BUILD_KEYWORDS,
        ):
            build_commands.append(command)

        if self._contains_keyword(
            normalized_command,
            self._TEST_KEYWORDS,
        ):
            test_commands.append(command)

        if self._contains_keyword(
            normalized_command,
            self._DEPLOYMENT_KEYWORDS,
        ):
            deployment_commands.append(command)

        if self._contains_keyword(
            normalized_command,
            self._SECURITY_KEYWORDS,
        ):
            security_commands.append(command)

    def _contains_keyword(
        self,
        value: str,
        keywords: tuple[str, ...],
    ) -> bool:
        """Return whether a value contains a known keyword."""

        return any(keyword in value for keyword in keywords)

    def _step_enables_cache(
        self,
        step: Mapping[object, object],
        action: str,
    ) -> bool:
        """Determine whether an action step enables caching."""

        if "actions/cache" in action:
            return True

        with_values = step.get("with")

        if not isinstance(with_values, Mapping):
            return False

        return any(
            str(key).lower() == "cache" and value not in {None, "", False}
            for key, value in with_values.items()
        )

    def _pipeline_name(
        self,
        relative_path: str,
    ) -> str:
        """Infer a workflow name from its filename."""

        file_name = relative_path.replace(
            "\\",
            "/",
        ).rsplit("/", maxsplit=1)[-1]

        for suffix in (".yml", ".yaml"):
            if file_name.endswith(suffix):
                return file_name[: -len(suffix)]

        return file_name

    def _optional_string(
        self,
        value: object,
    ) -> str | None:
        """Return a non-empty string value."""

        if not isinstance(value, str):
            return None

        stripped_value = value.strip()

        return stripped_value or None

    def _unique(
        self,
        values: list[str],
    ) -> list[str]:
        """Deduplicate strings while preserving order."""

        return list(dict.fromkeys(values))
