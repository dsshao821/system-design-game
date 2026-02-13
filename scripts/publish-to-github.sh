#!/usr/bin/env bash
set -euo pipefail

REPO_NAME="${1:-system-design-game}"
VISIBILITY="${2:-public}"   # public|private
WORKDIR="$(pwd)"
PROJECT_DIR="$WORKDIR/system-design-game"
EXPORT_DIR="$WORKDIR/.tmp-system-design-game-export"

if [[ ! -d "$PROJECT_DIR" ]]; then
  echo "Missing $PROJECT_DIR"
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI not found. Run: ./system-design-game/scripts/install-gh-cli.sh"
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Please authenticate first: gh auth login"
  exit 1
fi

rm -rf "$EXPORT_DIR"
mkdir -p "$EXPORT_DIR"
cp -R "$PROJECT_DIR"/. "$EXPORT_DIR"/

cd "$EXPORT_DIR"
rm -rf .git

git init
git add .
git commit -m "Initial commit: System Design Game scaffold"

gh repo create "$REPO_NAME" --"$VISIBILITY" --source=. --remote=origin --push

echo "Published https://github.com/$(gh api user --jq .login)/$REPO_NAME"

echo "This keeps airflow-dags unchanged as a separate repo and creates an independent GitHub repository from system-design-game/."
