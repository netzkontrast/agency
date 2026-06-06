<!-- agency-generated: v1 -->
# plugin.lint_explain

Return the rework recipe for a lint rule kind (Spec 074) — so you learn HOW to fix it.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `rule (the finding ``kind``, e.g. 'surface_size', 'reflection_link').` |  |  |

## Returns

``{kind, what, steps, reference, example?}`` (wire shape); or ``{error, known}`` when the rule kind is unrecognised.

## Chain-next

apply the ``steps``, then re-run ``plugin.lint_capability``.

## Details

(no further detail)

## Example

```bash
agency-plugin-lint_explain --intent-id $IID …
```
