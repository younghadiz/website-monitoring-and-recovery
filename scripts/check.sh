#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

.venv/bin/python -m py_compile monitor-website.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m pip check

bash -n scripts/git-milestone.sh
bash -n scripts/check.sh

if [ -f scripts/server-setup.sh ]; then
    bash -n scripts/server-setup.sh
fi

git diff --check
