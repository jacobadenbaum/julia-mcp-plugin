#!/usr/bin/env bash
# Poll for a Julia MCP background job sentinel file.
# Streams partial output via tail -f while waiting.
# Usage: poll-sentinel.sh <job_id>
#    or: poll-sentinel.sh <full_sentinel_path>   (legacy)
set -euo pipefail

arg="$1"

if [[ "$arg" == /* ]]; then
    # Full path provided (legacy)
    sentinel="$arg"
else
    # Job ID: find sentinel under SENTINEL_BASE
    base="${TMPDIR:-/tmp}/.julia-mcp-jobs/$USER"
    sentinel=$(find "$base" -name "${arg}.sentinel" -o -name "${arg}.log" 2>/dev/null \
        | head -1 \
        | sed 's/\.log$/.sentinel/')
    if [ -z "$sentinel" ]; then
        # Not created yet — pick the active server dir and wait for it
        server_dir=$(ls -td "$base"/*/ 2>/dev/null | head -1)
        sentinel="${server_dir}${arg}.sentinel"
    fi
fi

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

# Stop the streaming tail
kill "$stream_pid" 2>/dev/null || true
wait "$stream_pid" 2>/dev/null || true

# Print full output and final status
echo ""
echo "=== FULL OUTPUT ==="
if [ -f "$output" ]; then
    cat "$output"
fi
echo ""
echo "=== $(head -1 "$sentinel") ==="
