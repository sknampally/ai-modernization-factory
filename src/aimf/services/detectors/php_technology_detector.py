"""Technology detector for PHP repositories."""

import json
from typing import Any

from aimf.models import Repository, Technology, TechnologyCategory


class PhpTechnologyDetector:
    """Detects PHP ecosystem technologies."""

    def detect(self, repository: Repository) -> list[Technology]:
        """Detect PHP ecosystem technologies."""

        file_set = set(repository.files)
        technologies: list[Technology] = []

        has_php_files = any(file_path.endswith(".php") for file_path in repository.files)

        if has_php_files or "composer.json" in file_set:
            technologies.append(
                Technology(
                    name="PHP",
                    category=TechnologyCategory.LANGUAGE,
                    confidence=1.0,
                    source="file_extension_or_composer.json",
                )
            )

        if "composer.json" in file_set:
            technologies.append(
                Technology(
                    name="Composer",
                    category=TechnologyCategory.BUILD_TOOL,
                    confidence=1.0,
                    source="composer.json",
                )
            )

            composer_data = self._read_composer_json(repository)
            dependencies = self._collect_dependencies(composer_data)

            framework_mappings = {
                "laravel/framework": "Laravel",
                "symfony/framework-bundle": "Symfony",
            }

            for dependency_name, technology_name in framework_mappings.items():
                if dependency_name in dependencies:
                    technologies.append(
                        Technology(
                            name=technology_name,
                            version=dependencies[dependency_name],
                            category=TechnologyCategory.FRAMEWORK,
                            confidence=1.0,
                            source="composer.json",
                        )
                    )

            if "phpunit/phpunit" in dependencies:
                technologies.append(
                    Technology(
                        name="PHPUnit",
                        version=dependencies["phpunit/phpunit"],
                        category=TechnologyCategory.TESTING,
                        confidence=1.0,
                        source="composer.json",
                    )
                )

        if "artisan" in file_set:
            technologies.append(
                Technology(
                    name="Laravel",
                    category=TechnologyCategory.FRAMEWORK,
                    confidence=0.95,
                    source="artisan",
                )
            )

        if "wp-config.php" in file_set or any(
            file_path.startswith("wp-content/") for file_path in repository.files
        ):
            technologies.append(
                Technology(
                    name="WordPress",
                    category=TechnologyCategory.FRAMEWORK,
                    confidence=0.95,
                    source="wordpress_structure",
                )
            )

        return technologies

    def _read_composer_json(
        self,
        repository: Repository,
    ) -> dict[str, Any]:
        """Read and parse composer.json."""

        composer_file = repository.path / "composer.json"

        try:
            content = composer_file.read_text(
                encoding="utf-8",
                errors="ignore",
            )
            parsed_content = json.loads(content)

            if isinstance(parsed_content, dict):
                return parsed_content
        except (OSError, json.JSONDecodeError):
            pass

        return {}

    def _collect_dependencies(
        self,
        composer_data: dict[str, Any],
    ) -> dict[str, str]:
        """Combine Composer runtime and development dependencies."""

        dependencies: dict[str, str] = {}

        for section_name in ("require", "require-dev"):
            section = composer_data.get(section_name, {})

            if isinstance(section, dict):
                dependencies.update({str(name): str(version) for name, version in section.items()})

        return dependencies
