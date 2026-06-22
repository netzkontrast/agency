<!-- agency-generated: v1 -->
# loop.verify_report

Audit a loop's verification SET against verification-rubric.md (364).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `loop_id (str).` |  |  |

## Returns

``{criteria, programmatic_ratio, warnings, rubric_source}``.

## Chain-next

convert a judge/human criterion to programmatic where possible.

## Details

(no further detail)

## Example

```bash
agency-loop-verify_report --intent-id $IID …
```
