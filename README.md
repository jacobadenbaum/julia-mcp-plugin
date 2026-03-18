# Julia MCP Plugin for Claude Code

A Claude Code plugin that wraps the [Julia MCP server](https://github.com/aplavin/julia-mcp) with background job execution, a skill for session management guidance, and hooks for automatic polling and restart protection.

## Features

- **Background execution**: Long-running Julia jobs auto-background on timeout instead of being killed. No lost work, no destroyed sessions.
- **`timeout=0`**: Immediately background a job you know will be long (training, tests, precompilation).
- **Sentinel-based notifications**: Background job completion triggers a `TaskOutput` notification via a Bash poller, waking the agent automatically.
- **Session busy flag**: Prevents concurrent use of a session while a background job is running, with clear guidance on alternatives.
- **Skill**: Model-invoked skill teaches the agent when to use foreground vs background execution, how to handle notifications, and when not to restart sessions.
- **Hooks**: PostToolUse hook auto-injects the polling command; PreToolUse hooks nudge away from Bash Julia and guard against unnecessary restarts.

## Installation

```
/plugin marketplace add jacobadenbaum/julia-mcp-plugin
/plugin install julia-mcp@julia-mcp-plugin
/reload-plugins
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `julia_eval(code, env_path, timeout)` | Execute Julia code. `timeout=0` backgrounds immediately. `timeout>0` auto-backgrounds on expiry. |
| `julia_job_status(job_id)` | Check status and partial/full output of a background job. |
| `julia_job_cancel(job_id)` | Cancel a running background job via SIGINT. |
| `julia_restart(env_path)` | Restart a session (guarded by hook — escalates to user). |
| `julia_list_sessions()` | List active Julia sessions. |

## How background execution works

1. Agent calls `julia_eval` with `timeout=0` (or a job exceeds its timeout).
2. Server transitions the job to background, returns `[BACKGROUNDED] job_id=... sentinel=...`.
3. PostToolUse hook injects a Bash polling command.
4. Agent starts the poller as a background Bash task.
5. When the job completes, the server writes a sentinel file.
6. The Bash poller detects it, exits, and Claude Code's `TaskOutput` notification wakes the agent.

## Requirements

- Python 3.10+ with `uv`
- Julia (in PATH)

## Development

The plugin uses a git submodule pointing to a [fork of julia-mcp](https://github.com/jacobadenbaum/julia-mcp) with background execution support.

```bash
git clone --recursive https://github.com/jacobadenbaum/julia-mcp-plugin.git
cd julia-mcp-plugin

# Run tests
cd julia-mcp
uv run pytest test_server.py -v

# Use as a local plugin during development
claude --plugin-dir /path/to/julia-mcp-plugin
```

To update the server submodule:
```bash
cd julia-mcp && git pull origin background-execution && cd ..
git add julia-mcp && git commit -m "bump server submodule"
```
