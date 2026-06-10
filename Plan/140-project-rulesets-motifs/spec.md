---
spec_id: "140"
slug: project-rulesets-motifs
status: draft
last_updated: 2026-06-10
owner: "@agency"
depends_on: ["101", "104", "122", "132"]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_rulesets_motifs.py
domain: novel / editorial / project-lint
parent_spec: "101"
mvp-source:
  - "examples/kohaerenz-protokoll/05_welt-sensorik-drafting.md (§10 Self-Review-Regelwerk R-1..R-N, Defekt-Kategorien)"
  - "examples/kohaerenz-protokoll/05_welt-sensorik-drafting.md (§4 Foreshadowing-Programm, §5 Genesis-Motive, §2.1 Hitze-Polaritätsregel)"
---

# Spec 140 — Project rule-sets & motif discipline

## Why

The Kohärenz Protokoll ships its own per-scene **self-review rule-set** —
R-1 through R-N, each a project-specific hard rule with a defect-severity
(Critical / Medium / Low), checked before every commit. Examples: R-5 "cold
ozone (AEGIS) ≠ warmth (Juna), never mix in one place"; R-7 "max 1 Genesis-
echo per scene"; R-9 "Genesis style-markers never repeated verbatim". Plus a
**motif discipline**: 5 named Genesis motifs (Rauschen / Form / Klick /
Phantom / Resonanz), each echoed but **max 1 per scene** (stacking turns the
novel into allegory), and **foreshadowing anchors** (the number 734,
Telefon-Stille, the Silas half-sentence, the Wärme-debut) tracked across the
manuscript.

Spec 122's editorial gates are *generic* (filter-words, show-don't-tell).
Spec 132 (codex) tracks entities. Neither lets an author author their own
named R-rules with severity tiers, nor budgets motif-echoes per scene, nor
tracks foreshadowing-anchor payoffs. This turns the generic prose-lint into a
**project-extensible** discipline — the single highest-frequency operation in
the KP workflow (every scene runs the R-checklist before commit).

## Done When

- [ ] **`DEFECT_SEVERITY` enum** = `{critical, medium, low}` — the §10.2
      defect categories (Critical = strike/rewrite; Medium = reviewer check;
      Low = reviewer check).
- [ ] **`ProjectRule` node** `{novel, rule_id, name, severity, predicate_kind,
      params, rationale}` — an author-authored R-rule. `rule_id` is the
      stable handle (R-5); `predicate_kind` ∈ a documented decidable set
      (see below); `params` carries the rule's config (the two-set polarity
      lexicons for R-5; the echo cap for R-7).
- [ ] **Decidable predicate kinds** (the engine ships these; authors compose):
      - `mutual-exclusion` — two term-sets that must never co-occur in one
        scene (R-5 hot-polarity: cold-ozone terms ∩ warmth terms = ∅ per scene).
      - `per-scene-budget` — a tagged element capped per scene (R-6 max 1
        concept; R-7 max 1 Genesis-echo; R-4 max 3 micro-cues).
      - `forbidden-verbatim` — phrases that may not appear literally
        (R-9 Genesis style-markers; R-3 veil terms — though 139 owns timing).
      - `register-forbidden` — a token-class forbidden in a tagged speaker's
        lines (R-8 AEGIS no metaphor/moral/affect/"Ich").
  Each predicate is a pure transform over the scene body + params.
- [ ] **Verbs**:
      - `register_project_rule(novel_id, rule_id, name, severity,
        predicate_kind, params, rationale)` — author authors an R-rule.
      - `list_project_rules(novel_id, severity="")` — the rule registry.
      - `run_project_rules(scene_id)` — runs EVERY registered rule over the
        scene; returns `{passed, findings: [{rule_id, severity, message}]}`.
        The per-scene self-review checklist (§10.3) made executable.
      - `project_rule_gate(novel_id, block_at="critical")` composite — the
        manuscript fails iff any scene has an unresolved finding at or above
        `block_at` severity. Critical blocks; medium/low surface as warnings.
- [ ] **Motif discipline** (a built-in `per-scene-budget` application + a
      tracker):
      - `Motif` node `{novel, slug, first_event_chapter}` + `ECHOES_IN` edge
        (Motif → Scene) recording each echo.
      - `record_motif_echo(scene_id, motif_slug)` — logs an echo.
      - `motif_echo_report(novel_id)` — per scene, count of motif-echoes;
        flags scenes exceeding the cap (KP: 1). Per motif, the echo-trail
        from its first-event chapter forward (the foreshadowing spine).
- [ ] **Foreshadowing anchors** (the 734 / Telefon-Stille / anchor tracking):
      - `Anchor` node `{novel, name, planted_chapter, payoff_chapter?}` +
        `PLANTS`/`PAYS_OFF` edges (Anchor → Scene).
      - `anchor_status_report(novel_id)` — planted-but-unpaid anchors
        (the "Chekhov's gun" audit, project-specific; complements Spec 123's
        PlantedElement with named, cross-chapter anchors).
- [ ] TODO row + drift clean.

## Design notes

- **Author-extensible, decidable.** The four predicate kinds cover the KP's
  R-rules without LLM judgement; an author composes new R-rules from them
  without code. Rules that need *judgement* (R-1 "don't resolve the tragic
  irony") are out of scope for the decidable engine — they stay reviewer
  prompts (and could xcap to `thinking.red_team` in a future slice).
- **Severity tiers gate differently.** Critical blocks the gate; medium/low
  surface. This mirrors §10.2 exactly: Critical = strike, Medium/Low =
  reviewer-check.
- **Motif-budget is just a per-scene-budget rule** the engine ships built-in,
  plus a tracker so the foreshadowing spine is queryable. The KP's "max 1
  Genesis-echo per scene" IS a `per-scene-budget` predicate with cap 1.
- **Anchors vs PlantedElement (123).** 123's PlantedElement is the general
  Chekhov's-gun report; 140's Anchor is the *named, recurring* anchor (734
  appears ch2/10/25) with explicit plant→payoff chapters — the KP's tracked
  foreshadowing anchors.

## Open questions

1. Should `run_project_rules` short-circuit on the first critical, or collect
   all findings? **Recommend**: collect all — the author wants the full
   defect list per scene, not first-fail.
2. Rule params schema — freeform dict or typed-per-predicate-kind?
   **Recommend**: freeform dict v1 with documented keys per predicate kind;
   a typed schema is a Slice-2 refinement once the four kinds settle.

## Followup

(Populated when the PR ships.)
