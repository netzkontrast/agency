<!-- agency-generated: v1 -->
# novel.preflight_report

The pre-scene readiness audit (act) — every REGISTERED audit phase run read-only over the 137–144 stack, one composite ``{ready, blockers, warnings}``, and a recorded ``pre-flight`` Artefact.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scene_id; budget_ms (0 → PREFLIGHT_BUDGET_MS; overrun emits a PREFLIGHT_SLOW warning, never truncates); recurrence_n (0 → RECURRENCE_N); debug (assert derivation parity at runtime).` |  |  |

## Returns

``{scene_id, chapter_id, ready, verdicts (per-phase: legacy fields + status + findings + duration_ms), blockers, warnings, audit_verbs, audit_verb_set_hash, total_duration_ms, generated_at, proposals_minted, artefact_id}``.

## Chain-next

resolve the blockers, re-run; then draft (``prompt.compose_voice_locked_brief``).

## Details

(no further detail)

## Example

```bash
agency-novel-preflight_report --intent-id $IID …
```
