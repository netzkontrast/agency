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

## Schema

```text
# New enums
DEFECT_SEVERITY = {"critical", "medium", "low"}
PREDICATE_KIND  = {"mutual-exclusion", "per-scene-budget",
                   "forbidden-verbatim", "register-forbidden"}

# New nodes
ProjectRule {
  novel:           str
  rule_id:         str   # author-stable handle: "R-5"
  name:            str   # "hot-polarity"
  severity:        str   # ∈ DEFECT_SEVERITY
  predicate_kind:  str   # ∈ PREDICATE_KIND
  params:          dict  # see "Predicate params" below
  rationale:       str
}

Motif {
  novel:               str
  slug:                str   # "rauschen" | "form" | "klick" | "phantom" | "resonanz"
  first_event_chapter: int
  per_scene_cap:       int   # KP default: 1
}

Anchor {
  novel:           str
  name:            str   # "734", "Telefon-Stille", "Silas-Halbsatz", "Waerme-Debut"
  planted_chapter: int
  payoff_chapter:  int   # 0 when still open
}

# New edges
ECHOES_IN : Motif  --→ Scene       (cardinality N:N)
PLANTS    : Anchor --→ Scene       (cardinality 1:N — earliest plant kept)
PAYS_OFF  : Anchor --→ Scene       (cardinality 1:N)
```

## Predicate params (documented keys per kind)

```python
# 1) mutual-exclusion — two term sets that must not co-occur in a scene
{
  "set_a": ["kalt", "ozon", "Stahl", "AEGIS-Hand"],     # csv on disk
  "set_b": ["warm", "Haut", "Atem", "Juna-Tee"],
  "scope": "scene",                                       # "scene" | "paragraph"
  "case_insensitive": True,
}

# 2) per-scene-budget — a tagged element capped per scene
{
  "tag": "genesis-echo",     # what to count
  "cap": 1,                  # how many allowed
  "count_kind": "motif-edge" # "motif-edge" → count ECHOES_IN edges
                             # "substring"  → count substring hits of `terms`
                             # "regex"      → count regex hits of `pattern`
  "terms": ["…"],            # only if count_kind="substring"
  "pattern": "",             # only if count_kind="regex"
}

# 3) forbidden-verbatim — phrases that may not appear literally
{
  "phrases": ["…", "…"],
  "case_insensitive": False,
  "exemptions": [],          # scene_ids allowed to use them
}

# 4) register-forbidden — token classes forbidden in a tagged speaker's lines
{
  "speaker_tag": "AEGIS",         # match dialogue/narration tagged to this speaker
  "forbidden_classes": ["metaphor", "moral-language",
                        "affect-word", "ich-pronoun"],
  "class_terms": {                # decidable lexicons per class
    "metaphor": ["wie ein", "gleichsam"],
    "moral-language": ["sollte", "böse", "gut"],
    "affect-word": ["fühlte", "spürte", "Angst"],
    "ich-pronoun": ["ich", "Ich"],
  },
}
```

## Verb signatures

```python
def register_project_rule(
    novel_id: str,
    rule_id: str,
    name: str,
    severity: str,
    predicate_kind: str,
    params: dict,
    rationale: str = "",
) -> dict:
    """Upsert on (novel_id, rule_id). Validates enums + that params dict
    has the documented keys for the predicate_kind.
    Returns: {rule_node_id, rule_id, was_update: bool}
    """

def list_project_rules(novel_id: str, severity: str = "") -> dict:
    """Returns: {rules: [{rule_id, name, severity, predicate_kind, rationale}…],
                 count_by_severity: {…}}"""

def run_project_rules(scene_id: str) -> dict:
    """Runs EVERY rule for the scene's novel. Collects ALL findings (does NOT
    short-circuit).
    Returns: {
      passed: bool,                     # no `critical` findings
      findings: [{rule_id, severity, message, span: (start, end)|null}…],
      counts: {critical: int, medium: int, low: int},
    }
    """

def project_rule_gate(novel_id: str, block_at: str = "critical") -> dict:
    """Manuscript-wide gate.
    Returns: {
      passed: bool,                     # iff no scene has finding ≥ block_at
      blocking_scenes: [{scene_id, chapter, findings: [...]}…],
      warning_scenes:  [{scene_id, chapter, findings: [...]}…],  # below block_at
      block_at: str,
    }
    """

def record_motif(
    novel_id: str,
    slug: str,
    first_event_chapter: int,
    per_scene_cap: int = 1,
) -> dict:
    """Returns: {motif_id, slug}"""

def record_motif_echo(scene_id: str, motif_slug: str) -> dict:
    """Mints ECHOES_IN. Returns: {edge_id, scene_id, motif_slug, total_echoes_in_scene}"""

def motif_echo_report(novel_id: str) -> dict:
    """Returns: {
      per_scene: [{scene_id, chapter, echo_count, exceeds_cap: bool}…],
      per_motif: [{slug, first_event_chapter, echoes: [{scene_id, chapter}…]}…],
      cap_violations: [{scene_id, chapter, count, cap}…],
    }
    """

def record_anchor(
    novel_id: str,
    name: str,
    planted_chapter: int,
    planted_scene_id: str = "",
) -> dict:
    """Mints Anchor + PLANTS edge when scene supplied.
    Returns: {anchor_id, name}
    """

def pay_off_anchor(anchor_id: str, scene_id: str) -> dict:
    """Mints PAYS_OFF; updates payoff_chapter from scene.chapter.
    Returns: {anchor_id, payoff_chapter}
    """

def anchor_status_report(novel_id: str) -> dict:
    """Returns: {
      planted_unpaid: [{anchor_id, name, planted_chapter}…],
      paid:           [{anchor_id, name, planted_chapter, payoff_chapter, gap_chapters}…],
      summary: {total: int, unpaid: int, paid: int, avg_gap: float},
    }
    """
```

## Predicate evaluator outline

```python
# Pure functions over a scene body + params; the engine ships these four.
def _eval_mutual_exclusion(body: str, params: dict) -> list[dict]:
    """Return findings when set_a ∩ scene-tokens AND set_b ∩ scene-tokens are
    both non-empty. One finding per co-occurrence within scope ("scene" or
    "paragraph" — split body on \\n\\n for paragraph)."""

def _eval_per_scene_budget(scene_id, body, params, ctx) -> list[dict]:
    """count = (ECHOES_IN edges with motif_slug==params.tag) when count_kind
    is "motif-edge", else substring/regex hits. Finding when count > cap."""

def _eval_forbidden_verbatim(body, params) -> list[dict]:
    """One finding per phrase hit (respecting case + exemptions)."""

def _eval_register_forbidden(body, params, ctx) -> list[dict]:
    """Scan speaker_tag-attributed lines for class_terms; one finding per hit."""

_DISPATCH = {
    "mutual-exclusion":  _eval_mutual_exclusion,
    "per-scene-budget":  _eval_per_scene_budget,
    "forbidden-verbatim": _eval_forbidden_verbatim,
    "register-forbidden": _eval_register_forbidden,
}
```

## Test scaffold

```text
tests/test_novel_rulesets_motifs.py  (target ≥ 26 tests)
  test_defect_severity_enum_registered
  test_predicate_kind_enum_registered
  test_register_project_rule_upsert_by_rule_id
  test_register_project_rule_rejects_unknown_predicate_kind
  test_register_project_rule_validates_params_keys
  test_list_project_rules_filtered_by_severity
  test_run_project_rules_collects_all_findings
  test_run_project_rules_does_not_short_circuit_on_critical
  test_run_project_rules_no_rules_returns_passed
  # one happy + one fail per predicate kind:
  test_mutual_exclusion_passes_disjoint_sets
  test_mutual_exclusion_flags_cooccurrence
  test_mutual_exclusion_paragraph_scope
  test_per_scene_budget_passes_under_cap
  test_per_scene_budget_flags_over_cap_motif_edge
  test_per_scene_budget_flags_over_cap_substring
  test_forbidden_verbatim_passes_clean
  test_forbidden_verbatim_flags_phrase
  test_forbidden_verbatim_respects_exemptions
  test_register_forbidden_passes_clean
  test_register_forbidden_flags_metaphor_in_AEGIS_line
  test_project_rule_gate_passes_when_no_critical
  test_project_rule_gate_warns_below_block_at
  test_project_rule_gate_blocks_at_block_at
  test_record_motif_happy_path
  test_record_motif_echo_mints_ECHOES_IN
  test_motif_echo_report_flags_cap_violation
  test_record_anchor_mints_PLANTS_when_scene_supplied
  test_pay_off_anchor_mints_PAYS_OFF_and_updates_payoff_chapter
  test_anchor_status_report_separates_unpaid_and_paid
```

## Fixture (canonical KP R-rules)

```text
R-5  hot-polarity        critical  mutual-exclusion
R-6  one-concept-cap     medium    per-scene-budget(tag=concept, cap=1)
R-7  genesis-echo-cap    medium    per-scene-budget(tag=genesis-echo, cap=1)
R-8  AEGIS-register      critical  register-forbidden(speaker=AEGIS,…)
R-9  no-style-mimicry    critical  forbidden-verbatim(phrases=[…])
R-4  micro-cue-cap       low       per-scene-budget(tag=micro-cue, cap=3)

Motifs:  rauschen / form / klick / phantom / resonanz  (cap=1 each)
Anchors: 734, telefon-stille, silas-halbsatz, waerme-debut
```

## Open questions

1. Should `run_project_rules` short-circuit on the first critical, or collect
   all findings? **Recommend**: collect all — the author wants the full
   defect list per scene, not first-fail.
2. Rule params schema — freeform dict or typed-per-predicate-kind?
   **Recommend**: freeform dict v1 with documented keys per predicate kind
   (see "Predicate params" above); a typed-schema/dataclass refinement is a
   Slice-2 once the four kinds settle.
3. Where does Motif/Anchor recording fit in the prose loop — author calls
   manually, or scene-writer (Spec 130) phase 4 records automatically when
   the body contains a motif's documented signal-word? **Recommend**:
   Spec 130 phase-4 auto-records by signal-word lookup (so the author
   doesn't bookkeep), and `record_motif_echo` stays as an override.

## Followup

(Populated when the PR ships.)
