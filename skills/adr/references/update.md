<!-- agency-generated: v1 -->
# adr.update

UPDATE a ``Decision`` in place — advance its ``status`` and/or fill WH(Y) elements incrementally (the DOMAIN mutator; never reach into `manage` for an ADR).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `decision_id (str), status (the decision_status enum), and any WH(Y) element to (over)write; empty = leave unchanged.` |  |  |

## Returns

``{id, updated: [field…]}`` or ``{error}`` (e.g. an out-of-enum status the ontology rejects).

## Chain-next

adr.validate(id); adr.theme_status(theme_id) to see the roll-up.

## Details

(no further detail)

## Example

```bash
agency-adr-update --intent-id $IID …
```
