<!-- agency-generated: v1 -->
# intent.brooks_lint

BROOKS-LINT — the 9th critical-thinking method: a conceptual-integrity pass grounded in Fred Brooks (*Mythical Man-Month* / *No Silver Bullet*).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `target (a spec Document id, raw spec/design text, or "" → the serving intent's deliverable), kind (label — default "spec").` |  |  |

## Returns

``{target, kind, findings: [{principle, severity, msg, evidence}], conceptual_integrity_ok, summary}``.

## Chain-next

fold the findings into the spec's "## Brooks-lint findings folded in" section (workflow 358 improve-loop).

## Details

(no further detail)

## Example

```bash
agency-intent-brooks_lint --intent-id $IID …
```
