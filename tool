#!/usr/bin/env bash
# Wrapper so you can run: ./tool sync | ./tool build | ./tool new
# Creates/uses a local .venv and installs requirements on first run.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "Setting up virtual environment ..."
  python3 -m venv .venv
  .venv/bin/python -m pip install --quiet --upgrade pip
  .venv/bin/python -m pip install --quiet -r requirements.txt
fi

exec .venv/bin/python site.py "$@"
