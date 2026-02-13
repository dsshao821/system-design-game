# System Design Game

An interactive, browser-based platform to learn system design by **building architectures**, testing trade-offs, and receiving feedback in real time.

## What this project includes

- Product and delivery docs in `docs/`
- Landing page prototype in `web/index.html`
- Monorepo scaffold:
  - `frontend/` (React + TypeScript shell)
  - `backend/` (FastAPI API shell)
  - `sim-engine/` (deterministic simulation stub)
  - `infra/` (local docker-compose)
- Automation scripts:
  - `scripts/install-gh-cli.sh`
  - `scripts/publish-to-github.sh`

## Quick start

### View landing page prototype
Open `web/index.html` in a browser.

### Publish to a new GitHub repo

1. Install GitHub CLI:
   ```bash
   ./scripts/install-gh-cli.sh
   ```
2. Authenticate:
   ```bash
   gh auth login
   ```
3. Publish:
   ```bash
   ./scripts/publish-to-github.sh system-design-game public
   ```

See `docs/SETUP_AND_PUBLISH.md` for details, including how to keep work out of the parent `airflow-dags` repository.
