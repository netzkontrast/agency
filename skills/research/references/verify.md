<!-- agency-generated: v1 -->
# research.verify

Adversarial citation check; emits a Verification node.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `research_id (str — from prior research.lead).` |  |  |

## Returns

``{ok, checks: {evidence-supports-claim, contradiction-cluster}}``.

## Chain-next

walker's publish phase on ok=True; rerun specialists on ok=False.

## Details

(no further detail)

## Example

```bash
agency-research-verify --intent-id $IID …
```
