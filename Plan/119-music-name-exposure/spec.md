---
spec_id: "119"
slug: music-name-exposure
status: draft
last_updated: 2026-06-09
owner: "@agency"
depends_on: ["093", "095", "117"]
affects:
  - agency/capabilities/music/config.py                 # MusicConfig.name_exposure_blocklist
  - agency/capabilities/music/_main.py                  # check_name_exposure verb + name_exposure_gate + compose into lyrics_pregen_gate
  - tests/test_music_lyrics.py                          # name-exposure verb + gate + composite tests
domain: music / lyrics / authoring-safety
wave: 8
parent_spec: "117"
---

# Spec 119 — Music Name-Exposure Enforcement (project-DNA roster)

## Why

This is **F6** from Spec 117, promoted to its own spec. The Umschalten
dogfood run leaked a personal name ("Lex") into an S4 lyric draft. Nothing in
the music capability flagged it — it was caught only by the `theagencysystem`
skill's `name_exposure` rule, which lives **outside** both plugins.

`name_exposure` is a real authoring-safety rule for many projects: a personal
or character name must **never** reach a public-facing music field (a lyric,
streaming-lyric line, Suno style/metatag, or promo copy) — only function/role
descriptors may. Today the music capability's `scan_artist_names` checks a
**single configured artist name** against accidental drops; it has no notion of
a **project roster** of forbidden names (alters, characters, real people).

This spec adds generic, config-sourced name-exposure enforcement to the lyrics
cluster. It is **project-agnostic**: the roster is supplied by config — no
hardcoded Agency System names. A project with no roster gets a no-op (zero
behaviour change), so the gate is safe to compose by default.

## Done When

- [x] **Config.** `MusicConfig` gains `name_exposure_blocklist: list[str]`,
  sourced from `name_exposure.blocklist` in `music-config.yaml` (default `[]`).
  `as_dict()` round-trips it under a `name_exposure` key.
- [x] **`check_name_exposure(text, roster=None)`** — transform verb, driver-free
  + deterministic: case-insensitive, **whole-word** match (so "Lex" does not
  fire inside "lexicon"). `roster` defaults to the config blocklist. Returns
  `{hits: [{name, count}], count, roster_size}`.
- [x] **`name_exposure_gate(lifecycle_id, lyrics, roster=None)`** — effect gate
  mirroring `explicit_gate`: PASSED when zero forbidden names appear; records
  `gate.check` PASSED/BLOCKED_ON; returns typed `GATE_FAILED` + pauses the
  lifecycle on a hit. **No-op pass when the roster is empty** (rosterless
  projects + existing tests are unaffected).
- [x] **Live trigger (no dormant surface).** Compose `name_exposure` as a 5th
  sub-gate in `lyrics_pregen_gate` (additive; passes when roster empty, so the
  composite's verdict is unchanged for rosterless projects). Existing
  `lyrics_pregen_gate` tests that enumerate sub-gate keys get the additive
  `name_exposure` key (expectation update, not a weakened assertion).
- [x] **Tests** (`tests/test_music_lyrics.py`): verb finds a rostered name,
  respects word boundaries (`lexicon` ≠ `Lex`), is case-insensitive, and
  returns empty on an empty roster; gate blocks on a hit + passes clean;
  config loads the blocklist; the composite includes the `name_exposure`
  sub-gate and still passes with an empty roster.
- [x] **Promo layer (Slice 2).** `promo_review` scans copy against the roster;
  a hit is a `name_exposure` finding (severity `fail`) with a heavy score
  penalty, so the existing `promo_review_gate` score threshold blocks it — no
  new gate needed. Empty roster → no-op. So `name_exposure` is enforced across
  **both** public-facing text surfaces (lyrics + promo).
- [x] `scripts/check-drift` clean; `Plan/119-…/spec.md` Followup + `TODO.md`
  row 119 added.

## Design

### Roster source (project-supplied, not hardcoded)

```yaml
# music-config.yaml
name_exposure:
  blocklist: ["Kael", "Lex", "Alex", "Rhys", "Selene", "Nyx", "Kiko", "Lia",
              "Isabelle", "Moros", "Argus"]   # the project's forbidden roster
```

For the Agency System this list is exactly the alter roster the
`theagencysystem` skill already knows (function↔name resolver) — but the music
capability stays agnostic: it enforces whatever roster the project configures.

### Deterministic scan (driver-free)

`check_name_exposure` does pure text math (like `count_syllables` /
`validate_sections`): for each rostered name, a case-insensitive **word-boundary**
regex (`\bNAME\b`) over the text; collect `{name, count}` for any with ≥1 hit.
No driver dependency — it runs even before drivers are wired, and never touches
the network or disk.

### Gate + composition

`name_exposure_gate` follows the `explicit_gate` shape (records `gate.check`,
returns `GATE_FAILED` on block). It is added to the `lyrics_pregen_gate`
sub-gate loop. Because an empty roster yields zero hits → PASSED, composing it
is safe-by-default: rosterless projects see no change; rostered projects get
the name-exposure check for free in their pre-generation gate.

## Non-goals

- The **design** layer (cover-art / ASDLS image prompts) also carries
  `name_exposure` — out of scope here. A follow-up can reuse the shared
  `_name_exposure_hits` scan from a future design/art cluster. (The **promo**
  layer is now covered — Slice 2 above.)
- The roster is enforced, not authored: deriving the roster from a project's
  DNA files (e.g. the resolver) stays the project's / skill's job.

## Followup — Implementation Status (2026-06-09 — Shipped)

**Done.**

- **Config** (`agency/capabilities/music/config.py`):
  - `MusicConfig.name_exposure_blocklist: list` field (`:147`).
  - `_from_dict` reads `ne = d.get("name_exposure") or {}` →
    `name_exposure_blocklist=list(ne.get("blocklist") or [])` (`:243,:256`).
  - `as_dict` emits `"name_exposure": {"blocklist": [...]}` (`:290`).
- **Shared scan helper** `MusicCapability._name_exposure_hits(text, roster)`
  (`agency/capabilities/music/_main.py:897`) — `re.findall(r"\bNAME\b", text,
  re.I)` per rostered name; whole-word + case-insensitive; pure text math, no
  driver/network/disk. Used by both verb and gate (no duplication).
- **`check_name_exposure(text, roster=None)`** transform verb (`_main.py:917`)
  — defaults `roster` to `MusicConfig.load().name_exposure_blocklist`; returns
  `{hits:[{name,count}], count, roster_size}`.
- **`name_exposure_gate(lifecycle_id, lyrics, roster=None)`** effect gate
  (`_main.py:1090`) — mirrors `explicit_gate`: records `gate.check`
  PASSED/BLOCKED_ON; `passed = not hits`; typed `GATE_FAILED` + lifecycle pause
  on a hit; empty roster → PASSED no-op.
- **Composition** — `name_exposure_gate` added to the `lyrics_pregen_gate`
  sub-gate loop as the additive 5th `("name_exposure","name_exposure_gate")`
  (`_main.py:1846-1848`); empty roster keeps the composite verdict unchanged.
- **Regen** — `python -m agency.install` re-emitted `skills/help/SKILL.md`,
  `skills/music/SKILL.md`, the `lyrics_pregen_gate` reference + bin shim with
  the two new verbs. `scripts/check-drift` → **NO DRIFT DETECTED**.

**Tests** (all green — `99 passed`):
- `tests/test_music_production.py`: `test_config_loads_name_exposure_blocklist`
  (loads `name_exposure.blocklist` from a `music-config.yaml` + `as_dict`
  round-trip), `test_config_name_exposure_defaults_empty`.
- `tests/test_music_lyrics.py`:
  `test_check_name_exposure_finds_rostered_name`,
  `test_check_name_exposure_respects_word_boundary` (CRITICAL: `lexicon` ≠
  `Lex`), `test_check_name_exposure_is_case_insensitive`,
  `test_check_name_exposure_empty_roster_is_noop`,
  `test_name_exposure_gate_blocks_on_rostered_name` (GATE_FAILED + lifecycle
  `input-required`), `test_name_exposure_gate_passes_when_clean`,
  `test_name_exposure_gate_empty_roster_passes`,
  `test_lyrics_pregen_gate_includes_name_exposure_subgate` (stubs the other 4
  sub-gates, exercises the real `name_exposure_gate` with the default empty
  roster → composite green). `test_lyrics_cluster_verbs_discover` updated to
  enumerate `check_name_exposure` + `name_exposure_gate`.
- `tests/test_music_gates.py`: `test_lyrics_pregen_gate_composes_all_four_sub_gates`
  → renamed `…_composes_all_sub_gates`; expected sub-gate set extended from 4
  to 5 (additive expectation update, not a weakened assertion).

**Evidence.** `python -m pytest -q tests/test_music_lyrics.py
tests/test_music_capability.py tests/test_music_gates.py
tests/test_music_production.py` → `99 passed`. `scripts/check-drift` → NO DRIFT
DETECTED.

### Slice 2 (promo layer) — 2026-06-09

- `promo_review` (`_main.py`) now scans copy via the shared
  `_name_exposure_hits` against `MusicConfig.load().name_exposure_blocklist`;
  a hit appends a `{"kind":"name_exposure","names":[…],"severity":"fail"}`
  finding and a `-50` score penalty, so the existing `promo_review_gate`
  threshold blocks it — no new gate. Empty roster → no-op.
- Tests (`tests/test_music_promo.py`): `test_promo_review_flags_name_exposure`
  (rostered name → fail finding + score < 70), 
  `test_promo_review_name_exposure_noop_without_roster`. `test_music_promo.py`
  → 19 passed.

`name_exposure` is now enforced across **both** public text surfaces (lyrics +
promo). The **design/art** layer remains the one documented non-goal — a
follow-up can reuse `_name_exposure_hits` from a future art cluster.
