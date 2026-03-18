#!/usr/bin/env bash
# Poll for a Julia MCP background job sentinel file.
# Streams partial output via tail -f while waiting.
# Usage: poll-sentinel.sh <sentinel_path>
set -euo pipefail

sentinel="$1"
output="${sentinel%.sentinel}.log"

# Stream the output file as soon as it exists
(
    while [ ! -f "$output" ] && [ ! -f "$sentinel" ]; do
        sleep 0.5
    done
    if [ -f "$output" ]; then
        exec tail -f "$output"
    fi
) &
stream_pid=$!

# Wait for the sentinel file
while [ ! -f "$sentinel" ]; do
    sleep 2
done

# Let tail catch up, then stop it
sleep 0.5
kill "$stream_pid" 2>/dev/null || true
wait "$stream_pid" 2>/dev/null || true

# Print final status from sentinel
echo ""
echo "=== $(head -1 "$sentinel") ==="
