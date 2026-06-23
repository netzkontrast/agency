<!-- agency-generated: v1 -->
# plugin.lint_disciplines

The graduated discipline gate (Spec 378 Slice 4): strict-lint every registered discipline, partitioned into clean / warned (the migration tail) / blocked (a self-contained discipline that regressed).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `none.` |  |  |

## Returns

``{ok, clean: [name], warned: [{name, violations}], blocked: [{name, violations}]}`` — ``ok`` is False iff a self-contained discipline fails the contract.

## Chain-next

fix any ``blocked`` discipline; fill a ``warned`` one's phase instructions to move it into the gate.

## Details

(no further detail)

## Example

```bash
agency-plugin-lint_disciplines --intent-id $IID …
```
