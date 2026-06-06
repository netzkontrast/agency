<!-- agency-generated: v1 -->
# jules.plan

The latest generated plan — show it before approve_plan (no PR exists yet).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `session (sid), max_pages (int — walk back this many pages).` |  |  |

## Returns

``{plan: <markdown>, generated_at}`` or ``{error}`` if not found.

## Chain-next

review then ``jules.approve_plan(session=)``.

## Details

(no further detail)

## Example

```bash
agency-jules-plan --intent-id $IID …
```
