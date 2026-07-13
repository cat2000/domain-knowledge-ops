#!/usr/bin/env bash
# One-time local setup: .env, Python venv, pip deps.
# Run from repo root: ./scripts/setup.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .cursor/skills || ! -f scripts/domain_check.py ]]; then
  echo "error: run from knowledge_base repo root (missing .cursor/skills or scripts/)." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "error: python3 not found." >&2
  exit 1
fi

# --- .env ---
if [[ -f .env ]]; then
  echo "[setup] .env already exists — skipped"
else
  cp .env.example .env
  echo "[setup] created .env from .env.example — fill ATLASSIAN_EMAIL and ATLASSIAN_API_TOKEN"
fi

# --- venv ---
VENV="$ROOT/.venv"
if [[ -d "$VENV" ]]; then
  echo "[setup] .venv already exists — skipped"
else
  python3 -m venv "$VENV"
  echo "[setup] created .venv"
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "[setup] installed requirements.txt into .venv"

cat <<EOF

Done. Next steps:
  1. Edit .env with your Atlassian credentials (skip if you only use @requirement-risk / @ticket-splitter).
  2. Open this folder in Cursor (Privacy Mode recommended).
  3. Activate venv when running scripts: source .venv/bin/activate
  4. Try: @requirement-risk <JIRA-KEY>  or  python3 scripts/domain_check.py -h

Docs: README.md  ·  .cursor/skills/README.md
EOF
