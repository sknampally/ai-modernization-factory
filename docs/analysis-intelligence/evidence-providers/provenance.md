# Provenance

`EvidenceProvenance` records provider ID/version, source analyzer, extraction
method, origin, source path, transformation chain, and configuration
fingerprint.

Example chain:

```
raw_package_facts → normalized_language_evidence → ArchitectureAnalysisView
```

Source content is never logged in telemetry.
