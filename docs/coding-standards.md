# Coding standards

Follow the practices in [CONTRIBUTING.md](../CONTRIBUTING.md):

* Python 3.12+, type-checked with `mypy src`
* Lint/format with Ruff (`ruff check .`, `ruff format .`)
* Prefer focused modules under `src/aimf/` mirroring existing packages
* Keep deterministic analysis authoritative; AI must not invent findings
* Do not commit secrets or generated report trees
