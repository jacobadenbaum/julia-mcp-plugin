---
name: julia-repl
description: Use when running Julia code, managing Julia sessions, or working with Julia projects. Provides guidance on using the Julia MCP server's persistent REPL sessions and background job execution. DON'T FORGET TO LOAD THIS BEFORE USING THE MCP SERVER
---

# Julia REPL

## Prefer julia_eval for all interactive Julia work

Use `julia_eval` instead of running Julia via Bash. The MCP server maintains a persistent Julia session with Revise.jl loaded, so:
- Compilation is amortized across calls
- Code changes are picked up automatically without restarting
- Variables, functions, and loaded packages persist between calls

A PreToolUse hook on Bash will **block** foreground `julia` commands and redirect you to `julia_eval`. Background Bash Julia is allowed with a reminder. Do not fight the hook — use the MCP server.

## Timeout and background execution

**Default: do not set a `timeout` parameter at all.** The built-in default (60s) handles the vast majority of calls — short computations, tests of a function, plot generation, quick queries. Setting a timeout yourself is almost always wrong:

- **Don't set `timeout=0` speculatively.** Backgrounding has real overhead — the poller spins up, you have to wait on a Bash task, and a 20-second job becomes a multi-step polling dance. If the job turns out to be short, you have wasted time and tokens for no reason.
- **Only set `timeout=0` when you have concrete reason to believe the job will run for minutes or longer** — a large training run, a full test suite on a fresh session, heavy precompilation after `]add`, a long simulation. "It might be slow" is not sufficient; estimate based on what the code actually does.
- If a job exceeds the default timeout, it auto-backgrounds — no work is lost — and you can switch to polling then. Let the system tell you a job is long instead of guessing upfront.
- Pkg operations auto-disable the timeout, so you don't need to set `timeout=0` for those either.

## When a job is backgrounded

1. `julia_eval` returns `[BACKGROUNDED] job_id=<id> sentinel=<path>`.
2. A PostToolUse hook prints the exact `poll-sentinel.sh` Bash command to run.
3. **Start the poller immediately** with `Bash(command="<provided command>", run_in_background=true)`. A PermissionRequest hook auto-approves `poll-sentinel.sh` commands, so no user confirmation is needed.
4. The poller streams partial output via `tail -f` on a log file written alongside the sentinel. When the job finishes it prints `=== SUCCESS ===` or `=== ERROR ===` and exits, which surfaces as a TaskOutput notification.
5. **Then wait.** Work on other tasks, plan next steps, talk to the user. The notification will tell you when the job is done — you do not need to check on it.

## Do not repeatedly poll job status

Once a background job is running and the poller is attached, **do not keep calling `julia_job_status` or `TaskOutput` to "check in" on it**. This is a common failure mode: the agent polls every few seconds, burning tokens and time, when the poller is already going to notify on completion.

- **Default behavior: wait for the poller's completion notification.** Do nothing else related to the job until then.
- Only call `julia_job_status` or `TaskOutput` if (a) the user explicitly asks for a status update, or (b) you genuinely need partial output to decide what to do next (rare — usually you can wait).
- Use `julia_job_cancel(job_id)` to abort a running job if needed.

## Session busy

While a background job is running, `julia_eval` calls to the same session are rejected. You can:
- Check progress with `julia_job_status`
- Cancel with `julia_job_cancel`
- For independent concurrent work, use a background Bash `julia` command (it won't have the persistent session, but works independently)

## Don't restart sessions

Revise.jl handles code changes automatically. A PreToolUse hook on `julia_restart` will deny the first attempt and allow the second. This is a speed bump, not a wall — only restart if the session is truly broken.
