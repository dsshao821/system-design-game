# Setup and Publish Guide

## 1) Monorepo scaffold (included)

This folder now includes:

- `frontend/` (React + TypeScript starter shell)
- `backend/` (FastAPI starter with `/health`)
- `sim-engine/` (deterministic runner stub)
- `infra/docker-compose.yml` (local wiring)
- `scripts/` (GitHub CLI install + publish automation)

## 2) Install GitHub CLI from this environment

From repo root:

```bash
./system-design-game/scripts/install-gh-cli.sh
```

Then authenticate:

```bash
gh auth login
```

## 3) Publish as an independent GitHub repo

```bash
./system-design-game/scripts/publish-to-github.sh system-design-game public
```

This exports only `system-design-game/` into a clean temporary git repository and pushes it to GitHub.

## Why changes were showing in `airflow-dags`

Codex is currently running with working directory set to `/workspace/airflow-dags`, so edits naturally land in this repository.

To avoid that, use one of these patterns:

1. Open Codex directly in a dedicated checkout/path for `system-design-game`.
2. Use the publish script above to create a **separate** repository from only `system-design-game/`.
3. After publish, clone the new repo and continue work there as the primary project.
