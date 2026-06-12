<!-- agency-generated: v1 -->
# dogfood.recall_overflow_slice

Spec 154 Slice 3 — recall a paged view of a captured overflow body.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `body (str — the full captured body the agent is paging). slice (str — "full" or "<start>` |  | <stop>" line range). grep (str — pattern to filter matching lines). offset (int — grep paging offset). byte_offset (int — line slice intra-line cursor). max_tokens (int — budget for the returned slice). |

## Returns

``{body, slice_tokens, total_tokens, matches_returned, more_available, next_match_offset, next_byte_offset}``.

## Chain-next

``dogfood.replay_events`` when the agent needs to find the right body to recall first.

## Details

Slice 2 of Spec 154 wired `capture_body_overflow` through the envelope; this verb is the read side. The caller supplies the full body (e.g. from a previously-stored Artefact); the verb delegates to the pure `_overflow.recall_overflow_slice` library with the configured budget. Slice 4 will add an Artefact-id- keyed lookup so the body never has to round-trip through the agent.

## Example

```bash
agency-dogfood-recall_overflow_slice --intent-id $IID …
```
