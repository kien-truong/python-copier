#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

DEST="$SCRIPT_DIR/tmp"

cd "$DEST"

uv sync
uv run pytest || true

pre-commit install
pre-commit run -a
