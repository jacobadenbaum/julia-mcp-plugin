---
name: julia-repl
description: Use when running Julia code, managing Julia sessions, or working with Julia projects. Provides guidance on using the Julia MCP server's persistent REPL sessions and background job execution.
---

# Julia REPL

## Prefer julia_eval for all interactive Julia work

Use `julia_eval` instead of running Julia via Bash. The MCP server maintains a persistent Julia session with Revise.jl loaded, so:
- Compilation is amortized across calls
- Code changes are picked up automatically without restarting
- Variables, functions, and loaded packages persist between calls

A PreToolUse hook on Bash will **block** foreground `julia` commands and redirect you to `julia_eval`. Background Bash Julia is allowed with a reminder. Do not fight the hook — use the MCP server.

## Timeout and background execution

- **Generally, omit the `timeout` parameter.** The default (60s) is sufficient for most work. If a job exceeds the timeout, it auto-backgrounds instead of being killed — no work is lost. You will receive a `[BACKGROUNDED]` response with a job_id and sentinel path.
- **Set `timeout=0`** only when you want to background a job immediately (e.g., training runs, test suites, heavy precompilation) without waiting the 60s.
- Pkg operations auto-disable the timeout.

## When a job is backgrounded

1. `julia_eval` returns `[BACKGROUNDED] job_id=<id> sentinel=<path>`.
2. A PostToolUse hook prints the exact `poll-sentinel.sh` Bash command to run.
3. **Start the poller immediately** with `Bash(command="<provided command>", run_in_background=true)`. A PermissionRequest hook auto-approves `poll-sentinel.sh` commands, so no user confirmation is needed.
4. The poller streams partial output via `tail -f` on a log file written alongside the sentinel. You can check progress at any time with `TaskOutput`.
5. When the job finishes, the poller prints `=== SUCCESS ===` or `=== ERROR ===` and exits, giving you a TaskOutput notification.
6. **Use the waiting time productively** — work on other tasks, plan next steps, talk to the user.
7. Use `julia_job_status(job_id)` to check partial output via MCP (alternative to TaskOutput).
8. Use `julia_job_cancel(job_id)` to abort a running job if needed.

## Session busy

While a background job is running, `julia_eval` calls to the same session are rejected. You can:
- Check progress with `julia_job_status`
- Cancel with `julia_job_cancel`
- For independent concurrent work, use a background Bash `julia` command (it won't have the persistent session, but works independently)

## Don't restart sessions

Revise.jl handles code changes automatically. A PreToolUse hook on `julia_restart` will deny the first attempt and escalate to the user on retry. Only restart if the session is truly broken.
