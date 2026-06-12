<!-- agency-generated: v1 -->
# novel.fetch_scene_body

Spec 220 Slice 1.5 — public retrieval for a scene-body Artefact.

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `body_handle (Artefact id), max_chars (0 = full body; positive = head-slice cap).` |  |  |

## Returns

``{body, total_chars, total_tokens, voice_locked, alter_id, scene_id, driver, stop_reason, truncated}``.

## Chain-next

``novel.integrate_scene_body(scene_id, body)``. Failure modes: ``NOT_FOUND`` (body_handle missing), ``BAD_REQUEST`` (handle resolves to a non-scene- body Artefact).

## Details

``novel.generate_scene_body`` returns the body via ``body_handle`` (an Artefact id) instead of inlining the prose (Spec 146 prefix discipline + Spec 154 budget). This verb resolves the handle back to the body so the MCP/CLI surface has a documented fetch path — Codex review on PR #137 surfaced that ``memory.recall_overflow_slice`` isn't registered as a verb, leaving the body stranded behind a graph-internal field.

## Example

```bash
agency-novel-fetch_scene_body --intent-id $IID …
```
