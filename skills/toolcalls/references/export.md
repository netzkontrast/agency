<!-- agency-generated: v1 -->
# toolcalls.export

Distil the session's tool calls into a durable export — the top calls + responses + new-spec SUGGESTIONS (the dogfooding fold-back, Goal 6).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `top_n (int — 0 uses the `toolcalls.export_top_n` config default), apply (bool — write the report + record the artefact), prune (bool — clear the store after a successful export).` |  |  |

## Returns

``{top, suggestions, report, written, export_id}``.

## Chain-next

open a spec for a strong suggestion; `toolcalls.prune` when done.

## Details

Heuristic suggestions always run (a repeated command → a `shell.define` template; a repeated read → an index; a high-volume call → a filter); an LLM pass adds richer ideas when `toolcalls.suggest_via_llm` is set. With `apply` the FULL markdown report is written to `.agency/sessions/<session>-toolcalls.md` (never truncated) and a `ToolcallExport` artefact is recorded, so the signal survives a `prune`.

## Example

```bash
agency-toolcalls-export --intent-id $IID …
```
