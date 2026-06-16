<!-- agency-generated: v1 -->
# develop.port_plugin

Port an external plugin's prompt surface INTO agency as Documents, with a coverage gap-map (Spec 293/292).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `source (dir to walk), origin (label for provenance; defaults to the dir name), kind (command|agent|…), glob (file pattern), limit (max files).` |  |  |

## Returns

``{source, origin, kind, ported_count, covered, gaps, ported}``.

## Chain-next

turn each `gaps` entry into a native capability/verb.

## Details

Every command/agent markdown file IS a prompt — so a plugin ports into agency by ingesting each file as a `Document` (prompt-audited, NOT anchor-stamped — the external source is left untouched) and mapping each against agency's live capability/verb/skill vocabulary. The gap-map says what's already mirrored vs. what still needs a native verb, so the remaining port work is scoped rather than guessed.

## Example

```bash
agency-develop-port_plugin --intent-id $IID …
```
