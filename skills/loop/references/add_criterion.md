<!-- agency-generated: v1 -->
# loop.add_criterion

Add a typed verification criterion (programmatic|judge|human) to a loop (364).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `loop_id (str), kind (str), check (argv list — programmatic), expect (exit_zero|exit_nonzero|stdout_contains), contains (str), rubric (str — judge), prompt (str — human), cid (str — optional id).` |  |  |

## Returns

``{criterion_id, kind}``.

## Chain-next

loop.verify_report(loop_id) to audit the set.

## Details

(no further detail)

## Example

```bash
agency-loop-add_criterion --intent-id $IID …
```
