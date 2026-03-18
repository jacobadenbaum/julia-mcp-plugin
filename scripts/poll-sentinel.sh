#!/usr/bin/env bash
# Poll for a Julia MCP background job sentinel file.
# Usage: poll-sentinel.sh <sentinel_path>
# Exits with the sentinel file contents when it appears.
set -euo pipefail

sentinel="$1"

while [ ! -f "$sentinel" ]; do
    sleep 5
done

cat "$sentinel"
