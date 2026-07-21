"""Discover CI/CD pipeline configuration files."""

from __future__ import annotations

from collections.abc import Sequence

from aimf.models import (
    AnalyzerResult,
    CicdFacts,
    CicdPipeline,
    Repository,
    RepositoryFacts,
    Technology,
)


class CicdDiscoveryAnalyzer:
    """Discover supported CI/CD pipeline configurations."""

    _EXACT_PIPELINE_FILES = {
        ".gitlab-ci.yml": "gitlab-ci",
        ".gitlab-ci.yaml": "gitlab-ci",
        "Jenkinsfile": "jenkins",
        "azure-pipelines.yml": "azure-devops",
        "azure-pipelines.yaml": "azure-devops",
        ".circleci/config.yml": "circleci",
        ".circleci/config.yaml": "circleci",
        ".travis.yml": "travis-ci",
        ".travis.yaml": "travis-ci",
        "bitbucket-pipelines.yml": "bitbucket-pipelines",
        "bitbucket-pipelines.yaml": "bitbucket-pipelines",
        "buildspec.yml": "aws-codebuild",
        "buildspec.yaml": "aws-codebuild",
    }

    _GITHUB_WORKFLOW_PREFIX = ".github/workflows/"
    _GITHUB_WORKFLOW_SUFFIXES = (".yml", ".yaml")

    def analyze(
        self,
        repository: Repository,
        technologies: Sequence[Technology],
        facts: RepositoryFacts | None = None,
    ) -> AnalyzerResult:
        """Discover supported CI/CD files in the repository."""

        del technologies
        del facts

        pipelines: list[CicdPipeline] = []

        for relative_path in repository.files:
            provider = self._detect_provider(relative_path)

            if provider is None:
                continue

            pipelines.append(
                CicdPipeline(
                    provider=provider,
                    path=relative_path,
                    pipeline_name=self._pipeline_name(
                        relative_path=relative_path,
                        provider=provider,
                    ),
                )
            )

        pipelines.sort(
            key=lambda pipeline: (
                pipeline.provider,
                pipeline.path,
            )
        )

        providers = list(dict.fromkeys(pipeline.provider for pipeline in pipelines))

        pipeline_files = [pipeline.path for pipeline in pipelines]

        return AnalyzerResult(
            findings=[],
            facts=RepositoryFacts(
                cicd=CicdFacts(
                    pipelines=pipelines,
                    providers=providers,
                    pipeline_files=pipeline_files,
                    pipeline_count=len(pipelines),
                    job_count=0,
                    has_ci=bool(pipelines),
                )
            ),
        )

    def _detect_provider(
        self,
        relative_path: str,
    ) -> str | None:
        """Return the CI/CD provider for a repository path."""

        normalized_path = relative_path.replace("\\", "/")

        exact_provider = self._EXACT_PIPELINE_FILES.get(normalized_path)

        if exact_provider is not None:
            return exact_provider

        if normalized_path.startswith(self._GITHUB_WORKFLOW_PREFIX) and normalized_path.endswith(
            self._GITHUB_WORKFLOW_SUFFIXES
        ):
            return "github-actions"

        return None

    def _pipeline_name(
        self,
        relative_path: str,
        provider: str,
    ) -> str:
        """Infer a readable pipeline name from the file path."""

        normalized_path = relative_path.replace("\\", "/")
        file_name = normalized_path.rsplit("/", maxsplit=1)[-1]

        if provider == "github-actions":
            return self._remove_yaml_suffix(file_name)

        if provider == "jenkins":
            return "Jenkins Pipeline"

        return provider.replace("-", " ").title()

    def _remove_yaml_suffix(
        self,
        file_name: str,
    ) -> str:
        """Remove a YAML file extension."""

        for suffix in self._GITHUB_WORKFLOW_SUFFIXES:
            if file_name.endswith(suffix):
                return file_name[: -len(suffix)]

        return file_name
