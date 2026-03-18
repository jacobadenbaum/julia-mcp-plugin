#!/usr/bin/env python3
"""PostToolUse hook for julia_eval: inject background polling command.
PreToolUse hook for Bash: nudge toward Julia MCP server.
"""
import json
import os
import re
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

hook_event = data.get("hook_event_name", "")

# --- PostToolUse: inject poller for backgrounded julia_eval ---
if hook_event == "PostToolUse":
    tool_response = data.get("tool_response", "")
    if isinstance(tool_response, dict):
        content = tool_response.get("content", [])
        if content and isinstance(content[0], dict):
            tool_response = content[0].get("text", "")
    if not isinstance(tool_response, str):
        tool_response = str(tool_response)

    if "[BACKGROUNDED]" not in tool_response:
        sys.exit(0)

    match = re.search(r"sentinel=(\S+)", tool_response)
    if not match:
        sys.exit(0)

    sentinel = match.group(1)
    print(
        f"Background Julia job started. Run this to get notified when it completes:\n"
        f'Bash(command="while [ ! -f {sentinel} ]; do sleep 5; done && '
        f'cat {sentinel}", run_in_background=true)'
    )
    sys.exit(0)

# --- PreToolUse on Bash: nudge toward MCP for Julia commands ---
if hook_event == "PreToolUse":
    cmd = data.get("tool_input", {}).get("command", "")

    if not re.search(r"(?:^|[;&|]\s*)julia\s", cmd):
        if not re.search(r"(?:^|[;&|]\s*)/\S*/julia\s", cmd):
            sys.exit(0)

    stripped = cmd.strip()
    if re.match(r"^julia\s+--version\s*$", stripped):
        sys.exit(0)
    if re.match(r"^julia\s+-v\s*$", stripped):
        sys.exit(0)
    if re.match(r"^which\s+julia\s*$", stripped):
        sys.exit(0)

    is_background = bool(data.get("tool_input", {}).get("run_in_background"))
    session_id = data.get("session_id", "unknown")
    state_dir = "/tmp/.claude-hooks"
    os.makedirs(state_dir, exist_ok=True)

    if is_background:
        bg_state = os.path.join(state_dir, f"julia-bg-hint-{session_id}")
        verbose = True
        if os.path.exists(bg_state):
            try:
                mtime = os.path.getmtime(bg_state)
                if time.time() - mtime < 600:
                    verbose = False
            except OSError:
                pass
        try:
            with open(bg_state, "w"):
                pass
        except OSError:
            pass

        if verbose:
            output_decision("allow", (
                "Reminder: the Julia MCP server (julia_eval) is preferred for "
                "interactive work. It maintains a persistent session with Revise.jl. "
                "Background Bash is appropriate for genuinely long-running tasks "
                "(>5-10 min) or for independent concurrent work while an MCP "
                "session is busy with a background job."
            ))
        else:
            output_decision("allow",
                "Hint: consider julia_eval (MCP) instead."
            )

    # Foreground Bash Julia: deny once, allow override on retry
    fg_state = os.path.join(state_dir, f"julia-fg-hint-{session_id}")
    if os.path.exists(fg_state):
        try:
            mtime = os.path.getmtime(fg_state)
            if time.time() - mtime < 120:
                os.unlink(fg_state)
                sys.exit(0)
        except OSError:
            pass

    try:
        with open(fg_state, "w"):
            pass
    except OSError:
        pass

    output_decision("deny", (
        "Use the Julia MCP server (julia_eval) for interactive work instead of "
        "Bash. The MCP server maintains a persistent session with Revise.jl. "
        "Use timeout=0 to background long-running jobs. "
        "If you still need foreground Bash Julia, retry this command."
    ))
