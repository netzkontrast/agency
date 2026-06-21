<!-- agency-generated: v1 -->
# adr.architecture

ARCHITECTURE — rebuild the shorthand architecture digest: every recorded WH(Y) decision as a ONE-LINER, grouped by architecture layer, rolled up from the durable thematic ADRs (``docs/adr/<layer>.md``).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `adr_dir (where the thematic ADRs live), out (the digest path, repo-root-relative), apply (write the file; else preview only).` |  |  |

## Returns

``{path, layers, decisions, body, written}``.

## Chain-next

the SessionStart hook emits ``out``; `adr.hints` for the per-spec deep cut at implementation start.

## Details

(no further detail)

## Example

```bash
agency-adr-architecture --intent-id $IID …
```
