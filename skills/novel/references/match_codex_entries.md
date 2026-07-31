<!-- agency-generated: v1 -->
# novel.match_codex_entries

Scan ``text`` for codex triggers — word-boundary decidable + optional fuzzy judged (transform).

## Inputs

| Param | Type | Description |
|-------|------|-------------|
| `novel_id, text (the body to scan), fuzzy (opt-in advisory pass; default False).` |  |  |

## Returns

``{matches, decidable: [{entry_id, surface_form, span: [start, end], kind: "whole_word", confidence: None, slug, name}], judged: [... kind: "fuzzy", confidence, model_id], total, invalid, fuzzy_status}`` with ``total == len(decidable) + len(judged)``.

## Chain-next

feed matches to ``prompt.assemble_scene_brief``'s world_rules section; judged suggestions go to the author, never to a gate.

## Details

Spec 242 MatchResult: ``decidable`` matches are case-insensitive WHOLE-WORD regex hits (``\b…\b`` — "raven" never matches inside "ravenous"), each with a span aligned to word boundaries in ``text`` and ``confidence: None``. Only decidable matches feed continuity gates. With ``fuzzy=True`` a wired ``codex_match`` driver adds ``judged`` advisory matches (typos, partial mentions) with a float confidence + the driver's model id; no driver → graceful degrade (``judged=[]``, ``fuzzy_status`` names the code). A trigger prefixed ``re:`` is a raw regex; a malformed one lands the entry in ``invalid`` (CODEX_ENTRY_INVALID) while other entries still match. Archived entries are skipped. The legacy ``matches`` key remains — first decidable hit per entry in the Spec-132 shape.

## Example

```bash
agency-novel-match_codex_entries --intent-id $IID …
```
