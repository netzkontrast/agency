<!-- agency-generated: v1 -->
# subagent.develop

Dispatch a worker child and gate it through spec-review then quality-review (effect).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `driver (capability name), driver_verb (str), item (dict — task payload), spec_passed (bool), quality_passed (bool), spec_evidence/quality_evidence (str, optional).` |  |  |

## Returns

``{child, done, spec, quality}`` (wire shape).

## Chain-next

terminal — ``done=True`` flips the child Lifecycle to ``completed``; ``done=False`` leaves it ``input-required``.

## Details

(no further detail)

## Example

```bash
agency-subagent-develop --intent-id $IID …
```
