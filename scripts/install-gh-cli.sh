#!/usr/bin/env bash
set -euo pipefail

if command -v gh >/dev/null 2>&1; then
  echo "gh is already installed: $(gh --version | head -n 1)"
  exit 0
fi

if command -v apt-get >/dev/null 2>&1; then
  echo "Installing GitHub CLI via apt..."
  sudo apt-get update
  sudo apt-get install -y gh
elif command -v dnf >/dev/null 2>&1; then
  echo "Installing GitHub CLI via dnf..."
  sudo dnf install -y 'dnf-command(config-manager)'
  sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
  sudo dnf install -y gh
elif command -v brew >/dev/null 2>&1; then
  echo "Installing GitHub CLI via brew..."
  brew install gh
else
  echo "No supported package manager found (apt-get/dnf/brew)."
  exit 1
fi

gh --version | head -n 1
