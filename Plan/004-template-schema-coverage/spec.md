---
spec_id: "004"
slug: "template-schema-coverage"
status: draft
owner: "@agency"
depends_on: ["003"]
affects:
  - agency/templates.py
  - agency/ontology.py
  - agency/capabilities/delegate.py
  - agency/capabilities/jules.py
  - agency/capabilities/develop.py
  - agency/capabilities/plugin.py
  - tests/test_agency.py
source-repos:
  - "https://github.com/netzkontrast/the-agency-system @ 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22"
estimated_jules_sessions: 2
domain: core
wave: 1
---

> **Jules: read `Plan/JULES_PROTOCOL.md` before starting** (if present). Confidence ≥ 0.90,
> TDD Red-Green-Refactor, Evidence pasted under `## Evidence`, Self-Review answered.
> Only modify paths under `affects:`. **Do NOT start coding until the Open Questions
> below are answered** — the source research has an internal count discrepancy (18 vs 13
> vs 8) that must be reconciled with a maintainer ruling, or the wrong set of kinds
> gets covered.

# Spec 004 — Template & Schema Coverage for ALL Artefact Kinds

## Why

The generate/validate loop is the typed spine of the graph: a capability `act`
renders an Artefact from a `Template`, and `Memory.validate_schema`
(`agency/memory.py:144`) checks the recorded node against a `Schema` node's
`required` fields. Today that loop only closes for a minority of artefacts. The
strict required-field schemas live in `REQUIRED` (`agency/templates.py:72`) and
cover exactly **5 kinds**:

```python
REQUIRED = {
    "plugin-manifest":   ["name", "version", "description"],
    "skill-md":          ["name", "description", "body"],
    "command-md":        ["name", "description", "body"],
    "marketplace-entry": ["name", "version", "description", "source"],
    "step-doc":          ["step", "output"],
}
```

`plugin_ontology` registers these (and only these) as the capability's `schemas`
(`agency/capabilities/plugin.py:179`, `schemas=dict(templates.REQUIRED)`), so they
are the only artefact kinds the graph can validate. Every other artefact is
recorded as an opaque dict with no schema, so `validate_schema` cannot guard it —
e.g. the delegation reduction is `record("Artefact", {"kind": "reduction",
"children": children})` (`agency/capabilities/delegate.py:78`) and the Jules
session is `{"kind": "jules-session", "session": ..., "url": ...}`
(`agency/capabilities/jules.py:88`), neither paired with a `Template` or a
`REQUIRED` entry.

The templates-and-schemas research (`research/templates-and-schemas/`) catalogued
the gap and proposes a `REQUIRED.update({...})` plus a set of `string.Template`
constants. **Its counts do not agree with each other** — the spec/FINDINGS claim
"18 kinds, 5 covered, 13 remaining", the schemas-catalogue's `REQUIRED.update`
adds 13 keys, and the spec's prose + `Files` list name only **8** new templates.
This spec carries the concrete additions but **parks the count reconciliation as a
blocking Open Question** (below), because a verification pass against the live code
shows the research is conflating two distinct namespaces (artefact `kind`s vs skill
`produces` slot names). Picking the wrong set covers slots that are never recorded
as artefacts and misses real kinds.

## Verified counts (this spec's audit, do not skip)

Grepping the live tree (`agency/capabilities/*.py`) gives the ground truth the
research approximated:

**A. Artefact `kind` literals actually recorded** (`record("Artefact", {"kind":...})`
or returned as `"artefact": {"kind": ...}`) — **9 distinct**:

| kind | where | schema today? |
|---|---|---|
| `plugin-manifest` | plugin.py:43 | YES |
| `skill-md` | plugin.py:53 | YES |
| `command-md` | plugin.py:59 | YES |
| `marketplace-entry` | plugin.py:65 | YES |
| `step-doc` | plugin.py:74 | YES |
| `authoring` | plugin.py:136,155 (skill `kind`, not an Artefact record) | no |
| `discipline` | develop.py:29… (skill `kind`, not an Artefact record) | no |
| `jules-session` | jules.py:88 | **NO** |
| `reduction` | delegate.py:78 | **NO** |

So among kinds **actually written as Artefact nodes**, only `jules-session` and
`reduction` lack schemas. `authoring`/`discipline` are skill `kind`s
(`SKILL_CREATION_SKILL["kind"] == "authoring"`), never artefact `kind`s.

**B. Skill-phase `produces` slot names** (the 9 distinct `produces` entries the
walker validates per phase): `baseline`, `rationalizations`, `command_md`,
`entry`, `findings`, `lint`, `manifest`, `rationalization_table`, `red_flags`,
`skill_md`, `user_confirmed`. These are **phase output slots, snake_case**, not
artefact kinds — and the research's "remaining 13" is mostly this set, kebab-cased.

**The research's "18" = roughly (A ∪ B) with the two namespaces merged.** That is
the discrepancy. The 13-key `REQUIRED.update` mixes real artefact kinds
(`jules-session`, `reduction`) with phase-slot names that are never recorded as
Artefacts (`baseline`, `findings`, `discipline`, `lint`, `manifest`, `entry`,
`rationalizations`, `rationalization-table`, `red-flags`, `user-confirmed`,
`authoring`). The templates-catalogue then lists **13** numbered templates (items
1–13), while the spec's `Files`/`Done When` mention only **8**. See Open Q1 — this
must be resolved before implementation.

## Done When

- [ ] The exact set of artefact kinds to cover is **agreed with the maintainer**
      (Open Q1) and recorded in this spec before any code lands.
- [ ] For every agreed kind, `agency/templates.py` defines a `string.Template`
      constant (the generate side) AND a `REQUIRED[...]` entry (the validate side),
      so the generate/validate pair is complete.
- [ ] `REQUIRED.update({...})` (the concrete additions, below) is applied to
      `agency/templates.py`, scoped to the agreed set.
- [ ] `plugin_ontology.schemas` (or a dedicated core-schemas owner — Open Q2)
      registers every new `REQUIRED` key so `Ontology.schemas` carries them and
      `Memory.validate_schema` can validate the kinds.
- [ ] The two real uncovered Artefact kinds emit structured, validatable nodes:
      `delegate.join` records a `reduction` with the full required field set
      (`parent_intent`, `children`, `summary`), and `jules.dispatch` records a
      `jules-session` with (`session_id`, `url`, `state`, `history`) — reconciling
      the field-name mismatches noted in Open Q3.
- [ ] A round-trip test instantiates each new `Template` with mock fields, records
      the resulting Artefact, and asserts `Memory.validate_schema` returns `True`;
      a node missing a required field returns `False` (the schema bites).
- [ ] The field-naming discrepancy (snake `produces` slots vs kebab artefact
      `kind`s; `children` as count vs list) is resolved per Open Q3/Q4 and applied
      consistently — no silent guess.
- [ ] All existing tests pass (the 5 currently-covered kinds keep their schemas
      byte-identical).

## Design

### `agency/templates.py` — `REQUIRED.update({...})` additions

This is the catalogue from `research/templates-and-schemas/schemas-catalogue.md`
§1, **scoped per Open Q1**. The full proposed superset (13 keys) is reproduced so
the maintainer can strike rows; the recommended minimum (rows marked ★) covers the
two real uncovered Artefact kinds plus the kinds the skill walker's `produces`
slots map onto if 004 also normalises slots→kinds (Open Q4):

```python
REQUIRED.update({
    "jules-session":          ["session_id", "url", "state", "history"],   # ★ real Artefact kind
    "reduction":              ["parent_intent", "children", "summary"],    # ★ real Artefact kind
    "baseline":               ["workspace", "command", "exit_code", "output"],
    "findings":               ["branch", "base", "issues_found", "summary", "details"],
    "discipline":             ["name", "rules", "checklists"],
    "rationalization-table":  ["target", "rule", "rationalization", "verdict"],
    "red-flags":              ["source", "issues"],
    "user-confirmed":         ["prompt", "response", "timestamp"],
    "authoring":              ["task", "files", "diff"],
    "entry":                  ["key", "value"],
    "lint":                   ["source", "issues"],
    "manifest":               ["components"],
    "rationalizations":       ["items"],
})
```

> WARNING (do not skip): some of these keys are **skill-phase slot names**, not
> artefact kinds anything records. `baseline` collides with the `Workspace`/
> `Baseline` *node* schema (`workspace.py:20`, fields `command`/`passed`/`output`),
> which is a different shape than the proposed `["workspace","command","exit_code",
> "output"]`. `manifest`/`entry`/`lint`/`findings`/`discipline`/`rationalizations`
> are `produces` slots in `develop.py`/`plugin.py` skills, never `record("Artefact",
> {"kind": ...})`. Covering them as artefact schemas only does something IF 004 also
> changes the verbs to emit those kinds (Open Q4). Do not add a schema for a kind no
> code emits without the maintainer agreeing the verb change.

### `agency/templates.py` — new `Template` constants

Carried from `research/templates-and-schemas/templates-catalogue.md` (items 1–13).
The two ★ templates are mandatory; the rest land iff their kinds are in the agreed
set. Representative pair (the rest follow the same `---`-frontmatter shape — see
the catalogue for the full bodies):

```python
from string import Template

JULES_SESSION = Template(                                   # ★ pairs with kind "jules-session"
    "---\nkind: jules-session\nsession-id: $session_id\n"
    "url: $url\nstate: $state\n---\n\n# Session Log\n$history\n")

DELEGATION_REDUCTION = Template(                            # ★ pairs with kind "reduction"
    "---\nkind: reduction\nparent-intent: $parent_intent\n"
    "children: $children\n---\n\n# Reduction Summary\n$summary\n")

BASELINE_REPORT = Template(
    "---\nkind: baseline\nworkspace: $workspace\ncommand: $command\n"
    "exit-code: $exit_code\n---\n\n# Baseline Run\n\n## Output\n```\n$output\n```\n")

REVIEW_FINDINGS = Template(
    "---\nkind: findings\nbranch: $branch\nbase: $base\n"
    "issues-found: $issues_found\n---\n\n# Findings Summary\n$summary\n\n"
    "## Details\n$details\n")
# DISCIPLINE_DEF, RATIONALIZATION_TABLE, RED_FLAGS, USER_CONFIRMATION,
# AUTHORING_RECORD, GENERIC_ENTRY, LINT_REPORT, COMPONENT_MANIFEST,
# RATIONALIZATIONS_LIST — verbatim from templates-catalogue.md items 5–13.
```

### Verb changes for the two real uncovered kinds

**`delegate.join` (`agency/capabilities/delegate.py:78`) — BEFORE:**

```python
red = self.ctx.record("Artefact", {"kind": "reduction", "children": children})
```

**AFTER** (records the full `reduction` schema; note `children` is currently an
**int count**, but the catalogue schema expects a list of child intent IDs — Open
Q3):

```python
red = self.ctx.record("Artefact", {
    "kind": "reduction",
    "parent_intent": self.ctx.intent_id,
    "children": ",".join(child_ids),          # list-of-ids, not the count (Open Q3)
    "summary": f"reduced {children} children: {states}",
})
```

**`jules.dispatch` (`agency/capabilities/jules.py:88`) — BEFORE:**

```python
"artefact": {"kind": "jules-session", "session": sid or "", "url": s.get("url") or ""},
```

**AFTER** (matches `REQUIRED["jules-session"]`; field rename `session`→`session_id`,
adds `state`/`history` — Open Q3):

```python
"artefact": {
    "kind": "jules-session",
    "session_id": sid or "",
    "url": s.get("url") or "",
    "state": s.get("state", "submitted"),
    "history": s.get("history", ""),
},
```

### Registering the schemas

The new `REQUIRED` keys must reach `Ontology.schemas`. `plugin_ontology` already
does `schemas=dict(templates.REQUIRED)` (`plugin.py:179`); since the additions land
in `templates.REQUIRED`, they flow in automatically — but that puts cross-capability
schemas (`jules-session`, `reduction`) under the `plugin` capability's ownership,
which is wrong by the "schemata live with the capability that owns them" rule
(`agency/ontology.py:60-86`). Open Q2: move `jules-session` into the `jules`
capability's `OntologyExtension.schemas` and `reduction` into `delegate`'s, leaving
`templates.REQUIRED` as the plugin-owned set only.

## Files

- **Modify**:
  - `agency/templates.py` — add the agreed `Template` constants and the scoped
    `REQUIRED.update({...})`.
  - `agency/capabilities/delegate.py` — `join` records the full `reduction`
    artefact; add `schemas={"reduction": [...]}` to its `OntologyExtension` (Open Q2).
  - `agency/capabilities/jules.py` — `dispatch` records the full `jules-session`
    artefact; `JulesCapability.ontology = OntologyExtension(schemas={"jules-session":
    [...]})` (it currently has no `ontology` — confirm; `jules.py:72` defines no
    `ontology` attribute, so it inherits the empty `CapabilityBase.ontology`).
  - `agency/capabilities/develop.py`, `agency/capabilities/plugin.py` — ONLY if Open
    Q4 says the `produces`-slot kinds (`findings`, `baseline`, `lint`, `manifest`,
    `entry`, `discipline`, `rationalizations`, `rationalization-table`, `red-flags`,
    `user-confirmed`, `authoring`) become real recorded Artefacts; otherwise leave
    untouched.
  - `agency/ontology.py` — only if Open Q2 chooses to add a core-owned schemas slot
    rather than capability-owned.
  - `tests/test_agency.py` — round-trip generate/validate tests per new kind.
- **Create**: none required (research suggested `tests/test_templates_expansion.py`;
  this repo keeps tests in the single `tests/test_agency.py` — Open Q5).

## Open Questions / Needs Research

1. **Reconcile "18 / 5 / 13" vs the catalogue's 8 vs the verified 2.** (BLOCKING.)
   The research is internally inconsistent: `research/templates-and-schemas/spec.md`
   and `FINDINGS.md` say 18 kinds / 5 covered / 13 remaining; the
   `schemas-catalogue.md` `REQUIRED.update` adds **13** keys; the
   `templates-catalogue.md` lists **13** templates (items 1–13); but `spec.md`'s
   prose and `Files`/`Done When` name only **8** new `Template`s
   (`BASELINE_REPORT`, `REVIEW_FINDINGS`, `JULES_SESSION`, `DELEGATION_REDUCTION`,
   `DISCIPLINE_DEF`, `RATIONALIZATION_TABLE`, `RED_FLAGS`, `USER_CONFIRMATION`).
   **This spec's own grep of the live tree finds only 9 artefact `kind`s recorded,
   of which 2 (`jules-session`, `reduction`) actually lack schemas.** The "remaining
   13" is the research conflating artefact `kind`s with skill-phase `produces` slot
   names (two different namespaces). Maintainer must decide the intended scope:
   - (a) **Minimal/correct**: cover the 2 real uncovered Artefact kinds only.
   - (b) **Slots-become-artefacts**: also change `develop`/`plugin` verbs so every
     `produces` slot is recorded as an Artefact of that kind, then cover all of
     them (the research's intent, but it requires verb changes the research omits).
   - (c) **Research's literal list**: add all 13 `REQUIRED` keys as schemas even for
     kinds nothing records (dead schemas — not recommended).
   Recommend (a) for this wave with (b) as a follow-up spec. **Do not guess.**
2. **Schema ownership.** Should `jules-session` / `reduction` schemas live in the
   `jules` / `delegate` capabilities' `OntologyExtension.schemas` (per the
   "schemata live with the capability that owns them" doctrine, `ontology.py:60`),
   or stay in the plugin-owned `templates.REQUIRED`? Recommend capability-owned;
   needs confirmation because it changes which `affects:` files are touched.
3. **Field-name mismatches between live code and the catalogue.** `jules.dispatch`
   records `session` (catalogue wants `session_id`) and omits `state`/`history`;
   `delegate.join` records `children` as an **int count** (catalogue wants a list of
   child intent IDs) and omits `parent_intent`/`summary`. Renaming/extending these
   touches the verbs' public result shape and any test asserting on them
   (`test_agency.py` delegate/jules tests). Which name wins — the live field or the
   catalogue field? Recommend adopting the catalogue names and adapting the verbs.
4. **snake_case `produces` slots vs kebab-case artefact `kind`s.** (Shared with spec
   003 Open Q6.) `produces` slots are `skill_md`, `command_md`, `user_confirmed`,
   `rationalization_table`, `red_flags`; the catalogue schemas use kebab kinds
   `skill-md`, `command-md`, `user-confirmed`, `rationalization-table`, `red-flags`.
   Is the snake/kebab split intentional (phase-slot namespace ≠ artefact-kind
   namespace) or to be normalised? If 004 takes path (b) in Q1, a slot→kind mapping
   must be defined. One ruling, cited by both specs.
5. **Test location.** Research proposes `tests/test_templates_expansion.py`; the
   repo currently uses one `tests/test_agency.py`. Add a new file or extend the
   existing? (Cosmetic, but `affects:` should be accurate.)
6. **`baseline` schema vs the `Baseline`/`Workspace` node schema collision.**
   `workspace.py:20` already defines a `Baseline` *node* (`["command","passed","output"]`)
   recorded by `workspace.baseline`. The catalogue adds a `baseline` *artefact*
   schema with a different shape (`["workspace","command","exit_code","output"]`).
   These are two different things sharing a lowercase name. If `baseline` is added
   to `REQUIRED`, clarify it is the artefact-kind schema, not the node schema, and
   confirm nothing conflates them (`Ontology.schemas` is keyed separately from
   `Ontology.nodes`, so no hard clash — but the naming is a trap).

## Evidence

- `agency/templates.py:72-78` — `REQUIRED` covers exactly 5 kinds.
- `agency/capabilities/plugin.py:179` — `schemas=dict(templates.REQUIRED)` is the
  only place schemas reach the ontology.
- `agency/capabilities/delegate.py:78` — `reduction` recorded with only `children`
  (an int count), no schema.
- `agency/capabilities/jules.py:88` — `jules-session` artefact with `session`/`url`
  only, no schema, field named `session` not `session_id`.
- `agency/capabilities/workspace.py:45-48` — `Baseline` node schema
  (`command`/`passed`/`output`), distinct from the proposed `baseline` artefact schema.
- `agency/memory.py:144-153` — `validate_schema` reads a `Schema` node's
  comma-joined `required`; the validate side of the loop.
- Grep of `agency/capabilities/*.py`: 9 distinct `"kind": "..."` literals; 9
  distinct `"produces": [...]` slot sets — the two namespaces the research merges.
- `research/templates-and-schemas/spec.md:22-23,40,63` — "18 kinds / 5 covered / 13
  remaining" and the 8-template `Files`/`Done When` list (the internal 8-vs-13
  discrepancy).
- `research/templates-and-schemas/schemas-catalogue.md:10-24` — the 13-key
  `REQUIRED.update`.
- `research/templates-and-schemas/templates-catalogue.md` — 13 numbered templates.
- `research/templates-and-schemas/FINDINGS.md:7-29` — the gap matrix (18 rows) and
  the "13 remaining" claim, plus the residual-risk note that dynamic discovery may
  hide artefacts (corroborates the namespace-conflation finding).
