#!/usr/bin/env python3
"""PreToolUse hook: guard julia_restart. Deny once, escalate to user on retry."""
import json
import os
import sys
import time


def output_decision(decision, reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


try:
    data = json.loads(sys.stdin.read())
except Exception:
    sys.exit(0)

session_id = data.get("session_id", "unknown")
state_dir = "/tmp/.claude-hooks"
os.makedirs(state_dir, exist_ok=True)
state_file = os.path.join(state_dir, f"julia-restart-{session_id}")

if os.path.exists(state_file):
    try:
        mtime = os.path.getmtime(state_file)
        if time.time() - mtime < 60:
            os.unlink(state_file)
            output_decision("ask",
                "Escalating julia_restart to user for confirmation.")
    except OSError:
        pass

try:
    with open(state_file, "w"):
        pass
except OSError:
    pass

output_decision("deny", (
    "You almost certainly do not want to do this. Restarting the Julia "
    "session destroys all compiled code and session state. Revise.jl "
    "is loaded automatically and picks up code changes without restarting. "
    "Only restart if the session is truly broken, and check with the user "
    "first. If you still want to proceed, retry and the user will be asked."
))
