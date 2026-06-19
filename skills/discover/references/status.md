<!-- agency-generated: v1 -->
# discover.status

Smoke verb — report the registered ``discover`` ontology surface.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `(none).` |  |  |

## Returns

``{nodes, edges, enums, schemas}`` — the locked Spec 307 surface this capability registers.

## Chain-next

``discover.interview`` (Spec 309 — not yet shipped).

## Details

Proves the capability is wired and its ontology registered (Spec 308 acceptance). Pure introspection — records nothing. Removed/absorbed once ``discover.interview`` (Spec 309) lands as the real entry point.

## Example

```bash
agency-discover-status --intent-id $IID …
```
