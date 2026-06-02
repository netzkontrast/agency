# Cross-Platform Polyglot Hooks for Claude Code

> The agency plugin does not ship hooks today. This reference is included
> because (a) Claude Code on the web uses SessionStart hooks for setup,
> and (b) any future agency hook should follow this cross-platform pattern.

Claude Code runs hook commands through the system's default shell — CMD on Windows, bash/sh on macOS/Linux. That creates four problems:

1. **Script execution** — Windows CMD can't run `.sh` directly (opens in editor).
2. **Path format** — `C:\path` vs `/path`.
3. **Env vars** — `$VAR` is Unix syntax; CMD wants `%VAR%`.
4. **`bash` not in PATH** — even with Git for Windows installed.

## The polyglot `.cmd` wrapper

A polyglot script is valid in two languages simultaneously. The wrapper below is valid in both CMD and bash:

```cmd
: << 'CMDBLOCK'
@echo off
"C:\Program Files\Git\bin\bash.exe" -l -c "\"$(cygpath -u \"$CLAUDE_PLUGIN_ROOT\")/hooks/session-start.sh\""
exit /b
CMDBLOCK

# Unix shell runs from here
"${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh"
```

### How it works

**Windows (CMD.exe):**
1. `: << 'CMDBLOCK'` — CMD sees `:` as a label, ignores the rest of the line.
2. `@echo off` suppresses command echoing.
3. The `bash.exe` invocation uses `-l` (login shell, gets PATH) and `cygpath -u` (Windows path → Unix format).
4. `exit /b` exits the batch script; everything below `CMDBLOCK` is unreached.

**Unix (bash/sh):**
1. `: << 'CMDBLOCK'` — `:` is no-op, `<< 'CMDBLOCK'` starts a heredoc.
2. Everything until `CMDBLOCK` is consumed by the heredoc.
3. The Unix command runs.

## File structure

```
hooks/
├── hooks.json           # points to the .cmd wrapper
├── run-hook.cmd         # polyglot wrapper (cross-platform entry)
├── session-start.sh     # actual hook logic
└── validate-bash.sh
```

## `hooks.json`

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear|compact",
        "hooks": [
          { "type": "command",
            "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd\" session-start.sh" }
        ]
      }
    ]
  }
}
```

Note: the path is quoted because `${CLAUDE_PLUGIN_ROOT}` may contain spaces on Windows (e.g. `C:\Program Files\...`).

## Reusable wrapper — `run-hook.cmd`

One wrapper per plugin, takes the script name as argument:

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

> **POSIX compliance:** use `$0` (not `${BASH_SOURCE[0]:-$0}`). Some Ubuntu/Debian `/bin/sh` is dash, which errors with "Bad substitution" on the BASH_SOURCE form.

## Requirements

- **Windows:** Git for Windows installed (`C:\Program Files\Git\bin\bash.exe`). If installed elsewhere, edit the wrapper.
- **Unix:** standard bash/sh; `chmod +x` on the `.cmd` file.

## Writing cross-platform hook scripts

The actual logic goes in `.sh`. To make it work on Windows via Git Bash:

**Do:**
- Use bash builtins where possible.
- `$(command)` instead of backticks.
- Quote variable expansions: `"$VAR"`.
- `printf` or heredocs for output.

**Avoid:**
- External tools (`sed`, `awk`, `grep`) when avoidable — they ARE in Git Bash but require `bash -l` for the PATH.
- Backticks for command substitution (legacy, harder to nest).

### Example: JSON escaping without `sed`/`awk`

Pure bash:
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

## Troubleshooting

| Symptom | Cause / Fix |
|---|---|
| "bash is not recognized" | CMD can't find bash. Wrapper uses full path; if Git is elsewhere, edit the path. |
| "cygpath: command not found" | Bash isn't running as a login shell. Ensure `-l`. |
| Path contains `\/` | `${CLAUDE_PLUGIN_ROOT}` ended with backslash and `/hooks/...` was appended. Use `cygpath` to convert. |
| Script opens in text editor | `hooks.json` points directly to `.sh`. Point at the `.cmd` wrapper. |
| Works in terminal but not as hook | Simulate the hook environment: `$env:CLAUDE_PLUGIN_ROOT = ...; cmd /c "...\run-hook.cmd" session-start.sh`. |

## Related issues

- [anthropics/claude-code#9758](https://github.com/anthropics/claude-code/issues/9758) — `.sh` opens in editor on Windows
- [anthropics/claude-code#3417](https://github.com/anthropics/claude-code/issues/3417) — hooks don't work on Windows
- [anthropics/claude-code#6023](https://github.com/anthropics/claude-code/issues/6023) — `CLAUDE_PROJECT_DIR` not found
