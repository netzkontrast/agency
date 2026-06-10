---
spec_id: "132"
slug: codex-entity-tracking
status: shipped
last_updated: 2026-06-10
owner: "@agency"
depends_on: ["101", "127"]
affects:
  - agency/capabilities/novel/_main.py
  - agency/capabilities/prompt/_main.py
  - tests/test_novel_codex.py
domain: novel / codex / context-injection
parent_spec: "101"
mvp-source:
  - "Novelcrafter codex feature (smart context injection by trigger word)"
  - "Plan/127/spec.md _world_rules carve-out"
---

# Spec 132 — Codex entity tracking (Novelcrafter parity)

## Why

Novelcrafter's edge over agency today: when the author mentions "the
Iron Mask" in a chapter outline, Novelcrafter auto-injects its codex
entry into the prompt. Agency has richer structure (storyform + World
sub-graph) but no equivalent "mention → inject" mechanic. Spec 127's
`_world_rules` placeholder names this gap explicitly.

## Done When

- [ ] **`CodexEntry` node** — `{slug, name, kind, body, triggers}`.
      `kind` is an enum (location / minor-character / artefact /
      concept / faction); `triggers` is a comma-separated list of
      strings; `body` is the agent-facing description.
- [ ] **`CODEX_OF` edge** — CodexEntry → Novel (codex entries are
      per-novel; future spec can introduce shared-world codex).
- [ ] **5 verbs**:
      - `create_codex_entry(novel_id, slug, name, kind, body, triggers)`
      - `list_codex_entries(novel_id, kind=None)`
      - `match_codex_entries(novel_id, text)` — scans `text` for any
        registered trigger word; returns matched entries.
      - `update_codex_entry(entry_id, fields_dict)` — bi-temporal
        update for body / triggers refinement as the story matures.
      - `archive_codex_entry(entry_id, reason)` — flips a deprecated-
        kind flag; archived entries don't match.
- [ ] **`prompt.assemble_scene_brief` upgrade** — `_world_rules`
      composer becomes:
      1. Pull scene's chapter outline + cast names
      2. Call `match_codex_entries(novel_id, all_text)`
      3. Inject matched entries' `body` (token-budgeted to section cap)
      4. Add to `sources` array with `contributed: "world_rules"`
- [ ] Triggers are case-insensitive whole-word matches (the entry's
      `triggers` field already mirrors `body` content; matching is
      lookup, not NLP).
- [ ] TODO row + drift clean.

## Design notes

- This is the Novelcrafter "codex" feature plus a real graph behind it.
  Authors who already use Novelcrafter can import their codex via a
  future `import_novelcrafter_codex(file)` verb (Slice 2).
- `triggers` defaults to `[name, slug]` if empty — the common case
  ("mention the entity's name → inject it") works without authoring.

## Open questions

1. Shared-world codex (entries reused across novels)? **Recommend**:
   defer to Slice 2 once World ↔ Codex relationship is clear.
2. Auto-trigger from `kind=minor-character` mentions or all kinds?
   **Recommend**: all kinds; let the author archive aggressively.

## Followup — Implementation Status (2026-06-10)

**Done:**
- **Ontology**: `CodexEntry {novel, slug, name, kind}` node;
  `CODEX_ENTRY_KIND = {location, minor-character, artefact, concept, faction}`
  enum on `kind`; `CODEX_OF` edge CodexEntry → Novel.
- **5 verbs on novel cap**:
  - `create_codex_entry(novel_id, slug, name, kind, body, triggers="")` —
    mints + CODEX_OF; triggers defaults to `name, slug` when empty.
  - `list_codex_entries(novel_id, kind="")` — filters; skips archived.
  - `match_codex_entries(novel_id, text)` — case-insensitive substring
    scan over comma-separated triggers; one match per entry; skips
    archived. Returns `{matches: [{entry_id, slug, name, kind, body,
    trigger_hit}]}`.
  - `update_codex_entry(entry_id, body, triggers, name)` — partial
    update; empty args are no-ops.
  - `archive_codex_entry(entry_id, reason)` — soft delete via
    `archived="yes"`; node stays in graph for provenance.
- **Spec 127 `_compose_world_rules` upgrade**: composer gathers
  scannable text (chapter body + title + scene slug + scene cast),
  calls `match_codex_entries`, and renders `- **Name** (kind): body`
  bullets. Each match adds a `CodexEntry` node to the brief's
  `sources` array. Placeholder text retired.
- `_BriefContext` extended with `_ctx` field (additive; backwards
  compatible). `novel` dict gains `id` field on creation so composers
  can read `novel_id` directly.

**Still:** Word-boundary matching deferred — Slice 1 is plain
substring (case-insensitive). A trigger of "raven" in a body about
"ravenous appetites" would false-positive; Slice 2 should add
`\b...\b` word-boundary regex matching.

**Open Q resolutions:** Q1 — per-novel codex (CODEX_OF → Novel); shared
codex deferred to Slice 2. Q2 — all 5 kinds auto-trigger; author uses
archive aggressively (archived entries skip matching).

**Test:** 17 new tests (`tests/test_novel_codex.py`) — ontology
registration (node/enum/edge/verbs), create + CODEX_OF edge presence,
unknown-kind rejection, triggers auto-default to `name, slug`,
list + kind filter, match by trigger + case-insensitive + no-match +
archive-skip, update changes body, archive flags archived, and the
end-to-end `assemble_scene_brief` upgrade — world_rules section now
injects matched codex bodies and the "pending" placeholder is gone.
295 across novel/prompt/naming/install green; drift clean; lint clean.
