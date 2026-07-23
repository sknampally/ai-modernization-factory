# Examples

Sample repositories and command recipes for AIMF v0.1.0.

## Bundled sample: `sample-js-app`

Tiny Node.js app used for onboarding and tests.

### Deterministic assess (local)

```bash
# from repository root, with the package installed editable
aimf assess --repo examples/sample-js-app --output reports
```

**Expected:**

* Exit code `0`
* New directory: `reports/sample-js-app/<YYYYMMDD-HHMMSS>/`
* Files present:
  * `report.html`
  * `report.json`
  * `findings.json`
  * `recommendations.json`
  * `graphs/repository-graph.json`
  * `graphs/assessment-graph.json`
  * `graphs/graph-summary.json`
* `ai-enrichment.json` **absent**
* Console mentions HTML report path and deterministic completion

### Config-driven assess

Default `aimf.toml` points at `examples/sample-js-app`:

```bash
aimf assess --config aimf.toml --output reports
```

Same artifact expectations as above.

### AI mode (optional)

Requires AWS credentials and Bedrock model configuration in `aimf.toml`:

```bash
aimf assess --repo examples/sample-js-app --output reports --with-ai
```

**Expected on success:**

* Same deterministic artifacts as above
* Plus `ai-enrichment.json` (and typically `ai-execution.json`)
* Exactly one provider call
* HTML Report v2 includes an **AI Enrichment** section

**Expected on AI failure:**

* Deterministic artifacts still present
* Warning about AI enrichment; exit code still `0`
* No fabricated `ai-enrichment.json`

## GitHub repository (template)

```toml
# aimf.toml (excerpt)
[repository]
url = "https://github.com/OWNER/REPO"
branch = "main"
```

```bash
aimf assess --config aimf.toml --output reports
```

Private HTTPS clone: set a token in the environment and reference it via
`token_env` in config (never put the secret in TOML). See [SECURITY.md](../SECURITY.md).

## Inspecting HTML Report v2

Open `report.html` in a browser. Confirm section headings:

1. Executive Overview  
2. Repository Profile  
3. Technology and Version Summary  
4. Assessment Summary  
5. Findings  
6. Recommendations  
7. AI Enrichment (AI runs only)  
8. Graph and Artifact References  
9. Assessment Metadata  

## Screenshot placeholders

Add PNGs under `docs/images/` when capturing UI for the README:

* `docs/images/report-executive-overview.png`
* `docs/images/report-findings.png`
* `docs/images/report-recommendations.png`
* `docs/images/report-ai-enrichment.png`
