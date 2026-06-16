<!-- agency-generated: v1 -->
# mode.activate

Activate a behavioral posture — return its rules + record provenance (Spec 295).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `mode (auto | one of the five mode names), context (str — the request/situation, used for auto-resolution).` |  |  |

## Returns

``{mode, purpose, behaviors, flags, activation_id}`` or ``{error}``.

## Chain-next

adopt the behaviors; mode.activate again as the task shifts.

## Details

``mode="auto"`` resolves the top mode for ``context`` via ``detect`` (falls back to ``brainstorming`` when nothing matches — discovery is the safe default for an unclear request). Records a ``ModeActivation`` node SERVING the intent, so adopted postures are queryable provenance.

## Example

```bash
agency-mode-activate --intent-id $IID …
```
