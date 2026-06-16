<!-- agency-generated: v1 -->
# document.session_analytics

Cypher analytics over the Session Graph (Spec 292).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `session_id (str — bare or ``session` |  | ``-prefixed; empty = all), top (int — leaderboard cap for the cross-session view). |

## Returns

the analytics report dict.

## Chain-next

``document.restore_session`` to rebuild a flagged session.

## Details

``session_id`` set → a deep single-session report (event-type + tool-usage breakdown, raw-tool bypass profile, attached Documents, intents touched, tick-span). Empty → a cross-session aggregate (counts by status, busiest sessions, top tools/events, bypass totals). Delegates to ``Memory.session_analytics`` (raw Cypher lives in ``memory.py`` per the Management read-API doctrine).

## Example

```bash
agency-document-session_analytics --intent-id $IID …
```
