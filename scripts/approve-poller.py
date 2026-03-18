#!/usr/bin/env python3
"""PermissionRequest hook: auto-approve poll-sentinel.sh commands."""
import json
import sys

try:
    data = json.loads(sys.stdin.read())
except Exception:
    sys.exit(0)

cmd = data.get("tool_input", {}).get("command", "")

if "poll-sentinel.sh" in cmd:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PermissionRequest",
            "decision": {
                "behavior": "allow"
            }
        }
    }))
    sys.exit(0)

# Not a poller command — no opinion
sys.exit(0)
