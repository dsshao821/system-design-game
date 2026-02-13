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

### Run local MVP

Start backend:

```bash
cd backend
python -m venv .venv
# PowerShell
.\.venv\Scripts\Activate.ps1
# Bash
source .venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Start frontend (new terminal):

```bash
cd frontend
npm install
npm run dev
```

Open the frontend URL from Vite (usually `http://127.0.0.1:5173`).

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
