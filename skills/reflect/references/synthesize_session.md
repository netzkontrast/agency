<!-- agency-generated: v1 -->
# reflect.synthesize_session

Produce a session-reflection artefact at session close (act).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `session_lifecycle_id, lessons (multi-line), open_questions (multi-line), handoff_notes (next-session continuity).` |  |  |

## Returns

``{result, artefact}`` session-reflection artefact.

## Chain-next

terminal — agent closes the session.

## Details

Flips the SessionLifecycle to ``archived`` + records a ``session-reflection`` artefact PRODUCES'd against the intent. Also writes a ``Reflection{scope:'reflection'}`` for the synthesis-style notes so they surface in future-session search.

## Example

```bash
agency-reflect-synthesize_session --intent-id $IID …
```
