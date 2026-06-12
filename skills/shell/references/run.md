<!-- agency-generated: v1 -->
# shell.run

Run an ALLOWLISTED command (or a named template), FILTER its output, record it.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `command (raw — its first token MUST be allowlisted) OR template (a name from ``shell.templates``); args (appended); filter (output slice; defaults to the template's filter, else 'tail` |  | 20'). |

## Returns

``{exit_code, output, lines, run_id, template?}`` — the FILTERED delta (full output is bounded, never dumped); or ``{error, …}`` on a disallowed tool / unknown template.

## Chain-next

inspect the recorded command-run Artefact (``recall(run_id)``).

## Details

(no further detail)

## Example

```bash
agency-shell-run --intent-id $IID …
```
