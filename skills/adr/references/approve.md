<!-- agency-generated: v1 -->
# adr.approve

APPROVE — the DoD hinge (SPEC-001-E pre-approval gate).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `decision_id (str), approver (str — the human owner's identity; ``"agent"`` is rejected), override (bool — owner-only escape hatch).` |  |  |

## Returns

``{decision_id, approved, …}`` — see the branches above.

## Chain-next

adr.render(theme_id); the spec's /open→/inprogress gate (356).

## Details

- automated criterion fails → ``{blocked: True, failing}`` (no approval), unless a provenance-stamped OWNER ``override`` is supplied. - automated pass, no ``approver`` → tries `ctx.elicit`; with no host bound it returns ``{input_required: True, pending}`` (the owner resumes later). - OWNER ``approver`` given → advances to ``approved``.

## Example

```bash
agency-adr-approve --intent-id $IID …
```
