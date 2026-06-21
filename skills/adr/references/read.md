<!-- agency-generated: v1 -->
# adr.read

READ a ``Decision``'s current WH(Y) fields + status (the domain read — no need to reach into the generic `manage` tool for an ADR).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `decision_id (str).` |  |  |

## Returns

``{id, status, <WH(Y) fields>}`` or ``{error}`` if absent / not a Decision.

## Chain-next

adr.validate(id) / adr.update(id, status=…).

## Details

(no further detail)

## Example

```bash
agency-adr-read --intent-id $IID …
```
