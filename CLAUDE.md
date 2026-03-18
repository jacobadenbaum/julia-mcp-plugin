# julia-mcp-plugin

Claude Code plugin that bundles the julia-mcp MCP server with hooks and a skill for background job management.

## Repository structure

```
julia-mcp-plugin/          # Parent repo (jacobadenbaum/julia-mcp-plugin)
├── julia-mcp/             # Git submodule → jacobadenbaum/julia-mcp @ background-execution
│   ├── server.py          # MCP server (Python): sessions, background jobs, sentinel files
│   ├── test_server.py     # Server tests
│   └── pyproject.toml     # Python project config (uv)
├── scripts/
│   ├── poll-sentinel.sh   # Bash poller: tail -f output log, wait for sentinel
│   ├── inject-poller.py   # PostToolUse hook (julia_eval): prints polling command on [BACKGROUNDED]
│   │                      # PreToolUse hook (Bash): blocks foreground `julia` commands, nudges to julia_eval
│   ├── approve-poller.py  # PermissionRequest hook (Bash): auto-approves poll-sentinel.sh commands
│   └── restart-guard.py   # PreToolUse hook (julia_restart): deny once, escalate to user on retry
├── hooks/
│   └── hooks.json         # Hook registration (PostToolUse, PreToolUse, PermissionRequest)
├── skills/
│   └── julia-repl/
│       └── SKILL.md       # Skill: how to use julia_eval, background jobs, polling workflow
├── .claude-plugin/
│   ├── plugin.json        # Plugin metadata + version
│   └── marketplace.json   # Marketplace listing + version
├── .mcp.json              # MCP server registration
└── README.md              # User-facing install/usage docs
```

## Submodule

`julia-mcp/` is a submodule pointing to `jacobadenbaum/julia-mcp` on the `background-execution` branch. The upstream repo (`master`) is maintained by someone else; `background-execution` is the fork branch with background job support.

When making changes to `server.py`:
1. Commit and push inside `julia-mcp/` (pushes to `background-execution`)
2. Then commit the updated submodule pointer in the parent repo

## Versioning

**Bump the version in both `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` whenever you make a user-visible change** (hooks, scripts, skill, server behavior). Keep them in sync.

## Hook architecture

All hooks are registered in `hooks/hooks.json` and dispatched by script:

| Hook event        | Matcher                        | Script              | Behavior                                                    |
|-------------------|--------------------------------|---------------------|-------------------------------------------------------------|
| PostToolUse       | `mcp__.*julia__julia_eval`     | inject-poller.py    | On `[BACKGROUNDED]` response, prints poll-sentinel.sh command |
| PreToolUse        | `Bash`                         | inject-poller.py    | Blocks foreground `julia` Bash; allows background with hint |
| PreToolUse        | `mcp__.*julia__julia_restart`  | restart-guard.py    | Denies first attempt; escalates to user on retry            |
| PermissionRequest | `Bash`                         | approve-poller.py   | Auto-approves `poll-sentinel.sh` commands                   |
