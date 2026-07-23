# Changelog

All notable changes to AIMF are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-22

### Added

* CLI (`aimf version`, `aimf scan`, `aimf assess`) with local and GitHub sources
* Phase 1 analysis: detection, analyzers, optional PMD static analysis
* Repository Inventory, Repository Graph, Engineering Knowledge Graph
* Knowledge Pipeline and Assessment Graph
* Dependency and version extraction (Maven / npm manifests)
* Deterministic Rule Engine → `findings.json`
* Deterministic Recommendation Engine → `recommendations.json`
* Optional one-call Bedrock AI enrichment → `ai-enrichment.json`
* HTML Report v2 (`report.html`) and companion `report.json`
* Deterministic mode (zero AI calls) and AI mode (exactly one call)
* Open-source documentation, examples, and community files for the MVP release

### Notes

* Deterministic findings and recommendations are the source of truth.
* AI enrichment is interpretive only and does not mutate deterministic artifacts.
