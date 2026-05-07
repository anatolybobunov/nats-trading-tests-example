# Tooling setup

Available tooling:

- `uv` (already available in the environment)
- `ruff` (installed with `uv tool install`)
- `ty` (installed with `uv tool install`)
- `prek` (installed with `uv tool install`)

Notes:

- `prek` is installed locally and wired into Git hooks with `prek install`.
- That means the checks run automatically on every commit.
- The repository uses `.pre-commit-config.yaml` for compatibility with `pre-commit`.
