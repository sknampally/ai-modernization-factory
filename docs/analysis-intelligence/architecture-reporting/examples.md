# Examples

Enable the full Architecture Intelligence path for a local assess:

```toml
[rules]
enabled = true

[rules.architecture]
enabled = true

[evidence.language]
enabled = true

[analysis.architecture_conclusions]
enabled = true

[assessment.sections.architecture]
enabled = true

[report.sections.architecture]
enabled = true
```

Expected CodeStrata dogfood shape (illustrative):

- 3 architecture findings
- 2 conclusions (boundary integrity, broad dependency surface)
- 2 recommendation groups
- 0 strengths
- extraction measured ~100%; classification partial ~31%
- business impact Unknown / not assessed
- modernization relevance Wave 2
