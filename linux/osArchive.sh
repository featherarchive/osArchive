#!/usr/bin/env sh
set -eu

if command -v osarchive >/dev/null 2>&1; then
    exec osarchive
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
cd "$PROJECT_DIR"
exec python -m osint_tool
