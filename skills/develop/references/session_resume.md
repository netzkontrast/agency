<!-- agency-generated: v1 -->
# develop.session_resume

Spec 114 Slice 2 — cross-session handoff.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `for_intent_id (optional; empty → most-recent Intent — renamed from `intent_id` to avoid the Registry.invoke built-in-parameter collision).` |  |  |

## Returns

``{found, session_lifecycle_id, intent_id, mode, status, purpose, mode_history, suggested_action, last_active}``.

## Chain-next

when `found=True`, walk the suggested_action verb; when `found=False`, `develop.session_init` for a fresh start.

## Details

Find the most-recent ACTIVE SessionLifecycle SERVING the given intent (or the most-recent intent when `for_intent_id` is empty) so a fresh session can pick up where the prior one left off — no context re-derivation. Archived lifecycles are skipped; if no active lifecycle exists, returns `found=False`.

## Example

```bash
agency-develop-session_resume --intent-id $IID …
```
