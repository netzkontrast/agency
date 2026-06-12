<!-- agency-generated: v1 -->
# shell.run

Run an ALLOWLISTED command (or a named template), FILTER its output, record it.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `command (raw — its first token MUST be allowlisted) OR template (a name from ``shell.templates``); args (appended); filter (output slice; defaults to the template's filter, else 'tail` |  | 20'); hook_wrap (Spec 280 — opt-in foreign-hook wrap that BYPASSES the allowlist because the user already approved the command by authoring it in their `.claude/settings.json`; runs the command verbatim via the shell and forwards stdin to the wrapped process so a Claude Code hook stays semantically identical). |

## Returns

``{exit_code, output, lines, run_id, template?, wrapped?}`` — the FILTERED delta (full output is bounded, never dumped); or ``{error, …}`` on a disallowed tool / unknown template.

## Chain-next

inspect the recorded command-run Artefact (``recall(run_id)``).

## Details

(no further detail)

## Example

```bash
agency-shell-run --intent-id $IID …
```
