#!/usr/bin/env bash
# dimgaai one-line installer (Mac/Linux)
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/Charleschtsoi/dimgaai/main/scripts/install.sh | bash

set -euo pipefail

REPO="${DIMGAAI_REPO:-Charleschtsoi/dimgaai}"
BRANCH="${DIMGAAI_BRANCH:-main}"
ZIP_URL="https://github.com/${REPO}/archive/refs/heads/${BRANCH}.zip"
INSTALL_HOME="${DIMGAAI_HOME:-${HOME}/.local/share/dimgaai}"
CACHE_DIR="${INSTALL_HOME}/installer-cache"

echo ""
echo "dimgaai installer"
echo "================="
echo ""

PYTHON=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
  if "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 11) else 1)'; then
      PYTHON="$candidate"
      break
    fi
  fi
done

if [[ -z "$PYTHON" ]]; then
  echo "Python 3.11+ not found. Install from https://www.python.org/downloads/" >&2
  exit 1
fi

install_cli() {
  if command -v git >/dev/null 2>&1; then
    echo "Installing dimgaai CLI from GitHub (git)..."
    "$PYTHON" -m pip install --upgrade "git+https://github.com/${REPO}.git#subdirectory=backend" && return 0
  fi

  echo "Installing dimgaai CLI from zip (no git required)..."
  mkdir -p "$CACHE_DIR"
  zip_path="${CACHE_DIR}/dimgaai.zip"
  extract_path="${CACHE_DIR}/extract"
  rm -rf "$extract_path"
  mkdir -p "$extract_path"
  curl -fsSL "$ZIP_URL" -o "$zip_path"
  "$PYTHON" -c "import zipfile; zipfile.ZipFile('${zip_path}').extractall('${extract_path}')"
  repo_dir="$(find "$extract_path" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
  "$PYTHON" -m pip install --upgrade "${repo_dir}/backend"
}

install_cli

echo ""
echo "Starting dimgaai (downloads app + opens browser on first run)..."
echo ""

exec "$PYTHON" -m dimgaai_cli go
