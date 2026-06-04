# Polyglot Hooks — Cross-Platform Pattern

> **Agency doesn't ship hooks today** (see "Hook-enhanced workflow" in
> [`common-patterns.md`](common-patterns.md) for why). This reference
> is here in case we ever add one — and so the option is visible.

## When this matters for agency

Three plausible reasons agency might add a hook in the future:

1. **SessionStart on Claude Code on the web** — bootstrap `.agency/` and
   warm the MCP server before the agent's first tool call.
2. **PostToolUse to record provenance** — capture every external write as
   a `Reflection` node (today this is voluntary via `reflect.note`).
3. **PreCompact to flush the bi-temporal graph** — make sure the durable
   state is consistent before the host compacts conversation context.

Each carries doctrinal cost (auto-fire hooks have no `intent_id`, which
breaks SERVES-guard). If one ever ships, this pattern is mandatory.

## The problem hooks face

Claude Code runs hook commands through the host shell — CMD on Windows,
bash/sh on macOS/Linux. That's four problems:

1. **Script execution** — Windows CMD can't run `.sh` directly (opens in editor).
2. **Path format** — `C:\path` vs. `/path`.
3. **Env-var syntax** — `$VAR` (Unix) vs. `%VAR%` (CMD).
4. **`bash` not on PATH** — even with Git for Windows installed.

## The polyglot `.cmd` wrapper

One wrapper file valid in both CMD and bash:

```cmd
: << 'CMDBLOCK'
@echo off
REM Polyglot wrapper: runs .sh scripts cross-platform.
REM Usage: run-hook.cmd <script-name> [args...]
"C:\Program Files\Git\bin\bash.exe" -l "%~dp0%~1"
exit /b
CMDBLOCK

# Unix shell runs from here
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_NAME="$1"
shift
"${SCRIPT_DIR}/${SCRIPT_NAME}" "$@"
```

### How it works

**On Windows (CMD.exe):**
1. `: << 'CMDBLOCK'` — CMD treats `:` as a label, ignores the rest.
2. `@echo off` suppresses command echoing.
3. `bash.exe -l "%~dp0%~1"` invokes Git Bash with the script path.
4. `exit /b` exits the batch — everything below `CMDBLOCK` is unreached.

**On Unix (bash/sh):**
1. `: << 'CMDBLOCK'` — `:` is no-op, `<< 'CMDBLOCK'` starts a heredoc.
2. Everything until `CMDBLOCK` is consumed by the heredoc.
3. The Unix command runs.

> **POSIX compliance:** use `$0` (not `${BASH_SOURCE[0]:-$0}`). Some
> Ubuntu/Debian `/bin/sh` is `dash` and errors with "Bad substitution"
> on the BASH_SOURCE form.

## File layout (if agency ever adds hooks)

```
hooks/
├── hooks.json              # configures events → run-hook.cmd <script>
├── run-hook.cmd            # the polyglot wrapper (above)
├── session-start.sh        # actual hook logic (bash)
└── …
```

## `hooks/hooks.json`

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume",
        "hooks": [
          { "type": "command",
            "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd\" session-start.sh" }
        ]
      }
    ]
  }
}
```

Path quoting matters — `${CLAUDE_PLUGIN_ROOT}` may contain spaces on
Windows (`C:\Program Files\...`).

> **WARNING — duplicate hooks file:** `hooks/hooks.json` is auto-loaded.
> Do NOT also reference it in `plugin.json`'s `hooks` field — that causes
> "Duplicate hooks file detected" errors.

## Writing cross-platform hook scripts

The actual logic in `.sh`. For Git Bash compatibility:

**Do:**
- Use bash builtins where possible.
- `$(command)` instead of backticks.
- Quote variable expansions: `"$VAR"`.
- `printf` or heredocs for output.

**Avoid:**
- `sed`, `awk`, `grep` — they ARE in Git Bash but require `bash -l` for PATH.
- Backticks (legacy, harder to nest).

### Example — JSON escaping without sed/awk (pure bash)

```bash
escape_for_json() {
    local input="$1" output="" i char
    for (( i=0; i<${#input}; i++ )); do
        char="${input:$i:1}"
        case "$char" in
            $'\\') output+='\\' ;;
            '"') output+='\"' ;;
            $'\n') output+='\n' ;;
            $'\r') output+='\r' ;;
            $'\t') output+='\t' ;;
            *) output+="$char" ;;
        esac
    done
    printf '%s' "$output"
}
```

## Requirements

- **Windows:** Git for Windows installed (`C:\Program Files\Git\bin\bash.exe`).
  If installed elsewhere, edit the wrapper.
- **Unix:** standard bash/sh; `chmod +x` on the `.cmd` file + the `.sh`
  scripts. Commit with `git update-index --chmod=+x …`.

## Troubleshooting

| Symptom | Cause / Fix |
|---|---|
| "bash is not recognized" | CMD can't find bash. Wrapper uses the full path; edit if Git installed elsewhere. |
| "cygpath: command not found" | Bash isn't a login shell. Ensure `-l`. |
| Path contains `\/` | `${CLAUDE_PLUGIN_ROOT}` ends with backslash + `/hooks/…` appended. Use `cygpath`. |
| Script opens in editor | `hooks.json` points directly at `.sh`. Point at the `.cmd` wrapper. |
| Works in terminal, not as hook | Simulate the env: `$env:CLAUDE_PLUGIN_ROOT = "..."; cmd /c "...\run-hook.cmd" session-start.sh`. |

## Related upstream issues

- [anthropics/claude-code#9758](https://github.com/anthropics/claude-code/issues/9758) — `.sh` opens in editor on Windows
- [anthropics/claude-code#3417](https://github.com/anthropics/claude-code/issues/3417) — hooks don't work on Windows
- [anthropics/claude-code#6023](https://github.com/anthropics/claude-code/issues/6023) — `CLAUDE_PROJECT_DIR` not found
