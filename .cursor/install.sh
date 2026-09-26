#!/usr/bin/env bash
set -euo pipefail

# Django dev-environment bootstrap for Cloud Agents.
# Idempotent: safe to run repeatedly and against cached state.

cd "$(dirname "$0")/.."

# The Cursor default image ships Python 3.12 but not the venv module.
if ! python3 -c "import ensurepip" >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends python3.12-venv
fi

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py collectstatic --noinput
