<!-- agency-generated: v1 -->
# novel.preflight_report

The pre-scene readiness audit (act) — five read-only verdicts over the 137–144 stack, one composite ``{ready, blockers, warnings}``, and a recorded ``pre-flight`` Artefact.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `scene_id.` |  |  |

## Returns

``{scene_id, chapter_id, ready, verdicts, blockers, warnings, artefact_id}`` (spec §Composite verdict shape).

## Chain-next

resolve the blockers, re-run; then draft (``prompt.compose_voice_locked_brief``).

## Details

(no further detail)

## Example

```bash
agency-novel-preflight_report --intent-id $IID …
```
