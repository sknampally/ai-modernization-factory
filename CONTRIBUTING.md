# Contributing to AIMF

Thanks for contributing to AI Modernization Factory.

## Development setup

Requires Python 3.12+.

```bash
git clone https://github.com/sknampally/ai-modernization-factory.git
cd ai-modernization-factory
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Quality gates

Run before opening a PR:

```bash
pytest
ruff check .
ruff format --check .
mypy src
python -m build
```

Format with `ruff format .` when needed.

## Guidelines

* Prefer small, focused pull requests.
* Deterministic analysis remains the source of truth; do not let AI invent
  findings or recommendations.
* Match existing package layout and naming (`src/aimf/…`, tests under `tests/`).
* Do not commit secrets, `.env` files, or large generated `reports/` trees.
* Update docs under `docs/` when behavior or artifacts change.
* Follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Reporting security issues

See [SECURITY.md](SECURITY.md). Do not open public issues for vulnerabilities.

## License

By contributing, you agree that your contributions are licensed under the MIT
License ([LICENSE](LICENSE)).
