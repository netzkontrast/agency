<!-- agency-generated: v1 -->
# document.session

Render a Session as a Document — the four concepts converge (Spec 292).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `for_intent_id (str — defaults to the serving Intent), apply_path (str — explicit .md path; overrides archive), archive (bool — write into the past-sessions directory).` |  |  |

## Returns

``{document_id, content, tokens, sections, written}``.

## Chain-next

``document.ingest`` the written file to round-trip edits.

## Details

A Session Document gathers the substrate's four concepts under one artefact: **Intent** (the why/what/accept), **Capability** (the Invocations that served it), **Lifecycle** (the Lifecycle/skill phases walked), and **Memory** (the Reflections recorded). This is what "Documents are the artefact in which everything comes together" means concretely. The render is graph-authored (``source='graph'``) and, when archived/applied, written to disk with a stable anchor so it round-trips back via ``document.ingest`` — closing the bi-directional loop. ``archive=True`` (default) deposits the Document into the dedicated **past-sessions directory** (``<db-dir>/sessions/<intent>.md``, i.e. ``.agency/sessions/`` for the real engine), so every session is a durable, round-trippable artefact. ``apply_path`` overrides the location.

## Example

```bash
agency-document-session --intent-id $IID …
```
