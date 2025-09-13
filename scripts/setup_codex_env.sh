#!/usr/bin/env bash
set -e

# Ensure an appropriate Python version is being used
PYTHON_VERSION=$(python --version 2>&1)
if ! python - <<'PY'
import sys
sys.exit(0 if sys.version_info[:2] in {(3, 10), (3, 11)} else 1)
PY
then
  echo "Error: Python 3.10 or 3.11 is required. Current version: ${PYTHON_VERSION}" >&2
  exit 1
fi

pip install -r requirements.txt
pip install pytest pylint
