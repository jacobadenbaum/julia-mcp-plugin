#!/usr/bin/env python3
"""PermissionRequest hook: auto-approve poll-sentinel.sh commands."""
import json
import re
import sys

try:
    data = json.loads(sys.stdin.read())
except Exception:
    sys.exit(0)

cmd = data.get("tool_input", {}).get("command", "").strip()

# Only approve if the entire command is poll-sentinel.sh with a single argument
# (a job ID or absolute sentinel path). Reject compound commands.
if re.match(r'^(\S*/)?poll-sentinel\.sh\s+\S+\s*$', cmd):
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
