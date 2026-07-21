"""Classify commands and actions found in CI/CD pipelines."""

from __future__ import annotations

from enum import StrEnum


class CicdCommandCategory(StrEnum):
    """Supported classifications for CI/CD commands."""

    BUILD = "build"
    TEST = "test"
    DEPLOYMENT = "deployment"
    SECURITY = "security"
    PACKAGING = "packaging"
    INFRASTRUCTURE = "infrastructure"
    DATABASE = "database"


class CicdCommandClassifier:
    """Classify CI/CD commands using deterministic patterns."""

    _CATEGORY_PATTERNS: dict[
        CicdCommandCategory,
        tuple[str, ...],
    ] = {
        CicdCommandCategory.BUILD: (
            "mvn compile",
            "mvn package",
            "mvn install",
            "mvn verify",
            "gradle build",
            "./gradlew build",
            "npm run build",
            "npm build",
            "yarn build",
            "pnpm build",
            "composer install",
            "composer update",
            "dotnet build",
            "go build",
            "cargo build",
            "make build",
            "make all",
        ),
        CicdCommandCategory.TEST: (
            "mvn test",
            "mvn verify",
            "gradle test",
            "./gradlew test",
            "npm test",
            "npm run test",
            "yarn test",
            "pnpm test",
            "pytest",
            "phpunit",
            "vendor/bin/phpunit",
            "dotnet test",
            "go test",
            "cargo test",
            "jest",
            "vitest",
            "mocha",
            "cypress",
            "playwright test",
        ),
        CicdCommandCategory.DEPLOYMENT: (
            "deploy",
            "release",
            "kubectl apply",
            "kubectl rollout",
            "helm install",
            "helm upgrade",
            "terraform apply",
            "aws cloudformation deploy",
            "aws ecs update-service",
            "aws lambda update-function-code",
            "serverless deploy",
            "vercel deploy",
            "netlify deploy",
            "firebase deploy",
            "docker push",
        ),
        CicdCommandCategory.SECURITY: (
            "codeql",
            "dependabot",
            "snyk",
            "trivy",
            "sonarqube",
            "sonarcloud",
            "sonar-scanner",
            "semgrep",
            "gitleaks",
            "dependency-check",
            "npm audit",
            "yarn audit",
            "pnpm audit",
            "composer audit",
            "bandit",
            "safety check",
            "pip-audit",
            "checkov",
            "tfsec",
            "grype",
        ),
        CicdCommandCategory.PACKAGING: (
            "docker build",
            "docker buildx",
            "mvn package",
            "gradle assemble",
            "./gradlew assemble",
            "npm pack",
            "composer archive",
            "dotnet pack",
            "helm package",
        ),
        CicdCommandCategory.INFRASTRUCTURE: (
            "terraform plan",
            "terraform apply",
            "terraform validate",
            "pulumi preview",
            "pulumi up",
            "cdk synth",
            "cdk deploy",
            "cloudformation",
            "kubectl",
            "helm",
            "ansible-playbook",
        ),
        CicdCommandCategory.DATABASE: (
            "flyway migrate",
            "liquibase update",
            "prisma migrate",
            "sequelize db:migrate",
            "typeorm migration",
            "artisan migrate",
            "doctrine:migrations",
            "alembic upgrade",
            "rails db:migrate",
        ),
    }

    def classify(
        self,
        command: str,
    ) -> set[CicdCommandCategory]:
        """Return all categories matching a command or action."""

        normalized_command = self._normalize(command)

        if not normalized_command:
            return set()

        return {
            category
            for category, patterns in self._CATEGORY_PATTERNS.items()
            if any(pattern in normalized_command for pattern in patterns)
        }

    def belongs_to(
        self,
        command: str,
        category: CicdCommandCategory,
    ) -> bool:
        """Return whether a command belongs to a category."""

        return category in self.classify(command)

    def classify_many(
        self,
        commands: list[str],
    ) -> dict[CicdCommandCategory, list[str]]:
        """Group commands by their detected categories."""

        classified: dict[CicdCommandCategory, list[str]] = {
            category: [] for category in CicdCommandCategory
        }

        for command in commands:
            for category in self.classify(command):
                classified[category].append(command)

        return {category: self._unique(values) for category, values in classified.items()}

    def _normalize(
        self,
        command: str,
    ) -> str:
        """Normalize whitespace and casing for matching."""

        return " ".join(command.lower().split())

    def _unique(
        self,
        values: list[str],
    ) -> list[str]:
        """Deduplicate strings while preserving their order."""

        return list(dict.fromkeys(values))
