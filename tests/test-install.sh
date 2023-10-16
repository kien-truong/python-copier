#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

DEST="$SCRIPT_DIR/tmp"

cd "$DEST"

pdm install
pdm run pytest || true

pre-commit install
pre-commit run -a
